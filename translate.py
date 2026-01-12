import sys
import re
import os
import time

# --- Platform-specific imports for immediate key reading ---
if os.name == "nt":
    import msvcrt
else:
    import tty
    import termios

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


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


# --- Resume Logic ---
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
    found = next(
        (i for i in range(len(ids) - 1, -1, -1) if ids[i] == last_done_id),
        None,
    )
    start_idx = found + 1 if found is not None else 0

if start_idx >= len(lines):
    print("Nothing to do. All lines are already processed.")
    sys.exit(0)


# --- Cross-platform single key read ---
def read_key():
    if os.name == "nt":
        ch = msvcrt.getwch()
        if ch == "\x00" or ch == "\xe0":  # special keys
            ch2 = msvcrt.getwch()
            return f"special_{ch2}"
        return ch
    else:
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
            if ch == "\x1b":  # possible arrow key
                seq = sys.stdin.read(2)
                return f"special_{seq}"
            return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


# --- Main Loop ---
for idx in range(start_idx, len(lines)):
    line = lines[idx].rstrip("\n")
    match = quote_pattern.search(line)

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
    print(" [TAB]         -> Skip immediately")
    print(" [CTRL+C]      -> Exit script")
    print("-" * 30)

    new_text = ""
    print("New text: ", end="", flush=True)

    while True:
        key = read_key()

        # TAB: skip immediately
        if key == "\t":
            new_text = None
            print("\n\n[ACTION] Skipped. Nothing appended.")
            break

        # ENTER: confirm
        elif key in ("\r", "\n"):
            print()
            break

        # CTRL+C: exit
        elif key == "\x03":
            print("\n\nExiting script...")
            sys.exit(0)

        # BACKSPACE
        elif key in ("\x08", "\x7f"):
            if new_text:
                new_text = new_text[:-1]
                sys.stdout.write("\b \b")
                sys.stdout.flush()

        # arrow keys or special keys: ignored (no editing yet)
        elif key.startswith("special_"):
            continue

        # normal characters
        elif len(key) == 1 and ord(key) >= 32:
            new_text += key
            sys.stdout.write(key)
            sys.stdout.flush()

    # --- Save result ---
    if new_text is not None:
        if new_text.strip() == "":
            updated_line = line
            status = "Original kept and appended"
        else:
            updated_line = line.replace(f'"{old_text}"', f'"{new_text}"', 1)
            status = f'Updated to "{new_text}" and appended'

        with open(output_file, "a", encoding="utf-8") as out_f:
            out_f.write(updated_line + "\n")

    time.sleep(0.3)

print(f"\nFinished! All lines processed are in {output_file}.")
