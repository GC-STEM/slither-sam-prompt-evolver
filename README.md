# Slither Sam Prompt Evolver

**Evolutionary prompt optimization for Slither Sam. Uses automated tournaments and fitness scoring to iteratively improve AI prompts that generate stronger game-playing strategies.**

This repository is an experimental companion project for Microsoft's [Slither Slam](https://aka.ms/slither-slam) Hour of AI activity.

Slither Slam introduces artificial intelligence (AI), large language models (LLMs), prompt engineering, AI-assisted code generation, game AI, testing, and debugging through a competitive Snake-style game. Participants use natural-language prompts to generate code for a **SnakeBot** and then test their bot against other game-playing algorithms.

**Slither Sam Prompt Evolver** extends that idea with a new question:

> **Can we use an evolutionary algorithm to improve the prompt itself?**

Instead of manually rewriting the prompt after each match, this project treats the prompt as something that can be **tested, scored, selected, mutated, combined, and improved across generations**.

---

## Project Goals

This project supplements the original Slither Slam activity by demonstrating how several AI and computer science concepts connect:

- **Prompt engineering** — Small changes to instructions can produce different generated programs.
- **Automated testing** — Generated SnakeBots can be evaluated repeatedly under consistent conditions.
- **Fitness functions** — Performance can be translated into a numerical score.
- **Evolutionary algorithms** — Better-performing prompts can be selected and modified to create a new generation.
- **Optimization** — Repeated testing can search a large space of possible prompts.
- **Generalization** — A prompt should perform well against multiple opponents rather than exploiting one specific opponent.
- **Overfitting** — Optimizing too closely against a fixed test environment can produce solutions that fail under different conditions.
- **Reproducibility** — AI-generated outputs and game simulations may vary, so meaningful evaluation requires repeated trials and controlled experiments.

The objective is not simply to produce the strongest possible SnakeBot. The project uses a game as a small, visible environment for exploring how **AI-generated software can be evaluated and iteratively improved**.

---

## How It Works

At a high level, the experiment follows this cycle:

```text
Population of prompts
        │
        ▼
Large Language Model
        │
        ▼
Generated SnakeBots
        │
        ▼
Automated tournaments
        │
        ▼
Performance measurements
        │
        ▼
Fitness scores
        │
        ▼
Select stronger prompts
        │
        ├───────────────┐
        ▼               ▼
    Mutation        Crossover
        │               │
        └───────┬───────┘
                ▼
       Next generation
                │
                └──────► Repeat
```

The important experimental constraint is that the **prompt changes while the evaluation system remains controlled**.

A candidate prompt is sent to the same LLM under the same experimental conditions. The generated SnakeBot is then tested through repeated matches against the Slither Slam opponents.

Performance determines which prompts are more likely to contribute to the next generation.

---

## Prompt Evolution

The initial population may contain a baseline Slither Slam prompt plus several variations.

After each generation, the system can create new prompts using operations analogous to biological evolution.

### Selection

Prompts that generate stronger SnakeBots receive higher fitness scores and are more likely to continue into the next generation.

### Mutation

A prompt can be changed slightly by:

- adding or removing instructions,
- changing priorities,
- clarifying ambiguous instructions,
- reorganizing constraints,
- emphasizing defensive or offensive behavior, or
- changing how the generated program should reason about the game state.

### Crossover

Useful instructions from two successful prompts can be combined to create a new candidate prompt.

For example:

```text
Parent A
├── Strong collision-avoidance instructions
└── Weak food-selection strategy

Parent B
├── Weak collision-avoidance instructions
└── Strong food-selection strategy

              ↓

Child Prompt
├── Strong collision-avoidance instructions
└── Strong food-selection instructions
```

The resulting prompt must still be tested. Combining two successful prompts does **not** guarantee a better result.

---

## Fitness Function

A fitness function converts tournament performance into a score that the evolutionary algorithm can optimize.

An initial fitness function for this project is:

```text
fitness =
    (0.70 × overall_win_rate)
    +
    (0.30 × worst_opponent_win_rate)
```

The **overall win rate** rewards generally strong performance.

The **worst-opponent win rate** discourages the evolutionary process from producing a strategy that dominates several opponents while consistently failing against another.

For example:

```text
Prompt A

Opponent 1: 92%
Opponent 2: 88%
Opponent 3: 90%
Opponent 4: 20%

Overall win rate:        72.5%
Worst-opponent win rate: 20.0%

Fitness:
(0.70 × 0.725) + (0.30 × 0.20)
= 0.5675
```

The exact scoring system is experimental and may change as the project develops.

---

## Avoiding Overfitting

Winning the training tournament does not necessarily mean that a prompt has discovered a generally effective strategy.

An evolutionary system may eventually exploit:

- predictable opponent behavior,
- fixed starting conditions,
- repeated random seeds,
- characteristics of the scoring system, or
- unintended properties of the game engine.

For that reason, the project should separate **optimization matches** from additional evaluation conditions whenever practical.

Potential approaches include:

- randomized starting conditions,
- multiple tournament runs,
- unseen random seeds,
- withheld evaluation matches, and
- testing against opponents or configurations not used directly during optimization.

The goal is to evolve prompts that produce **robust strategies**, not prompts that memorize one tournament.

---

