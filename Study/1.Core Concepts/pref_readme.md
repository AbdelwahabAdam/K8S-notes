# Core Concepts — Pref Revision (CKA)

Quick exam revision. See [enhanced_readme.md](./enhanced_readme.md) for full detail.

---

## Architecture (must know)

| Component | Role |
|-----------|------|
| **etcd** | Only cluster datastore (key-value) |
| **kube-apiserver** | Auth, validate, read/write etcd |
| **kube-scheduler** | Assigns Pods to nodes (filter → score → bind) |
| **kube-controller-manager** | Reconciliation loops |
| **kubelet** | Agent on every node; runs containers via CRI |
| **kube-proxy** | Service → Pod routing (iptables/IPVS) |
| **CNI** | Pod IP assignment |

- Control plane = static Pods in `/etc/kubernetes/manifests/` (kubeadm)
- **dockershim removed v1.24** → use containerd/CRI-O; debug with `crictl`
- Node controller: 5s checks, 40s unreachable, 5min eviction

---

## Workloads hierarchy

`Deployment → ReplicaSet → Pod`

| Object | Purpose |
|--------|---------|
| **Pod** | Smallest unit; shared network/volumes |
| **ReplicaSet** | Maintains N replicas (use Deployments instead of RC) |
| **Deployment** | RollingUpdate (default) or Recreate |
| **DaemonSet** | One Pod per node (logs, kube-proxy) |
| **Service** | Stable endpoint; ClusterIP / NodePort / LoadBalancer |

---

## kubectl essentials

```bash
kubectl apply -f file.yaml      # declarative, idempotent
kubectl create -f file.yaml     # fails if exists
kubectl get po,rs,deploy,svc -A
kubectl describe / logs / exec
kubectl explain pod.spec --recursive
export ETCDCTL_API=3
```

**Three-way merge:** local YAML + last-applied annotation + live object

---

## Namespaces & quotas

- `default`, `kube-system`, `kube-public`, `kube-node-lease`
- **ResourceQuota** = namespace totals; **LimitRange** = per-container defaults

---

## Scheduling quick ref

| Mechanism | Effect |
|-----------|--------|
| **nodeName** | Skip scheduler; force node |
| **Labels/selectors** | Services, RS, Deployments match Pods |
| **Taints/tolerations** | Repel or allow Pods on nodes |
| **nodeSelector** | Simple label match |
| **nodeAffinity** | Required vs preferred; In/NotIn/Exists/Gt/Lt |
| **requests/limits** | Scheduler uses requests; runtime enforces limits |
| **Static Pods** | kubelet-managed from manifest dir |
| **PriorityClass** | Preemption; range up to 1e9 |

**Taints ≠ affinity:** taints say who *may* run; affinity says who *should* run.

---

## CPU / memory units

- CPU: `1` = 1 core, `500m` = half core
- Memory: `Gi/Mi` (1024) vs `G/M` (1000)

---

## Service ports

| Field | Meaning |
|-------|---------|
| `targetPort` | Pod port |
| `port` | Service port (cluster-internal) |
| `nodePort` | Node port 30000–32767 |

---

## Exam tips

1. Know static Pod paths and etcd backup/restore basics
2. `kubectl apply` stores last-applied in annotation
3. ReplicaSet vs ReplicationController: RS supports set-based selectors
4. Control plane components are **not** ReplicationControllers — they're in controller-manager
5. kubelet is **not** installed by kubeadm as a Pod

---

## Kubernetes Docs — YAML Example Locations

| Topic | Official docs (YAML examples) |
|-------|-------------------------------|
| Pod | [Configure a Pod](https://kubernetes.io/docs/tasks/configure-pod-container/) |
| Deployment | [Run a Stateless Application](https://kubernetes.io/docs/tasks/run-application/run-stateless-application-deployment/) |
| Service | [Service](https://kubernetes.io/docs/concepts/services-networking/service/) |
| Namespace / ResourceQuota | [Namespaces](https://kubernetes.io/docs/tasks/administer-cluster/namespaces/) · [Resource Quotas](https://kubernetes.io/docs/concepts/policy/resource-quotas/) |
| Taints / affinity | [Taints](https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/) · [Node Affinity](https://kubernetes.io/docs/tasks/configure-pod-container/assign-pods-nodes-using-node-affinity/) |
| Resources | [Assign CPU/Memory](https://kubernetes.io/docs/tasks/configure-pod-container/assign-cpu-resource/) |
| DaemonSet | [DaemonSet](https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/) |
| Static Pod | [Static Pods](https://kubernetes.io/docs/tasks/configure-pod-container/static-pod/) |
| PriorityClass | [Pod Priority](https://kubernetes.io/docs/concepts/scheduling-eviction/pod-priority-preemption/) |
