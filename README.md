# PTM Translator Tools

This repository holds a couple of small Python scripts used by volunteer
translators of the **Public Transport Mod (PTM)** for Minecraft.  It is **not** a
general-purpose project; if you are not translating the mod you can ignore it.

Missing translation files are supplied by the community.  To get the current
`missing_translations.txt` for your language, open the PTM Discord server and
send the word **`query`** in the designated translation channel.

---

## What’s included

- `translate.py` – interactive command‑line helper that steps through each line
  in a `missing_translations.txt` file and lets you type or confirm the
  translated text.  A progress tracker allows you to interrupt and resume.

- `compare.py` – compares two text files (`translations.txt` and
  `posttranslation.txt`) and reports cases where the same source string has
  been translated in more than one way.  You pick the version you want to keep
  and the script writes the results to `compared_output.txt`.

- `missing_translations.txt` – example/input list of untranslated strings in the
  format used by the mod (`add(TranslationID.FOO, "bar");`).  You will
  replace this with the file obtained from Discord.

- `translations.txt` / `posttranslation.txt` – files consumed by `compare.py`.

- `done.txt` – default output for `translate.py`.

---

## Requirements

- **Python 3.6 or newer.**
- No third‑party packages; everything uses the standard library.

The scripts run on Windows, macOS, and Linux.  On Windows, `msvcrt` is used for
single‑key input; the other platforms use `tty`/`termios`.

---

## Usage

1. Place the Python scripts and your text files in the same folder (or edit the
   filename constants at the top of each script).
2. Run one of the tools from a real terminal (not an IDE output pane).

### Filling missing translations

```bash
python translate.py
```

- `Enter` – finish editing or accept the original text
- `Tab` – skip the line (write it unchanged)
- `Ctrl+C` – cancel; progress is saved in `done.txt`

The script remembers the last processed `TranslationID` in the output file so
you can restart where you left off.

### Resolving conflicts

```bash
python compare.py
```

Put your untranslated lines in `translations.txt` and a tentative set of
translated lines in `posttranslation.txt`.  If more than one different
translation exists for the same source text, you’ll be prompted to choose the
preferred one.  Only the resolved entries are written to `compared_output.txt`.

---

## Customization & tips

- Change input/output filenames by editing the constants near the top of each
  script.
- The regex used to extract quoted text (`QUOTE_PATTERN`) can be adjusted if
your file format differs.
- Keep backups of your original files in case of mistakes.
- The interactive mode works best in a proper console.

---

Happy translating!
