# CKA Practice — Networking

> Practice questions aligned with [enhanced_readme.md](./enhanced_readme.md). Answers include **Imperative** (`kubectl` / Linux commands) and **Declarative** (YAML) where applicable.

---

## Topic Questions

### 1. Prerequisites: Switching, Routing & DNS

**Q1.1** Explain switching vs routing. When does a host use its default gateway?

<details>
<summary>Answer</summary>

| Concept | Scope |
|---------|-------|
| **Switching** | Forward frames within the same L2 network (same subnet) |
| **Routing** | Forward packets between different networks via routing table |
| **Default gateway** | Next hop for traffic destined outside the local subnet |

**Imperative — inspect routing on a node:**

```bash
ip route
ip route show default
cat /etc/resolv.conf
```

</details>

**Q1.2** What port does DNS use? Name three record types and the Kubernetes DNS implementation.

<details>
<summary>Answer</summary>

- **Port:** 53 (UDP/TCP)
- **Record types:** A (IPv4), AAAA (IPv6), CNAME (alias)
- **Kubernetes:** CoreDNS in `kube-system`

**Imperative:**

```bash
kubectl get pods -n kube-system -l k8s-app=kube-dns
kubectl get svc -n kube-system kube-dns
nslookup kubernetes.default
dig kubernetes.default.svc.cluster.local
```

</details>

---

### 2. Network Namespaces

**Q2.1** Create two network namespaces `red` and `blue` and list them.

<details>
<summary>Answer</summary>

**Imperative (on Linux node):**

```bash
ip netns add red
ip netns add blue
ip netns list
ip netns exec red ip link
ip -n red link
```

</details>

**Q2.2** Connect namespaces `red` and `blue` with a veth pair and assign IPs `192.168.15.1/24` and `192.168.15.2/24`. Verify connectivity.

<details>
<summary>Answer</summary>

**Imperative:**

```bash
ip link add veth-red type veth peer name veth-blue
ip link set veth-red netns red
ip link set veth-blue netns blue
ip -n red addr add 192.168.15.1/24 dev veth-red
ip -n blue addr add 192.168.15.2/24 dev veth-blue
ip -n red link set veth-red up
ip -n blue link set veth-blue up
ip netns exec red ping -c 2 192.168.15.2
```

> This mirrors how CNI plugins connect Pod network namespaces to the host.

</details>

---

### 3. Linux Bridge

**Q3.1** Create a Linux bridge `v-net-0` and bring it up. Why are bridges used in container networking?

<details>
<summary>Answer</summary>

Bridges act as software switches — multiple veth interfaces (Pods/containers) share the same L2 segment.

**Imperative:**

```bash
ip link add v-net-0 type bridge
ip link set dev v-net-0 up
ip link show v-net-0
brctl show    # if bridge-utils installed
```

</details>

---

### 4. Docker Networking

**Q4.1** Compare Docker networking modes: `none`, `host`, and `bridge` (default).

<details>
<summary>Answer</summary>

| Mode | Behavior |
|------|----------|
| **none** | No external connectivity |
| **host** | Uses host network stack directly (port conflicts possible) |
| **bridge** | Private bridge (e.g. `172.17.0.0/16`); NAT to outside |

**Imperative:**

```bash
docker network ls
docker network inspect bridge
docker run --network host nginx
docker run --network none busybox
```

> Docker uses **CNM**; Kubernetes uses **CNI**.

</details>

---

### 5. CNI — Container Networking Interface

**Q5.1** What is CNI and what are its main plugin categories?

<details>
<summary>Answer</summary>

CNI is the standard for attaching network interfaces to containers/Pods.

| Type | Purpose |
|------|---------|
| bridge | Linux bridge |
| vlan | VLAN tagging |
| ipvlan / macvlan | L2/L3 virtual interfaces |
| host-local | IPAM — local IP pool |
| flannel / calico / cilium | Full networking solutions |

**Imperative — on a node:**

```bash
ls /opt/cni/bin
ls /etc/cni/net.d
cat /etc/cni/net.d/*.conflist
```

</details>

**Q5.2** Name four popular Kubernetes CNI implementations and their models.

<details>
<summary>Answer</summary>

| Plugin | Model |
|--------|-------|
| **Flannel** | Simple overlay (VXLAN) |
| **Calico** | BGP or overlay; NetworkPolicy |
| **Cilium** | eBPF-based |
| **Weave** | Mesh overlay |

**Imperative — identify installed CNI:**

```bash
kubectl get pods -n kube-system | grep -E 'flannel|calico|cilium|weave'
```

</details>

---

### 6. Cluster Networking Requirements

