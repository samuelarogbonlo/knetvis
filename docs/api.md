# API Reference

## CLI Commands

### `visualize`

Visualizes network policies in a namespace.

**Usage:**
```bash
knetvis visualize NAMESPACE [OPTIONS]
```

**Options:**
- `-o, --output`: Output file path
- `--show-external`: Include external connections
- `--layout`: Graph layout algorithm

### `test`

Tests connectivity between Kubernetes resources.

**Usage:**
```bash
knetvis test SOURCE DESTINATION
```

### `validate`

Validates network policy files.

**Usage:**
```bash
knetvis validate [OPTIONS] POLICY_FILE
```

## Python API

### PolicyParser

```python
from knetvis import PolicyParser

parser = PolicyParser()
policy = parser.load_policy_file("policy.yaml")
issues = parser.validate_policy(policy)
```

### TrafficSimulator

```python
from knetvis import TrafficSimulator

simulator = TrafficSimulator(parser)
allowed = simulator.test_connectivity(source, destination)
```

### NetworkVisualizer

```python
from knetvis import NetworkVisualizer

visualizer = NetworkVisualizer()
visualizer.create_graph(namespace, policies)
visualizer.save_graph("output.png")
```