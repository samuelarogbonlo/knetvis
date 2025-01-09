# Frequently Asked Questions

## General Questions

**Q: How does knetvis differ from other network policy tools?**
A: knetvis focuses on visualization and testing, providing an integrated approach to understanding and validating network policies.

**Q: Can I use knetvis with any CNI?**
A: Yes, knetvis works with any CNI that implements the Kubernetes NetworkPolicy API.

## Troubleshooting

**Q: Why isn't my policy visualization showing any connections?**
A: Check if:
1. The namespace exists
2. There are pods matching the policy selectors
3. The policy is correctly formatted

**Q: How do I debug connectivity issues?**
A: Use the `--verbose` flag with the test command for detailed information:
```bash
knetvis test pod/source pod/destination --verbose
```