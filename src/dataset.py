import csv
import os
import argparse

from src.tac_parser import parse_file
from src.liveness import analyze_liveness
from src.interference import build_interference
from src.features import extract_features
from src.spill_rewrite import rewrite_spills


def generate_dataset(program_files, output_file):
    rows = []

    for filename in program_files:
        instructions = parse_file(filename)

        _, _, _, live_out = analyze_liveness(instructions)
        graph = build_interference(instructions, live_out)
        features = extract_features(instructions, graph)

        for var, values in features.items():
            _, spill_loads, spill_stores = rewrite_spills(instructions, {var})
            rows.append({
                "program": os.path.basename(filename),
                "variable": var,
                **values,
                "spill_loads": spill_loads,
                "spill_stores": spill_stores,
                "spill_ops": spill_loads + spill_stores,
            })

    os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)

    with open(output_file, "w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "program",
                "variable",
                "degree",
                "live_range_length",
                "use_frequency",
                "definition_frequency",
                "spill_loads",
                "spill_stores",
                "spill_ops",
            ]
        )

        writer.writeheader()
        writer.writerows(rows)

    print(f"Dataset saved to {output_file}")
    print(f"Total examples: {len(rows)}")


def main():
    parser = argparse.ArgumentParser(description="Build spill-cost training data")
    parser.add_argument("--input-dir", default="data/generated/train")
    parser.add_argument("--output", default="data/train/spill_cost_dataset.csv")
    args = parser.parse_args()
    program_files = sorted(
        os.path.join(args.input_dir, name)
        for name in os.listdir(args.input_dir)
        if name.endswith(".tac")
    )
    generate_dataset(program_files, args.output)


if __name__ == "__main__":
    main()
