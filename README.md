# knetvis - Kubernetes Network Policy Visualizer

[![PyPI version](https://badge.fury.io/py/knetvis.svg)](https://badge.fury.io/py/knetvis)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://github.com/yourusername/knetvis/workflows/CI/badge.svg)](https://github.com/yourusername/knetvis/actions)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

A powerful CLI tool for visualizing and testing Kubernetes Network Policies.

## Demo
![Knetvis Operation](images/demo.gif)

## Features

- 🎯 **Visual Network Policy Analysis**: Generate clear visualizations of your network policies
- 🔍 **Policy Testing**: Test connectivity between pods and services
- ✅ **Policy Validation**: Validate network policies before applying them
- 🌐 **Cross-Namespace Support**: Analyze policies across multiple namespaces

## Quick Start

```bash
# Install knetvis
pip install knetvis

# Visualize network policies in a namespace
knetvis visualize my-namespace

# Test connectivity between pods
knetvis test pod/frontend pod/backend

# Validate a policy file
knetvis validate policy.yaml
```

## Installation

### Prerequisites
- Python 3.8 or higher
- Access to a Kubernetes cluster
- kubectl configured with cluster access

### Install Methods
```bash
# Via pip
pip install knetvis

# From source
git clone https://github.com/yourusername/knetvis.git
cd knetvis
pip install -e .
```

## Usage Examples

### Visualizing Network Policies
```bash
# Basic visualization
knetvis visualize production -o network.png

# Show cross-namespace connections
knetvis visualize production --show-external
```

### Testing Connectivity
```bash
# Test pod-to-pod connectivity
knetvis test pod/frontend pod/backend

# Test with namespace specification
knetvis test namespace/front/pod/web namespace/back/pod/api
```

### Validating Policies
```bash
# Validate a single policy
knetvis validate policy.yaml

# Validate multiple policies
knetvis validate -d policies/
```

## Documentation

- [Installation Guide](docs/installation.md)
- [Usage Guide](docs/usage.md)
- [API Reference](docs/api.md)
- [Contributing Guide](CONTRIBUTING.md)
- [FAQ](docs/faq.md)

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- 📫 [GitHub Issues](https://github.com/yourusername/knetvis/issues)
- 💬 [Discussions](https://github.com/yourusername/knetvis/discussions)
- 📖 [Wiki](https://github.com/yourusername/knetvis/wiki)

## Acknowledgments

- The Kubernetes community
- All contributors and maintainers