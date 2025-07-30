"""
Command-line tools for DAMD operations.
"""

import click
from pathlib import Path

from damd.core import DAMDFile
from damd.handlers import list_handlers, get_handler
from damd.utils import format_size


@click.group()
def cli():
    """DAMD - Data As Metadata in Data CLI Tools."""
    pass


@click.command()
@click.argument("filepath", type=click.Path(exists=True), required=True)
def damdls(filepath):
    """List DAMD segments in a file."""
    damd_file = DAMDFile(filepath)
    
    try:
        damd_file.load()
    except Exception as e:
        click.echo(f"Error loading DAMD file: {e}")
        return
    
    segments = damd_file.list_segments()
    if not segments:
        click.echo("No DAMD segments found.")
    else:
        click.echo(f"Found {len(segments)} DAMD segments:")
        for i, segment in enumerate(segments, 1):
            click.echo(f"  {i}. {segment}")


@click.command()
@click.argument("filepath", type=click.Path(exists=True), required=True)
@click.argument("key", type=str)
def damdcat(filepath, key):
    """Display DAMD segment data."""
    damd_file = DAMDFile(filepath)
    
    try:
        damd_file.load()
        data = damd_file.get_text(key)
        if data is None:
            click.echo(f"Segment '{key}' not found.")
        else:
            click.echo(data)
    except Exception as e:
        click.echo(f"Error accessing DAMD file: {e}")


@click.command()
@click.argument("filepath", type=click.Path(exists=True), required=True)
@click.argument("key", type=str)
def damdrm(filepath, key):
    """Remove a DAMD segment."""
    damd_file = DAMDFile(filepath)
    
    try:
        damd_file.load()
        success = damd_file.remove_segment(key)
        if success:
            damd_file.save()
            click.echo(f"Segment '{key}' removed.")
        else:
            click.echo(f"Segment '{key}' not found.")
    except Exception as e:
        click.echo(f"Error modifying DAMD file: {e}")


@click.command()
def damdinfo():
    """Display information about registered DAMD handlers."""
    handlers = list_handlers()
    if not handlers:
        click.echo("No handlers registered.")
    else:
        click.echo(f"Registered handlers ({len(handlers)}):")
        for i, handler in enumerate(handlers, 1):
            click.echo(f"  {i}. {handler}")


@click.command()
@click.argument("filepath", type=click.Path(exists=True), required=True)
def damdwrite(filepath):
    """Process file and write DAMD metadata."""
    path = Path(filepath)
    handler = get_handler(path)
    
    if handler is None:
        click.echo(f"No handler available for file type '{path.suffix}'.")
        return
    
    damd_file = DAMDFile(filepath)
    
    try:
        handler.process_file(path, damd_file)
        damd_file.save()
        click.echo(f"DAMD metadata written for '{path.name}'.")
    except Exception as e:
        click.echo(f"Error processing file: {e}")


cli.add_command(damdls)
cli.add_command(damdcat)
cli.add_command(damdrm)
cli.add_command(damdinfo)
cli.add_command(damdwrite)

