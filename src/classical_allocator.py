from src.tac_parser import parse_file
from src.liveness import analyze_liveness
from src.interference import build_interference
from src.spill_cost import heuristic_spill_cost


def allocate_registers(graph, k, features=None):
    if k < 1:
        raise ValueError("Number of registers must be positive")

    original = {v: set(n) for v, n in graph.items()}
    remaining = {v: set(n) for v, n in graph.items()}
    stack = []

    while remaining:
        node = next(
            (v for v in remaining if len(remaining[v]) < k),
            None
        )

        if node is None:
            # Optimistically remove the cheapest spill candidate; the final
            # coloring pass determines whether it actually needs spilling.
            if features is None:
                node = min(remaining, key=lambda v: (len(remaining[v]), v))
            else:
                node = min(
                    remaining,
                    key=lambda v: (heuristic_spill_cost(features[v]), v),
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


if __name__ == "__main__":
    instructions = parse_file("data/test/program1.tac")
    _, _, _, live_out = analyze_liveness(instructions)
    graph = build_interference(instructions, live_out)

    registers, spilled = allocate_registers(graph, 2)

    print("Interference Graph:")
    for var in sorted(graph):
        print(f"{var}: {sorted(graph[var])}")

    print("\nRegister Allocation:")
    for var in sorted(registers):
        print(f"{var} -> R{registers[var] + 1}")

    print("\nSpilled Variables:", sorted(spilled))
    print("Spill Count:", len(spilled))
