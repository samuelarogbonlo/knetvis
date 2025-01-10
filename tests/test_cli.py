import os
from unittest.mock import Mock, patch

from click.testing import CliRunner

from knetvis.cli import cli


@patch("knetvis.cli.NetworkVisualizer")
@patch("knetvis.cli.PolicyParser")
def test_visualize_command(mock_policy_parser, mock_visualizer):
    # Setup mock instances
    mock_parser_instance = Mock()
    mock_visualizer_instance = Mock()

    # Configure mock returns
    mock_policy_parser.return_value = mock_parser_instance
    mock_visualizer.return_value = mock_visualizer_instance

    # Ensure the mock returns something valid
    mock_parser_instance.get_namespace_policies.return_value = []
    mock_visualizer_instance.create_graph.return_value = Mock()
    mock_visualizer_instance.save_graph.return_value = None

    # Run command
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create any necessary files or directories
        os.makedirs("output", exist_ok=True)
        result = runner.invoke(cli, ["visualize", "default"])
        assert result.exit_code == 0
        assert "Visualization created for namespace 'default'" in result.output

    # Verify our mocks were called correctly
    mock_parser_instance.get_namespace_policies.assert_called_once_with("default")
    mock_visualizer_instance.create_graph.assert_called_once()
    mock_visualizer_instance.save_graph.assert_called_once()


@patch("knetvis.cli.TrafficSimulator")
def test_test_command(mock_simulator):
    # Setup mock
    mock_simulator_instance = Mock()
    mock_simulator.return_value = mock_simulator_instance
    mock_simulator_instance.check_resource_exists.return_value = True
    mock_simulator_instance.test_connectivity.return_value = True

    runner = CliRunner()
    result = runner.invoke(cli, ["test", "default/pod/frontend", "default/pod/backend"])
    assert result.exit_code == 0
    assert "Traffic is allowed" in result.output

    # Verify the simulator was called correctly
    mock_simulator_instance.check_resource_exists.assert_called()
    mock_simulator_instance.test_connectivity.assert_called_once()


@patch("knetvis.cli.PolicyParser")
def test_validate_command(mock_policy_parser):
    # Setup mock
    mock_parser_instance = Mock()
    mock_policy_parser.return_value = mock_parser_instance
    mock_parser_instance.validate_policy.return_value = (True, "Valid")

    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create a test policy file
        with open("test-policy.yaml", "w") as f:
            f.write("apiVersion: networking.k8s.io/v1\nkind: NetworkPolicy\n")

        result = runner.invoke(cli, ["validate", "test-policy.yaml"])
        assert result.exit_code == 0
        assert "Policy is valid" in result.output

        # Verify the parser was called correctly
        mock_parser_instance.validate_policy.assert_called_once_with("test-policy.yaml")
