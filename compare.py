import re
import os
import sys

# ---------------- CONFIG ----------------
UNTRANSLATED_FILE = "translations.txt"
TRANSLATED_FILE = "posttranslation.txt"
OUTPUT_FILE = "compared_output.txt"

QUOTE_PATTERN = re.compile(r'"(.*?)"')
# ----------------------------------------


def read_lines(path):
    if not os.path.exists(path):
        print(f"ERROR: {path} not found.")
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as f:
        return f.readlines()


def extract_texts(lines):
    """
    Returns a list of extracted quoted texts, or None per line
    """
    result = []
    for line in lines:
        m = QUOTE_PATTERN.search(line)
        result.append(m.group(1) if m else None)
    return result


def ask_user_choice(original, options):
    print("\n" + "=" * 60)
    print("UNTRANSLATED TEXT:")
    print(f"\"{original}\"")
    print("\nConflicting translations:\n")

    for i, opt in enumerate(options, start=1):
        print(f" {i}) \"{opt}\"")

    print("\nChoose the translation to keep.")
    print("Enter number and press ENTER.")

    while True:
        choice = input("> ").strip()
        if choice.isdigit():
            choice = int(choice)
            if 1 <= choice <= len(options):
                return options[choice - 1]

        print("Invalid choice. Try again.")


def main():
    untranslated_lines = read_lines(UNTRANSLATED_FILE)
    translated_lines = read_lines(TRANSLATED_FILE)

    untranslated_texts = extract_texts(untranslated_lines)
    translated_texts = extract_texts(translated_lines)

    # Map: untranslated -> set of translations
    conflicts = {}

    for idx, u_text in enumerate(untranslated_texts):
        if u_text is None:
            continue
        if idx >= len(translated_texts):
            continue

        t_text = translated_texts[idx]
        if t_text is None:
            continue

        conflicts.setdefault(u_text, set()).add(t_text)

    # Keep only real conflicts
    conflicts = {
        u: sorted(list(t))
        for u, t in conflicts.items()
        if len(t) > 1
    }

    if not conflicts:
        print("No conflicting translations found.")
        return

    resolved = {}

    for original, options in conflicts.items():
        resolved_choice = ask_user_choice(original, options)
        resolved[original] = resolved_choice

    # Write ONLY resolved comparisons
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for original, chosen in resolved.items():
            f.write(f"\"{original}\" -> \"{chosen}\"\n")

    print("\n" + "=" * 60)
    print("Comparison complete.")
    print(f"Resolved entries written to {OUTPUT_FILE}")
    print("Only compared items were included.")
    print("=" * 60)


if __name__ == "__main__":
    main()
