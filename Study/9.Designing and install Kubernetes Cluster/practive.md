# CKA Practice — Designing & Installing Kubernetes Cluster

> Practice questions aligned with [enhanced_readme.md](./enhanced_readme.md). Answers include **Imperative** (`kubeadm` / `kubectl` commands) and **Declarative** (YAML / config) where applicable.

---

## Topic Questions

### 1. Designing a Kubernetes Cluster

**Q1.1** List five design questions to answer before building a cluster.

<details>
<summary>Answer</summary>

| Area | Questions |
|------|-----------|
| **Purpose** | Education, dev/test, or production? |
| **Location** | Cloud vs on-premises |
| **Workloads** | How many? Web, big data, stateful? |
| **Resources** | CPU vs memory intensive? |
| **Traffic** | Steady vs bursty? |
| **Storage** | Local, NFS, cloud block storage? |

**Imperative — assess existing cluster capacity:**

```bash
kubectl top nodes
kubectl describe nodes | grep -A5 "Allocated resources"
kubectl get nodes --no-headers | wc -l
```

</details>

**Q1.2** What are the approximate Kubernetes scale limits (nodes, Pods, Pods per node)?

<details>
<summary>Answer</summary>

| Limit | Value |
|-------|-------|
| Max nodes | ~5000 |
| Max Pods | ~150,000 |
| Max containers | ~300,000 |
| Max Pods per node | ~100 |

</details>

---

### 2. Purpose & Topology

**Q2.1** Match cluster purpose to recommended setup.

<details>
<summary>Answer</summary>

| Purpose | Setup |
|---------|-------|
| **Education** | minikube, kind, single-node kubeadm |
| **Development & testing** | Single control plane + multiple workers |
| **Production** | HA multi-master, odd etcd count, load-balanced apiserver |

**Imperative — check current topology:**

```bash
kubectl get nodes -o wide
kubectl get pods -n kube-system -o wide | grep -E 'etcd|apiserver|scheduler|controller'
```

</details>

**Q2.2** When is a single control plane acceptable vs when is HA required?

<details>
<summary>Answer</summary>

- **Single control plane:** Learning, dev/test, non-critical workloads — acceptable downtime
- **HA required:** Production — no single point of failure for API, etcd quorum for data safety

**Declarative — production HA sketch:**

```
Clients → Load Balancer (:6443) → 3× kube-apiserver → 3-node etcd cluster
                                  → scheduler (leader elected)
                                  → controller-manager (leader elected)
```

</details>

---

### 3. Choosing Infrastructure

**Q3.1** Compare manual/kubeadm, turnkey, and hosted deployment models.

<details>
<summary>Answer</summary>

| Model | You provision VMs | You install K8s | Provider maintains |
|-------|-------------------|-----------------|-------------------|
| **Manual / kubeadm** | Yes | Yes | You |
| **Turnkey** (KOPS, etc.) | Yes | Scripts | You maintain VMs |
| **Hosted** (GKE/EKS/AKS) | Provider | Provider | Provider |

**Imperative — identify cluster type:**

```bash
kubectl cluster-info
kubectl get nodes -o jsonpath='{.items[0].metadata.labels}' | jq .
# GKE: cloud.google.com/gke-nodepool
# EKS: eks.amazonaws.com/nodegroup
# AKS: kubernetes.azure.com/cluster
```

</details>

**Q3.2** Match tools to their use case: minikube, kubeadm, KOPS, GKE.

<details>
<summary>Answer</summary>

| Tool | Use case |
|------|----------|
| **minikube** | Local single-node learning |
| **kubeadm** | Manual install on your VMs (single or multi-node) |
| **KOPS** | Production clusters on AWS/GCP (provisions VMs) |
| **GKE** | Managed Kubernetes on Google Cloud |

**Imperative:**

```bash
minikube status          # local
kubeadm version          # manual install tool
```

</details>

---

### 4. High Availability Architecture

**Q4.1** Describe HA architecture for kube-apiserver, scheduler, and controller-manager.

<details>
<summary>Answer</summary>

**kube-apiserver:** Multiple instances behind load balancer on port **6443**; all point to same etcd.

**Scheduler & controller-manager:** Multiple instances but only **one active leader** via leader election (`--leader-elect=true`).

**Imperative — check leader election:**

```bash
kubectl get lease -n kube-system
kubectl describe lease kube-controller-manager -n kube-system
kubectl describe lease kube-scheduler -n kube-system
```

**Declarative — leader election flags (static Pod manifest):**

