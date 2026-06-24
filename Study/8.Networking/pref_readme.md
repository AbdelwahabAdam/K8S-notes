# Networking — Pref Revision (CKA)

Quick exam revision. See [enhanced_readme.md](./enhanced_readme.md) for full detail.

---

## Linux fundamentals

| Concept | Tool / detail |
|---------|---------------|
| Interfaces | `ip link`, `ip addr` |
| Routes | `ip route`, default gateway |
| ARP | `arp` |
| DNS | port **53**, A/AAAA/CNAME, `nslookup`, `dig` |
| IP forwarding | `/proc/sys/net/ipv4/ip_forward` |

---

## Network namespaces & CNI basics

- `ip netns add/exec` — isolated network stacks
- **veth pair** connects two namespaces (same as Pod ↔ host)
- **Linux bridge** — software switch on node
- K8s uses **CNI** (not Docker CNM)

CNI paths: `/opt/cni/bin`, `/etc/cni/net.d`

CNI steps: veth → attach → IP (IPAM) → up → routes

---

## Docker network modes

| Mode | Behavior |
|------|----------|
| none | Isolated |
| host | Uses host network |
| bridge | Default private network (172.17.0.0/16) |

---

## Cluster networking rules

- Every Pod gets **own IP**
- Pods must reach each other **without NAT** between nodes
- Unique hostname + MAC per node (watch VM clones)

---

## Required ports (memorize)

| Port | Component |
|------|-----------|
| **6443** | kube-apiserver |
| **10250** | kubelet |
| **10259** | scheduler |
| **10257** | controller-manager |
| **2379** | etcd client |
| **2380** | etcd peer (HA) |
| **30000–32767** | NodePort |

---

## Service networking

| Type | Use |
|------|-----|
| ClusterIP | Internal (default) |
| NodePort | External via node port |
| LoadBalancer | Cloud LB |

**kube-proxy** → iptables/IPVS rules → Pod IPs

DNS: `<svc>.<ns>.svc.cluster.local` via **CoreDNS**

---

## Popular CNI plugins

Flannel, Calico, Cilium, Weave — know they provide Pod networking + often NetworkPolicy

---

## Key commands

```bash
ip link / ip addr / ip route / arp
kubectl get svc,endpoints -A
kubectl get pods -n kube-system -l k8s-app=kube-dns
ls /opt/cni/bin && ls /etc/cni/net.d
```

---

## Exam tips

1. CNI assigns Pod IPs; kube-proxy handles Services
2. CoreDNS in `kube-system`
3. NodePort range 30000–32767
4. etcd peer port 2380 for HA
5. Service `port` vs `targetPort` vs `nodePort`

---

## Kubernetes Docs — YAML Example Locations

| Topic | Official docs (YAML examples) |
|-------|-------------------------------|
| Service | [Service](https://kubernetes.io/docs/concepts/services-networking/service/) |
| Ingress | [Ingress resource](https://kubernetes.io/docs/concepts/services-networking/ingress/#the-ingress-resource) |
| NetworkPolicy | [Declare Network Policy](https://kubernetes.io/docs/tasks/administer-cluster/declare-network-policy/) |
| CoreDNS | [Customizing DNS](https://kubernetes.io/docs/tasks/administer-cluster/dns-custom-nameservers/) |
