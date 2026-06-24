# CKA Practice — Cluster Maintenance
> Based on [enhanced_readme.md](./enhanced_readme.md)

---

## Topic Questions

### 1. OS & Node Maintenance

**Q1.** Prepare node `node-1` for kernel patching: prevent new Pods from scheduling and safely evict existing workloads (ignore DaemonSets, delete `emptyDir` data).

**Answer**

*Imperative:*
```bash
kubectl drain node-1 --ignore-daemonsets --delete-emptydir-data
```

After maintenance:
```bash
kubectl uncordon node-1
```

**Q2.** What is the difference between `cordon`, `drain`, and `uncordon`?

**Answer**

| Command | Schedules new Pods? | Evicts existing? |
|---------|---------------------|------------------|
| **cordon** | No | No |
| **drain** | No (cordons first) | Yes |
| **uncordon** | Yes (re-enables) | — |

Default timings: node marked **Unreachable** after **40s** without heartbeat; Pods evicted after **5 minutes**.

---

### 2. Kubernetes Versioning & Support

**Q1.** Cluster runs kube-apiserver v1.29. What kubelet versions are allowed? Can kubectl v1.31 connect?

**Answer**

| Component | Allowed skew vs kube-apiserver |
|-----------|-------------------------------|
| kube-controller-manager, scheduler | Up to **1 minor lower** (≥ v1.28) |
| kubelet, kube-proxy | Up to **2 minor lower** (≥ v1.27) |
| kubectl | Up to **1 higher or lower** (v1.28–v1.30 OK; v1.31 is **too new**) |

No component may be **newer** than kube-apiserver.

**Q2.** Can you upgrade directly from Kubernetes v1.27 to v1.29? How many minor versions does Kubernetes support concurrently?

**Answer**

**No** — upgrade **one minor version at a time** (v1.27 → v1.28 → v1.29). Kubernetes supports the **latest 3 minor versions**.

---

### 3. Cluster Upgrade Process

**Q1.** List the correct order to upgrade a kubeadm cluster from v1.28 to v1.29.

**Answer**

1. Upgrade **control plane** (`kubeadm upgrade apply`)
2. Upgrade **kubelet** (and kubectl) on control plane node
3. For each **worker** (one at a time):
   - `kubectl drain <node>`
   - Upgrade kubeadm on worker → `kubeadm upgrade node`
   - Upgrade kubelet on worker
   - `kubectl uncordon <node>`

> **kubeadm does NOT upgrade kubelet** — you must upgrade kubelet separately on every node.

**Q2.** Name three cluster upgrade approaches and when each applies.

**Answer**

| Method | Description |
|--------|-------------|
| **Managed cloud** (GKE, EKS, AKS) | Provider handles upgrades |
| **kubeadm** | `kubeadm upgrade plan` / `apply` / `node` |
| **Manual** | Upgrade each component individually |

---

### 4. Kubeadm Upgrade Walkthrough

**Q1.** On the control plane node, upgrade kubeadm from v1.28 to v1.29. Show the full command sequence.

**Answer**

```bash
# Check available versions
apt-cache madison kubeadm

# Upgrade kubeadm binary
apt-get update && apt-get install -y kubeadm=1.29.x-00

# Preview upgrade
kubeadm upgrade plan

# Apply to control plane (updates static Pod manifests)
kubeadm upgrade apply v1.29.x

# Upgrade kubelet & kubectl on control plane
apt-get install -y kubelet=1.29.x-00 kubectl=1.29.x-00
systemctl daemon-reload
systemctl restart kubelet

kubectl get nodes
```

**Q2.** Upgrade worker node `node01` after control plane is on v1.29. Commands on control plane and worker?

**Answer**

*Control plane:*
```bash
kubectl drain node01 --ignore-daemonsets --delete-emptydir-data
```

*Worker node:*
```bash
apt-get install -y kubeadm=1.29.x-00
kubeadm upgrade node
apt-get install -y kubelet=1.29.x-00
systemctl daemon-reload && systemctl restart kubelet
```

*Control plane:*
```bash
kubectl uncordon node01
```

Repeat for remaining workers one at a time.

---

### 5. Backup & Restore Methods

**Q1.** Export all API objects in all namespaces to a YAML file for quick backup.

**Answer**

*Imperative:*
```bash
kubectl get all --all-namespaces -o yaml > cluster-backup.yaml
```

**Q2.** Compare backup methods: Git/YAML manifests, kubectl export, Velero, and etcd snapshot. Which is required for control plane disaster recovery?

**Answer**

| Method | Scope | Notes |
|--------|-------|-------|
| **Git / declarative YAML** | Workloads you defined | Best practice for apps |
| **kubectl get -o yaml** | API objects | Quick export; not etcd-native |
| **Velero** | Cluster + PV backups | API + object storage |
| **etcd snapshot** | Full cluster state | **Required for control plane DR** |

---

### 6. etcd Backup & Restore

**Q1.** Take a live etcd snapshot to `/opt/snapshot.db` on the control plane node.

**Answer**

```bash
ETCDCTL_API=3 etcdctl snapshot save /opt/snapshot.db \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key
```

Verify:
```bash
ETCDCTL_API=3 etcdctl snapshot status /opt/snapshot.db --write-out=table
```

**Q2.** Restore etcd from `/opt/snapshot.db` after disaster. List the steps.

**Answer**