```yaml
# In /etc/kubernetes/manifests/kube-scheduler.yaml
spec:
  containers:
    - command:
        - kube-scheduler
        - --leader-elect=true
        - --leader-elect-lease-duration=15s
        - --leader-elect-renew-deadline=10s
        - --leader-elect-retry-period=2s
```

</details>

**Q4.2** Compare stacked vs external etcd topologies.

<details>
<summary>Answer</summary>

| Topology | Description |
|----------|-------------|
| **Stacked** | etcd runs on control plane nodes (common with kubeadm) |
| **External** | etcd on dedicated separate nodes (better isolation) |

**Declarative — apiserver etcd endpoints flag:**

```bash
--etcd-servers=https://10.240.0.10:2379,https://10.240.0.11:2379,https://10.240.0.12:2379
```

**Imperative — view apiserver config:**

```bash
cat /etc/kubernetes/manifests/kube-apiserver.yaml | grep etcd-servers
```

</details>

---

### 5. etcd in HA

**Q5.1** Calculate quorum and fault tolerance for 1, 3, and 5 etcd nodes.

<details>
<summary>Answer</summary>

| etcd nodes | Quorum (N/2+1) | Tolerate failures (N-1)/2 |
|------------|----------------|---------------------------|
| 1 | 1 | 0 |
| 3 | 2 | 1 |
| 5 | 3 | 2 |

**Rule:** Always use an **odd** number of nodes (5 tolerates 2 failures; 6 also tolerates 2 but wastes a node).

</details>

**Q5.2** An etcd cluster has 5 members and 2 nodes fail. Can it accept writes? What if 3 fail?

<details>
<summary>Answer</summary>

- **2 failures (3 remain):** Quorum = 3 → **yes**, writes succeed
- **3 failures (2 remain):** Quorum = 3 but only 2 nodes → **no**, cluster read-only / unavailable

**Imperative — check etcd health:**

```bash
kubectl exec -n kube-system etcd-<node> -- etcdctl \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  endpoint health

ETCDCTL_API=3 etcdctl member list
```

</details>

---

### 6. Install Kubernetes with kubeadm

**Q6.1** List kubeadm prerequisites on all nodes (swap, kernel modules, sysctl, container runtime).

<details>
<summary>Answer</summary>

**Imperative:**

```bash
# Disable swap
swapoff -a
sed -i '/ swap / s/^/#/' /etc/fstab

# Kernel modules
cat <<EOF | tee /etc/modules-load.d/k8s.conf
overlay
br_netfilter
EOF
modprobe overlay && modprobe br_netfilter

# Sysctl
cat <<EOF | tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
EOF
sysctl --system

# containerd
apt-get install -y containerd
mkdir -p /etc/containerd
containerd config default | tee /etc/containerd/config.toml
systemctl restart containerd

# kubeadm, kubelet, kubectl
apt-get install -y kubelet kubeadm kubectl
apt-mark hold kubelet kubeadm kubectl
```

</details>

**Q6.2** Initialize a single control plane with pod CIDR `10.244.0.0/16` and configure kubectl for a regular user.

<details>
<summary>Answer</summary>

**Imperative:**

```bash
kubeadm init --pod-network-cidr=10.244.0.0/16

mkdir -p $HOME/.kube
cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
chown $(id -u):$(id -g) $HOME/.kube/config

kubectl get nodes
kubectl get pods -n kube-system
```

**Declarative — kubeadm config file (optional):**

```yaml
apiVersion: kubeadm.k8s.io/v1beta3
kind: ClusterConfiguration
networking:
  podSubnet: 10.244.0.0/16
```

```bash
kubeadm init --config kubeadm-config.yaml
```

</details>

**Q6.3** What does kubeadm install on the master, and how does each component run?

<details>
<summary>Answer</summary>

| Component | How it runs |
|-----------|-------------|
| kube-apiserver | Static Pod (`/etc/kubernetes/manifests/`) |
| kube-controller-manager | Static Pod |
| kube-scheduler | Static Pod |
| etcd | Static Pod (unless external) |
| kubelet | **systemd service** (not a Pod) |

**Imperative:**

```bash
ls /etc/kubernetes/manifests/
systemctl status kubelet
crictl pods | grep kube-system
```

</details>

---

### 7. Post-Install: CNI & Join Workers

**Q7.1** After `kubeadm init`, Pods stay `Pending`. Why and how do you fix it?

<details>
<summary>Answer</summary>

CNI plugin is not installed — Pods cannot get network until a Pod network is deployed.

**Imperative — install Flannel:**

```bash
kubectl apply -f https://github.com/flannel-io/flannel/releases/latest/download/kube-flannel.yml
kubectl get pods -n kube-system -w
```

