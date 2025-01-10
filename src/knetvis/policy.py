from typing import List, Tuple

import yaml
from kubernetes import client, config


class PolicyParser:
    def __init__(self) -> None:
        # Load kubernetes configuration
        try:
            config.load_kube_config()
        except Exception:
            config.load_incluster_config()

        self.api = client.NetworkingV1Api()

    def load_policy_file(self, filename: str) -> List[dict]:
        with open(filename, "r") as f:
            return list(yaml.safe_load_all(f))

    def get_namespace_policies(self, namespace: str) -> List[dict]:
        """Retrieve all NetworkPolicies in a namespace"""
        try:
            policies = self.api.list_namespaced_network_policy(namespace)
            return [p.to_dict() for p in policies.items]
        except Exception as e:
            raise Exception(f"Failed to get policies: {str(e)}")

    def validate_policy(self, policy_file: str) -> Tuple[bool, str]:
        """Validate a network policy file"""
        try:
            policies = self.load_policy_file(policy_file)
            all_issues = []

            for doc in policies:
                if not doc:  # Skip empty documents
                    continue

                if doc.get("kind") == "NetworkPolicy":
                    # Validate NetworkPolicy
                    issues = self._validate_network_policy(doc)
                    all_issues.extend(issues)
                elif doc.get("kind") == "Namespace":
                    # Basic namespace validation
                    if "metadata" not in doc or "name" not in doc["metadata"]:
                        all_issues.append(
                            "Namespace missing required metadata.name field"
                        )
                elif doc.get("kind") == "Pod":
                    # Basic pod validation
                    if "metadata" not in doc or "name" not in doc["metadata"]:
                        all_issues.append("Pod missing required metadata.name field")

            if all_issues:
                return False, "\n".join(all_issues)
            return True, "All documents are valid"

        except yaml.YAMLError as e:
            return False, f"YAML validation error: {str(e)}"
        except Exception as e:
            return False, f"Validation error: {str(e)}"

    def _validate_network_policy(self, policy: dict) -> List[str]:
        """Validate a single NetworkPolicy document"""
        issues = []

        # Check required fields
        required_fields = ["apiVersion", "kind", "metadata", "spec"]
        for field in required_fields:
            if field not in policy:
                issues.append(f"Missing required field: {field}")

        if not issues:  # Only continue if basic structure is valid
            spec = policy.get("spec", {})
            if not spec:
                issues.append("Empty spec in NetworkPolicy")
                return issues

            # Check podSelector exists
            if "podSelector" not in spec:
                issues.append("Missing podSelector in spec")

            # Validate ingress rules
            if "ingress" in spec:
                ingress_issues = self._validate_ingress_rules(spec["ingress"])
                issues.extend(ingress_issues)

            # Validate egress rules
            if "egress" in spec:
                egress_issues = self._validate_egress_rules(spec["egress"])
                issues.extend(egress_issues)

        return issues

    def _validate_ingress_rules(self, rules: List[dict]) -> List[str]:
        """Validate ingress rules in a NetworkPolicy"""
        issues = []

        for i, rule in enumerate(rules, 1):
            # Validate ports
            if "ports" in rule:
                for port in rule.get("ports", []):
                    if "port" not in port:
                        issues.append(
                            f"Ingress rule {i}: Port specification missing port number"
                        )
                    if "protocol" in port and port["protocol"] not in [
                        "TCP",
                        "UDP",
                        "SCTP",
                    ]:
                        issues.append(
                            f"Ingress rule {i}: Invalid protocol {port['protocol']}"
                        )

            # Validate from section
            if "from" in rule:
                for peer in rule["from"]:
                    if not any(
                        k in peer
                        for k in [
                            "podSelector",
                            "namespaceSelector",
                            "ipBlock",
                        ]
                    ):
                        issues.append(f"Ingress rule {i}: Peer missing selector")

        return issues

    def _validate_egress_rules(self, rules: List[dict]) -> List[str]:
        """Validate egress rules in a NetworkPolicy"""
        issues = []

        for i, rule in enumerate(rules, 1):
            # Validate ports
            if "ports" in rule:
                for port in rule.get("ports", []):
                    if "port" not in port:
                        issues.append(
                            f"Egress rule {i}: Port specification missing port number"
                        )
                    if "protocol" in port and port["protocol"] not in [
                        "TCP",
                        "UDP",
                        "SCTP",
                    ]:
                        issues.append(
                            f"Egress rule {i}: Invalid protocol {port['protocol']}"
                        )

            # Validate to section
            if "to" in rule:
                for peer in rule["to"]:
                    if not any(
                        k in peer
                        for k in [
                            "podSelector",
                            "namespaceSelector",
                            "ipBlock",
                        ]
                    ):
                        issues.append(f"Egress rule {i}: Peer missing selector")

        return issues
