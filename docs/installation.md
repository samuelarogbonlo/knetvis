# Installation Guide

## Prerequisites

- Python 3.8 or higher
- Access to a Kubernetes cluster
- `kubectl` configured with cluster access

## Installation Methods

### Via pip (Recommended)

```bash
pip install knetvis
```

### From Source

```bash
git clone https://github.com/yourusername/knetvis.git
cd knetvis
pip install -e .
```

## Verification

Verify the installation:
```bash
knetvis --version
```

# docs/usage.md
# Usage Guide

## Basic Commands

### Visualizing Network Policies

```bash
# Basic visualization
knetvis visualize my-namespace

# Save to specific file
knetvis visualize my-namespace -o network.png
```

### Testing Connectivity

```bash
# Basic connectivity test
knetvis test pod/source pod/destination

# Cross-namespace test
knetvis test namespace/test-a/pod/frontend namespace/test-b/pod/backend
```

### Validating Policies

```bash
# Validate single policy
knetvis validate policy.yaml

# Validate directory of policies
knetvis validate -d policies/
```

## Advanced Usage

### Working with Multiple Namespaces

```bash
# Show cross-namespace policies
knetvis visualize my-namespace --show-external

# Analyze specific namespace combinations
knetvis visualize my-namespace --related-namespaces other-namespace
```

### Custom Visualization Options

```bash
# Change graph layout
knetvis visualize my-namespace --layout spring

# Customize colors
knetvis visualize my-namespace --highlight-denied
```