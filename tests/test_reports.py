"""Recalculation, cross-format, incomplete-evidence, and export boundary checks."""

from contextlib import redirect_stderr, redirect_stdout
import copy
import csv
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from slither_evolver.__main__ import main
from slither_evolver.config import load_config
from slither_evolver.reports import ReportError, build_report, export_report, verify_report
from slither_evolver.scoring import configuration_hash, load_results, slot_id

FIXTURES = Path(__file__).resolve().parents[1] / 'fixtures/reporting'


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.config = load_config(FIXTURES / 'comparison.config.json')
        self.bundles = [load_results(FIXTURES / f'{phase}-{role}.results.json')
                        for phase in ('optimization', 'holdout') for role in ('baseline', 'selected')]
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.output = Path(self.temporary.name) / 'report'

    def build(self, bundles=None, **kwargs):
        return build_report(self.config, self.bundles if bundles is None else bundles,
                            baseline_id=kwargs.get('baseline_id', 'baseline'),
                            selected_id=kwargs.get('selected_id', 'selected'))

    def export(self, bundles=None):
        return export_report(self.output, self.config, self.bundles if bundles is None else bundles,
                             baseline_id='baseline', selected_id='selected')

    def csv(self, name):
        with (self.output / name).open(newline='', encoding='utf-8') as stream:
            return list(csv.DictReader(stream))

    def receipt(self):
        # Rehash altered files to ensure verification does more than compare receipts.
        files = sorted(p for p in self.output.rglob('*') if p.is_file() and p.name != 'files.sha256')
        (self.output / 'files.sha256').write_text(''.join(
            hashlib.sha256(p.read_bytes()).hexdigest() + '  ' + p.relative_to(self.output).as_posix() + '\n'
            for p in files), encoding='utf-8')

    def reidentify(self, bundle, identity=None, prompt_hash=None):
        if identity is not None:
            bundle['prompt_id'] = identity
        if prompt_hash is not None:
            bundle['prompt_hash'] = prompt_hash
        samples = {s['sample_id']: s for s in bundle['samples']}
        for r in bundle['results']:
            r['slot_id'] = slot_id(configuration_hash(self.config), bundle['prompt_id'], bundle['prompt_hash'],
                                   bundle['phase'], r['sample_id'], samples[r['sample_id']]['source_hash'],
                                   r['opponent_id'], r['seed'])

    def test_handwritten_comparison_oracle(self):
        expected = json.loads((FIXTURES / 'comparison.expected.json').read_text())
        report = self.build()
        self.assertEqual(report['status'], 'complete')
        for entry in report['entries']:
            key = f"{entry['phase']}-{entry['prompt_id']}"
            self.assertEqual(entry['score']['fitness_fraction'], expected['fitness_fractions'][key])
            self.assertEqual(entry['counts']['scheduled_slots'], expected['scheduled_slots'][entry['phase']])
        self.assertEqual([r['fitness_delta_fraction'] for r in report['comparisons']], ['11/40', '7/80'])

    def test_formats_agree_and_recalculate(self):
        self.export()
        result = verify_report(self.output)
        self.assertEqual(result, {'run_id': self.config.run_id, 'status': 'complete', 'provenance': 'synthetic'})
        report = json.loads((self.output / 'report.json').read_text())
        rows = self.csv('summary.csv')
        for entry, row in zip(report['entries'], rows):
            self.assertEqual(row['fitness_fraction'], entry['score']['fitness_fraction'])
            self.assertEqual(int(row['wins']), entry['counts']['wins'])
        self.assertEqual([r['fitness_delta_fraction'] for r in self.csv('comparisons.csv')], ['11/40', '7/80'])
        self.assertEqual(len(self.csv('slots.csv')), 40)
        self.assertEqual(len(self.csv('opponents.csv')), 8)
        md = (self.output / 'report.md').read_text()
        self.assertIn('SYNTHETIC FIXTURE', md)
        self.assertIn('11/40', md)
        self.assertIn('7/80', md)
        self.assertIn('sample-0', md)
        self.assertIn('not actual played games', md)

    def test_missing_slot_has_no_final_score_or_rate(self):
        self.bundles[1]['results'].pop()
        self.export()
        report = self.build()
        entry = report['entries'][1]
        self.assertIsNone(entry['score'])
        self.assertEqual(entry['blockers']['missing_slots'], 1)
        self.assertEqual(report['comparisons'][0]['status'], 'unavailable')
        self.assertIsNone(report['comparisons'][0]['fitness_delta'])
        self.assertEqual(self.csv('summary.csv')[1]['fitness'], '')
        self.assertEqual(self.csv('opponents.csv')[2]['effective_win_rate'], '')
        self.assertEqual(verify_report(self.output)['status'], 'partial')

    def test_missing_phase_is_explicit_without_fabricating_slots(self):
        report = self.build(self.bundles[:2])
        self.assertEqual(report['status'], 'partial')
        self.assertEqual(report['missing_evidence'], [{'phase':'holdout','prompt_id':'baseline'},
                                                     {'phase':'holdout','prompt_id':'selected'}])
        self.assertEqual(report['comparisons'][0]['fitness_delta_fraction'], '11/40')
        self.assertIsNone(report['comparisons'][1]['fitness_delta_fraction'])
        self.assertEqual(len(report['entries']), 2)

    def test_missing_role_makes_comparison_unavailable(self):
        report = self.build([self.bundles[0]])
        self.assertEqual(len(report['missing_evidence']), 3)
        self.assertTrue(all(r['status'] == 'unavailable' for r in report['comparisons']))

    def test_infrastructure_and_interruptions_are_blockers(self):
        for status,cause in [('infrastructure_fault','runner'),('interrupted','operator_interrupt')]:
            with self.subTest(status=status):
                bundles = copy.deepcopy(self.bundles)
                bundles[0]['results'][0].update(status=status,outcome=None,cause=cause,reason='Fixture stop')
                report = self.build(bundles)
                self.assertEqual(report['status'], 'partial')
                self.assertIsNone(report['entries'][0]['score'])
                self.assertEqual(report['entries'][0]['counts']['wins'], 5)

    def test_bot_fault_is_loss_and_keeps_score_complete(self):
        self.bundles[0]['results'][0].update(status='bot_fault',outcome='loss',cause='decision_timeout',reason='Synthetic bot timeout')
        entry = self.build()['entries'][0]
        self.assertEqual(entry['status'], 'complete')
        self.assertEqual(entry['counts']['bot_faults'], 1)
        self.assertEqual(entry['counts']['played_matches'], 12)
        self.assertEqual(entry['counts']['wins'], 5)

    def test_invalid_generation_is_not_a_played_match(self):
        bundle = self.bundles[0]
        sample = bundle['samples'][0]
        sample.update(generation_status='invalid',source_hash=None,reason='Synthetic generation failure')
        for r in bundle['results']:
            if r['sample_id'] == sample['sample_id']:
                r.update(status='invalid_generation',outcome=None,cause='generation_contract',reason='Synthetic generation failure')
        self.reidentify(bundle)
        self.export()
        entry = self.build()['entries'][0]
        self.assertEqual(entry['status'], 'complete')
        self.assertEqual(entry['counts']['synthetic_failures'], 6)
        self.assertEqual(entry['counts']['played_matches'], 6)
        self.assertEqual(entry['counts']['scheduled_slots'], 12)
        self.assertEqual(entry['invalid_samples'], 1)
        self.assertEqual(verify_report(self.output)['status'], 'complete')

    def test_missing_samples_counted_in_partial_report(self):
        bundle = self.bundles[0]
        sample = bundle['samples'].pop()
        bundle['results'] = [r for r in bundle['results'] if r['sample_id'] != sample['sample_id']]
        entry = self.build()['entries'][0]
        self.assertEqual(entry['blockers']['missing_samples'], 1)
        self.assertEqual(entry['blockers']['missing_slots'], 6)
        self.assertIsNone(entry['score'])

    def test_bad_schedules_are_rejected_instead_of_partial(self):
        for mutate in [lambda b: b['results'].append(copy.deepcopy(b['results'][0])),
                       lambda b: b.update(configuration_hash='f'*64),
                       lambda b: b['results'][0].update(outcome='invented')]:
            with self.subTest(mutate=mutate):
                bundles = copy.deepcopy(self.bundles)
                mutate(bundles[0])
                with self.assertRaises(ReportError):
                    self.build(bundles)

    def test_frozen_baseline_hash_is_enforced(self):
        self.reidentify(self.bundles[0],prompt_hash='f'*64)
        with self.assertRaisesRegex(ReportError, 'frozen baseline'):
            self.build()

    def test_changed_strategy_between_phases_is_rejected(self):
        self.reidentify(self.bundles[3],prompt_hash='f'*64)
        with self.assertRaisesRegex(ReportError, 'changes between phases'):
            self.build()

    def test_duplicate_and_unrequested_bundles_are_rejected(self):
        with self.assertRaisesRegex(ReportError, 'duplicate'):
            self.build([self.bundles[0],self.bundles[0]])
        self.reidentify(self.bundles[1],identity='other')
        with self.assertRaisesRegex(ReportError, 'requested'):
            self.build()

    def test_no_bundles_or_too_many_rejected(self):
        for bundles in ([],self.bundles+[self.bundles[0]]):
            with self.assertRaises(ReportError):
                self.build(bundles)

    def test_mixed_provenance_rejected(self):
        self.bundles[0]['provenance']['kind']='manual'
        with self.assertRaisesRegex(ReportError, 'provenance'):
            self.build()

    def test_manual_and_automated_provenance_retained(self):
        for kind in ('manual','automated'):
            for b in self.bundles:
                b['provenance']['kind']=kind
            report = self.build()
            self.assertEqual(report['provenance_kind'],kind)
            self.assertIn('declarations',report['limitations'][1])

    def test_shared_baseline_selection_counted_once(self):
        report = self.build([self.bundles[0],self.bundles[2]],selected_id='baseline')
        self.assertEqual(len(report['entries']),2)
        self.assertEqual(report['status'],'complete')
        self.assertTrue(report['same_strategy_hash'])
        self.assertTrue(all(r['fitness_delta_fraction']=='0/1' and r['shared_prompt_identity']
                            for r in report['comparisons']))

    def test_distinct_ids_with_same_strategy_are_explicit(self):
        for b in (self.bundles[1],self.bundles[3]):
            self.reidentify(b,prompt_hash=self.config.fixed_context.baseline_prompt_hash)
        self.assertTrue(self.build()['same_strategy_hash'])

    def test_report_detached_and_inputs_unchanged(self):
        before = copy.deepcopy(self.bundles)
        report = self.build()
        report['entries'][0]['samples'][0]['reason']='Edited returned report'
        self.assertEqual(self.bundles,before)
        self.assertIsNone(self.build()['entries'][0]['samples'][0]['reason'])

    def test_input_order_does_not_change_export(self):
        self.export()
        second = Path(self.temporary.name)/'reversed'
        export_report(second,self.config,list(reversed(self.bundles)),baseline_id='baseline',selected_id='selected')
        self.assertEqual((self.output/'files.sha256').read_bytes(),(second/'files.sha256').read_bytes())

    def test_existing_output_preserved(self):
        self.export()
        before = (self.output/'files.sha256').read_bytes()
        with self.assertRaisesRegex(ReportError,'already exists'):
            self.export()
        self.assertEqual((self.output/'files.sha256').read_bytes(),before)

    def test_stale_lock_preserved_for_inspection(self):
        lock = self.output.parent/'.report.report-lock'
        lock.mkdir()
        with self.assertRaisesRegex(ReportError,'lock exists'):
            self.export()
        self.assertTrue(lock.is_dir())
        self.assertFalse(self.output.exists())

    def test_write_or_publish_failure_leaves_no_partial_output(self):
        for function in ('os.fsync','os.rename'):
            with self.subTest(function=function):
                with patch('slither_evolver.reports.'+function,side_effect=OSError('Synthetic failure')):
                    with self.assertRaises(ReportError):
                        self.export()
                self.assertFalse(self.output.exists())
                self.assertEqual(list(self.output.parent.iterdir()),[])

    def test_secret_email_and_sensitive_field_gate_before_writes(self):
        for value in ('SYNTHETIC_SECRET_DO_NOT_EXPORT','ghp_'+'a'*24,'Bearer '+'a'*16,
                      'api_key=abcdefghi','student@example.test'):
            with self.subTest(value=value):
                self.bundles[0]['provenance']['description']=value
                with self.assertRaises(ReportError) as error:
                    self.export()
                self.assertNotIn(value,str(error.exception))
                self.assertFalse(self.output.exists())
        self.bundles[0]['provenance']['description']='Fixture note'
        self.bundles[0]['credentials']='abcdefghi'
        with self.assertRaisesRegex(ReportError,'field'):
            self.export()

    def test_markdown_notes_are_inert(self):
        self.bundles[0]['provenance']['description']="Operator's note: <script>alert(1)</script> [click](https://example.test) ![image](url) |\n# title"
        self.export()
        md = (self.output/'report.md').read_text()
        self.assertNotIn('<script>',md)
        self.assertIn('&lt;script&gt;',md)
        self.assertIn("Operator's note",md)
        self.assertIn('\\[click\\]\\(https://example.test\\)',md)
        self.assertIn('\\|',md)
        self.assertIn('\\# title',md)
        verify_report(self.output)

    def test_csv_formula_reason_escaped_archive_unchanged(self):
        for value in ('=HYPERLINK("https://example.test")','  +1+1','-1+1','@SUM(1)','\tformula'):
            with self.subTest(value=value):
                self.bundles[0]['results'][0].update(status='bot_fault',outcome='loss',cause='exception',reason=value)
                out = self.output.parent / ('formula-'+str(len(list(self.output.parent.iterdir()))))
                export_report(out,self.config,self.bundles,baseline_id='baseline',selected_id='selected')
                with (out/'slots.csv').open(newline='') as stream:
                    reasons=[r['reason'] for r in csv.DictReader(stream)]
                self.assertIn("'"+value,reasons)
                saved=load_results(out/'evidence/optimization-baseline.results.json')
                self.assertEqual(saved['results'][0]['reason'],value)
                verify_report(out)

    def test_negative_comparison_remains_machine_numeric(self):
        for r in self.bundles[1]['results']:
            r['outcome']='loss'
        self.export()
        row=self.csv('comparisons.csv')[0]
        self.assertEqual(row['fitness_delta_fraction'],'-9/20')
        self.assertEqual(float(row['fitness_delta']),-0.45)

    def test_changed_deleted_and_extra_files_rejected(self):
        self.export()
        path=self.output/'summary.csv'
        original=path.read_bytes()
        path.write_bytes(original+b'changed\n')
        with self.assertRaisesRegex(ReportError,'hash mismatch'): verify_report(self.output)
        path.unlink()
        with self.assertRaises(ReportError): verify_report(self.output)
        path.write_bytes(original)
        (self.output/'extra.txt').write_text('extra')
        with self.assertRaisesRegex(ReportError,'unexpected'): verify_report(self.output)

    def test_rehashed_derived_fitness_and_csv_tampering_rejected(self):
        self.export()
        path=self.output/'report.json'
        original=path.read_bytes()
        report=json.loads(original)
        report['entries'][0]['score']['fitness']=1
        path.write_text(json.dumps(report))
        self.receipt()
        with self.assertRaisesRegex(ReportError,'derived values'): verify_report(self.output)
        path.write_bytes(original)
        report=json.loads(original)
        report['entries'][0]['counts']['scheduled_slots']=6
        path.write_text(json.dumps(report))
        self.receipt()
        with self.assertRaisesRegex(ReportError,'derived values'): verify_report(self.output)
        path.write_bytes(original)
        path=self.output/'summary.csv'
        path.write_text(path.read_text().replace('9/20','1/1'))
        self.receipt()
        with self.assertRaisesRegex(ReportError,'formats disagree'): verify_report(self.output)

    def test_rehashed_suppressed_loss_cannot_match_saved_report(self):
        self.export()
        path=self.output/'evidence/optimization-baseline.results.json'
        evidence=load_results(path)
        index=next(i for i,r in enumerate(evidence['results']) if r['outcome']=='loss')
        evidence['results'].pop(index)
        path.write_text(json.dumps(evidence))
        self.receipt()
        with self.assertRaisesRegex(ReportError,'derived values'): verify_report(self.output)

    def test_manifest_traversal_duplicate_and_oversized_rejected(self):
        self.export()
        path=self.output/'files.sha256'
        original=path.read_text()
        for bad in ('0'*64+'  ../outside\n',original+original.splitlines()[0]+'\n','x'*8193):
            path.write_text(bad)
            with self.assertRaises(ReportError): verify_report(self.output)

    def test_root_file_and_directory_links_rejected(self):
        self.export()
        linked=self.output.parent/'linked'
        linked.symlink_to(self.output,target_is_directory=True)
        with self.assertRaises(ReportError): verify_report(linked)
        path=self.output/'report.md'
        external=self.output.parent/'outside.md'
        path.rename(external)
        path.symlink_to(external)
        with self.assertRaises(ReportError): verify_report(self.output)
        path.unlink(); external.rename(path)
        directory=self.output/'evidence'
        external=self.output.parent/'outside-evidence'
        directory.rename(external); directory.symlink_to(external,target_is_directory=True)
        with self.assertRaises(ReportError): verify_report(self.output)

    def test_unexpected_empty_directory_rejected(self):
        self.export()
        (self.output/'unexpected').mkdir()
        with self.assertRaisesRegex(ReportError,'unexpected'): verify_report(self.output)

    def test_no_network_credentials_or_source_execution(self):
        with patch('socket.socket',side_effect=AssertionError('network')), \
             patch('os.getenv',side_effect=AssertionError('credentials')), \
             patch('subprocess.run',side_effect=AssertionError('execution')):
            self.export()
            verify_report(self.output)

    def test_cli_complete_partial_verify_and_errors(self):
        args=['report','--config',str(FIXTURES/'comparison.config.json'),'--baseline','baseline',
              '--selected','selected','--output',str(self.output)]
        for phase in ('optimization','holdout'):
            for role in ('baseline','selected'):
                args += ['--results',str(FIXTURES/f'{phase}-{role}.results.json')]
        stdout,stderr=io.StringIO(),io.StringIO()
        with redirect_stdout(stdout),redirect_stderr(stderr):
            self.assertEqual(main(args),0)
            self.assertEqual(main(['verify-report','--report',str(self.output)]),0)
            self.assertEqual(main(args),4)
        self.assertIn('complete declared evidence',stdout.getvalue())
        self.assertIn('already exists',stderr.getvalue())
        partial=self.output.parent/'partial.json'
        self.bundles[0]['results'].pop()
        partial.write_text(json.dumps(self.bundles[0]))
        args=args[:9]+['--results',str(partial)]
        args[8]=str(self.output.parent/'partial-report')
        with redirect_stdout(io.StringIO()) as stdout,redirect_stderr(io.StringIO()):
            self.assertEqual(main(args),0)
            self.assertIn('partial declared evidence',stdout.getvalue())
            self.assertEqual(main(['score','--config',str(FIXTURES/'comparison.config.json'),
                                   '--results',str(partial)]),5)


if __name__ == '__main__':
    unittest.main()
