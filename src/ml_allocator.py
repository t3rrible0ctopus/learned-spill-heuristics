import joblib
import pandas as pd

from src.tac_parser import parse_file
from src.liveness import analyze_liveness
from src.interference import build_interference
from src.features import extract_features


def allocate_ml(graph, features, model, k):
    if k < 1:
        raise ValueError("Number of registers must be positive")

    original = {v: set(n) for v, n in graph.items()}
    remaining = {v: set(n) for v, n in graph.items()}
    stack = []

    variables = list(remaining)
    if variables:
        X = pd.DataFrame(
            [[
                features[v]["degree"],
                features[v]["live_range_length"],
                features[v]["use_frequency"],
                features[v]["definition_frequency"],
            ] for v in variables],
            index=variables,
            columns=[
                "degree",
                "live_range_length",
                "use_frequency",
                "definition_frequency",
            ],
        )
        costs = dict(zip(variables, model.predict(X)))
    else:
        costs = {}

    while remaining:
        node = next(
            (v for v in remaining if len(remaining[v]) < k),
            None
        )

        if node is None:
            node = min(
                remaining,
                key=lambda v: (
                    costs[v]
                )
            )

        stack.append(node)

        for neighbor in remaining[node]:
            if neighbor in remaining:
                remaining[neighbor].discard(node)

        del remaining[node]

    registers = {}
    spilled = set()

    while stack:
        node = stack.pop()

        unavailable = {
            registers[n]
            for n in original[node]
            if n in registers
        }

        reg = next(
            (r for r in range(k) if r not in unavailable),
            None
        )

        if reg is None:
            spilled.add(node)
        else:
            registers[node] = reg

    return registers, spilled


def main():
    instructions = parse_file("data/test/program1.tac")

    _, _, _, live_out = analyze_liveness(instructions)
    graph = build_interference(instructions, live_out)
    features = extract_features(instructions, graph)

    model = joblib.load("models/spill_cost_model.pkl")

    registers, spilled = allocate_ml(graph, features, model, 3)

    print("Register Allocation")
    print("Registers:", registers)
    print("Spilled variables:", spilled)


if __name__ == "__main__":
    main()
