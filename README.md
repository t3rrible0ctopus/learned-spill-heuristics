# Learned spill heuristics

A small compiler register-allocation experiment that compares a classical
graph-coloring heuristic with a learned spill-cost heuristic on three-address
code (TAC) programs.

## Setup

Use Python 3.10 or newer, then install the dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Reproduce the experiment

Run these commands from the repository root:

```powershell
python -m src.generate_programs
python -m src.dataset
python -m src.train_model
python -m src.evaluate
```

The evaluation compares both allocators for 2, 3, and 4 registers across 100
generated programs. It writes the per-program measurements to
`results/evaluation.csv` and prints average spill counts, runtimes, and
allocation validity. Generated training data is kept out of version control;
the TAC corpus and evaluation table are checked in.

The learned score is trained against a hand-designed spill-cost formula, so
this experiment measures whether the model reproduces that heuristic. It does
not claim to measure runtime or code-size improvements for compiled programs.
