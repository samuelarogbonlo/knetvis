# src/visualzer.py
from dataclasses import dataclass
from typing import Dict, List, Set

import matplotlib.pyplot as plt
import networkx as nx
from kubernetes import client
from rich.console import Console

console = Console()


@dataclass(frozen=True)
class NetworkNode:
    name: str
    kind: str
    namespace: str
    labels: Dict[str, str]

    def __hash__(self) -> int:
        return hash((self.name, self.namespace))


class NetworkVisualizer:
    def __init__(self) -> None:
        self.graph = nx.DiGraph()
        self.core_api = client.CoreV1Api()
        self.colors: Dict[str, str] = {
            "pod": "#4299E1",
            "namespace": "#48BB78",
            "ipblock": "#F6AD55",
            "allow": "#48BB78",
            "deny": "#F56565",
        }

    def create_graph(self, namespace: str, policies: List[dict]) -> None:
        self.namespace = namespace
        self.graph.clear()
        self._add_namespace_pods(namespace)
        for policy in policies:
            self._add_policy_to_graph(policy)

        nodes_count = self.graph.number_of_nodes()
        edges_count = self.graph.number_of_edges()
        console.print(
            f"[green]Created graph with {nodes_count} nodes "
            f"and {edges_count} edges[/green]"
        )

    def save_graph(self, output_file: str) -> None:
        plt.figure(figsize=(12, 8))
        pos = nx.spring_layout(self.graph, k=1, iterations=50)
        self._draw_nodes(pos)
        self._draw_edges(pos)
        self._add_labels(pos)
        plt.title("Network Policy Visualization")
        plt.axis("off")
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches="tight")
        plt.close()

        console.print(f"[green]Network visualization saved to {output_file}[/green]")

    def _add_namespace_pods(self, namespace: str) -> None:
        """Add all pods in the namespace to the graph"""
        try:
            pods = self.core_api.list_namespaced_pod(namespace)
            console.print("\nPod Label Information:")
            for pod in pods.items:
                console.print(
                    f"Pod: {pod.metadata.name}, " f"Labels: {pod.metadata.labels}"
                )
                node = NetworkNode(
                    name=pod.metadata.name,
                    kind="pod",
                    namespace=namespace,
                    labels=pod.metadata.labels or {},
                )
                self._add_node(node)
        except Exception as e:
            message = f"[yellow]Warning: Failed to fetch pods: {str(e)}[/yellow]"
            console.print(message)

    def _add_policy_to_graph(self, policy: dict) -> None:
        """Process a network policy and add its rules to the graph"""
        spec = policy.get("spec", {})

        # Get pods selected by this policy
        pod_selector = spec.get("pod_selector") or spec.get("podSelector", {})
        selected_pods = self._get_selected_pods(self.namespace, pod_selector)

        pod_names = [pod.name for pod in selected_pods]
        console.print(f"Selected pods: {pod_names}")

        # Process ingress rules if they exist
        ingress_rules = spec.get("ingress", [])
        if ingress_rules is not None:  # Check if ingress rules are defined
            console.print("Processing ingress rules")
            for rule in ingress_rules:
                self._process_ingress_rule(rule, selected_pods)

        # Process egress rules if they exist
        egress_rules = spec.get("egress", [])
        if egress_rules is not None:  # Check if egress rules are defined
            console.print("Processing egress rules")
            for rule in egress_rules:
                self._process_egress_rule(rule, selected_pods)

    def _get_selected_pods(self, namespace: str, selector: dict) -> Set[NetworkNode]:
        """Get pods that match a label selector"""
        try:
            label_selector = self._build_label_selector(selector)
            pods = self.core_api.list_namespaced_pod(
                namespace, label_selector=label_selector
            )

            selected = {
                NetworkNode(
                    name=pod.metadata.name,
                    kind="pod",
                    namespace=namespace,
                    labels=pod.metadata.labels or {},
                )
                for pod in pods.items
            }

            pod_names = [pod.name for pod in selected]
            console.print(f"Found matching pods: {pod_names}")
            return selected

        except Exception as e:
            msg = f"[yellow]Warning: Failed to get selected pods: " f"{str(e)}[/yellow]"
            console.print(msg)
            return set()

    def _process_ingress_rule(self, rule: dict, target_pods: Set[NetworkNode]) -> None:
        from_peers = rule.get("from", []) or rule.get("_from", [])
        if not from_peers:
            return

        for from_peer in from_peers:
            ns_selector = from_peer.get("namespace_selector") or from_peer.get(
                "namespaceSelector"
            )
            pod_selector = from_peer.get("pod_selector") or from_peer.get("podSelector")

            try:
                # When we have both selectors in same peer (AND condition)
                if ns_selector and pod_selector:
                    self._handle_dual_selector(ns_selector, pod_selector, target_pods)
                # Handle single namespace selector
                elif ns_selector:
                    self._handle_namespace_selector(ns_selector, target_pods)
                # Handle single pod selector
                elif pod_selector:
                    self._handle_pod_selector(pod_selector, self.namespace, target_pods)

            except Exception as e:
                msg = (
                    f"[yellow]Warning: Error processing selectors: "
                    f"{str(e)}[/yellow]"
                )
                console.print(msg)

    def _handle_dual_selector(
        self,
        ns_selector: dict,
        pod_selector: dict,
        target_pods: Set[NetworkNode],
    ) -> None:
        """Handle both namespace and pod selectors"""
        ns_label_selector = self._build_label_selector(ns_selector)
        namespaces = self.core_api.list_namespace(label_selector=ns_label_selector)

        ns_names = [ns.metadata.name for ns in namespaces.items]
        console.print(f"Found namespaces matching selector: {ns_names}")

        for ns in namespaces.items:
            pod_label_selector = self._build_label_selector(pod_selector)
            pods = self.core_api.list_namespaced_pod(
                ns.metadata.name, label_selector=pod_label_selector
            )
            console.print(f"Checking pods in namespace {ns.metadata.name}")

            for pod in pods.items:
                source = NetworkNode(
                    name=pod.metadata.name,
                    kind="pod",
                    namespace=ns.metadata.name,
                    labels=pod.metadata.labels or {},
                )
                self._add_node(source)
                for target in target_pods:
                    console.print(
                        f"Adding edge: {source.namespace}/{source.name} "
                        f"-> {target.namespace}/{target.name}"
                    )
                    self._add_edge(source, target, "allow")

    def _handle_namespace_selector(
        self, ns_selector: dict, target_pods: Set[NetworkNode]
    ) -> None:
        """Handle namespace selector only"""
        label_selector = self._build_label_selector(ns_selector)
        namespaces = self.core_api.list_namespace(label_selector=label_selector)
        for ns in namespaces.items:
            source = NetworkNode(
                name=ns.metadata.name,
                kind="namespace",
                namespace="",
                labels=ns.metadata.labels or {},
            )
            self._add_node(source)
            for target in target_pods:
                console.print(f"Adding namespace edge: {source.name} -> {target.name}")
                self._add_edge(source, target, "allow")

    def _handle_pod_selector(
        self,
        pod_selector: dict,
        namespace: str,
        target_pods: Set[NetworkNode],
    ) -> None:
        """Handle pod selector only"""
        source_pods = self._get_selected_pods(namespace, pod_selector)
        for source in source_pods:
            for target in target_pods:
                console.print(f"Adding edge: {source.name} -> {target.name}")
                self._add_node(source)
                self._add_edge(source, target, "allow")

    def _process_egress_rule(self, rule: dict, source_pods: Set[NetworkNode]) -> None:
        """Process an egress rule and add relevant edges"""
        pod_names = [pod.name for pod in source_pods]
        console.print(f"Processing egress rule for sources: {pod_names}")

        for to_peer in rule.get("to", []):
            target_pods = self._get_pods_from_peer(to_peer)
            target_names = [pod.name for pod in target_pods]
            console.print(f"Found target pods: {target_names}")

            for source in source_pods:
                for target in target_pods:
                    console.print(f"Adding edge: {source.name} -> {target.name}")
                    self._add_node(target)
                    self._add_edge(source, target, "allow")

    def _get_pods_from_peer(self, peer: dict) -> Set[NetworkNode]:
        """Get pods that match both namespace and pod selectors"""
        pods = set()

        pod_selector = peer.get("pod_selector") or peer.get("podSelector")
        ns_selector = peer.get("namespace_selector") or peer.get("namespaceSelector")

        try:
            if ns_selector and pod_selector:
                pods = self._get_pods_with_dual_selector(ns_selector, pod_selector)
            elif ns_selector:
                pods = self._get_pods_with_ns_selector(ns_selector)
            elif pod_selector:
                pods = self._get_selected_pods(self.namespace, pod_selector)

        except Exception as e:
            msg = (
                f"[yellow]Warning: Error getting pods from peer: " f"{str(e)}[/yellow]"
            )
            console.print(msg)

        return pods

    def _get_pods_with_dual_selector(
        self, ns_selector: dict, pod_selector: dict
    ) -> Set[NetworkNode]:
        """Get pods matching both namespace and pod selectors"""
        pods = set()
        ns_label_selector = self._build_label_selector(ns_selector)
        namespaces = self.core_api.list_namespace(label_selector=ns_label_selector)

        pod_label_selector = self._build_label_selector(pod_selector)
        for ns in namespaces.items:
            ns_pods = self.core_api.list_namespaced_pod(
                ns.metadata.name, label_selector=pod_label_selector
            )
            for pod in ns_pods.items:
                pods.add(
                    NetworkNode(
                        name=pod.metadata.name,
                        kind="pod",
                        namespace=ns.metadata.name,
                        labels=pod.metadata.labels or {},
                    )
                )
            pod_names = [p.name for p in pods]
            console.print(f"Found pods in namespace {ns.metadata.name}: {pod_names}")

        return pods

    def _get_pods_with_ns_selector(self, ns_selector: dict) -> Set[NetworkNode]:
        """Get pods using namespace selector only"""
        pods = set()
        label_selector = self._build_label_selector(ns_selector)
        namespaces = self.core_api.list_namespace(label_selector=label_selector)
        for ns in namespaces.items:
            pods.add(
                NetworkNode(
                    name=ns.metadata.name,
                    kind="namespace",
                    namespace="",
                    labels=ns.metadata.labels or {},
                )
            )
        return pods

    def _build_label_selector(self, selector: dict) -> str:
        """Build a label selector string from a selector dict"""
        if not selector:
            return ""

        parts = []
        match_labels = selector.get("match_labels") or selector.get("matchLabels", {})
        for key, value in match_labels.items():
            parts.append(f"{key}={value}")

        return ",".join(parts)

    def _add_node(self, node: NetworkNode) -> None:
        """Add a node to the graph if it doesn't exist"""
        node_id = f"{node.namespace}/{node.name}"
        if node_id not in self.graph:
            self.graph.add_node(
                node_id,
                kind=node.kind,
                namespace=node.namespace,
                labels=node.labels,
            )

    def _add_edge(
        self, source: NetworkNode, target: NetworkNode, policy_type: str
    ) -> None:
        """Add an edge between nodes"""
        source_id = f"{source.namespace}/{source.name}"
        target_id = f"{target.namespace}/{target.name}"
        self.graph.add_edge(source_id, target_id, type=policy_type)

    def _draw_nodes(self, pos: dict) -> None:
        """Draw nodes with different colors based on type"""
        for kind in ["pod", "namespace", "ipblock"]:
            nodes = [n for n, d in self.graph.nodes(data=True) if d["kind"] == kind]
            if nodes:
                nx.draw_networkx_nodes(
                    self.graph,
                    pos,
                    nodelist=nodes,
                    node_color=self.colors[kind],
                    node_size=1000,
                    alpha=0.8,
                )

    def _draw_edges(self, pos: dict) -> None:
        """Draw edges with different colors based on policy type"""
        for policy_type in ["allow", "deny"]:
            edges = [
                (u, v)
                for u, v, d in self.graph.edges(data=True)
                if d["type"] == policy_type
            ]
            if edges:
                nx.draw_networkx_edges(
                    self.graph,
                    pos,
                    edgelist=edges,
                    edge_color=self.colors[policy_type],
                    arrows=True,
                    arrowsize=20,
                )

    def _add_labels(self, pos: dict) -> None:
        """Add labels to nodes"""
        labels = {}
        for node in self.graph.nodes():
            name = node.split("/")[-1]
            kind = self.graph.nodes[node]["kind"]
            labels[node] = f"{kind}\n{name}"

        nx.draw_networkx_labels(
            self.graph, pos, labels, font_size=8, font_weight="bold"
        )
