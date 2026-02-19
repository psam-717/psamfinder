# psamfinder — File duplicate finder

[![PyPI](https://img.shields.io/pypi/v/psamfinder)](https://pypi.org/project/psamfinder/)
[![Python](https://img.shields.io/pypi/pyversions/psamfinder)](https://pypi.org/project/psamfinder/)

psamfinder is a lightweight CLI tool that recursively scans directories for files with identical content (using SHA-256 hashing) and helps you manage duplicates interactively.

## Requirements
- Python 3.8+
- hatchling (for building, referenced in pyproject.toml)

## Installation
Once published:
```bash
pip install psamfinder
# or for isolated CLI install (recommended)
pipx install psamfinder


# For development/ from source
git clone https://github.com/psam-717/psamfinder.git
cd psamfinder
pip install -e .


## Running
- As a CLI (installed entry point):
  psamfinder scan <DIRECTORY> [--delete] [-q]

- From source:
  python -m psamfinder

Examples:
- Scan a directory and list duplicates:
  psamfinder scan C:\path\to\dir

- Scan and interactively delete duplicates (asks which file to keep per group):
  psamfinder scan C:\path\to\dir --delete

- Quiet scan (suppresses the scanning line):
  psamfinder scan C:\path\to\dir -q

## What the code does (line-level summary)

Files of interest:
- pyproject.toml
  - Project metadata: name `psamfinder`, version `0.1.0`, description "File duplicate finder".
  - Entry point: `psamfinder = "psamfinder.cli:app"` (Typer app).
  - Build system: hatchling.

- psamfinder/__main__.py
  - Imports `app` from psamfinder.cli and calls `sys.exit(app())` so `python -m psamfinder` runs the CLI.

- psamfinder/cli.py
  - Uses Typer to create a CLI app named `psamfinder` with help text.
  - Exposes a `scan` command that accepts:
    - directory: pathlib.Path (must exist, resolved, must be a directory)
    - --delete / -d: boolean option to enable interactive deletion after listing
    - --quiet / -q: boolean option to suppress the scanning message
  - Behavior:
    - Prints "Scanning: <directory> ..." unless -q is used (lines 51-52).
    - Calls `find_duplicates(str(directory))` from psamfinder.finder (line 54).
    - If no duplicates are found, prints "No duplicates found" and exits with code 0 (lines 56-58).
    - Otherwise calls `print_duplicates(duplicates)`, and if `--delete` was passed, asks for confirmation and calls `delete_duplicates(duplicates)`.

- psamfinder/finder.py
  - compute_hash(filepath)
    - Computes SHA-256 digest of file content in 4 KiB chunks (line 12 uses 4096 bytes).
    - Returns the hex digest string, or `None` if a PermissionError or FileNotFoundError occurs (lines 15-17). Errors are printed to stderr.
  - find_duplicates(directory)
    - Walks the directory recursively with os.walk (line 25).
    - For every file, builds its absolute path and computes its SHA-256 hash using `compute_hash`.
    - Collects paths in a dict mapping hash -> list of file paths (lines 24, 30-32).
    - Returns a dictionary of only the hashes that have 2 or more files (duplicates) (line 34).
    - Return type: dict[str, list[str]] where keys are hex SHA-256 strings and values are lists of file paths.
  - print_duplicates(duplicates)
    - Nicely prints a header and then each duplicate group showing the shared hash and the file paths (lines 42-47).
    - If duplicates is empty or falsy, prints "No duplicates found" and returns (lines 39-41).
  - delete_duplicates(duplicates)
    - For each duplicate group, lists the files with indices and prompts the user to enter the number of the file to keep (line 55), or type `skip` to keep all.
    - If a valid index is provided, removes all other files in that group using `os.remove` and prints the path deleted (lines 61-64).
    - If input is invalid (non-integer or out of bounds) it prints a message and skips deletion for that group (lines 65-68).

## Notes, gotchas, and suggestions
- compute_hash uses a 4 KiB read buffer; this is a reasonable trade-off between memory usage and speed. For very large files or performance-sensitive use cases, consider tuning the chunk size or using a faster hashing approach.
- Files that cannot be read due to permissions or that disappear during scanning are skipped and reported to stderr by compute_hash (the hash function returns None on these errors).
- The deletion flow is interactive and destructive: ensure backups or use version control if accidental deletion is a concern.
- The CLI `--delete` option first requests a confirmation prompt; deletion then asks which single file to keep in each group.
- The tool identifies duplicates strictly by file content hash. Files with identical content but different metadata (timestamps, permissions, names) are considered duplicates.

## Packaging
- The project is configured with pyproject.toml; the package includes the `psamfinder` module and exposes a console script in [project.scripts]. Use `python -m build` or `hatch build` in a properly configured environment to build a wheel.

## Extending / Contributing
- Possible improvements:
  - Add unit tests for compute_hash and find_duplicates.
  - Add options to automatically pick which files to keep (e.g., keep newest, keep largest, keep by pattern) for non-interactive deletion.
  - Add progress reporting for large scans, or parallel hashing for performance.
- Contributions via pull requests are welcome. Add tests and update the README with usage examples for new features.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact
Author:
- Marvinphil Annorbah(psam) (GitHub: [@psam-717](https://github.com/psam-717))

