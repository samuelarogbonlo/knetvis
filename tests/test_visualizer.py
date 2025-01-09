import pytest
from unittest.mock import Mock, patch
import networkx as nx
from src.visualizer import NetworkVisualizer

@patch('kubernetes.client.CoreV1Api')
def test_create_graph(mock_core_api):
    # Mock pod list response
    mock_pod = Mock()
    mock_pod.metadata.name = 'test-pod'
    mock_pod.metadata.labels = {'app': 'web'}
    mock_core_api.return_value.list_namespaced_pod.return_value.items = [mock_pod]

    visualizer = NetworkVisualizer()

    # Test policy that selects the pod
    policies = [{
        'metadata': {'namespace': 'default'},
        'spec': {
            'podSelector': {
                'matchLabels': {'app': 'web'}
            },
            'ingress': [{
                'from': [{
                    'podSelector': {
                        'matchLabels': {'role': 'frontend'}
                    }
                }]
            }]
        }
    }]

    visualizer.create_graph('default', policies)

    # Verify graph structure
    assert visualizer.graph.number_of_nodes() > 0

def test_save_graph(tmp_path):
    visualizer = NetworkVisualizer()

    # Add some test nodes and edges
    visualizer.graph.add_node('pod1', kind='pod', namespace='default', labels={})
    visualizer.graph.add_node('pod2', kind='pod', namespace='default', labels={})
    visualizer.graph.add_edge('pod1', 'pod2', type='allow')

    # Test saving the graph
    output_file = str(tmp_path / "test_graph.png")
    visualizer.save_graph(output_file)

    assert tmp_path.exists()