**Imperative — install Calico:**

```bash
kubectl apply -f https://docs.projectcalico.org/manifests/calico.yaml
```

</details>

**Q7.2** Generate a new worker join command after the original token expired.

<details>
<summary>Answer</summary>

**Imperative:**

```bash
kubeadm token create --print-join-command
```

Output example:

```bash
kubeadm join 192.168.1.100:6443 \
  --token <token> \
  --discovery-token-ca-cert-hash sha256:<hash>
```

Run on each worker node, then verify:

```bash
kubectl get nodes
kubectl get pods -n kube-system -o wide
```

</details>

**Q7.3** Join a worker node to an existing cluster. What flags are required?

<details>
<summary>Answer</summary>

**Imperative (on worker node):**

```bash
kubeadm join <control-plane-host>:6443 \
  --token <token> \
  --discovery-token-ca-cert-hash sha256:<hash>
```

Optional for HA control plane:

```bash
kubeadm join <lb-host>:6443 \
  --token <token> \
  --discovery-token-ca-cert-hash sha256:<hash> \
  --control-plane    # for additional control plane nodes
```

**Verify from control plane:**

```bash
kubectl get nodes -o wide
```

</details>

---

### 8. Cheat Sheet & Resources

**Q8.1** List commands to check cluster health, token status, and certificate expiration.

<details>
<summary>Answer</summary>

**Imperative:**

```bash
kubectl get nodes -o wide
kubectl get pods -n kube-system
kubeadm token list
kubeadm certs check-expiration
kubectl cluster-info
kubectl get componentstatuses    # deprecated but may appear on exam
```

</details>

**Q8.2** How do you safely reset a node for re-initialization?

<details>
<summary>Answer</summary>

**Imperative (destructive — on the node):**

```bash
kubeadm reset
rm -rf /etc/cni/net.d
rm -rf $HOME/.kube/config
iptables -F && iptables -t nat -F && iptables -t mangle -F && iptables -X
```

Then re-run prerequisites and `kubeadm init` or `kubeadm join`.

</details>

---

## Mixed Topic Questions

### Scenario 1 — Choose Cluster Design for a Startup

A startup needs a production cluster for a web API (bursty traffic, stateless) with a PostgreSQL StatefulSet. Budget is limited. Cloud vs on-prem? HA or single master? Recommend topology and tooling.

<details>
<summary>Answer</summary>

**Recommendation:**

| Decision | Choice | Reason |
|----------|--------|--------|
| **Location** | Cloud (GKE/EKS/AKS) | Limited ops budget; managed control plane |
| **Topology** | Managed HA (provider handles control plane) | Production requires HA without etcd ops burden |
| **Workers** | 3+ nodes, autoscaling | Handle bursty traffic |
| **Storage** | Cloud block StorageClass (CSI) | StatefulSet PostgreSQL with dynamic provisioning |

**Imperative — verify managed cluster:**

```bash
kubectl get nodes
kubectl get sc
kubectl get pods -n kube-system
```

**Declarative — PostgreSQL StatefulSet snippet:**

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
        - name: postgres
          image: postgres:15
          volumeMounts:
            - name: data
              mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        accessModes: [ReadWriteOnce]
        storageClassName: standard
        resources:
          requests:
            storage: 20Gi
```

</details>

---

### Scenario 2 — Build a Dev Cluster with kubeadm

You have 1 master (192.168.1.10) and 2 workers. Install a working 3-node cluster from scratch.

<details>
<summary>Answer</summary>

**Imperative — on ALL nodes:**

```bash
swapoff -a
sed -i '/ swap / s/^/#/' /etc/fstab
modprobe overlay && modprobe br_netfilter
cat <<EOF | tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
EOF
sysctl --system
apt-get update && apt-get install -y containerd kubelet kubeadm kubectl
apt-mark hold kubelet kubeadm kubectl
systemctl enable --now containerd kubelet
```

**Imperative — on master only:**

```bash
kubeadm init --pod-network-cidr=10.244.0.0/16 --apiserver-advertise-address=192.168.1.10
mkdir -p $HOME/.kube && cp /etc/kubernetes/admin.conf $HOME/.kube/config
kubectl apply -f https://github.com/flannel-io/flannel/releases/latest/download/kube-flannel.yml
kubeadm token create --print-join-command
```

**Imperative — on each worker:**

```bash
kubeadm join 192.168.1.10:6443 --token <token> --discovery-token-ca-cert-hash sha256:<hash>
```

**Verify:**

```bash
kubectl get nodes
kubectl get pods -n kube-system
```

</details>

---

### Scenario 3 — Plan HA Production Cluster

Design a 3-master HA cluster with stacked etcd. What components need a load balancer? How many etcd failures can you tolerate?

<details>
<summary>Answer</summary>

**Architecture:**

```
                    ┌── master-1 (apiserver + etcd)
