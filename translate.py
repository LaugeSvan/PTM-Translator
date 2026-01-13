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
INPUT_FILE = "missing_translations.txt"
OUTPUT_FILE = "done.txt"

QUOTE_PATTERN = re.compile(r'"(.*?)"')
ID_PATTERN = re.compile(r'add\(\s*([^,]+)\s*,')

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def get_last_processed_id():
    """Finds the last ID recorded in the output file to resume progress."""
    if not os.path.exists(OUTPUT_FILE):
        return None
    
    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
        for line in reversed(lines):
            match = ID_PATTERN.search(line)
            if match:
                return match.group(1).strip()
    return None

def read_key():
    """Cross-platform single key read."""
    if os.name == "nt":
        ch = msvcrt.getwch()
        if ch in ("\x00", "\xe0"):  # Special keys
            return f"special_{msvcrt.getwch()}"
        return ch
    else:
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            if ch == "\x1b":  # Possible arrow key
                seq = sys.stdin.read(2)
                return f"special_{seq}"
            return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def get_user_input(current_line, old_text, current_idx, total_count):
    """Handles the interactive CLI for entering new text."""
    clear_screen()
    
    # Logic to isolate only the "code shell" and remove trailing comma/space
    match = QUOTE_PATTERN.search(current_line)
    if match:
        start_idx = match.start()
        end_idx = match.end()
        # Take the prefix, remove the trailing comma and space, then add the suffix
        prefix = current_line[:start_idx].rstrip(", ")
        suffix = current_line[end_idx:].strip()
        code_preview = f"{prefix}{suffix}"
    else:
        code_preview = current_line.strip()

    print("-" * 60)
    print(f" PROGRESS: Line {current_idx + 1} / {total_count}")
    print("-" * 60)
    print(f" {code_preview}")
    print(f" \"{old_text}\"")
    print("-" * 60)
    print(" [ENTER] -> Confirm/Original | [TAB] -> Skip | [CTRL+C] -> Exit")
    print("-" * 60)
    sys.stdout.write(" ")
    sys.stdout.flush()

    new_text = ""
    while True:
        key = read_key()

        if key == "\t":  # Tab to skip
            print("\n[SKIPPED]")
            return None
        elif key in ("\r", "\n"):  # Enter to confirm
            print()
            return new_text
        elif key == "\x03":  # Ctrl+C
            raise KeyboardInterrupt
        elif key in ("\x08", "\x7f"):  # Backspace
            if new_text:
                new_text = new_text[:-1]
                sys.stdout.write("\b \b")
                sys.stdout.flush()
        elif key.startswith("special_"):
            continue
        elif len(key) == 1 and ord(key) >= 32:
            new_text += key
            sys.stdout.write(key)
            sys.stdout.flush()

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"ERROR: {INPUT_FILE} not found.")
        sys.exit(1)

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        all_lines = f.readlines()

    total_lines = len(all_lines)
    last_id = get_last_processed_id()
    start_idx = 0
    if last_id:
        for idx, line in enumerate(all_lines):
            match = ID_PATTERN.search(line)
            if match and match.group(1).strip() == last_id:
                start_idx = idx + 1
                break

    if start_idx >= total_lines:
        print("All lines already processed.")
        return

    # Load auto-fill map
    auto_fill_map = {}
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            for line in f:
                match = QUOTE_PATTERN.search(line)
                if match:
                    txt = match.group(1)
                    auto_fill_map[txt] = txt

    try:
        with open(OUTPUT_FILE, "a", encoding="utf-8") as out_f:
            for i in range(start_idx, total_lines):
                line = all_lines[i].rstrip("\n")
                match = QUOTE_PATTERN.search(line)

                if not match:
                    out_f.write(line + "\n")
                    continue

                old_text = match.group(1)

                if old_text in auto_fill_map:
                    updated = line.replace(f'"{old_text}"', f'"{auto_fill_map[old_text]}"', 1)
                    out_f.write(updated + "\n")
                    continue

                new_text = get_user_input(line, old_text, i, total_lines)
                
                if new_text is not None:
                    if new_text.strip() == "":
                        final_line = line
                    else:
                        final_line = line.replace(f'"{old_text}"', f'"{new_text}"', 1)
                        auto_fill_map[old_text] = new_text
                    
                    out_f.write(final_line + "\n")
                    out_f.flush() 
                
                time.sleep(0.05)

    except KeyboardInterrupt:
        print("\n\nProgress saved. Exiting...")
    finally:
        print(f"\nFinished! Results are in {OUTPUT_FILE}")

if __name__ == "__main__":
    main()