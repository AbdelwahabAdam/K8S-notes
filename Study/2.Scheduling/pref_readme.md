# Scheduling — Pref Revision (CKA)

Quick exam revision. See [enhanced_readme.md](./enhanced_readme.md) for full detail.

---

## Scheduler flow

**Filter → Score → Bind** — scheduler does NOT run containers; kubelet does.

---

## Manual scheduling

| Method | When |
|--------|------|
| `spec.nodeName: node02` | At Pod creation; skips scheduler |
| **Binding API** | POST binding to apiserver at runtime |

---

## Labels & selectors

- Used by Services, RS, Deployments, NetworkPolicies, affinity
- Add: `kubectl label pod x key=val`; remove: `key-`

---

## Taints & tolerations

| Effect | Meaning |
|--------|---------|
| `NoSchedule` | Won't schedule without toleration |
| `PreferNoSchedule` | Soft avoid |
| `NoExecute` | Evicts existing Pods without toleration |

```bash
kubectl taint nodes node1 app=blue:NoSchedule
kubectl taint nodes node1 app=blue:NoSchedule-   # remove
```

**Taints repel; affinity attracts.** Use both for dedicated nodes.

---

## Node affinity operators

`In`, `NotIn`, `Exists`, `Gt`, `Lt`

| Type | Hard vs soft |
|------|--------------|
| `requiredDuringSchedulingIgnoredDuringExecution` | Hard requirement |
| `preferredDuringSchedulingIgnoredDuringExecution` | Soft preference |

---

## Resources

| | Used by |
|--|---------|
| **requests** | Scheduler placement |
| **limits** | Runtime cap (OOMKill, CPU throttle) |

Units: CPU `500m` = 0.5 core; memory `Gi/Mi` (1024).

**QoS:** Guaranteed (req=lim) > Burstable > BestEffort

---

## DaemonSet vs Deployment

| | DaemonSet | Deployment |
|--|-----------|------------|
| Pods per node | One per matching node | N replicas total |
| Use | Agents, logs, kube-proxy | Apps |

---

## Static Pods

- kubelet reads `/etc/kubernetes/manifests/` (or `staticPodPath`)
- Mirror Pod visible in API as `name-nodeName`
- Control plane = static Pods (kubeadm)

---

## Priority & preemption

```yaml
preemptionPolicy: PreemptLowerPriority  # default
# or Never
spec.priorityClassName: high-priority
```

Range: up to **1,000,000,000**; default Pod priority **0**.

---

## Node maintenance

```bash
kubectl cordon node-1      # no new Pods
kubectl drain node-1       # evict + cordon
kubectl uncordon node-1    # allow scheduling again
```

Node controller: **40s** unreachable, **5min** eviction.

---

## Custom scheduler

```yaml
spec.schedulerName: my-scheduler
```

---

## Admission controllers (exam awareness)

Mutating → Validating → etcd. Examples: `ResourceQuota`, `LimitRanger`, `PodSecurity`.

---

## Key commands

```bash
kubectl get nodes --show-labels
kubectl describe node <n>
kubectl top nodes / kubectl top pods   # needs metrics-server
kubectl get priorityclasses
```

---

## Kubernetes Docs — YAML Example Locations

| Topic | Official docs (YAML examples) |
|-------|-------------------------------|
| Manual scheduling | [Assign Pods to Nodes](https://kubernetes.io/docs/tasks/configure-pod-container/assign-pods-nodes/) |
| Taints / tolerations | [Taints and Tolerations](https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/) |
| Node / Pod affinity | [Node Affinity](https://kubernetes.io/docs/tasks/configure-pod-container/assign-pods-nodes-using-node-affinity/) · [Inter-Pod Affinity](https://kubernetes.io/docs/tasks/configure-pod-container/assign-pods-nodes-using-inter-pod-affinity-and-anti-affinity/) |
| Resources / quotas | [CPU/Memory](https://kubernetes.io/docs/tasks/configure-pod-container/assign-cpu-resource/) · [Resource Quotas](https://kubernetes.io/docs/concepts/policy/resource-quotas/) |
| DaemonSet / Static Pod | [DaemonSet](https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/) · [Static Pods](https://kubernetes.io/docs/tasks/configure-pod-container/static-pod/) |
| PriorityClass | [Pod Priority](https://kubernetes.io/docs/concepts/scheduling-eviction/pod-priority-preemption/) |
| Cordon / drain | [Safely Drain a Node](https://kubernetes.io/docs/tasks/administer-cluster/safely-drain-node/) |