Clients → LB:6443 ──┼── master-2 (apiserver + etcd)
                    └── master-3 (apiserver + etcd)
Workers join via LB:6443
```

| Component | HA mechanism |
|-----------|--------------|
| **kube-apiserver** | 3 instances behind LB on port 6443 |
| **etcd** | 3-node Raft cluster (stacked on masters) |
| **scheduler** | Leader election (1 active) |
| **controller-manager** | Leader election (1 active) |

**Fault tolerance:** 3 etcd nodes → quorum 2 → tolerate **1 failure**.

**Declarative — kubeadm HA config snippet:**

```yaml
apiVersion: kubeadm.k8s.io/v1beta3
kind: ClusterConfiguration
controlPlaneEndpoint: "192.168.1.50:6443"    # LB address
etcd:
  local:
    dataDir: /var/lib/etcd
---
apiVersion: kubeadm.k8s.io/v1beta3
kind: InitConfiguration
localAPIEndpoint:
  advertiseAddress: 192.168.1.11
nodeRegistration:
  criSocket: unix:///var/run/containerd/containerd.sock
```

**Imperative — verify HA:**

```bash
kubectl get nodes -l node-role.kubernetes.io/control-plane
kubectl get lease -n kube-system
```

</details>

---

### Scenario 4 — etcd Disaster Recovery Planning

Your production cluster has 5 etcd members. Operations wants to know: (a) how many can fail, (b) should they add a 6th node, (c) what happens during a network partition.

<details>
<summary>Answer</summary>

**(a) Failures tolerated:** 5 nodes → quorum 3 → tolerate **2 failures**

**(b) 6th node?** **No** — 6 nodes also tolerate only 2 failures (quorum 4) but adds cost without benefit. Always prefer **odd** counts.

**(c) Network partition:** The partition with **majority** continues accepting writes; the minority partition becomes read-only/unavailable (split-brain protection via Raft).

**Imperative — monitor etcd:**

```bash
kubectl get pods -n kube-system | grep etcd
ETCDCTL_API=3 etcdctl --endpoints=<endpoints> \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  endpoint health
```

</details>

---

### Scenario 5 — Worker Node Won't Join

A worker runs `kubeadm join` but fails with token expired. Fix and successfully join the node.

<details>
<summary>Answer</summary>

**Imperative — on control plane:**

```bash
kubeadm token list
kubeadm token create --print-join-command
```

**Imperative — on worker (use fresh output):**

```bash
kubeadm reset    # if previous failed join left partial state
kubeadm join 192.168.1.10:6443 \
  --token <new-token> \
  --discovery-token-ca-cert-hash sha256:<hash>
```

**If hash unknown:**

```bash
# On control plane:
openssl x509 -pubkey -in /etc/kubernetes/pki/ca.crt | \
  openssl rsa -pubin -outform der 2>/dev/null | \
  openssl dgst -sha256 -hex | sed 's/^.* //'
```

**Verify:**

```bash
kubectl get nodes
kubectl describe node <worker-name>
```

</details>

---

### Scenario 6 — Post-Install Troubleshooting

After `kubeadm init` and Flannel install, `kubectl get nodes` shows master `NotReady` and CoreDNS Pods are `Pending`.

<details>
<summary>Answer</summary>

**Imperative — diagnose:**

```bash
kubectl get nodes
kubectl describe node <master>
kubectl get pods -n kube-system
kubectl describe pod -n kube-system <coredns-pod>
journalctl -u kubelet -n 50
```

**Common causes and fixes:**

| Symptom | Cause | Fix |
|---------|-------|-----|
| Node `NotReady` | CNI not running | `kubectl apply -f kube-flannel.yml` |
| CNI CrashLoopBackOff | Wrong pod CIDR | Re-init with matching `--pod-network-cidr` |
| kubelet errors | Swap enabled | `swapoff -a` |
| containerd issues | Misconfigured runtime | `systemctl restart containerd` |

**Imperative — verify CNI matches init CIDR:**

```bash
# Flannel default: 10.244.0.0/16
kubeadm init --pod-network-cidr=10.244.0.0/16   # must match CNI
kubectl get pods -n kube-flannel   # or kube-system for flannel
kubectl logs -n kube-flannel <flannel-pod>
```

**Imperative — remove master taint (single-node dev only):**

```bash
kubectl taint nodes --all node-role.kubernetes.io/control-plane-
```

</details>
