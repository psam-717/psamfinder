from pathlib import Path
import typer

# from file_duplicate_finder import fin

from psamfinder.finder import (
    find_duplicates,
    print_duplicates,
    delete_duplicates
)

app = typer.Typer(
    name="psamfinder",
    help="Find duplicate files by content (SHA-256)",
    add_completion=True,
    no_args_is_help=True
)

@app.callback(invoke_without_command=True)   # ← this makes it a group
def main(ctx: typer.Context):
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
    )
):
    """Scan directories (and subdirectories) for files with identical content"""
    if not quiet:
        typer.echo(f"Scanning: {directory.resolve()} ...")
    
    duplicates = find_duplicates(str(directory))
    
    if not duplicates:
        typer.echo("No duplicates found")
        raise typer.Exit(0)
    
    print_duplicates(duplicates)
    
    if delete:
        if not typer.confirm("\n Proceed with deletion"):
            typer.echo("Cancelled")
            raise typer.Exit(0)
        
        deleted_anything = delete_duplicates(duplicates, dry_run=dry_run)
        if dry_run:
            typer.echo("\nDry run complete — no files were actually deleted.")
        elif deleted_anything:
            typer.echo("Selected duplicates removed")
        else:
            typer.echo("No files deleted (all groups skipped or invalid choices)")
    # else:
    #     typer.echo("\nUse --delete to remove copies after review")
        
