from unittest.mock import Mock, patch

from src.knetvis.policy import PolicyParser


def test_load_policy_file(tmp_path):
    # Create a test policy file
    policy_content = """
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: test-policy
  namespace: default
spec:
  podSelector:
    matchLabels:
      app: web
  policyTypes:
    - Ingress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              role: frontend
    """
    policy_file = tmp_path / "test-policy.yaml"
    policy_file.write_text(policy_content)

    parser = PolicyParser()
    policies = parser.load_policy_file(str(policy_file))

    # Get the first policy since we only have one
    policy = policies[0]
    assert policy["metadata"]["name"] == "test-policy"
    assert policy["spec"]["podSelector"]["matchLabels"]["app"] == "web"


@patch("kubernetes.client.NetworkingV1Api")
def test_get_namespace_policies(mock_api):
    # Mock the kubernetes API response
    mock_policy = Mock()
    mock_policy.to_dict.return_value = {
        "metadata": {"name": "test-policy"},
        "spec": {"podSelector": {}},
    }
    mock_api.return_value.list_namespaced_network_policy.return_value.items = [
        mock_policy
    ]

    parser = PolicyParser()
    policies = parser.get_namespace_policies("default")

    assert len(policies) == 1
    assert policies[0]["metadata"]["name"] == "test-policy"