## What Are We Actually Optimizing?

This distinction is important.

We are **not directly evolving the SnakeBot source code**.

We are evolving the **natural-language prompt used to ask an LLM to generate the SnakeBot**.

```text
Prompt
  │
  ▼
LLM
  │
  ▼
Program
  │
  ▼
Game behavior
  │
  ▼
Measured performance
```

The fitness signal therefore travels indirectly from game performance back to natural-language instructions.

This creates an interesting optimization problem because a prompt does not directly specify every action the SnakeBot takes. Instead, it influences another AI system that generates the program that controls those actions.

---

## What Should We Look For?

The final winning prompt may be less interesting than **how the prompts change during evolution**.

As generations improve, we can examine whether successful prompts become:

- more specific,
- more structured,
- more defensive,
- more strategic,
- more explicit about planning,
- better at describing priorities,
- more effective at using the available game API, or
- better at balancing competing objectives.

We can also look for unexpected behavior.

For example:

> Does evolution produce a long and detailed prompt, or does it eventually discover that a shorter prompt works better?

That is an empirical question. We should let the experiment answer it.

---

## Hour of AI Extension

This repository is intended as a supplement to an **Hour of AI session in December 2026**.

Participants should first experience the original Slither Slam activity so they understand the connection between a prompt, generated code, and SnakeBot behavior.

The extension then changes the perspective:

```text
Original Slither Slam

Human
  ↓
writes prompt
  ↓
LLM generates code
  ↓
SnakeBot competes
  ↓
Human evaluates result
  ↓
Human revises prompt
```

This project explores:

```text
Slither Sam Prompt Evolver

Evolutionary system
  ↓
creates prompts
  ↓
LLM generates code
  ↓
SnakeBots compete
  ↓
software measures results
  ↓
fitness function evaluates prompts
  ↓
system creates next generation
```

The same basic prompt-engineering loop remains, but part of the iterative improvement process becomes automated.

---

## Questions to Explore

As you experiment with the project, consider questions such as:

1. Does evolutionary optimization consistently outperform manual prompt engineering?
2. How many generations are required before improvement begins to level off?
3. Which types of prompt mutations are most useful?
4. Do successful prompts become longer or shorter?
5. Do independently evolved populations discover similar strategies?
6. Does a prompt optimized for one LLM work well with another LLM?
7. Does the best-performing prompt still perform well against previously unseen conditions?
8. Can the evolutionary process discover useful instructions that a human prompt engineer did not consider?
9. How much variation comes from the prompt versus the nondeterministic behavior of the LLM?
10. What does "best prompt" actually mean when different generated programs can result from the same prompt?

These questions turn a game tournament into a small experiment in **AI evaluation, optimization, and software engineering**.

---

## Project Status

> [!IMPORTANT]
> **This repository is experimental and under active development.**

The initial goal is to create a reproducible pipeline that can:

1. maintain a population of candidate prompts,
2. generate SnakeBot implementations from those prompts,
3. run automated Slither Slam matches,
4. record tournament results,
5. calculate fitness scores,
6. select successful prompts,
7. generate a new population through mutation and crossover, and
8. repeat the process for multiple generations.

The design, scoring model, experiment parameters, and repository structure may change as we learn from early experiments.

---

## Original Slither Slam Activity

Before using this extension, explore the original Microsoft activity:

- **Student activity:** [Slither Slam — VS Code for Education](https://aka.ms/slither-slam)
- **Educator resources:** [Slither Slam Educator Resources](https://aka.ms/slither-slam-educator)

Slither Slam is designed as an introductory AI and prompt-engineering experience in which learners generate a SnakeBot and compete against other AI-controlled snakes.

This repository builds on those ideas for educational experimentation. It is not a replacement for the original activity.

---

## Responsible Use

AI-generated code should be treated as **unverified code**.

Generated solutions may:

- contain logical errors,
- misunderstand the game API,
- violate intended constraints,
- perform differently across runs, or
- appear successful because of weaknesses in the evaluation process.

Tournament success is evidence of performance under the tested conditions—not proof that the generated program is correct, optimal, safe, or generally intelligent.

Human review, testing, and critical evaluation remain essential parts of the experiment.

---

## Contributing

This project is currently being developed as an educational experiment.

Contributions, experiments, alternative fitness functions, evaluation methods, and reproducibility improvements are welcome as the project matures.

When proposing changes, try to preserve an important principle of the experiment:

> **Change the prompt. Measure the result.**

Changes to the game engine, opponents, scoring system, model configuration, or evaluation environment should be clearly identified because they can affect comparisons between prompt generations.

---

## License

Licensing information for this repository will be documented separately.

Slither Slam and any Microsoft source code, assets, or instructional materials incorporated into or referenced by this project remain subject to their respective licenses and terms.

---

## Acknowledgements

This project would not exist without **Microsoft's Hour of AI and Visual Studio Code for Education teams**, whose Slither Slam activity provides the game, learning experience, and inspiration for this experiment.

Special thanks to **Ben Villalobos**, creator of Slither Slam, for developing an approachable and engaging activity that connects artificial intelligence, prompt engineering, code generation, game AI, testing, and debugging.

**Slither Sam Prompt Evolver is an independent educational extension of the Slither Slam activity and is not an official Microsoft project.**
