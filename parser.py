import re

# --- Patterns ---
BLOCK_PATTERN = re.compile(
    r";(\w+)\((.*?)\)"       # function name and args
    r"(?:\s*:\s*(.*?))?"    # optional content after colon
    r"(?=(?:\n\s*;|$))",    # stop at next ;func or end of text
    re.DOTALL
)

VAR_ASSIGN_PATTERN = re.compile(
    r";(\w+)\s*=\s*(.*?)(?=(?:\n\s*;|$))",
    re.DOTALL
)

variables = {}

def parse_value(val: str):
    val = val.strip().rstrip(",")

    # function reference (escaped semicolon)
    if val.startswith(r"\;"):
        return val[2:]

    # variable reference
    if val.startswith(";"):
        return variables.get(val[1:], val)

    # booleans
    lower_val = val.lower()
    if lower_val == "true":
        return True
    if lower_val == "false":
        return False

    # tuples (with nesting support)
    if val.startswith("(") and val.endswith(")"):
        inner = val[1:-1].strip()
        if not inner:
            return ()
        parts, depth, current = [], 0, []
        for c in inner:
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
            if c == "," and depth == 0:
                parts.append("".join(current).strip())
                current = []
            else:
                current.append(c)
        if current:
            parts.append("".join(current).strip())
        return tuple(parse_value(p) for p in parts)

    # integers / floats
    try:
        return int(val)
    except ValueError:
        try:
            return float(val)
        except ValueError:
            return val  # fallback: keep as string

def parse_args(args_str: str):
    args = {}
    if not args_str:
        return args
    depth = 0
    current = ""
    parts = []
    for c in args_str:
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
        if c == "," and depth == 0:
            parts.append(current.strip())
            current = ""
        else:
            current += c
    if current.strip():
        parts.append(current.strip())
    for part in parts:
        if "=" in part:
            k, v = part.split("=", 1)
            args[k.strip()] = parse_value(v)
        else:
            args["arg"] = parse_value(part)
    return args

# First pass: collect variable assignments
def parse_vars(text: str):
    for m in VAR_ASSIGN_PATTERN.finditer(text):
        var_name, val = m.groups()
        variables[var_name] = parse_value(val)

# Second pass: parse function blocks
def parse_blocks(text: str):
    result = []
    for func, args_str, content in BLOCK_PATTERN.findall(text):
        func = func.strip()
        # resolve variable function reference
        if func in variables:
            func = variables[func]
        args = parse_args(args_str) if args_str else {}
        result.append({
            "func": func,
            "args": args,
            "content": content.strip() if content else ""
        })
    return result

def interpret(cls:object, code:str):
    parse_vars(code)
    for parsed in parse_blocks(code):
        if hasattr(cls, parsed["func"]):
            if parsed["content"]:
                parsed["args"]["content"] = parsed["content"]
            getattr(cls, parsed["func"])(**parsed["args"])
        else:
            print(f"Ignoring unknown function: {parsed['func']}")

