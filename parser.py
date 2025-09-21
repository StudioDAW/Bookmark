import re
from pprint import pprint

text = """;document()

;p = \\;paragraph

;sm = \\;setmargin(top=20)

;sm

;p(): testing
"""

class DOC:
    def document(self, **kwargs):
        print("Document block called")
    def setmargin(self, **kwargs):
        print(kwargs)
    def paragraph(self, **kwargs):
        print("Paragraph:", kwargs.get("arg", ""))

# --- Patterns ---
BLOCK_PATTERN = re.compile(
    r";(\w+)\((.*?)\)"       # function name and args
    r"(?:\s*:\s*(.*?))?"    # optional content after colon
    r"(?=(?:\n\s*;|$))",    # stop at next ;func or end of text
    re.DOTALL
)

VAR_ASSIGN_PATTERN = re.compile(r";(\w+)\s*=\s*(.+)")

variables = {}

def parse_value(val: str):
    val = val.strip().rstrip(",")
    # escaped semicolon means "function reference"
    if val.startswith(r"\;"):
        return val[2:]  # remove \; and store function name
    # normal variable reference
    if val.startswith(";"):
        var_name = val[1:]
        return variables.get(var_name, val)
    # boolean / number
    if val.lower() == "true":
        return True
    if val.lower() == "false":
        return False
    try:
        return int(val)
    except ValueError:
        try:
            return float(val)
        except ValueError:
            return val

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
for line in text.splitlines():
    line = line.strip()
    m = VAR_ASSIGN_PATTERN.match(line)
    if m:
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

parsed = parse_blocks(text)
doc = DOC()
for parse in parsed:
    if hasattr(doc, parse["func"]):
        getattr(doc, parse["func"])(**parse["args"])
    else:
        print(f"Skipping unknown function: {parse['func']}")

print("Variables:", variables)
pprint(parsed)