**Q6.1** List three requirements every Kubernetes node must meet for networking.

<details>
<summary>Answer</summary>

1. At least one network interface with an IP
2. Unique hostname and MAC address
3. **No NAT** between nodes for Pod-to-Pod traffic

**Imperative — verify on node:**

```bash
hostname
ip link show | grep ether
cat /proc/sys/net/ipv4/ip_forward   # should be 1
```

</details>

**Q6.2** List the required ports for CKA (apiserver, kubelet, etcd, NodePort, CoreDNS).

<details>
<summary>Answer</summary>

| Component | Port | Nodes |
|-----------|------|-------|
| kube-apiserver | **6443** | Control plane |
| kubelet API | **10250** | All nodes |
| kube-scheduler | **10259** | Control plane |
| kube-controller-manager | **10257** | Control plane |
| etcd client | **2379** | Control plane |
| etcd peer | **2380** | Control plane (HA) |
| NodePort Services | **30000–32767** | Workers |
| CoreDNS | **53** | Cluster DNS |

**Imperative:**

```bash
netstat -plant | grep -E '6443|10250|2379'
ss -tlnp | grep 6443
```

</details>

---

### 7. Pod Networking

**Q7.1** What IP model does Kubernetes use for Pods? List the five CNI responsibilities when a Pod is created.

<details>
<summary>Answer</summary>

**Every Pod gets its own IP.** Pods on any node communicate directly (unless NetworkPolicy blocks).

CNI responsibilities:
1. Create **veth** pair
2. Attach one end to Pod, one to bridge/host
3. Assign **IP address** (via IPAM)
4. Bring interface **up**
5. Configure **routes** as needed

**Imperative:**

```bash
kubectl get pods -o wide
ip link | grep veth
```

</details>

---

### 8. CNI in Kubernetes

**Q8.1** Where are CNI plugin binaries and config files located?

<details>
<summary>Answer</summary>

| Path | Contents |
|------|----------|
| `/opt/cni/bin` | CNI plugin binaries |
| `/etc/cni/net.d` | Plugin config (`.conflist`, `.conf`) |

**Imperative:**

```bash
ls /opt/cni/bin
ls /etc/cni/net.d
cat /etc/cni/net.d/10-flannel.conflist
```

</details>

**Q8.2** Show a minimal CNI config using bridge type with host-local IPAM.

<details>
<summary>Answer</summary>

**Declarative (CNI config on node — `/etc/cni/net.d/mynet.conflist`):**

```json
{
  "cniVersion": "0.4.0",
  "name": "mynet",
  "type": "bridge",
  "ipam": {
    "type": "host-local",
    "subnet": "10.244.0.0/16"
  }
}
```

**Imperative — validate CNI on node:**

```bash
/opt/cni/bin/bridge --help
cat /etc/cni/net.d/*.conflist | jq .
```

</details>

---

### 9. IPAM

**Q9.1** What is IPAM and name three IPAM plugins used with CNI.

<details>
<summary>Answer</summary>

**IP Address Management** assigns IPs from a pool.

| Plugin | Description |
|--------|-------------|
| **host-local** | File-based local IP pool |
| **dhcp** | DHCP server |
| **calico-ipam** | Calico integrated IPAM |

Configured in the CNI config under the `"ipam"` section (see Q8.2).

</details>

---

### 10. Service Networking

**Q10.1** Create a ClusterIP Service `my-service` selecting `app: myapp`, port 80 → targetPort 8080.

<details>
<summary>Answer</summary>

**Imperative:**

```bash
kubectl expose pod myapp --name=my-service --port=80 --target-port=8080
# Or from deployment:
kubectl expose deployment myapp --name=my-service --port=80 --target-port=8080
kubectl get svc my-service
kubectl describe svc my-service
```

**Declarative:**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-service
spec:
  type: ClusterIP
  selector:
    app: myapp
  ports:
    - port: 80
      targetPort: 8080
```

```bash
kubectl apply -f my-service.yaml
```

</details>

**Q10.2** Compare Service types: ClusterIP, NodePort, LoadBalancer, ExternalName.

<details>
<summary>Answer</summary>

| Type | Access |
|------|--------|
| **ClusterIP** | Internal cluster only |
| **NodePort** | Port on every node (30000–32767) |
| **LoadBalancer** | Cloud LB → NodePort |
| **ExternalName** | CNAME to external DNS |

**Declarative — NodePort:**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-nodeport
spec:
  type: NodePort
  selector:
    app: myapp
  ports:
    - port: 80
      targetPort: 8080
      nodePort: 30080
```

**Imperative:**

