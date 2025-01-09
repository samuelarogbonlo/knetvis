# src/main.py
import os
import click
from rich.console import Console
from .policy import PolicyParser
from .simulator import TrafficSimulator
from .visualizer import NetworkVisualizer

console = Console()

class Target:
    """Represents a Kubernetes resource target"""
    def __init__(self, target_str: str):
        parts = target_str.split('/')
        if len(parts) == 2:
            self.namespace = 'default'
            self.kind, self.name = parts
        elif len(parts) == 3:
            self.namespace, self.kind, self.name = parts
        else:
            raise ValueError(f"Invalid target format: {target_str}")

@click.group()
def cli():
    """knetvis - Kubernetes Network Policy Visualization Tool"""
    pass

@cli.command()
@click.argument('namespace')
@click.option('--output', '-o', default='network.png', help='Output file for visualization')
def visualize(namespace: str, output: str):
    """Visualize network policies in a namespace"""
    try:
        parser = PolicyParser()
        visualizer = NetworkVisualizer()

        # Get policies in namespace
        policies = parser.get_namespace_policies(namespace)

        # Check if namespace exists and has policies
        if not policies:
            console.print(f"[yellow]Warning: No network policies found in namespace '{namespace}'[/yellow]")

        # Create and save visualization
        visualizer.create_graph(namespace, policies)
        visualizer.save_graph(output)

        console.print(f"[green]Network visualization saved to {output}[/green]")
    except client.exceptions.ApiException as e:
        if e.status == 404:
            console.print(f"[red]Error: Namespace '{namespace}' not found[/red]")
        else:
            console.print(f"[red]Error: {str(e)}[/red]")
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")

@cli.command()
@click.argument('source')
@click.argument('destination')
def test(source: str, destination: str):
    """Test connectivity between two resources"""
    try:
        source_target = Target(source)
        dest_target = Target(destination)

        parser = PolicyParser()
        simulator = TrafficSimulator(parser)

        # First check if resources exist
        if not simulator.check_resource_exists(source_target):
            console.print(f"[red]Error: Source resource {source} not found[/red]")
            return
        if not simulator.check_resource_exists(dest_target):
            console.print(f"[red]Error: Destination resource {destination} not found[/red]")
            return

        allowed = simulator.test_connectivity(source_target, dest_target)

        if allowed:
            console.print("[green]✓ Traffic is allowed[/green]")
        else:
            console.print("[red]✗ Traffic is blocked[/red]")

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")

@cli.command()
@click.argument('policy-file')
def validate(policy_file: str):
    """Validate a network policy file"""
    try:
        # First check if file exists
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

if __name__ == '__main__':
    cli()