# psamfinder — Duplicate File Finder

[![PyPI](https://img.shields.io/pypi/v/psamfinder)](https://pypi.org/project/psamfinder/)
[![Python](https://img.shields.io/pypi/pyversions/psamfinder)](https://pypi.org/project/psamfinder/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**psamfinder** is a fast, lightweight CLI tool that recursively scans directories for:

- 🔍 **Exact duplicate files** — identified by SHA-256 content hash
- 🖼️ **Near-duplicate images** — detected via perceptual hashing (optional)

---

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Commands](#commands)
  - [scan](#scan)
  - [threshold](#threshold)
- [Examples](#examples)
- [How It Works](#how-it-works)
- [Project Structure](#project-structure)
- [Building from Source](#building-from-source)
- [Contributing](#contributing)
- [License](#license)

---

## Installation

### From PyPI (recommended)

```bash
pip install psamfinder

# Isolated install with pipx (keeps your global Python clean)
pipx install psamfinder
```

### With fuzzy image duplicate detection

Fuzzy mode requires extra dependencies (`imagehash` + `Pillow`):

```bash
pip install "psamfinder[fuzzy]"

# or with pipx
pipx install "psamfinder[fuzzy]"
```

### From source (development)

```bash
git clone https://github.com/psam-717/psamfinder.git
cd psamfinder

pip install -e .                  # exact duplicates only
pip install -e ".[fuzzy]"         # with fuzzy image support
```

---

## Quick Start

```bash
# Scan a directory for exact duplicates
psamfinder scan ~/Downloads

# Find and interactively delete duplicates
psamfinder scan ~/Downloads --delete

# Preview what would be deleted (safe dry-run)
psamfinder scan ~/Downloads --delete --dry-run

# Find near-duplicate images (resized, recompressed, cropped)
psamfinder scan ~/Photos --fuzzy-images --similarity-threshold 0.82
```

---

## Commands

### `scan`

Recursively scans a directory for duplicate files and optionally deletes them.

```
psamfinder scan <DIRECTORY> [OPTIONS]
```

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--delete` | `-d` | `False` | Prompt to delete copies after listing duplicates |
| `--dry-run` | `-n` | `False` | Preview which files would be deleted, without touching anything |
| `--quiet` | `-q` | `False` | Suppress the "Scanning…" status message |
| `--fuzzy-images` | | `False` | Use perceptual hashing for near-duplicate image detection |
| `--similarity-threshold` | | `0.80` | Similarity cutoff for fuzzy mode (`0.0`–`1.0`); try `0.75`–`0.85` for resized photos |

> **Tip:** Always run with `--dry-run` first. Deletion is interactive but **permanent**.

---

### `threshold`

Analyzes pairwise image similarity in a directory to help you choose an appropriate `--similarity-threshold` value before running a fuzzy scan.

```
psamfinder threshold <DIRECTORY> [OPTIONS]
```

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--max-images` | | `300` | Maximum number of images to process (`0` = no limit) |
| `--quiet` | `-q` | `False` | Suppress the "Analyzing…" status message |
| `--verbose` | `-v` | `False` | Show all pairs and a full distance distribution |

> **Note:** This command is read-only — it never modifies or deletes any files.

---

## Examples

```bash
# List exact duplicates in a folder
psamfinder scan ~/Documents

# Find near-duplicate photos and interactively remove copies
psamfinder scan ~/Photos --fuzzy-images --similarity-threshold 0.80 --delete

# Dry-run: preview deletions without removing anything
psamfinder scan ~/Downloads --delete --dry-run

# Analyze your image library to pick the right fuzzy threshold
psamfinder threshold ~/Photos --max-images 500 --verbose

# Quiet scan — only print duplicate groups, no status messages
psamfinder scan ~/Music -q

# Show installed version
psamfinder --version
```

---

## How It Works

### Exact duplicate detection (default)

1. Walks the target directory recursively.
2. Computes a **SHA-256 hash** of each file's raw content (in 4 KiB chunks).
3. Groups files that share the same hash — these are byte-for-byte identical, regardless of filename or metadata.

### Fuzzy / perceptual image detection (`--fuzzy-images`)

1. Collects image files with common extensions (`.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`).
2. Computes a **perceptual hash (pHash)** for each image using `imagehash`.
3. Compares all pairs using **Hamming distance** — the number of differing bits.
4. Groups near-duplicates using a **union-find** data structure based on the configured similarity threshold.

The similarity score is derived from the Hamming distance over 64 bits:

```
similarity = 1 - (hamming_distance / 64)
```

| Threshold | Use case |
|-----------|----------|
| `0.90`–`0.95` | Near-exact matches only |
| `0.75`–`0.85` | Resized, cropped, or recompressed versions |
| `0.65`–`0.74` | Lenient — may include false positives |

Use `psamfinder threshold` to inspect your image library's similarity distribution before committing to a threshold.

---

## Project Structure

```
psamfinder/
├── cli.py        # Typer CLI — defines scan and threshold commands
├── finder.py     # Core logic — hashing, grouping, printing, deletion
└── __init__.py
pyproject.toml    # Package metadata, dependencies, build config
```

**`finder.py` key functions:**

| Function | Description |
|----------|-------------|
| `compute_hash(filepath)` | SHA-256 hash of a file; returns `None` on permission/IO errors |
| `find_duplicates(directory, fuzzy_images, similarity_threshold)` | Returns `List[List[str]]` of duplicate groups |
| `print_duplicates(dupe_groups)` | Prints groups in a clean, numbered format |
| `delete_duplicates(dupe_groups, dry_run)` | Interactive per-group deletion; prompts user to pick which file to keep |

---

## Building from Source

psamfinder uses [Hatchling](https://hatch.pypa.io/) as its build backend.

```bash
pip install hatch
hatch build          # produces dist/ with wheel and sdist

# or with build directly
python -m build
```

---

## Contributing

Pull requests are welcome! Here are some ideas for future improvements:

- ✅ Unit tests (hashing, grouping, fuzzy logic, deletion flows)
- 🔢 Auto-keep rules (newest / largest / shortest path / regex match)
- ⚡ Progress bar or parallel processing for large directories
- 📄 JSON / CSV report export
- 📊 Better summary statistics after a scan

Please include tests with your PR and update the README examples if you add new features.

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## Author

**Marvinphil Annorbah (psam)** · GitHub: [@psam-717](https://github.com/psam-717)

