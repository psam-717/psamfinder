from pathlib import Path
from typing import Optional, List
import typer
from importlib.metadata import version as pkg_version
import os
import sys

__version__ = pkg_version("psamfinder")

from psamfinder.finder import (
    find_duplicates,
    print_duplicates,
    delete_duplicates
)

app = typer.Typer( # pylint: disable=unexpected-keyword-arg
    name="psamfinder",
    help="Find duplicate files by content (SHA-256)",
    add_completion=True,
    no_args_is_help=True,
    invoke_without_command=True,

)



def version_callback(value: bool) -> None:
    if value:
        typer.echo(f"{app.info.name} {__version__}")
        raise typer.Exit(0)

@app.callback(invoke_without_command=True)   # ← this makes it a group
def main(
    ctx: typer.Context,
    version: Optional[bool] = typer.Option(  # pylint: disable=unused-argument
        None,
        "--version", "-V",
        callback=version_callback,
        is_eager=True,
        help="Show the version and exit"
    )
):
    """
    Find duplicate files by content (SHA-256).
    Use 'scan' to start searching a directory.
    """
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


@app.command()
def scan(
    directory: Path = typer.Argument(
        ...,
        help="Directory to scan (it should be absolute)",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True
    ),
    delete: bool = typer.Option(
        False,
        "--delete", "-d",
        help="After listing duplicates, ask for confirmation to delete copies"
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet", "-q",
        help="Only show duplicate groups - no scanning message"
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run", "-n",
        help="Simulate deletion: show which files would be removed without touching anything"
    ),
    fuzzy_images: bool = typer.Option(
        False,
        "--fuzzy-images",
        help="Enable perceptual (fuzzy) duplicate detection for images instead of exact hashing"
    ),
    similarity_threshold: float = typer.Option(
        0.80,
        "--similarity-threshold",
        min=0.0,
        max=1.0,
        help="Similarity threshold for fuzzy detection (0.0 to 1.0; try 0.75-0.85 for resized photos)"
    )
):
    """Scan directories (and subdirectories) for files with identical content"""
    if not quiet:
        typer.echo(f"Scanning: {directory.resolve()} ...")
    
    dupe_groups = find_duplicates(
        str(directory),
        fuzzy_images=fuzzy_images,
        similarity_threshold=similarity_threshold
    )
    
    if not dupe_groups:
        typer.echo("No duplicates found")
        raise typer.Exit(0)
    
    print_duplicates(dupe_groups)
    
    if delete:
        if not typer.confirm("\n Proceed with deletion"):
            typer.echo("Cancelled")
            raise typer.Exit(0)
        
        deleted_anything = delete_duplicates(dupe_groups, dry_run=dry_run)
        if dry_run:
            typer.echo("\nDry run complete — no files were actually deleted.")
        elif deleted_anything:
            typer.echo("Selected duplicates removed")
        else:
            typer.echo("No files deleted (all groups skipped or invalid choices)")
    # else:
    #     typer.echo("\nUse --delete to remove copies after review")
        

@app.command()
def threshold(
    directory: Path = typer.Argument(
        ..., 
        help="Directory to analyze for image similarity thresholds",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True
    ),
    max_images: int = typer.Option(
        300,
        "--max-images",
        help="Maximum number of images ot process (to avoid long runtimes; 0 = no limit)",
        min=0
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet", "-q",
        help="Suppress scanning message"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose", "-v",
        help="Show detailed output (all pairs, full distribution)"
    )
):
    """Analyze pairwise image similarities to help choose --similarity-threshold"""
    if not quiet:
        typer.echo(f"Analyzing images in: {directory.resolve()} ...")
        
    try:
        from PIL import Image
        from imagehash import phash
    except ImportError as exc:
        raise ImportError("This command requires fuzzy dependencies. Install with: pip install psamfinder[fuzzy]") from exc
    
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp')
    image_paths: List[str] = []
    for root, _, files in os.walk(str(directory)):
        for filename in files:
            if filename.lower().endswith(image_extensions):
                image_paths.append(os.path.join(root, filename))

    if max_images > 0:
        image_paths = image_paths[:max_images]
        
    n = len(image_paths)
    if n < 2:
        typer.echo("Not enough images to compare (need at least 2).")
        raise typer.Exit(1)

    typer.echo(f"Processing {n} images...")
    
    # compute hashes
    hashes = []
    valid_paths = []
    for path in image_paths:
        try:
            img = Image.open(path)
            h = phash(img)
            hashes.append(h)
            valid_paths.append(path)
        except Exception as e: # pylint: disable=broad-exception-caught
            print(f"Skipped {path}: {e}", file=sys.stderr)
    
    n = len(hashes)
    if n < 2:
        typer.echo("Too few valid images after processing")
        raise typer.Exit(1)
    
    # Collect all pairwise distances (upper triangle only)
    distances = []
    for i in range(n):
        for j in range(i + 1, n):
            dist = hashes[i] - hashes[j]
            distances.append((dist, valid_paths[i], valid_paths[j]))
    
    if not distances:
        typer.echo("No pairs to compare")
        raise typer.Exit(0)

    # Sort ascending (smallest distance = most similar first)
    distances.sort(key=lambda x: x[0])
    
    # Always show top similar pairs
    typer.echo("\nMost similar pairs:")
    for dist, p1, p2 in distances[:10]:  # limit to 10 for readability
        sim = 1 - (dist / 64.0)
        typer.echo(f"  dist {dist:2d} → sim {sim:.3f} | {os.path.basename(p1)} ↔ {os.path.basename(p2)}")
    
    # Always show simple suggestion
    if distances:
        non_zero_dists = [d for d, _, _ in distances if d > 0]
        if non_zero_dists:
            min_nonzero = min(non_zero_dists)
            buffer_bits = 3  # tune this: 2=tighter, 4–6=more forgiving
            suggested_dist = min_nonzero + buffer_bits
            suggested_sim = 1 - (suggested_dist / 64.0)
            suggested_sim = max(0.70, min(0.90, round(suggested_sim, 2)))
        else:
            suggested_sim = 0.95

        typer.echo(f"\nQuick suggestion: try --similarity-threshold {suggested_sim:.2f} "
                   f"to catch resized/edited versions like these.")
    
    if verbose:
        typer.echo("\nAll pairs (sorted by distance):")
        for dist, p1, p2 in distances:
            sim = 1 - (dist / 64.0)
            typer.echo(f"  dist {dist:2d} → sim {sim:.3f} | {os.path.basename(p1)} ↔ {os.path.basename(p2)}")
        
        # Cumulative distribution
        typer.echo("\nDistance distribution (cumulative):")
        thresholds = [0, 5, 10, 15, 20, 25, 30]
        counts = {t: 0 for t in thresholds}
        
        for dist, _, _ in distances:
            for t in thresholds:
                if dist <= t:
                    counts[t] += 1
                    break
            else:
                counts[30] += 1
        
        total_pairs = len(distances)
        for t in thresholds:
            label = f"≤ {t:2d} bits"
            typer.echo(f"  {label}: {counts[t]:4d} pairs ({counts[t]/total_pairs*100:.1f}%)")
        typer.echo(f"  > 30 bits: {counts[30]:4d} pairs ({counts[30]/total_pairs*100:.1f}%)")
        
        typer.echo("\nDetailed suggestions:")
        typer.echo("  • Very strict (near-exact): 0.90 to 0.95 (≤ 3–6 bits)")
        typer.echo("  • Good for resized/cropped: 0.75 to 0.85 (≤ 10–16 bits)")
        typer.echo("  • Lenient: 0.65 to 0.74 (≤ 17–22 bits)")