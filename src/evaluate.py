import os
import statistics
import time
import argparse
import joblib
import pandas as pd

from src.tac_parser import parse_file
from src.liveness import analyze_liveness
from src.interference import build_interference
from src.features import extract_features
from src.classical_allocator import allocate_registers
from src.ml_allocator import allocate_ml
from src.validate_allocator import validate_allocation
from src.spill_rewrite import rewrite_spills, run_tac


def evaluate(model_file="models/spill_cost_model.pkl",
             test_dir="data/generated/test",
             output_file="results/evaluation.csv", seed=42):
    model = joblib.load(model_file)
    results = []
    timing_repeats = 5
    checked_programs = 0

    programs = sorted(
        os.path.join(test_dir, name)
        for name in os.listdir(test_dir)
        if name.endswith(".tac")
    )

    for program in programs:
        instructions = parse_file(program)

        _, _, _, live_out = analyze_liveness(instructions)
        graph = build_interference(instructions, live_out)
        features = extract_features(instructions, graph)
        original_output = run_tac(instructions)
        checked_programs += 1

        for k in [2, 3, 4]:
            # Warm up prediction before timing, then use the median of repeated
            # runs to reduce noise from first-call setup and OS scheduling.
            allocate_registers(graph, k, features)
            allocate_ml(graph, features, model, k)

            classical_runs = []
            ml_runs = []
            classical_registers, classical_spills = None, None
            ml_registers, ml_spills = None, None
            for _ in range(timing_repeats):
                start = time.perf_counter()
                classical_registers, classical_spills = allocate_registers(
                    graph, k, features
                )
                classical_runs.append(time.perf_counter() - start)

                start = time.perf_counter()
                ml_registers, ml_spills = allocate_ml(
                    graph, features, model, k
                )
                ml_runs.append(time.perf_counter() - start)

            classical_time = statistics.median(classical_runs)

            classical_valid = validate_allocation(
                graph, classical_registers, classical_spills
            )

            ml_time = statistics.median(ml_runs)

            ml_valid = validate_allocation(
                graph, ml_registers, ml_spills
            )

            classical_rewrite, classical_loads, classical_stores = rewrite_spills(
                instructions, classical_spills
            )
            ml_rewrite, ml_loads, ml_stores = rewrite_spills(
                instructions, ml_spills
            )
            classical_rewrite_valid = run_tac(classical_rewrite) == original_output
            ml_rewrite_valid = run_tac(ml_rewrite) == original_output

            results.append({
                "Seed": seed,
                "Program": os.path.basename(program),
                "Registers": k,
                "Classical Spills": len(classical_spills),
                "ML Spills": len(ml_spills),
                "Classical Valid": classical_valid,
                "ML Valid": ml_valid,
                "Classical Spill Loads": classical_loads,
                "Classical Spill Stores": classical_stores,
                "Classical Rewritten TAC Instructions": len(classical_rewrite),
                "Classical Added TAC Instructions": len(classical_rewrite) - len(instructions),
                "Classical Rewrite Semantics Valid": classical_rewrite_valid,
                "ML Spill Loads": ml_loads,
                "ML Spill Stores": ml_stores,
                "ML Rewritten TAC Instructions": len(ml_rewrite),
                "ML Added TAC Instructions": len(ml_rewrite) - len(instructions),
                "ML Rewrite Semantics Valid": ml_rewrite_valid,
                "Classical Time (ms)": round(classical_time * 1000, 4),
                "ML Time (ms)": round(ml_time * 1000, 4)
            })

    df = pd.DataFrame(results)

    os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
    df.to_csv(output_file, index=False)

    summary = df.groupby("Registers").agg({
        "Classical Spills": "mean",
        "ML Spills": "mean",
        "Classical Added TAC Instructions": "mean",
        "ML Added TAC Instructions": "mean",
        "Classical Time (ms)": "mean",
        "ML Time (ms)": "mean"
    }).round(4)

    print(f"\nAverage Results Across {len(programs)} held-out programs:\n")
    print(summary.to_string())

    print("\nAllocation Validation:")
    print(f"Classical valid: {df['Classical Valid'].all()}")
    print(f"ML valid: {df['ML Valid'].all()}")
    print(f"Classical spill rewrites preserve output: {df['Classical Rewrite Semantics Valid'].all()}")
    print(f"ML spill rewrites preserve output: {df['ML Rewrite Semantics Valid'].all()}")
    print(f"Held-out programs interpreted: {checked_programs}")

    print(f"\nDetailed results saved to {output_file}")
    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate register allocators")
    parser.add_argument("--model", default="models/spill_cost_model.pkl")
    parser.add_argument("--test-dir", default="data/generated/test")
    parser.add_argument("--output", default="results/evaluation.csv")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    evaluate(args.model, args.test_dir, args.output, args.seed)