```bash
kubectl apply -f my-nodeport.yaml
kubectl get svc my-nodeport
curl <node-ip>:30080
```

</details>

**Q10.3** What are the two kube-proxy modes and when prefer IPVS?

<details>
<summary>Answer</summary>

| Mode | Notes |
|------|-------|
| **iptables** | Default; rule-based load balancing |
| **ipvs** | Better at scale; supports more load-balancing algorithms |

**Imperative:**

```bash
kubectl get configmap kube-proxy -n kube-system -o yaml | grep mode
```

</details>

---

### 11. CoreDNS & DNS Resolution

**Q11.1** What is the fully qualified DNS name for Service `my-svc` in namespace `apps`?

<details>
<summary>Answer</summary>

```
my-svc.apps.svc.cluster.local
```

Shorthand within same namespace: `my-svc`

**Imperative — test DNS from a Pod:**

```bash
kubectl run -it --rm debug --image=busybox --restart=Never -- nslookup my-svc.apps
kubectl run -it --rm debug --image=busybox --restart=Never -- nslookup kubernetes.default
```

</details>

**Q11.2** CoreDNS Pods are not running. How do you investigate?

<details>
<summary>Answer</summary>

**Imperative:**

```bash
kubectl get pods -n kube-system -l k8s-app=kube-dns
kubectl describe pod -n kube-system -l k8s-app=kube-dns
kubectl logs -n kube-system -l k8s-app=kube-dns
kubectl get svc -n kube-system kube-dns
kubectl get endpoints -n kube-system kube-dns
kubectl get configmap coredns -n kube-system -o yaml
```

</details>

---

### 12. Linux Networking Commands

**Q12.1** Show IP addresses, add IP `192.168.1.10/24` to `eth0`, and display the routing table.

<details>
<summary>Answer</summary>

**Imperative:**

```bash
ip link
ip addr
ip addr add 192.168.1.10/24 dev eth0
ip route
ip route add 192.168.1.0/24 via 192.168.2.1
netstat -plant
arp
cat /proc/sys/net/ipv4/ip_forward
```

</details>

**Q12.2** Enable IP forwarding on a Linux node (required for Pod routing).

<details>
<summary>Answer</summary>

**Imperative:**

```bash
echo 1 > /proc/sys/net/ipv4/ip_forward
sysctl -w net.ipv4.ip_forward=1
# Persistent:
echo 'net.ipv4.ip_forward = 1' >> /etc/sysctl.d/k8s.conf
sysctl --system
```

</details>

---

### 13. Cheat Sheet & Resources

**Q13.1** A Service has no endpoints. Diagnose and fix.

<details>
<summary>Answer</summary>

**Imperative:**

```bash
kubectl get svc <name>
kubectl get endpoints <name>
kubectl describe svc <name>
kubectl get pods --show-labels
```

**Common fix:** Service selector doesn't match Pod labels.

**Declarative — fix selector:**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-service
spec:
  selector:
    app: myapp    # must match Pod labels
  ports:
    - port: 80
      targetPort: 8080
```

```bash
kubectl apply -f my-service.yaml
kubectl get endpoints my-service
```

</details>

---

## Mixed Topic Questions

### Scenario 1 — Service Discovery Failure

Pods in namespace `apps` cannot resolve `backend.apps.svc.cluster.local`. CoreDNS is running. Diagnose step by step.

<details>
<summary>Answer</summary>

**Imperative — diagnostic sequence:**

```bash
# 1. Verify CoreDNS
kubectl get pods -n kube-system -l k8s-app=kube-dns
kubectl get svc -n kube-system kube-dns

# 2. Verify backend Service exists
kubectl get svc -n apps backend
kubectl get endpoints -n apps backend

# 3. Test DNS from a Pod in apps namespace
kubectl run -it --rm dns-test -n apps --image=busybox --restart=Never \
  -- nslookup backend.apps.svc.cluster.local

# 4. Check Pod resolv.conf
kubectl run -it --rm dns-test -n apps --image=busybox --restart=Never \
  -- cat /etc/resolv.conf
# Should contain: nameserver <cluster-dns-ip> and search apps.svc.cluster.local svc.cluster.local cluster.local

# 5. Check NetworkPolicy blocking DNS (port 53)
kubectl get networkpolicy -n apps
kubectl get networkpolicy -n kube-system
```

**Fix examples:**
- Service missing → create Service with correct selector
- Endpoints empty → fix Pod labels or selector
- NetworkPolicy blocking → allow egress to kube-system DNS on port 53

**Declarative — backend Service:**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: backend
  namespace: apps
spec:
  selector:
    app: backend
  ports:
    - port: 80
      targetPort: 8080
```

