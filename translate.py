import sys
import re
import os
import time

# --- Dependency Check ---
missing_deps = []

try:
    import readchar
except ImportError:
    missing_deps.append("readchar (Run: pip install readchar)")

if missing_deps:
    print("ERROR: Missing required dependencies:")
    for dep in missing_deps:
        print(f" - {dep}")
    sys.exit(1)


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


# --- Config ---
input_file = "missing_translations.txt"
output_file = "done.txt"

quote_pattern = re.compile(r'"(.*?)"')
id_pattern = re.compile(r'add\(\s*([^,]+)\s*,')

if not os.path.exists(input_file):
    print(f"ERROR: {input_file} not found.")
    sys.exit(1)

with open(input_file, "r", encoding="utf-8") as f:
    lines = f.readlines()

# --- Resuming Logic ---
last_done_id = None
if os.path.exists(output_file):
    with open(output_file, "r", encoding="utf-8") as df:
        output_content = df.readlines()
        for l in reversed(output_content):
            m = id_pattern.search(l)
            if m:
                last_done_id = m.group(1).strip()
                break

ids = []
for l in lines:
    m = id_pattern.search(l)
    ids.append(m.group(1).strip() if m else None)

if last_done_id is None:
    start_idx = 0
else:
    found = next((i for i in range(len(ids) - 1, -1, -1) if ids[i] == last_done_id), None)
    start_idx = found + 1 if found is not None else 0

if start_idx >= len(lines):
    print("Nothing to do. All lines are already processed.")
    sys.exit(0)

# --- Main Interaction Loop ---
for idx in range(start_idx, len(lines)):
    line = lines[idx].rstrip("\n")
    match = quote_pattern.search(line)

    # If line format is wrong, append as-is and move on
    if not match:
        with open(output_file, "a", encoding="utf-8") as out_f:
            out_f.write(line + "\n")
        continue

    old_text = match.group(1)
    
    clear_screen()
    print(f"Line {idx + 1} of {len(lines)} | Last ID: {last_done_id}")
    print("-" * 30)
    print(f"Code: {line}")
    print(f"Current Text: \"{old_text}\"")
    print("-" * 30)
    print(" [ENTER]       -> Save (Appends to file)")
    print(" [ESC]         -> Skip (Does NOT append)")
    print(" [CTRL+C]      -> Exit script")
    print("-" * 30)

    # Custom Input Logic
    new_text = ""
    print("New text: ", end="", flush=True)

    while True:
        key = readchar.readkey()

        # ESCAPE: Discard entirely
        if key == readchar.key.ESC:
            new_text = None
            print("\n\n[ACTION] Skipped. Nothing appended.")
            break

        # ENTER: Confirm
        elif key == readchar.key.ENTER or key == readchar.key.CR:
            print() 
            break

        # BACKSPACE: Edit
        elif key == readchar.key.BACKSPACE or key == '\x7f':
            if len(new_text) > 0:
                new_text = new_text[:-1]
                sys.stdout.write('\b \b')
                sys.stdout.flush()

        # CTRL+C: Exit
        elif key == readchar.key.CTRL_C:
            print("\n\nExiting script...")
            sys.exit(0)

        # Normal characters
        elif len(key) == 1 and ord(key) >= 32:
            new_text += key
            sys.stdout.write(key)
            sys.stdout.flush()

    # --- Processing Result ---
    if new_text is not None:
        # If user pressed Enter
        if new_text.strip() == "":
            updated_line = line
            status = "Original kept & appended"
        else:
            updated_line = line.replace(f'"{old_text}"', f'"{new_text}"', 1)
            status = f"Updated to \"{new_text}\" & appended"

        with open(output_file, "a", encoding="utf-8") as out_f:
            out_f.write(updated_line + "\n")
        
        print(f"Success: {status}")
    else:
        # If user pressed Esc
        pass 

    time.sleep(0.3)

print(f"\nFinished! All lines processed are in {output_file}.")