from typing import List

from kubernetes import client

from .models import Target
from .policy import PolicyParser


class TrafficSimulator:
    def __init__(self, policy_parser: PolicyParser) -> None:
        self.policy_parser = policy_parser
        self.core_api = client.CoreV1Api()

    def check_resource_exists(self, target: "Target") -> bool:
        """Check if a pod exists in the specified namespace"""
        try:
            self.core_api.read_namespaced_pod(target.name, target.namespace)
            return True
        except client.exceptions.ApiException as e:
            if e.status == 404:
                return False
            raise e

    def test_connectivity(self, source: "Target", dest: "Target") -> bool:
        try:
            source_policies = self.policy_parser.get_namespace_policies(
                source.namespace
            )
            dest_policies = self.policy_parser.get_namespace_policies(dest.namespace)

            # If no policies affect either pod, traffic is allowed
            source_affected = self._policies_affect_pod(source_policies, source)
            dest_affected = self._policies_affect_pod(dest_policies, dest)

            if not source_affected and not dest_affected:
                return True

            egress_allowed = self._check_egress_policies(source, dest, source_policies)
            ingress_allowed = self._check_ingress_policies(source, dest, dest_policies)

            print(f"Source affected: {source_affected}")
            print(f"Dest affected: {dest_affected}")
            print(f"Egress allowed: {egress_allowed}")
            print(f"Ingress allowed: {ingress_allowed}")

            return egress_allowed and ingress_allowed

        except Exception as e:
            raise Exception(f"Failed to test connectivity: {str(e)}")

    def _policies_affect_pod(self, policies: List[dict], target: "Target") -> bool:
        for policy in policies:
            spec = policy.get("spec", {})
            pod_selector = spec.get("pod_selector", {}) or spec.get("podSelector", {})
            if self._matches_selector(target, pod_selector):
                return True
        return False

    def _check_egress_policies(
        self, source: "Target", dest: "Target", policies: List[dict]
    ) -> bool:
        matching_policies = [
            p
            for p in policies
            if self._matches_selector(
                source,
                p["spec"].get("pod_selector", {}) or p["spec"].get("podSelector", {}),
            )
        ]

        if not matching_policies:
            return True

        for policy in matching_policies:
            if self._policy_allows_egress(policy, source, dest):
                return True
        return False

    def _check_ingress_policies(
        self, source: "Target", dest: "Target", policies: List[dict]
    ) -> bool:
        matching_policies = [
            p
            for p in policies
            if self._matches_selector(
                dest,
                p["spec"].get("pod_selector", {}) or p["spec"].get("podSelector", {}),
            )
        ]

        if not matching_policies:
            return True

        for policy in matching_policies:
            if self._policy_allows_ingress(policy, source, dest):
                return True
        return False

    def _matches_selector(self, target: "Target", selector: dict) -> bool:
        try:
            obj = self.core_api.read_namespaced_pod(target.name, target.namespace)
            pod_labels = obj.metadata.labels or {}

            match_labels = selector.get("match_labels", {}) or selector.get(
                "matchLabels", {}
            )
            match_expressions = selector.get("match_expressions", []) or selector.get(
                "matchExpressions", []
            )

            if match_labels and not all(
                pod_labels.get(k) == v for k, v in match_labels.items()
            ):
                return False

            for expr in match_expressions:
                key = expr["key"]
                operator = expr["operator"]
                values = expr.get("values", [])

                if operator == "In" and pod_labels.get(key) not in values:
                    return False
                elif operator == "NotIn" and pod_labels.get(key) in values:
                    return False
                elif operator == "Exists" and key not in pod_labels:
                    return False
                elif operator == "DoesNotExist" and key in pod_labels:
                    return False

            return True
        except Exception as e:
            print(f"Error matching selector: {e}")
            return False

    def _policy_allows_egress(
        self, policy: dict, source: "Target", dest: "Target"
    ) -> bool:
        spec = policy.get("spec", {})
        if "egress" not in spec and "policyTypes" not in spec:
            return True

        egress_rules = spec.get("egress", [])
        if not egress_rules:
            return "Egress" not in spec.get("policyTypes", [])

        for rule in egress_rules:
            if self._egress_rule_matches(rule, dest):
                return True
        return False

    def _policy_allows_ingress(
        self, policy: dict, source: "Target", dest: "Target"
    ) -> bool:
        spec = policy.get("spec", {})
        if "ingress" not in spec and "policyTypes" not in spec:
            return True

        ingress_rules = spec.get("ingress", [])
        if not ingress_rules:
            return "Ingress" not in spec.get("policyTypes", [])

        for rule in ingress_rules:
            if self._ingress_rule_matches(rule, source):
                return True
        return False

    def _egress_rule_matches(self, rule: dict, dest: "Target") -> bool:
        if not rule.get("to", []):
            return True

        for to_peer in rule.get("to", []):
            pod_selector = to_peer.get("pod_selector", {}) or to_peer.get(
                "podSelector", {}
            )
            if pod_selector and self._matches_selector(dest, pod_selector):
                return True

            namespace_selector = to_peer.get("namespace_selector", {}) or to_peer.get(
                "namespaceSelector", {}
            )
            if namespace_selector:
                try:
                    ns = self.core_api.read_namespace(dest.namespace)
                    ns_labels = ns.metadata.labels or {}
                    match_labels = namespace_selector.get(
                        "match_labels", {}
                    ) or namespace_selector.get("matchLabels", {})
                    if all(ns_labels.get(k) == v for k, v in match_labels.items()):
                        return True
                except client.exceptions.ApiException as e:
                    print(f"Error checking namespace: {e}")
                    return False
        return False

    def _ingress_rule_matches(self, rule: dict, source: "Target") -> bool:
        # Handle both 'from' and '_from' keys
        from_peers = rule.get("from", []) or rule.get("_from", [])
        if not from_peers:
            return True

        for from_peer in from_peers:
            pod_selector = from_peer.get("pod_selector", {}) or from_peer.get(
                "podSelector", {}
            )
            if pod_selector and self._matches_selector(source, pod_selector):
                return True

            namespace_selector = from_peer.get(
                "namespace_selector", {}
            ) or from_peer.get("namespaceSelector", {})
            if namespace_selector:
                try:
                    ns = self.core_api.read_namespace(source.namespace)
                    ns_labels = ns.metadata.labels or {}
                    match_labels = namespace_selector.get(
                        "match_labels", {}
                    ) or namespace_selector.get("matchLabels", {})
                    if all(ns_labels.get(k) == v for k, v in match_labels.items()):
                        return True
                except client.exceptions.ApiException as e:
                    print(f"Error checking namespace: {e}")
                    return False
        return False
