from copy import deepcopy

from src.liveness import get_use_def


def rewrite_spills(instructions, spilled):
    """Insert pseudo-TAC loads and stores for every spilled variable."""
    spilled = set(spilled)
    used_names = set()
    for instruction in instructions:
        uses, defs = get_use_def(instruction)
        used_names.update(uses)
        used_names.update(defs)

    rewritten = []
    load_count = 0
    store_count = 0
    next_temp = 0

    def fresh_temp():
        nonlocal next_temp
        while True:
            name = f"spill_tmp_{next_temp}"
            next_temp += 1
            if name not in used_names:
                used_names.add(name)
                return name

    for instruction in instructions:
        rewritten_instruction = deepcopy(instruction)
        kind = instruction["type"]
        uses, defs = get_use_def(instruction)
        operands = []
        if kind == "copy":
            operands = [instruction["src"]]
        elif kind == "binary":
            operands = [instruction["left"], instruction["right"]]
        elif kind == "print":
            operands = [instruction["var"]]
        elif kind == "branch":
            operands = [instruction["left"], instruction["right"]]

        replacements = {}
        for variable in operands:
            if isinstance(variable, str) and variable in spilled:
                if variable not in replacements:
                    temp = fresh_temp()
                    replacements[variable] = temp
                    rewritten.append({
                        "type": "spill_load",
                        "dest": temp,
                        "slot": variable,
                    })
                    load_count += 1

        if kind == "copy":
            rewritten_instruction["src"] = replacements.get(
                instruction["src"], instruction["src"]
            )
        elif kind == "binary":
            for side in ("left", "right"):
                value = instruction[side]
                rewritten_instruction[side] = replacements.get(value, value)
        elif kind == "print":
            rewritten_instruction["var"] = replacements.get(
                instruction["var"], instruction["var"]
            )
        elif kind == "branch":
            for side in ("left", "right"):
                value = instruction[side]
                rewritten_instruction[side] = replacements.get(value, value)

        spilled_definitions = [variable for variable in defs if variable in spilled]
        definition_temps = {}
        for variable in spilled_definitions:
            temp = fresh_temp()
            definition_temps[variable] = temp
            rewritten_instruction["dest"] = temp

        rewritten.append(rewritten_instruction)
        for variable, temp in definition_temps.items():
            rewritten.append({
                "type": "spill_store",
                "src": temp,
                "slot": variable,
            })
            store_count += 1

    return rewritten, load_count, store_count


def run_tac(instructions, max_steps=100_000):
    """Execute the project's TAC subset, including rewritten spill ops."""
    labels = {
        instruction["label"]: index
        for index, instruction in enumerate(instructions)
        if instruction["type"] == "label"
    }
    values = {}
    slots = {}
    output = []
    pc = 0
    steps = 0
    comparisons = {
        "==": lambda left, right: left == right,
        "!=": lambda left, right: left != right,
        "<": lambda left, right: left < right,
        "<=": lambda left, right: left <= right,
        ">": lambda left, right: left > right,
        ">=": lambda left, right: left >= right,
    }

    while pc < len(instructions):
        steps += 1
        if steps > max_steps:
            raise RuntimeError("TAC execution exceeded the step limit")

        instruction = instructions[pc]
        kind = instruction["type"]
        next_pc = pc + 1

        if kind == "assign":
            values[instruction["dest"]] = instruction["value"]
        elif kind == "copy":
            values[instruction["dest"]] = values[instruction["src"]]
        elif kind == "binary":
            left = instruction["left"]
            right = instruction["right"]
            left = values[left] if isinstance(left, str) else left
            right = values[right] if isinstance(right, str) else right
            operations = {
                "+": lambda: left + right,
                "-": lambda: left - right,
                "*": lambda: left * right,
                "/": lambda: left / right,
            }
            values[instruction["dest"]] = operations[instruction["op"]]()
        elif kind == "print":
            output.append(values[instruction["var"]])
        elif kind == "branch":
            left = instruction["left"]
            right = instruction["right"]
            left = values[left] if isinstance(left, str) else left
            right = values[right] if isinstance(right, str) else right
            if comparisons[instruction["op"]](left, right):
                next_pc = labels[instruction["label"]]
        elif kind == "goto":
            next_pc = labels[instruction["label"]]
        elif kind == "label":
            pass
        elif kind == "spill_load":
            values[instruction["dest"]] = slots[instruction["slot"]]
        elif kind == "spill_store":
            slots[instruction["slot"]] = values[instruction["src"]]
        else:
            raise ValueError(f"Unsupported TAC instruction: {kind}")

        pc = next_pc

    return output


def render_instruction(instruction):
    """Render regular or spill pseudo-TAC as readable text."""
    kind = instruction["type"]
    if kind == "label":
        return f"{instruction['label']}:"
    if kind == "goto":
        return f"goto {instruction['label']}"
    if kind == "branch":
        return (
            f"if {instruction['left']} {instruction['op']} "
            f"{instruction['right']} goto {instruction['label']}"
        )
    if kind == "print":
        return f"print {instruction['var']}"
    if kind == "assign":
        return f"{instruction['dest']} = {instruction['value']}"
    if kind == "copy":
        return f"{instruction['dest']} = {instruction['src']}"
    if kind == "binary":
        return (
            f"{instruction['dest']} = {instruction['left']} "
            f"{instruction['op']} {instruction['right']}"
        )
    if kind == "spill_load":
        return f"{instruction['dest']} = load [{instruction['slot']}]"
    if kind == "spill_store":
        return f"store [{instruction['slot']}] = {instruction['src']}"
    raise ValueError(f"Unsupported TAC instruction: {kind}")
