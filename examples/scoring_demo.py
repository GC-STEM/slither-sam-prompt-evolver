"""Verify the design arithmetic fixture; no actual game results are claimed."""

import json
from pathlib import Path

from slither_evolver.config import load_config
from slither_evolver.scoring import load_results, score_results


def main():
    directory = Path(__file__).resolve().parents[1] / "fixtures" / "scoring"
    config = load_config(directory / "design_example.config.json")
    result = score_results(config, load_results(directory / "design_example.results.json"))
    expected = json.loads((directory / "design_example.expected.json").read_text(encoding="utf-8"))
    actual = {
        "provenance": result.provenance.kind,
        **vars(result.counts),
        "per_opponent_wins": [opponent.counts.wins for opponent in result.opponents],
        "per_opponent_denominator": result.opponents[0].counts.scheduled_slots,
        "overall_effective_win_rate": result.overall_effective_win_rate,
        "overall_effective_win_rate_fraction": result.overall_effective_win_rate_fraction,
        "worst_opponent_effective_win_rate": result.worst_opponent_effective_win_rate,
        "worst_opponent_effective_win_rate_fraction": result.worst_opponent_effective_win_rate_fraction,
        "fitness": result.fitness,
        "fitness_fraction": result.fitness_fraction,
    }
    for key, value in expected.items():
        if actual[key] != value:
            raise ValueError(f"Synthetic fixture expectation failed: {key}")
    print("Synthetic scoring demo: overall=0.725; worst=0.2; fitness=0.5675 (227/400).")
    print("200 declared exposures; no provider requests, bot execution, or actual games.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
