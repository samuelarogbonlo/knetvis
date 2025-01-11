import pytest
from unittest.mock import patch


@pytest.fixture(autouse=True)
def mock_kube_config():
    """Mock kubernetes config for all tests"""
    with patch('kubernetes.config.load_kube_config') as mock_kube, \
         patch('kubernetes.config.load_incluster_config') as mock_incluster:
        mock_kube.side_effect = Exception()  # Force fallback to incluster
        mock_incluster.return_value = None
        yield