```bash
# 1. Stop kube-apiserver (stop kubelet or move apiserver static Pod manifest)
systemctl stop kubelet

# 2. Restore to new data directory
ETCDCTL_API=3 etcdctl snapshot restore /opt/snapshot.db \
  --data-dir=/var/lib/etcd-from-backup \
  --initial-cluster-token=etcd-cluster-1 \
  --initial-advertise-peer-urls=https://127.0.0.1:2380 \
  --name=master \
  --initial-cluster=master=https://127.0.0.1:2380

# 3. Update etcd static Pod manifest to use /var/lib/etcd-from-backup
# 4. Restart etcd, then start kubelet
systemctl daemon-reload && systemctl restart kubelet
```

Always use `ETCDCTL_API=3`. etcd client port **2379**, peer port **2380**.

---

## Mixed Topic Questions

### Scenario 1 — Safe Node Maintenance During Business Hours

Node `worker-03` needs OS patches. Ensure no new Pods schedule there, evict workloads safely, patch and reboot, then return the node to service. A Deployment-managed app should reschedule automatically.

**Answer**

```bash
# Before maintenance
kubectl drain worker-03 --ignore-daemonsets --delete-emptydir-data

# Verify Pods rescheduled
kubectl get pods -o wide --all-namespaces | grep worker-03

# On worker-03: patch, reboot
# After node returns (within 5 min, Deployment Pods may return automatically)

kubectl uncordon worker-03
kubectl get nodes worker-03
```

If using PodDisruptionBudgets, ensure `minAvailable` allows eviction.

---

### Scenario 2 — Full Cluster Upgrade v1.28 → v1.29

3-node kubeadm cluster (1 control plane, 2 workers). Backup etcd first, then upgrade. Document every step.

**Answer**

```bash
# 0. Backup etcd FIRST
ETCDCTL_API=3 etcdctl snapshot save /opt/pre-upgrade.db \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# 1. Control plane
apt-get install -y kubeadm=1.29.x-00
kubeadm upgrade plan
kubeadm upgrade apply v1.29.x
apt-get install -y kubelet=1.29.x-00 kubectl=1.29.x-00
systemctl daemon-reload && systemctl restart kubelet

# 2. Each worker (one at a time)
kubectl drain worker-01 --ignore-daemonsets --delete-emptydir-data
# on worker-01:
apt-get install -y kubeadm=1.29.x-00 && kubeadm upgrade node
apt-get install -y kubelet=1.29.x-00
systemctl daemon-reload && systemctl restart kubelet
kubectl uncordon worker-01
# repeat for worker-02

kubectl get nodes
```

---

### Scenario 3 — Version Skew Troubleshooting

After a partial upgrade, `kubectl get nodes` shows control plane v1.29, workers v1.27, and one worker's kubelet v1.30 (misconfigured). Which components violate skew policy? What do you fix?

**Answer**

Violations:
- Worker kubelet **v1.30** is **newer than apiserver v1.29** — **not allowed**
- Workers v1.27 are **2 minor versions behind** v1.29 — **allowed** (exactly at limit)

Fix the v1.30 worker:
```bash
kubectl drain worker-bad --ignore-daemonsets --delete-emptydir-data
apt-get install -y kubelet=1.29.x-00 kubeadm=1.29.x-00
kubeadm upgrade node
systemctl daemon-reload && systemctl restart kubelet
kubectl uncordon worker-bad
```

Then upgrade remaining v1.27 workers to v1.29 one at a time.

---

### Scenario 4 — etcd Disaster Recovery

Control plane etcd data is corrupted. Snapshot `/opt/snapshot.db` exists from yesterday. Restore cluster state.

**Answer**

```bash
# Stop API server
systemctl stop kubelet
# or: mv /etc/kubernetes/manifests/kube-apiserver.yaml /tmp/

ETCDCTL_API=3 etcdctl snapshot restore /opt/snapshot.db \
  --data-dir=/var/lib/etcd-restored \
  --initial-cluster-token=etcd-cluster-1 \
  --initial-advertise-peer-urls=https://127.0.0.1:2380 \
  --name=master \
  --initial-cluster=master=https://127.0.0.1:2380

# Edit /etc/kubernetes/manifests/etcd.yaml:
#   change --data-dir to /var/lib/etcd-restored

systemctl daemon-reload
systemctl restart kubelet

# Verify
kubectl get nodes
kubectl get pods --all-namespaces
```

---

### Scenario 5 — Cordon vs Drain Decision

You need to run a quick diagnostic on `node-02` without disrupting running Pods, but also need to prevent new Pods from landing there. Later, you must fully decommission the node. What commands for each phase?

**Answer**

**Phase 1 — diagnostic, keep Pods running:**
```bash
kubectl cordon node-02
# run diagnostics
kubectl uncordon node-02   # when done
```

**Phase 2 — decommission:**
```bash
kubectl drain node-02 --ignore-daemonsets --delete-emptydir-data
# remove node from cluster if needed
kubectl delete node node-02
```

---

### Scenario 6 — Multi-Method Backup Strategy

Design a backup plan: daily app manifests in Git, weekly Velero for PVs, etcd snapshot before every upgrade. Write the etcd and kubectl export commands.

**Answer**

```bash
# Before every upgrade — etcd snapshot (mandatory)
ETCDCTL_API=3 etcdctl snapshot save /backup/etcd-$(date +%F).db \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

ETCDCTL_API=3 etcdctl snapshot status /backup/etcd-$(date +%F).db --write-out=table

# Quick API export (supplementary)
kubectl get all --all-namespaces -o yaml > /backup/api-$(date +%F).yaml

# Velero (installed separately)
velero backup create daily-backup --include-namespaces production,staging

# Git — declarative manifests committed to repo (best practice for workloads)
```

Recovery priority: **etcd snapshot** for full cluster state; Git/Velero for workload-specific restores.
