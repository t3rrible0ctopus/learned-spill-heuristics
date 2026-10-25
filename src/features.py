from src.tac_parser import parse_file
from src.liveness import analyze_liveness
from src.interference import build_interference


def extract_features(instructions, graph):
    first_def = {}
    last_use = {}
    use_count = {}
    definition_count = {}

    for i, instruction in enumerate(instructions):
        kind = instruction["type"]

        if kind in ("assign", "copy", "binary"):
            dest = instruction["dest"]

            if dest not in first_def:
                first_def[dest] = i
            definition_count[dest] = definition_count.get(dest, 0) + 1

        if kind == "copy":
            uses = [instruction["src"]]

        elif kind == "binary":
            uses = [
                value
                for value in (
                    instruction["left"],
                    instruction["right"]
                )
                if isinstance(value, str)
            ]

        elif kind == "print":
            uses = [instruction["var"]]

        elif kind == "branch":
            uses = [
                value for value in (instruction["left"], instruction["right"])
                if isinstance(value, str)
            ]

        else:
            uses = []

        for var in set(uses):
            last_use[var] = i
            use_count[var] = use_count.get(var, 0) + 1

    features = {}

    for var in graph:
        start = first_def.get(var, 0)
        end = last_use.get(var, start)

        features[var] = {
            "degree": len(graph[var]),
            "live_range_length": end - start,
            "use_frequency": use_count.get(var, 0),
            "definition_frequency": definition_count.get(var, 0),
        }

    return features


if __name__ == "__main__":
    instructions = parse_file("data/test/program1.tac")

    _, _, _, live_out = analyze_liveness(instructions)
    graph = build_interference(instructions, live_out)

    features = extract_features(instructions, graph)

    print("Extracted Features:\n")

    for var in sorted(features):
        print(f"{var}: {features[var]}")
