import re
import os

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

input_file = "missing_translations.txt"
output_file = "done.txt"

quote_pattern = re.compile(r'"(.*?)"')
id_pattern = re.compile(r'add\(\s*([^,]+)\s*,')

with open(input_file, "r", encoding="utf-8") as f:
    lines = f.readlines()

last_done_id = None
if os.path.exists(output_file):
    with open(output_file, "r", encoding="utf-8") as df:
        for l in reversed(df.readlines()):
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

new_lines = [l.rstrip("\n") for l in lines[:start_idx]]

if start_idx >= len(lines):
    print("Nothing to do — all lines already processed.")
else:
    print(f"Resuming at line {start_idx+1}/{len(lines)} (last processed: {last_done_id})")

for idx in range(start_idx, len(lines)):
    line = lines[idx].rstrip("\n")
    match = quote_pattern.search(line)

    if not match:
        new_lines.append(line)
        continue

    old_text = match.group(1)

    clear_screen()
    print(line)
    print(f'Current text: "{old_text}"')

    new_text = input("New text (empty=unchanged): ")

    if new_text.strip() == "":
        new_lines.append(line)
    else:
        updated_line = line.replace(f'"{old_text}"', f'"{new_text}"', 1)
        new_lines.append(updated_line)

        with open(output_file, "a", encoding="utf-8") as out_f:
            out_f.write(updated_line + "\n")
        print(f'Appended to {output_file}')

with open(output_file, "w", encoding="utf-8") as f:
    for line in new_lines:
        f.write(line + "\n")

print(f"\nDone. Updated lines saved to {output_file}. Good job!")