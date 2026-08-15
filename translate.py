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


# Matches:
#
# add(ModSounds.SOMETHING.get(), "Text");
#
# and:
#
# add("translation.key", "Text");
#
ID_PATTERN = re.compile(
    r'add\(\s*(?:"([^"]+)"|([^,]+?))\s*,'
)

QUOTE_PATTERN = re.compile(
    r'"((?:\\.|[^"\\])*)"'
)


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def get_line_id(line):
    """
    Returns the identifier of an add(...) line.

    Supports:

        add(ModSounds.SOMETHING.get(), "Text");

    and:

        add("translation.key", "Text");
    """

    match = ID_PATTERN.search(line)

    if not match:
        return None

    # add("translation.key", "Text");
    if match.group(1) is not None:
        return match.group(1).strip()

    # add(ModSounds.SOMETHING.get(), "Text");
    return match.group(2).strip()


def get_translation_match(line):
    """
    Finds the actual translation text.

    Supports:

        add(ModSounds.SOMETHING.get(), "Translation");

    and:

        add("translation.key", "Translation");
    """

    matches = list(QUOTE_PATTERN.finditer(line))

    if not matches:
        return None

    # add("translation.key", "Translation");
    #
    # First quoted string is the translation key.
    # Second quoted string is the translation.
    if line.lstrip().startswith('add("') and len(matches) >= 2:
        return matches[1]

    # add(ModSounds.SOMETHING.get(), "Translation");
    #
    # First quoted string is the translation.
    return matches[0]


def read_key():
    """Cross-platform single key read."""

    if os.name == "nt":
        ch = msvcrt.getwch()

        if ch in ("\x00", "\xe0"):
            return f"special_{msvcrt.getwch()}"

        return ch

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)

    try:
        tty.setraw(fd)

        ch = sys.stdin.read(1)

        if ch == "\x1b":
            seq = sys.stdin.read(2)
            return f"special_{seq}"

        return ch

    finally:
        termios.tcsetattr(
            fd,
            termios.TCSADRAIN,
            old_settings
        )


def get_user_input(
    current_line,
    old_text,
    current_idx,
    total_count
):
    """Interactive CLI for entering translation text."""

    clear_screen()

    match = get_translation_match(current_line)

    if match:
        start_idx = match.start()
        end_idx = match.end()

        prefix = current_line[:start_idx].rstrip(", ")
        suffix = current_line[end_idx:].strip()

        code_preview = f"{prefix}{suffix}"

    else:
        code_preview = current_line.strip()

    print("-" * 60)
    print(
        f" PROGRESS: Source line {current_idx + 1} / {total_count}"
    )
    print("-" * 60)
    print(f" {code_preview}")
    print(f' "{old_text}"')
    print("-" * 60)
    print(
        " [ENTER] -> Keep original"
        " | [TAB] -> Skip"
        " | [CTRL+C] -> Exit"
    )
    print("-" * 60)

    sys.stdout.write(" ")
    sys.stdout.flush()

    new_text = ""

    while True:
        key = read_key()

        # TAB = skip
        if key == "\t":
            print("\n[SKIPPED]")
            return None

        # ENTER = accept
        elif key in ("\r", "\n"):
            print()
            return new_text

        # CTRL+C
        elif key == "\x03":
            raise KeyboardInterrupt

        # Backspace
        elif key in ("\x08", "\x7f"):
            if new_text:
                new_text = new_text[:-1]

                sys.stdout.write("\b \b")
                sys.stdout.flush()

        # Arrow keys etc.
        elif key.startswith("special_"):
            continue

        # Normal printable character
        elif len(key) == 1 and ord(key) >= 32:
            new_text += key

            sys.stdout.write(key)
            sys.stdout.flush()


def replace_translation(line, match, new_text):
    """
    Replace only the translation text, preserving everything else.
    """

    return (
        line[:match.start()]
        + '"'
        + new_text
        + '"'
        + line[match.end():]
    )


def load_completed_ids():
    """
    Read done.txt and collect every ID that has already been processed.

    This means done.txt can be reordered or have entries deleted.
    """

    completed_ids = set()

    if not os.path.exists(OUTPUT_FILE):
        return completed_ids

    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line_id = get_line_id(line)

            if line_id:
                completed_ids.add(line_id)

    return completed_ids


def load_translation_map():
    """
    Load translations from done.txt.

    This allows previously translated text to be reused automatically
    when the same original text appears again.
    """

    translation_map = {}

    if not os.path.exists(OUTPUT_FILE):
        return translation_map

    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            match = get_translation_match(line)

            if not match:
                continue

            text = match.group(1)

            if text:
                translation_map[text] = text

    return translation_map


def main():

    if not os.path.exists(INPUT_FILE):
        print(f"ERROR: {INPUT_FILE} not found.")
        sys.exit(1)

    # Read source file
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        all_lines = f.readlines()

    total_lines = len(all_lines)

    # Load everything already processed
    completed_ids = load_completed_ids()

    # Load previous translations
    auto_fill_map = load_translation_map()

    print(f"Loaded {total_lines} source lines.")
    print(f"Found {len(completed_ids)} already completed entries.")

    remaining = 0

    for line in all_lines:
        line_id = get_line_id(line)

        if line_id and line_id not in completed_ids:
            remaining += 1

    print(f"{remaining} entries remaining.")

    if remaining == 0:
        print("All lines already processed.")
        return

    print()
    print("Press any key to start...")

    read_key()

    out_f = None

    try:
        out_f = open(
            OUTPUT_FILE,
            "a",
            encoding="utf-8"
        )

        processed_this_run = 0

        for i, raw_line in enumerate(all_lines):

            line = raw_line.rstrip("\n")

            # Get ID
            line_id = get_line_id(line)

            # If this isn't a valid add(...) line,
            # preserve it.
            if not line_id:
                continue

            # Already present in done.txt
            if line_id in completed_ids:
                continue

            # Find translation text
            match = get_translation_match(line)

            if not match:
                print(
                    f"\nWARNING: Could not find translation "
                    f"for line {i + 1}:"
                )
                print(line)

                out_f.write(line + "\n")
                out_f.flush()

                completed_ids.add(line_id)

                continue

            old_text = match.group(1)

            # Automatic translation reuse
            if old_text in auto_fill_map:

                updated = replace_translation(
                    line,
                    match,
                    auto_fill_map[old_text]
                )

                out_f.write(updated + "\n")
                out_f.flush()

                completed_ids.add(line_id)

                processed_this_run += 1

                continue

            # Ask user
            new_text = get_user_input(
                line,
                old_text,
                i,
                total_lines
            )

            if new_text is None:

                # User pressed TAB.
                #
                # Do NOT mark this as completed.
                # This allows it to appear again next run.
                continue

            if new_text.strip() == "":
                final_line = line

            else:
                final_line = replace_translation(
                    line,
                    match,
                    new_text
                )

                auto_fill_map[old_text] = new_text

            # Write result
            out_f.write(final_line + "\n")
            out_f.flush()

            # Mark this ID as completed
            completed_ids.add(line_id)

            processed_this_run += 1

            time.sleep(0.05)

        out_f.close()

        print()
        print(
            f"Processed {processed_this_run} new entries."
        )
        print(
            f"Results are in {OUTPUT_FILE}"
        )

    except KeyboardInterrupt:

        if out_f:
            out_f.close()

        print()
        print()
        print("Progress saved. Exiting...")

    finally:

        if out_f and not out_f.closed:
            out_f.close()


if __name__ == "__main__":
    main()
