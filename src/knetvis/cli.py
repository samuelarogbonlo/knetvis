import os
from typing import Any, Dict, List

import click
from rich.console import Console

from knetvis.visualizer import NetworkVisualizer

from .models import Target
from .policy import PolicyParser
from .simulator import TrafficSimulator

console = Console()


@click.group()
def cli() -> None:
    """knetvis - Kubernetes Network Policy Visualization Tool"""
    pass


@cli.command()
@click.argument("namespace")
def visualize(namespace: str) -> None:
    """Visualize network policies in a namespace."""
    try:
        parser = PolicyParser()
        policies: List[Dict[str, Any]] = parser.get_namespace_policies(namespace)

        visualizer = NetworkVisualizer()
        # Passing required namespace and policies arguments
        visualizer.create_graph(namespace=namespace, policies=policies)

        # Create output directory if it doesn't exist
        os.makedirs("output", exist_ok=True)

        # Save graph with output filename
        output_file = os.path.join("output", f"{namespace}-network-policies.png")
        visualizer.save_graph(output_file=output_file)

        console.print(
            f"[green]✓ Visualization created for namespace '{namespace}'[/green]"
        )
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")


@cli.command()
@click.argument("source")
@click.argument("destination")
def test(source: str, destination: str) -> None:
    """Test connectivity between resources."""
    try:
        source_target = Target.from_str(source)
        dest_target = Target.from_str(destination)
        parser = PolicyParser()
        simulator = TrafficSimulator(parser)

        if not simulator.check_resource_exists(source_target):
            console.print(f"[red]Error: Source resource {source} not found[/red]")
            return
        if not simulator.check_resource_exists(dest_target):
            console.print(
                f"[red]Error: Destination resource {destination} not found[/red]"
            )
            return

        allowed = simulator.test_connectivity(source_target, dest_target)

        if allowed:
            console.print("[green]✓ Traffic is allowed[/green]")
        else:
            console.print("[red]✗ Traffic is blocked[/red]")

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")


@cli.command()
@click.argument("policy-file")
def validate(policy_file: str) -> None:
    """Validate a network policy file"""
    try:
        if not os.path.exists(policy_file):
            console.print(f"[red]Error: File '{policy_file}' does not exist[/red]")
            return

        parser = PolicyParser()
        is_valid, message = parser.validate_policy(policy_file)

        if is_valid:
            console.print("[green]✓ Policy is valid[/green]")
        else:
            console.print("[yellow]Policy has potential issues:[/yellow]")
            console.print(f"[yellow]{message}[/yellow]")

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")


if __name__ == "__main__":
    cli()
