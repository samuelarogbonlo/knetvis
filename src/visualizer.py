# src/visualzer.py
from typing import List, Dict, Set, Optional
import networkx as nx
import matplotlib.pyplot as plt
from kubernetes import client
from dataclasses import dataclass
from rich.console import Console

console = Console()

@dataclass(frozen=True)
class NetworkNode:
    """Represents a node in the network graph"""
    name: str
    kind: str  # 'pod', 'namespace', 'ipblock'
    namespace: str
    labels: Dict[str, str]

    def __hash__(self):
        # Hash based on name and namespace which should be unique
        return hash((self.name, self.namespace))

class NetworkVisualizer:
    """Creates visual representations of network policies"""

    def __init__(self):
        self.graph = nx.DiGraph()
        self.core_api = client.CoreV1Api()

        # Color scheme
        self.colors = {
            'pod': '#4299E1',       # Blue
            'namespace': '#48BB78',  # Green
            'ipblock': '#F6AD55',    # Orange
            'allow': '#48BB78',      # Green
            'deny': '#F56565'        # Red
        }

    def create_graph(self, namespace: str, policies: List[dict]):
        """Create a graph representation of network policies"""
        self.namespace = namespace
        self.graph.clear()

        # Add nodes for all pods in the namespace
        self._add_namespace_pods(namespace)

        # Process each policy
        for policy in policies:
            self._add_policy_to_graph(policy)

        console.print(f"[green]Created graph with {self.graph.number_of_nodes()} nodes "
                     f"and {self.graph.number_of_edges()} edges[/green]")

    def save_graph(self, output_file: str):
        """Save the network graph visualization to a file"""
        plt.figure(figsize=(12, 8))

        # Create layout
        pos = nx.spring_layout(self.graph, k=1, iterations=50)

        # Draw nodes
        self._draw_nodes(pos)

        # Draw edges
        self._draw_edges(pos)

        # Add labels
        self._add_labels(pos)

        plt.title("Network Policy Visualization")
        plt.axis('off')
        plt.tight_layout()

        # Save to file
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()

        console.print(f"[green]Network visualization saved to {output_file}[/green]")

    def _add_namespace_pods(self, namespace: str):
        """Add all pods in the namespace to the graph"""
        try:
            pods = self.core_api.list_namespaced_pod(namespace)
            console.print("\nPod Label Information:")
            for pod in pods.items:
                console.print(f"Pod: {pod.metadata.name}, Labels: {pod.metadata.labels}")
                node = NetworkNode(
                    name=pod.metadata.name,
                    kind='pod',
                    namespace=namespace,
                    labels=pod.metadata.labels or {}
                )
                self._add_node(node)
        except Exception as e:
            console.print(f"[yellow]Warning: Failed to fetch pods: {str(e)}[/yellow]")

    def _add_policy_to_graph(self, policy: dict):
        """Process a network policy and add its rules to the graph"""
        spec = policy.get('spec', {})

        # Get pods selected by this policy
        pod_selector = spec.get('pod_selector') or spec.get('podSelector', {})
        selected_pods = self._get_selected_pods(self.namespace, pod_selector)

        console.print(f"Selected pods: {[pod.name for pod in selected_pods]}")

        # Process ingress rules if they exist
        ingress_rules = spec.get('ingress', [])
        if ingress_rules is not None:  # Check if ingress rules are defined
            console.print("Processing ingress rules")
            for rule in ingress_rules:
                self._process_ingress_rule(rule, selected_pods)

        # Process egress rules if they exist
        egress_rules = spec.get('egress', [])
        if egress_rules is not None:  # Check if egress rules are defined
            console.print("Processing egress rules")
            for rule in egress_rules:
                self._process_egress_rule(rule, selected_pods)

    def _get_selected_pods(self, namespace: str, selector: dict) -> Set[NetworkNode]:
        """Get pods that match a label selector"""
        try:
            label_selector = self._build_label_selector(selector)
            pods = self.core_api.list_namespaced_pod(
                namespace,
                label_selector=label_selector
            )

            selected = {
                NetworkNode(
                    name=pod.metadata.name,
                    kind='pod',
                    namespace=namespace,
                    labels=pod.metadata.labels or {}
                )
                for pod in pods.items
            }
            console.print(f"Found matching pods: {[pod.name for pod in selected]}")
            return selected

        except Exception as e:
            console.print(f"[yellow]Warning: Failed to get selected pods: {str(e)}[/yellow]")
            return set()

    def _process_ingress_rule(self, rule: dict, target_pods: Set[NetworkNode]):
        from_peers = rule.get('from', []) or rule.get('_from', [])
        if not from_peers:
            return

        for from_peer in from_peers:
            namespace_selector = from_peer.get('namespace_selector') or from_peer.get('namespaceSelector')
            pod_selector = from_peer.get('pod_selector') or from_peer.get('podSelector')

            try:
                # When we have both selectors in same peer (AND condition)
                if namespace_selector and pod_selector:
                    ns_label_selector = self._build_label_selector(namespace_selector)
                    namespaces = self.core_api.list_namespace(label_selector=ns_label_selector)
                    console.print(f"Found namespaces matching selector: {[ns.metadata.name for ns in namespaces.items]}")

                    # For each matching namespace, find matching pods
                    for ns in namespaces.items:
                        pod_label_selector = self._build_label_selector(pod_selector)
                        pods = self.core_api.list_namespaced_pod(
                            ns.metadata.name,
                            label_selector=pod_label_selector
                        )
                        console.print(f"Checking pods in namespace {ns.metadata.name}")

                        # Add edges for each matching pod
                        for pod in pods.items:
                            source = NetworkNode(
                                name=pod.metadata.name,
                                kind='pod',
                                namespace=ns.metadata.name,
                                labels=pod.metadata.labels or {}
                            )
                            self._add_node(source)
                            for target in target_pods:
                                console.print(f"Adding edge: {source.namespace}/{source.name} -> {target.namespace}/{target.name}")
                                self._add_edge(source, target, 'allow')

                # Handle single namespace selector
                elif namespace_selector:
                    label_selector = self._build_label_selector(namespace_selector)
                    namespaces = self.core_api.list_namespace(label_selector=label_selector)
                    for ns in namespaces.items:
                        source = NetworkNode(
                            name=ns.metadata.name,
                            kind='namespace',
                            namespace='',
                            labels=ns.metadata.labels or {}
                        )
                        self._add_node(source)
                        for target in target_pods:
                            console.print(f"Adding namespace edge: {source.name} -> {target.name}")
                            self._add_edge(source, target, 'allow')

                # Handle single pod selector
                elif pod_selector:
                    source_pods = self._get_selected_pods(self.namespace, pod_selector)
                    for source in source_pods:
                        for target in target_pods:
                            console.print(f"Adding edge: {source.name} -> {target.name}")
                            self._add_node(source)
                            self._add_edge(source, target, 'allow')

            except Exception as e:
                console.print(f"[yellow]Warning: Error processing selectors: {str(e)}[/yellow]")

    def _process_egress_rule(self, rule: dict, source_pods: Set[NetworkNode]):
        """Process an egress rule and add relevant edges"""
        console.print(f"Processing egress rule for sources: {[pod.name for pod in source_pods]}")

        for to_peer in rule.get('to', []):
            target_pods = self._get_pods_from_peer(to_peer)
            console.print(f"Found target pods: {[pod.name for pod in target_pods]}")

            for source in source_pods:
                for target in target_pods:
                    console.print(f"Adding edge: {source.name} -> {target.name}")
                    self._add_node(target)
                    self._add_edge(source, target, 'allow')

    def _get_pods_from_peer(self, peer: dict) -> Set[NetworkNode]:
        """Get pods that match both namespace and pod selectors when specified"""
        pods = set()

        # Handle snake_case vs camelCase
        pod_selector = peer.get('pod_selector') or peer.get('podSelector')
        namespace_selector = peer.get('namespace_selector') or peer.get('namespaceSelector')

        try:
            # If we have both selectors, we need pods matching both conditions
            if namespace_selector and pod_selector:
                # First get matching namespaces
                ns_label_selector = self._build_label_selector(namespace_selector)
                namespaces = self.core_api.list_namespace(label_selector=ns_label_selector)

                # Then for each matching namespace, get matching pods
                pod_label_selector = self._build_label_selector(pod_selector)
                for ns in namespaces.items:
                    ns_pods = self.core_api.list_namespaced_pod(
                        ns.metadata.name,
                        label_selector=pod_label_selector
                    )
                    for pod in ns_pods.items:
                        pods.add(NetworkNode(
                            name=pod.metadata.name,
                            kind='pod',
                            namespace=ns.metadata.name,
                            labels=pod.metadata.labels or {}
                        ))
                    console.print(f"Found pods in namespace {ns.metadata.name}: {[p.name for p in pods]}")

            # If just namespace selector
            elif namespace_selector:
                label_selector = self._build_label_selector(namespace_selector)
                namespaces = self.core_api.list_namespace(label_selector=label_selector)
                for ns in namespaces.items:
                    pods.add(NetworkNode(
                        name=ns.metadata.name,
                        kind='namespace',
                        namespace='',
                        labels=ns.metadata.labels or {}
                    ))

            # If just pod selector
            elif pod_selector:
                pods.update(self._get_selected_pods(self.namespace, pod_selector))

        except Exception as e:
            console.print(f"[yellow]Warning: Error getting pods from peer: {str(e)}[/yellow]")

        return pods

    def _build_label_selector(self, selector: dict) -> str:
        """Build a label selector string from a selector dict"""
        if not selector:
            return ''

        parts = []
        # Handle snake_case match_labels
        match_labels = selector.get('match_labels') or selector.get('matchLabels', {})
        for key, value in match_labels.items():
            parts.append(f"{key}={value}")

        return ','.join(parts)

    def _add_node(self, node: NetworkNode):
        """Add a node to the graph if it doesn't exist"""
        node_id = f"{node.namespace}/{node.name}"
        if node_id not in self.graph:
            self.graph.add_node(
                node_id,
                kind=node.kind,
                namespace=node.namespace,
                labels=node.labels
            )

    def _add_edge(self, source: NetworkNode, target: NetworkNode, policy_type: str):
        """Add an edge between nodes"""
        source_id = f"{source.namespace}/{source.name}"
        target_id = f"{target.namespace}/{target.name}"

        self.graph.add_edge(
            source_id,
            target_id,
            type=policy_type
        )

    def _draw_nodes(self, pos):
        """Draw nodes with different colors based on type"""
        for kind in ['pod', 'namespace', 'ipblock']:
            nodes = [n for n, d in self.graph.nodes(data=True) if d['kind'] == kind]
            if nodes:
                nx.draw_networkx_nodes(
                    self.graph,
                    pos,
                    nodelist=nodes,
                    node_color=self.colors[kind],
                    node_size=1000,
                    alpha=0.8
                )

    def _draw_edges(self, pos):
        """Draw edges with different colors based on policy type"""
        for policy_type in ['allow', 'deny']:
            edges = [(u, v) for u, v, d in self.graph.edges(data=True)
                    if d['type'] == policy_type]
            if edges:
                nx.draw_networkx_edges(
                    self.graph,
                    pos,
                    edgelist=edges,
                    edge_color=self.colors[policy_type],
                    arrows=True,
                    arrowsize=20
                )

    def _add_labels(self, pos):
        """Add labels to nodes"""
        labels = {}
        for node in self.graph.nodes():
            name = node.split('/')[-1]
            kind = self.graph.nodes[node]['kind']
            labels[node] = f"{kind}\n{name}"

        nx.draw_networkx_labels(
            self.graph,
            pos,
            labels,
            font_size=8,
            font_weight='bold'
        )