</details>

---

### Scenario 2 — Expose Application Externally

Deployment `web` (labels `app: web`, container port 8080) must be reachable internally on port 80 and externally via NodePort 30080.

<details>
<summary>Answer</summary>

**Imperative:**

```bash
kubectl expose deployment web --port=80 --target-port=8080 --type=NodePort
kubectl patch svc web -p '{"spec":{"ports":[{"port":80,"targetPort":8080,"nodePort":30080}]}}'
kubectl get svc web
curl <worker-node-ip>:30080
```

**Declarative:**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web
spec:
  type: NodePort
  selector:
    app: web
  ports:
    - port: 80
      targetPort: 8080
      nodePort: 30080
```

```bash
kubectl apply -f web-svc.yaml
kubectl get endpoints web
```

</details>

---

### Scenario 3 — Pod-to-Pod Connectivity Across Nodes

Pod `A` on `node-1` cannot ping Pod `B` on `node-2`. CNI is Flannel. Troubleshoot.

<details>
<summary>Answer</summary>

**Imperative — on both nodes:**

```bash
# Verify Pod IPs
kubectl get pods -o wide

# On node-1: check routes to Pod CIDR
ip route | grep 10.244
ip link | grep flannel

# Check CNI pods
kubectl get pods -n kube-system | grep flannel
kubectl logs -n kube-system <flannel-pod>

# Check IP forwarding
cat /proc/sys/net/ipv4/ip_forward   # must be 1

# Check firewall
iptables -L -n | head -20

# Test from Pod
kubectl exec -it pod-A -- ping <pod-B-ip>
```

**Common fixes:**
- CNI not installed or Flannel pods crashing
- `ip_forward` disabled
- Firewall blocking VXLAN (UDP 8472 for Flannel)
- VM clones with duplicate MAC addresses

**Imperative — fix IP forwarding:**

```bash
sysctl -w net.ipv4.ip_forward=1
```

</details>

---

### Scenario 4 — NetworkPolicy Restricting Traffic

Namespace `prod` has a default-deny policy. Allow frontend Pods (`app: frontend`) to reach backend Pods (`app: backend`) on port 8080 only.

<details>
<summary>Answer</summary>

**Declarative:**

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend-to-backend
  namespace: prod
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
    - Ingress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: frontend
      ports:
        - protocol: TCP
          port: 8080
```

**Imperative:**

```bash
kubectl apply -f netpol.yaml
kubectl get networkpolicy -n prod
kubectl exec -n prod <frontend-pod> -- wget -qO- backend:8080
```

> Requires a CNI that supports NetworkPolicy (Calico, Cilium, Weave).

</details>

---

### Scenario 5 — Debug CNI on a New Node

A new worker node joins but all Pods stay `ContainerCreating` with network setup errors.

<details>
<summary>Answer</summary>

**Imperative — on the failing node:**

```bash
# Check kubelet logs
journalctl -u kubelet -f

# Verify CNI binaries and config
ls /opt/cni/bin
ls /etc/cni/net.d
cat /etc/cni/net.d/*.conflist

# Check container runtime CNI config path
grep -i cni /etc/containerd/config.toml

# Verify bridge/CNI state
ip link
brctl show 2>/dev/null || bridge link

# On control plane — check CNI daemonset pods on new node
kubectl get pods -n kube-system -o wide | grep <new-node>
```

**Common fixes:**
- Missing `/opt/cni/bin` binaries — install CNI plugins
- Missing `/etc/cni/net.d` config — CNI not deployed to node
- containerd not configured for CNI path
- CNI DaemonSet not scheduled on new node (taints/tolerations)

**Imperative — reinstall CNI (example Flannel):**

```bash
kubectl apply -f https://github.com/flannel-io/flannel/releases/latest/download/kube-flannel.yml
```

</details>

---

### Scenario 6 — Ingress + Service Chain

Expose `web` Deployment via Ingress `web-ingress` at path `/` on host `app.example.com`, backed by ClusterIP Service port 80.

<details>
<summary>Answer</summary>

**Declarative:**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web
spec:
  type: ClusterIP
  selector:
    app: web
  ports:
    - port: 80
      targetPort: 8080
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: web-ingress
spec:
  rules:
    - host: app.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: web
                port:
                  number: 80
```

**Imperative:**

```bash
kubectl apply -f web-ingress.yaml
kubectl get ingress web-ingress
kubectl describe ingress web-ingress
# Add to /etc/hosts: <ingress-ip> app.example.com
curl -H "Host: app.example.com" http://<ingress-ip>/
```

</details>
