import os
import random
import shutil
import argparse

TOTAL_PROGRAMS = 300
TRAIN_PROGRAMS = 240


def generate_program(program_id, num_vars=12, rng=None):
    rng = rng or random
    lines = []
    mode = program_id % 6

    if mode == 0:
        limit = rng.randint(3, 8)
        lines.extend([
            "v0 = 0",
            f"v1 = {limit}",
            "v2 = 1",
            "loop:",
            "v0 = v0 + 1",
            "v2 = v2 * v0",
            "if v0 < v1 goto loop",
            "v3 = v2 + v1",
            "print v3",
        ])
    elif mode == 1:
        left = rng.randint(2, 30)
        right = rng.randint(2, 30)
        lines.extend([
            f"v0 = {left}",
            f"v1 = {right}",
            "if v0 < v1 goto smaller",
            "v2 = v0 - v1",
            "goto join",
            "smaller:",
            "v2 = v1 - v0",
            "join:",
            "v3 = v2 * 2",
            "print v3",
        ])
    elif mode == 2:
        variables = []
        for i in range(max(5, num_vars - 3)):
            dest = f"v{i}"
            if not variables:
                lines.append(f"{dest} = {rng.randint(10, 100)}")
            else:
                left = rng.choice(variables)
                right = rng.choice(variables) if rng.random() >= 0.3 else str(rng.randint(1, 20))
                op = rng.choice(["+", "-", "*"])
                lines.append(f"{dest} = {left} {op} {right}")
            variables.append(dest)
        lines.append(f"print {rng.choice(variables)}")
    elif mode == 3:
        left, middle, right = (rng.randint(2, 30) for _ in range(3))
        lines.extend([
            f"v0 = {left}",
            f"v1 = {middle}",
            f"v2 = {right}",
            "if v0 < v1 goto outer_true",
            "v3 = v0 + v1",
            "if v3 > v2 goto inner_true",
            "v4 = v3 - v2",
            "goto join",
            "inner_true:",
            "v4 = v2 - v3",
            "goto join",
            "outer_true:",
            "v3 = v1 * v2",
            "if v3 != 0 goto outer_nonzero",
            "v4 = 1",
            "goto join",
            "outer_nonzero:",
            "v4 = v3 + v0",
            "join:",
            "v5 = v4 + v0",
            "v6 = v5 + v1",
            "print v6",
        ])
    elif mode == 4:
        limit = rng.randint(18, 35)
        lines.extend([
            "v0 = 0",
            f"v1 = {limit}",
            "v2 = 0",
            "v3 = 1",
            "v4 = 2",
            "long_loop:",
            "v0 = v0 + 1",
            "v2 = v2 + v0",
            "v3 = v3 + v2",
            "v4 = v4 + v0",
            "if v0 < v1 goto long_loop",
            "v5 = v2 + v3",
            "v6 = v5 + v2",
            "v7 = v6 + v3",
            "print v7",
        ])
    else:
        first, second = rng.randint(3, 30), rng.randint(3, 30)
        lines.extend([
            f"v0 = {first}",
            f"v1 = {second}",
            "v2 = v0 + v1",
            "v3 = v2 + v0",
            "v4 = v3 + v0",
            "v5 = v4 + v1",
            "v6 = v5 + v2",
            "v7 = v6 + v0",
            "v8 = v7 + v1",
            "print v8",
        ])

    return lines


def generate_corpus(seed=42, total_programs=300, train_programs=240,
                    output_dir="data/generated"):
    if train_programs >= total_programs:
        raise ValueError("train_programs must be less than total_programs")
    rng = random.Random(seed)
    if os.path.isdir(output_dir):
        for name in os.listdir(output_dir):
            path = os.path.join(output_dir, name)
            if name in {"train", "test"} and os.path.isdir(path):
                shutil.rmtree(path)
            elif name.startswith("program") and name.endswith(".tac"):
                os.remove(path)

    for i in range(1, total_programs + 1):
        lines = generate_program(i, rng.randint(8, 20), rng)
        split = "train" if i <= train_programs else "test"
        split_dir = os.path.join(output_dir, split)
        os.makedirs(split_dir, exist_ok=True)
        filename = os.path.join(
            split_dir,
            f"program{i}.tac"
        )

        with open(filename, "w") as file:
            file.write("\n".join(lines) + "\n")

    return os.path.join(output_dir, "train"), os.path.join(output_dir, "test")


def main():
    parser = argparse.ArgumentParser(description="Generate seeded TAC programs")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--total-programs", type=int, default=TOTAL_PROGRAMS)
    parser.add_argument("--train-programs", type=int, default=TRAIN_PROGRAMS)
    parser.add_argument("--output-dir", default="data/generated")
    args = parser.parse_args()
    train_dir, test_dir = generate_corpus(
        args.seed, args.total_programs, args.train_programs, args.output_dir
    )
    print(
        f"Seed {args.seed}: generated {args.train_programs} training and "
        f"{args.total_programs - args.train_programs} held-out programs "
        f"under {os.path.dirname(train_dir)}"
    )


if __name__ == "__main__":
    main()
