# Cluster Maintenance — Pref Revision (CKA)

Quick exam revision. See [enhanced_readme.md](./enhanced_readme.md) for full detail.

---

## Node maintenance

| Command | Effect |
|---------|--------|
| `kubectl cordon node` | No new Pods scheduled |
| `kubectl drain node` | Evict Pods + cordon |
| `kubectl uncordon node` | Allow scheduling again |

- Node offline → **40s** unreachable → **5min** eviction
- Drain workers **one at a time** during upgrades
- Use `--ignore-daemonsets` on drain

---

## Version skew (memorize)

| Component | vs kube-apiserver |
|-----------|-------------------|
| controller-manager, scheduler | ≤ **1** minor lower |
| kubelet, kube-proxy | ≤ **2** minor lower |
| kubectl | ± **1** version |
| **Nothing** | Higher than apiserver ❌ |

- Support **latest 3 minors** only
- Upgrade **one minor at a time**
- etcd & CoreDNS have **own versions**

---

## kubeadm upgrade order

1. Upgrade **kubeadm** on control plane
2. `kubeadm upgrade plan` → `kubeadm upgrade apply vX.Y.Z`
3. Upgrade **kubelet** (+ kubectl) on control plane — **kubeadm does NOT upgrade kubelet**
4. For each worker: **drain** → upgrade kubeadm → `kubeadm upgrade node` → upgrade kubelet → **uncordon**

---

## Backup methods

| Method | What |
|--------|------|
| Git/YAML | Declarative app config |
| `kubectl get all -A -o yaml` | API export |
| Velero | Full cluster + PV |
| **etcd snapshot** | Complete cluster state — **CKA critical** |

---

## etcd backup (exam pattern)

```bash
export ETCDCTL_API=3
etcdctl snapshot save /opt/snap.db \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

etcdctl snapshot status /opt/snap.db --write-out=table
```

**Restore:** stop apiserver → `etcdctl snapshot restore` with new `--data-dir` → update etcd manifest → restart

| Port | Use |
|------|-----|
| 2379 | client |
| 2380 | peer |

---

## Key facts

- Control plane components = same version in kubeadm package
- `kubectl get nodes` VERSION = **kubelet** version on that node
- Always `ETCDCTL_API=3`
- Static Pod manifests live in `/etc/kubernetes/manifests/`

---

## Kubernetes Docs — YAML Example Locations

| Topic | Official docs (YAML examples) |
|-------|-------------------------------|
| Cordon / drain | [Safely Drain a Node](https://kubernetes.io/docs/tasks/administer-cluster/safely-drain-node/) |
| kubeadm upgrade | [Upgrading kubeadm clusters](https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/kubeadm-upgrade/) |
| Control plane static Pods | [kubeadm setup — manifests](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/setup-kubeadm/) |
| etcd backup / restore | [Operating etcd](https://kubernetes.io/docs/tasks/administer-cluster/configure-upgrade-etcd/) |
| Cluster backup | [Backup a cluster](https://kubernetes.io/docs/tasks/administer-cluster/backup-restore/backup-cluster/) |
| Version skew | [Version Skew Policy](https://kubernetes.io/releases/version-skew-policy/) |
