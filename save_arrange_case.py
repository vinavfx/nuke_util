import argparse
import re
import sys
from pathlib import Path

DEFAULT_CASES_DIRECTORY = Path(__file__).parent / "arrange_nodes_cases"


def split_commands(text):
    start = 0
    depth = 0
    quoted = False
    escaped = False
    comment = False
    for index, character in enumerate(text):
        if comment:
            if character == "\n":
                end = index + 1
                yield text[start:end]
                start = end
                comment = False
            continue
        if escaped:
            escaped = False
            continue
        if character == "\\":
            escaped = True
            continue
        if character == "#" and not text[start:index].strip():
            comment = True
            continue
        if character == '"':
            quoted = not quoted
        elif not quoted:
            if character == "{":
                depth += 1
            elif character == "}":
                depth -= 1
                if depth < 0:
                    raise ValueError("Unexpected closing brace")
        if character == "\n" and depth == 0 and not quoted:
            end = index + 1
            yield text[start:end]
            start = end
    if depth or quoted or escaped:
        raise ValueError("Unterminated node, string, or escape sequence")
    if start < len(text):
        yield text[start:]


def node_class(command, references):
    header, separator, _ = command.partition("{")
    if not separator:
        return ""
    words = header.split()
    if len(words) == 1 and re.fullmatch(r"[A-Za-z_]\w*", words[0]):
        return words[0]
    if len(words) == 2 and words[0] == "clone":
        source = words[1]
        if source.startswith("$"):
            if source[1:] not in references:
                raise ValueError(f"Unknown clone reference: {source}")
            return references[source[1:]]
        parts = source.split("|")
        if len(parts) == 3:
            return parts[1]
        raise ValueError(f"Unsupported clone source: {source}")
    return ""


def clear_read_file(command):
    opening = command.index("{")
    closing = command.rindex("}")
    body_start = opening + 1
    body = command[body_start:closing]
    commands = []
    for knob in split_commands(body):
        if re.match(r"\s*file(?:\s|$)", knob):
            indent = knob[: len(knob) - len(knob.lstrip())]
            ending = "\n" if knob.endswith("\n") else ""
            knob = f'{indent}file ""{ending}'
        commands.append(knob)
    return command[: opening + 1] + "".join(commands) + command[closing:]


def simplify_script(text):
    output = []
    depth = 0
    references = {}
    last_class = ""
    node_count = 0
    for command in split_commands(text):
        stripped = command.strip()
        if stripped == "end_group":
            if not depth:
                raise ValueError("Unexpected end_group")
            depth -= 1
            if not depth:
                output.append(command)
            continue
        if depth:
            current_class = node_class(command, references)
            if current_class == "Group":
                depth += 1
            elif depth == 1 and current_class == "Input":
                output.append(command)
            continue
        current_class = node_class(command, references)
        if current_class:
            node_count += 1
            last_class = current_class
            if current_class == "Read":
                command = clear_read_file(command)
            elif current_class == "Group":
                depth += 1
        else:
            reference = re.fullmatch(r"set\s+(\w+)\s+\[stack 0\]", stripped)
            if reference:
                references[reference.group(1)] = last_class
            pushed = re.fullmatch(r"push\s+\$(\w+)", stripped)
            if pushed:
                last_class = references.get(pushed.group(1), "")
        output.append(command)
    if depth:
        raise ValueError("Missing end_group")
    if not node_count:
        raise ValueError("No nodes found")
    return "".join(output)


def save_case(text, directory):
    simplified = simplify_script(text)
    directory.mkdir(parents=True, exist_ok=True)
    indices = []
    for path in directory.iterdir():
        match = re.fullmatch(r"case_(\d+)\.nk", path.name)
        if match:
            indices.append(int(match.group(1)))
    index = max(indices, default=0) + 1
    while True:
        destination = directory / f"case_{index:03d}.nk"
        try:
            stream = destination.open("x", encoding="utf-8", newline="")
        except FileExistsError:
            index += 1
            continue
        with stream:
            stream.write(simplified)
        return destination


def main():
    parser = argparse.ArgumentParser(
        description="Save a lightweight Nuke script as an indexed arrangement case."
    )
    parser.add_argument("source", help="Source .nk file, or - for standard input")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_CASES_DIRECTORY,
        help="Case directory (default: arrange_nodes_cases next to this script)",
    )
    arguments = parser.parse_args()
    try:
        if arguments.source == "-":
            text = sys.stdin.read()
        else:
            text = Path(arguments.source).read_text(encoding="utf-8")
        destination = save_case(text, arguments.output_dir)
    except (OSError, ValueError) as error:
        parser.exit(1, f"Error: {error}\n")
    print(destination)


if __name__ == "__main__":
    main()
