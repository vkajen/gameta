from typing import Tuple, Dict

import click

from gameta.context import GametaContext


__all__ = ['exec']


@click.option('--command', '-c', 'commands', type=str, multiple=True, required=True,
              help='Gameta commands to be invoked')
@click.pass_context
def exec(context: click.Context, commands: Tuple[str]) -> None:
    """
    Executes Gameta commands from the CLI command store
    \f
    Args:
        context (click.Context): Click Context
        commands (Tuple[str]): Gameta commands to be executed

    Returns:
        None

    Raises:
        click.ClickException: If errors occur during processing
    """
    def get_command(command_name: str) -> Dict:
        """
        Structures a command for execution

        Args:
            command_name (str): Command to be executed

        Returns:
            Dict: Structured command output
        """
        return {
            p: g_context.commands[command_name][p]
            for p in ['commands', 'tags', 'repositories', 'verbose', 'shell', 'raise_errors', 'python']
        }

    from gameta.apply import apply

    g_context: GametaContext = context.obj
    if any(c not in g_context.commands for c in commands):
        raise click.ClickException(
            f"One of the commands in {list(commands)} does not exist in the Gameta command store, please run "
            f"`gameta cmd add` to add it first"
        )

    try:
        click.echo(f"Executing {list(commands)}")
        for command in commands:
            click.echo(f"Executing Gameta command {command}")
            context.invoke(apply, **get_command(command))
    except Exception as e:
        raise click.ClickException(f"{e.__class__.__name__}.{str(e)}")
