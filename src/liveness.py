from src.tac_parser import build_successors, parse_file


def get_use_def(instruction):
    uses = set()
    defs = set()

    kind = instruction["type"]

    if kind == "assign":
        defs.add(instruction["dest"])

    elif kind == "copy":
        defs.add(instruction["dest"])
        uses.add(instruction["src"])

    elif kind == "binary":
        defs.add(instruction["dest"])

        if isinstance(instruction["left"], str):
            uses.add(instruction["left"])

        if isinstance(instruction["right"], str):
            uses.add(instruction["right"])

    elif kind == "print":
        uses.add(instruction["var"])

    elif kind == "branch":
        if isinstance(instruction["left"], str):
            uses.add(instruction["left"])
        if isinstance(instruction["right"], str):
            uses.add(instruction["right"])

    elif kind in ("label", "goto"):
        pass

    else:
        raise ValueError(f"Unsupported instruction type: {kind}")

    return uses, defs


def analyze_liveness(instructions, successors=None):
    n = len(instructions)
    if successors is None:
        successors = build_successors(instructions)

    uses = []
    defs = []

    for instruction in instructions:
        use, define = get_use_def(instruction)
        uses.append(use)
        defs.append(define)

    live_in = [set() for _ in range(n)]
    live_out = [set() for _ in range(n)]

    changed = True

    while changed:
        changed = False

        for i in range(n - 1, -1, -1):
            new_out = set().union(*(live_in[j] for j in successors[i]))

            new_in = uses[i] | (new_out - defs[i])

            if new_in != live_in[i] or new_out != live_out[i]:
                live_in[i] = new_in
                live_out[i] = new_out
                changed = True

    return uses, defs, live_in, live_out


if __name__ == "__main__":
    instructions = parse_file("data/test/program1.tac")

    uses, defs, live_in, live_out = analyze_liveness(instructions)

    for i, instruction in enumerate(instructions):
        print(f"\nInstruction {i + 1}: {instruction}")
        print("USE:", sorted(uses[i]))
        print("DEF:", sorted(defs[i]))
        print("IN: ", sorted(live_in[i]))
        print("OUT:", sorted(live_out[i]))
