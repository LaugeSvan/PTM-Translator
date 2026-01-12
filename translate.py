import sys
import re
import os

missing_deps = []

try:
    import re
except ImportError:
    missing_deps.append("re (standard library, something is seriously wrong)")

try:
    import os
except ImportError:
    missing_deps.append("os (standard library, something is seriously wrong)")

# readline is optional on Windows
try:
    import readline
except ImportError:
    if sys.platform.startswith("win"):
        print(
            "WARNING: 'readline' is not available on Windows by default.\n"
            "Input history and arrow-key navigation will not work.\n"
            "To fix this, run:\n"
            "  pip install pyreadline3\n"
        )
    else:
        missing_deps.append("readline")

if missing_deps:
    print("ERROR: Missing required dependencies:")
    for dep in missing_deps:
        print(f" - {dep}")
    print("\nFix the issues above and rerun the script.")
    sys.exit(1)


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


input_file = "missing_translations.txt"
output_file = "done.txt"

quote_pattern = re.compile(r'"(.*?)"')
id_pattern = re.compile(r'add\(\s*([^,]+)\s*,')

# Check if input file exists
if not os.path.exists(input_file):
    print(f"ERROR: {input_file} not found.")
    sys.exit(1)

with open(input_file, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Resuming logic: Find the last ID processed in done.txt
last_done_id = None
if os.path.exists(output_file):
    with open(output_file, "r", encoding="utf-8") as df:
        output_content = df.readlines()
        for l in reversed(output_content):
            m = id_pattern.search(l)
            if m:
                last_done_id = m.group(1).strip()
                break

# Map IDs from the input file
ids = []
for l in lines:
    m = id_pattern.search(l)
    ids.append(m.group(1).strip() if m else None)

# Calculate where to start
if last_done_id is None:
    start_idx = 0
else:
    found = next(
        (i for i in range(len(ids) - 1, -1, -1) if ids[i] == last_done_id),
        None
    )
    start_idx = found + 1 if found is not None else 0

if start_idx >= len(lines):
    print("Nothing to do. All lines are already processed.")
    sys.exit(0)
else:
    print(f"Resuming at line {start_idx + 1}/{len(lines)} (last ID: {last_done_id})")

# Main Loop
for idx in range(start_idx, len(lines)):
    line = lines[idx].rstrip("\n")
    match = quote_pattern.search(line)

    # If the line doesn't match the expected "add(ID, "text")" format,
    # just save it as is and move on.
    if not match:
        with open(output_file, "a", encoding="utf-8") as out_f:
            out_f.write(line + "\n")
        continue

    old_text = match.group(1)

    clear_screen()
    print(f"Line {idx + 1} of {len(lines)}")
    print("-" * 20)
    print(f"Code: {line}")
    print(f'Current Text: "{old_text}"')
    print("-" * 20)

    new_text = input("New text (Enter to keep unchanged, or type new text): ")

    # Determine final version of the line
    if new_text.strip() == "":
        updated_line = line
        status = "Kept original"
    else:
        # Replaces only the first occurrence of the quoted text
        updated_line = line.replace(f'"{old_text}"', f'"{new_text}"', 1)
        status = "Updated"

    # IMMEDIATELY append to the output file
    with open(output_file, "a", encoding="utf-8") as out_f:
        out_f.write(updated_line + "\n")

    print(f"Result: {status}. Progress saved.")

print(f"\nFinished! All processed lines are in {output_file}.")