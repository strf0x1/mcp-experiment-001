"""CLI tool for managing forum database."""

import os

import click

from database import ForumDatabase


@click.group
@click.pass_context
def cli(ctx: click.Context) -> None:
    """Forum database management CLI.

    Manage threads, posts, and other forum data.
    """
    # Initialize database and pass to subcommands
    db_path = os.environ.get("FORUM_DB_PATH")
    ctx.ensure_object(dict)
    ctx.obj["db"] = ForumDatabase(db_path=db_path)


@cli.command
@click.option(
    "-d",
    "--delete",
    type=int,
    required=True,
    help="Post ID to delete",
)
@click.pass_context
def post(ctx: click.Context, delete: int) -> None:
    """Manage posts.

    Examples:
        forum-manage post --delete 5
        forum-manage post -d 5
    """
    db = ctx.obj["db"]

    if delete:
        if db.delete_post(delete):
            click.secho(
                f"✓ Post {delete} deleted successfully",
                fg="green",
            )
        else:
            click.secho(
                f"✗ Post {delete} not found",
                fg="red",
            )
            raise click.Exit(1)


@cli.command
@click.option(
    "-d",
    "--delete",
    type=int,
    required=True,
    help="Thread ID to delete",
)
@click.pass_context
def thread(ctx: click.Context, delete: int) -> None:
    """Manage threads.

    Examples:
        forum-manage thread --delete 3
        forum-manage thread -d 3
    """
    db = ctx.obj["db"]

    if delete:
        if db.delete_thread(delete):
            click.secho(
                f"✓ Thread {delete} deleted successfully",
                fg="green",
            )
        else:
            click.secho(
                f"✗ Thread {delete} not found",
                fg="red",
            )
            raise click.Exit(1)


def main() -> None:
    """Entry point for CLI."""
    cli(obj={})


if __name__ == "__main__":
    main()

