# Getting Started with knetvis

## Basic Tutorial

1. Install knetvis
2. Setup test environment
3. Create sample policies
4. Visualize and test

## Example Scenarios

### Scenario 1: Basic Web Application

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: web-policy
spec:
  podSelector:
    matchLabels:
      app: web
  ingress:
    - from:
        - podSelector:
            matchLabels:
              role: frontend
```

### Scenario 2: Microservices Communication

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-policy
spec:
  podSelector:
    matchLabels:
      app: api
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              environment: production
```
