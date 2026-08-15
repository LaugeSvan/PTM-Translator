import re
import os
import sys

# ---------------- CONFIG ----------------
UNTRANSLATED_FILE = "translations.txt"
TRANSLATED_FILE = "posttranslation.txt"
OUTPUT_FILE = "compared_output.txt"
# ----------------------------------------


# Matches both:
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


def read_lines(path):
    if not os.path.exists(path):
        print(f"ERROR: {path} not found.")
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as f:
        return f.readlines()


def get_line_id(line):
    """
    Get the unique ID of an add(...) entry.

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


def get_translation(line):
    """
    Extract the actual translation text.

    For:

        add(ModSounds.SOMETHING.get(), "Text");

    returns "Text".

    For:

        add("translation.key", "Text");

    returns "Text".
    """

    matches = list(QUOTE_PATTERN.finditer(line))

    if not matches:
        return None

    # add("translation.key", "Text");
    if line.lstrip().startswith('add("'):

        if len(matches) >= 2:
            return matches[1].group(1)

        return None

    # add(ModSounds.SOMETHING.get(), "Text");
    return matches[0].group(1)


def build_entry_map(lines):
    """
    Build:

        ID -> translation

    Duplicate IDs are stored with all their translations.
    """

    entries = {}

    for line in lines:
        line_id = get_line_id(line)

        if not line_id:
            continue

        translation = get_translation(line)

        if translation is None:
            continue

        entries.setdefault(line_id, set()).add(translation)

    return entries


def ask_user_choice(line_id, original, options):
    print("\n" + "=" * 70)
    print("TRANSLATION CONFLICT")
    print("=" * 70)

    print(f"ID:")
    print(f"  {line_id}")

    print()
    print("ORIGINAL:")
    print(f'  "{original}"')

    print()
    print("CONFLICTING TRANSLATIONS:")

    for i, option in enumerate(options, start=1):
        print(f'  {i}) "{option}"')

    print()
    print("Choose the translation to keep.")
    print("Enter the number and press ENTER.")
    print()

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

    # Build maps based on the add(...) ID.
    untranslated_entries = build_entry_map(untranslated_lines)
    translated_entries = build_entry_map(translated_lines)

    print(f"Loaded {len(untranslated_entries)} untranslated entries.")
    print(f"Loaded {len(translated_entries)} translated entries.")

    # Find IDs that exist in both files.
    common_ids = (
        set(untranslated_entries.keys())
        & set(translated_entries.keys())
    )

    print(f"Found {len(common_ids)} matching entries.")

    conflicts = []

    for line_id in common_ids:
        original_options = untranslated_entries[line_id]
        translation_options = translated_entries[line_id]

        # Normally there should only be one original text.
        # If there are multiple, compare each one.
        for original in original_options:

            if len(translation_options) > 1:
                conflicts.append(
                    (
                        line_id,
                        original,
                        sorted(translation_options)
                    )
                )

    if not conflicts:
        print()
        print("No conflicting translations found.")
        return

    print()
    print(f"Found {len(conflicts)} conflicting entries.")

    resolved = {}

    for line_id, original, options in conflicts:

        chosen = ask_user_choice(
            line_id,
            original,
            options
        )

        resolved[line_id] = chosen

    # Write ONLY resolved conflicts.
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:

        for line_id, chosen in resolved.items():
            f.write(
                f'{line_id} -> "{chosen}"\n'
            )

    print()
    print("=" * 70)
    print("Comparison complete.")
    print(f"Resolved entries written to {OUTPUT_FILE}")
    print(f"Resolved conflicts: {len(resolved)}")
    print("=" * 70)


if __name__ == "__main__":
    main()
