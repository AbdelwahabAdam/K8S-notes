# Logging & Monitoring — Pref Revision (CKA)

Quick exam revision. See [enhanced_readme.md](./enhanced_readme.md) for full detail.

---

## Key facts

- K8s has **no built-in full monitoring** — add Metrics Server, Prometheus, ELK, etc.
- **Heapster = deprecated** → use **Metrics Server** (1 per cluster, in-memory, no history)
- **cAdvisor** runs inside **kubelet** → exposes container CPU/memory metrics
- Metrics Server scrapes kubelet → powers `kubectl top` and **HPA** (CPU)

---

## Metrics Server deploy & verify

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
kubectl get pods -n kube-system | grep metrics-server
kubectl top nodes
kubectl top pods
kubectl top pod <name> --containers
```

---

## Application logs

| Command | Purpose |
|---------|---------|
| `kubectl logs <pod>` | Current logs |
| `kubectl logs -f <pod>` | Follow / tail |
| `kubectl logs <pod> -c <container>` | Multi-container Pod |
| `kubectl logs <pod> --previous` | Crashed container |
| `kubectl logs -l app=x` | By label |

Logs = container **stdout/stderr** → kubelet → apiserver → kubectl

---

## Cluster component logs

Control plane = **static Pods** in `kube-system`:

```bash
kubectl get pods -n kube-system
kubectl logs -n kube-system kube-apiserver-<node>
kubectl logs -n kube-system etcd-<node>
crictl ps -a && crictl logs <id>
journalctl -u kubelet
```

---

## Common stacks (awareness)

| Tool | Role |
|------|------|
| Metrics Server | `kubectl top`, HPA |
| Prometheus | Metrics collection |
| Fluentd/Filebeat | Log shipping (often DaemonSet) |
| Elasticsearch/Kibana | Log search |
| Datadog/Dynatrace | Commercial APM |

---

## Probes (often tested with monitoring)

- **Liveness** — restart if fails
- **Readiness** — remove from Service endpoints if fails
- **Startup** — disable other probes until success

---

## Exam tips

1. `kubectl top` needs Metrics Server + RBAC
2. Multi-container → always specify `-c`
3. `--previous` for crash debugging
4. Node/agent logs: `crictl`, `journalctl -u kubelet`
5. Log collectors often run as **DaemonSets**

---

## Kubernetes Docs — YAML Example Locations

| Topic | Official docs (YAML examples) |
|-------|-------------------------------|
| Metrics Server | [Resource metrics pipeline](https://kubernetes.io/docs/tasks/debug/debug-cluster/resource-metrics-pipeline/) |
| Liveness / Readiness / Startup probes | [Configure Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/) |
| Logging architecture | [Logging](https://kubernetes.io/docs/concepts/cluster-administration/logging/) |
| Debug cluster / component logs | [Troubleshoot Clusters](https://kubernetes.io/docs/tasks/debug/debug-cluster/) |
| Log collector DaemonSet | [DaemonSet](https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/) |
