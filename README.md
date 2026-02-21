# psamfinder — File duplicate finder

[![PyPI](https://img.shields.io/pypi/v/psamfinder)](https://pypi.org/project/psamfinder/)
[![Python](https://img.shields.io/pypi/pyversions/psamfinder)](https://pypi.org/project/psamfinder/)

psamfinder is a lightweight CLI tool that recursively scans directories for **exact duplicate files** (using SHA-256 hashing) **and near-duplicate images** (using perceptual hashing when enabled).

## Requirements
- Python 3.8+
- hatchling (for building, referenced in pyproject.toml)

## Installation
**From PyPI (recommended):**
```bash
pip install psamfinder
# or for isolated CLI install (recommended)
pipx install psamfinder

# With fuzzy (perceptual) image duplicate detection support:
pip install "psamfinder[fuzzy]"
# or
pipx install "psamfinder[fuzzy]"


# For development/ from source
git clone https://github.com/psam-717/psamfinder.git
cd psamfinder
pip install -e .
pip install -e ".[fuzzy]" # with fuzzy image support


## Running
- Basic scan (exact duplicates only)
  psamfinder scan <DIRECTORY>

- Scan + interactive deletion
  psamfinder scan <DIRECTORY> --delete

- Dry-run deletion preview
psamfinder scan <DIRECTORY> --delete --dry-run

- Quiet mode (no "Scanning..." message)
psamfinder scan <DIRECTORY> -q

- Fuzzy/perceptual image duplicate detection (near-duplicates, resized/cropped, etc.)
psamfinder scan <DIRECTORY> --fuzzy-images --similarity-threshold 0.82

- Help choose a good similarity threshold by analyzing your images
psamfinder threshold <DIRECTORY> [--max-images 300] [--verbose]

Examples:
- List exact duplicates
psamfinder scan ~/Photos

- Find near-duplicate photos (good for resized/edited versions)
psamfinder scan ~/Photos --fuzzy-images --similarity-threshold 0.80

- Analyze similarity distribution to pick a threshold
psamfinder threshold ~/Photos --max-images 500 --verbose

- Dry-run deletion of exact duplicates
psamfinder scan ~/Downloads --delete --dry-run

- Show version
psamfinder --version

## How the code works (high-level overview)

**Key files & responsibilities**

- `pyproject.toml`
  - Project metadata, version (now 0.3.6), MIT license
  - Console entry point: `psamfinder = "psamfinder.cli:app"`
  - Optional `[fuzzy]` extra: `imagehash` + `pillow` for perceptual image detection

- `psamfinder/cli.py`
  - Typer-based CLI with two commands:
    - `scan` — finds duplicates (exact or fuzzy), lists them, offers interactive deletion
      Flags: `--delete`, `--dry-run`, `--quiet`, `--fuzzy-images`, `--similarity-threshold`
    - `threshold` — analyzes pairwise image similarities to help choose a good fuzzy threshold
      Flags: `--max-images`, `--quiet`, `--verbose`
  - `--version` / `-V` shows package version

- `psamfinder/finder.py`
  - `compute_hash()` — SHA-256 of file content (4 KiB chunks), skips on permission/IO errors
  - `find_duplicates(directory, fuzzy_images=False, similarity_threshold=0.80)`
    - **Exact mode** (default): groups files by identical SHA-256 hash → `List[List[str]]`
    - **Fuzzy mode** (`--fuzzy-images`): uses perceptual hashing (`phash`) on images only
      - Groups near-duplicates using union-find + Hamming distance threshold
      - Returns `List[List[str]]` of similar-image groups
  - `print_duplicates(dupe_groups: List[List[str]])` — clean grouped output
  - `delete_duplicates(dupe_groups: List[List[str]], dry_run=False)` — interactive keep/skip per group

**Main behavioral changes**
- Duplicate groups are now consistently returned and handled as `List[List[str]]` (no more hash dict)
- Fuzzy mode requires `pip install psamfinder[fuzzy]` and only processes common image formats
- New `threshold` command helps tune `--similarity-threshold` by showing similar pairs and distribution

## Important notes & gotchas
- Always test with `--dry-run` — deletion is interactive and permanent
- Make backups before using `--delete` without `--dry-run`
- Exact mode ignores metadata (only content matters)
- Fuzzy mode is perceptual — good for resized/cropped/recompressed images, but may include false positives depending on threshold
- `threshold` command is read-only (no deletion)
- Skipped files (permissions, corrupt images, etc.) are logged to stderr

## Packaging
Configured with `pyproject.toml` + hatchling.  
Build: `hatch build` or `python -m build`

## Contributing & future ideas
- Add tests (hashing, grouping, fuzzy logic, deletion flows)
- Auto-keep rules (newest/largest/shortest-path/regex)
- Progress bar or parallel processing for large directories
- JSON/CSV report export
- Better error handling & summary stats

Pull requests welcome — include tests and update README examples for new features.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact
Author:
- Marvinphil Annorbah(psam) (GitHub: [@psam-717](https://github.com/psam-717))

