# Learned spill heuristics

A register-allocation experiment that compares an optimistic classical
graph-coloring heuristic with a learned spill-cost heuristic on generated
three-address code (TAC). The TAC subset supports assignments, arithmetic,
prints, labels, conditional branches, and unconditional jumps, including
back-edges for loops.

## Setup

Use Python 3.10 or newer, then install the dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## React dashboard

The React dashboard presents the multi-seed metrics, seed-level comparisons,
and searchable per-program results. From the repository root:

```powershell
python -m src.export_dashboard_data
cd web
npm install
npm run dev
```

Open the local URL printed by Vite. Running `python -m src.run_benchmarks`
refreshes the dashboard JSON together with the CSV reports.

## Reproduce the experiment

Run these commands from the repository root:

```powershell
python -m src.generate_programs
python -m src.dataset
python -m src.train_model
python -m src.evaluate
```

To generate the varied control-flow patterns and repeat the experiment across
three fixed random seeds (7, 42, and 2026), run:

```powershell
python -m src.run_benchmarks
```

You can pass other seeds with `--seeds`, for example
`python -m src.run_benchmarks --seeds 11 29 101`. This writes the full
per-program results to `results/benchmark_runs.csv`, per-seed means to
`results/benchmark_seed_summary.csv`, cross-seed means and standard deviations
to `results/benchmark_summary.csv`, and grouped model validation scores to
`results/model_validation_by_seed.csv`. Per-seed datasets and models are
reproducible artifacts under the ignored `data/benchmarks/` directory.

The generator creates 240 training programs and 60 separate held-out programs
per seed, using straight-line code, branches, nested branches, short and longer
loops, and programs with repeated variable uses.
Liveness is computed over control-flow successors, including loop back-edges.
The learned model is trained only on the 240 training programs; the allocator
comparison uses only the held-out programs, for 2, 3, and 4 registers. The
classical baseline uses a hand-designed cost directly. The ML model instead
learns to predict the number of load/store pseudo-instructions produced when a
variable is spilled, using degree, live-range length, use frequency, and
definition frequency. Training labels come from running the spill-rewrite pass
on each training variable. The pass assigns each spilled value a memory slot,
inserts pseudo-TAC loads before uses and stores after definitions, and checks
the rewritten program's output against the original with a TAC interpreter.
Per-program results are written to
`results/evaluation.csv`, including spill loads/stores, added TAC instruction
counts, semantic checks, and allocation validity. Allocator timings are
medians of five warmed runs. Training data and the model are reproducible
generated artifacts.

The ML target is the measured static pseudo-TAC rewrite overhead, not a
hand-designed spill-cost formula. Spill rewrites use pseudo-TAC memory
operations: their added instruction counts are a static code-size proxy, not
machine-code size or dynamic spill traffic. This is not a production compiler
and does not measure native execution speed.
