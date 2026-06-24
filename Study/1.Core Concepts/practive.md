# CKA Practice — Core Concepts

> Based on [enhanced_readme.md](./enhanced_readme.md)

---

## 1. Cluster Architecture

**Q1.** List the control plane components and describe the role of each.

**Answer:**
- **etcd** — distributed key-value store; cluster source of truth
- **kube-apiserver** — front door; authenticates, validates, persists state
- **kube-scheduler** — assigns unscheduled Pods to nodes
- **kube-controller-manager** — reconciles desired vs actual state via controllers
- **Container runtime** (containerd/CRI-O) — runs containers on control plane nodes where applicable

Worker nodes run **kubelet**, **kube-proxy**, and a **container runtime**.

**Imperative:**
```bash
kubectl get nodes
kubectl get pods -n kube-system
kubectl cluster-info
```

---

**Q2.** Which component is responsible for maintaining network rules so Services can load-balance to backend Pods?

**Answer:** **kube-proxy** on each worker node maintains iptables or IPVS rules for Service routing. Pod IPs are assigned by the **CNI plugin**.

---

## 2. Docker vs containerd & CRI

**Q1.** Starting with Kubernetes v1.24, why can you no longer use Docker Engine directly as the container runtime?

**Answer:** **dockershim was removed** in v1.24. Kubernetes communicates with runtimes through the **CRI (Container Runtime Interface)**. Docker Engine is not CRI-native; use **containerd** or **CRI-O** instead.

**Imperative:**
```bash
crictl ps -a
crictl images
crictl pods
```

---

**Q2.** Which CLI tool should you use to debug containers on any CRI-compatible runtime?

**Answer:** **crictl** — the CRI debugging CLI. **ctr** is low-level containerd; **nerdctl** is Docker-like for containerd.

```bash
crictl pull busybox
crictl logs <container_id>
```

---

## 3. etcd

**Q1.** Back up all etcd data on a kubeadm control plane node. What environment variable must be set for etcdctl v3?

**Answer:** Set `ETCDCTL_API=3` (default in modern clusters).

**Imperative:**
```bash
export ETCDCTL_API=3
ETCDCTL_API=3 etcdctl \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  snapshot save /var/backups/etcd-snapshot.db
```

---

**Q2.** What types of objects does etcd store?

**Answer:** All cluster state: Nodes, Pods, Deployments, Services, ConfigMaps, Secrets, ServiceAccounts, Roles, RoleBindings, and all desired configuration.

---

## 4. kube-apiserver — Request Flow

**Q1.** A user runs `kubectl run nginx --image=nginx`. Describe the request flow until the container starts.

**Answer:**
1. kubectl sends POST to kube-apiserver
2. apiserver authenticates/validates and stores Pod in etcd (no node assigned)
3. kube-scheduler watches, filters/scores nodes, binds Pod to a node
4. kubelet on that node pulls image and starts container via CRI
5. kubelet reports Pod status back to apiserver

---

**Q2.** Where are static Pod manifests for control plane components located on a kubeadm cluster?

**Answer:** `/etc/kubernetes/manifests/` — e.g. `kube-apiserver.yaml`, `kube-controller-manager.yaml`, `kube-scheduler.yaml`, `etcd.yaml`.

**Imperative:**
```bash
ls /etc/kubernetes/manifests/
kubectl get pods -n kube-system
```

---

## 5. kube-controller-manager

**Q1.** What happens when a node stops sending heartbeats?

**Answer:**
- Health check every **5 seconds**
- After **40 seconds** of missed heartbeats → node marked **Unreachable**
- After **5 minutes** → Pods evicted and rescheduled (if managed by a controller)

---

**Q2.** Name three controllers managed by kube-controller-manager.

**Answer:** Deployment controller, ReplicaSet controller, Node controller, ServiceAccount controller, Job/CronJob controller, StatefulSet controller, Endpoints controller (any three).

---

## 6. kube-scheduler

**Q1.** What are the three scheduling phases?

**Answer:**
1. **Filtering** — remove nodes that don't meet requirements
2. **Scoring** — rank remaining nodes
3. **Binding** — assign Pod to highest-scoring node

The scheduler does **not** run containers; kubelet does.

---

**Q2.** A Pod remains in `Pending` with no node assigned. Which component should you investigate first?

**Answer:** **kube-scheduler** — check scheduler logs, node resources, taints/tolerations, affinity rules, and resource requests.

```bash
kubectl describe pod <pod-name>
kubectl logs -n kube-system kube-scheduler-<node>
```

---

## 7. kubelet

**Q1.** Does kubeadm deploy kubelet as a Pod? How is kubelet installed?

**Answer:** **No.** kubelet must be installed **manually on every node** (systemd service). It registers the node, creates/destroys Pods, and reports status to the apiserver.

**Imperative:**
```bash
systemctl status kubelet
journalctl -u kubelet
```

---

**Q2.** What is the relationship between kubelet and the container runtime?

**Answer:** kubelet receives Pod specs from the apiserver and makes **CRI calls** to the container runtime to pull images and start/stop containers.

---

## 8. kube-proxy & Pod Networking

**Q1.** Create a ClusterIP Service that routes port 80 to Pods labeled `app=web` on targetPort 8080.

**Imperative:**
```bash
kubectl expose pod web-pod --port=80 --target-port=8080 --name=web-svc
```

**Declarative:**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-svc
spec:
  type: ClusterIP
  selector:
    app: web
  ports:
    - port: 80
      targetPort: 8080
```

---

**Q2.** Which three layers handle Pod networking, DNS, and Service routing?

**Answer:**
| Layer | Component |
|-------|-----------|
| Pod network | CNI plugin (assigns Pod IP) |
| Service discovery | CoreDNS |
| Service routing | kube-proxy (iptables/IPVS) |

---

## 9. Pods

**Q1.** Create a Pod named `nginx` using image `nginx:1.25` with label `app=nginx`.

**Imperative:**
```bash
kubectl run nginx --image=nginx:1.25 --labels=app=nginx
```

**Declarative:**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx
  labels:
    app: nginx
spec:
  containers:
    - name: nginx
      image: nginx:1.25
```

---

**Q2.** Export the YAML of Pod `webapp` to `my-new-pod.yaml`, then create a new Pod from it with a different name.

**Imperative:**
```bash
kubectl get pod webapp -o yaml > my-new-pod.yaml
# Edit metadata.name, then:
kubectl apply -f my-new-pod.yaml
```

---

## 10. ReplicaSet & ReplicationController

**Q1.** Scale ReplicaSet `myapp-replicaset` to 6 replicas.

**Imperative:**
```bash
kubectl scale --replicas=6 replicaset myapp-replicaset
kubectl get rs myapp-replicaset
```

**Declarative:**
```yaml
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: myapp-replicaset
spec:
  replicas: 6
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
        - name: nginx
          image: nginx
```

---

**Q2.** What is the key difference between ReplicationController and ReplicaSet?

**Answer:** ReplicationController (legacy) supports **equality-based selectors only**. ReplicaSet supports `matchLabels` and **`matchExpressions`** (set-based selectors). ReplicaSet is the current standard.

---

## 11. Deployments

**Q1.** Update Deployment `myapp-deployment` to use image `nginx:1.9.1` and watch the rollout.

**Imperative:**
```bash
kubectl set image deployment/myapp-deployment nginx=nginx:1.9.1
kubectl rollout status deployment/myapp-deployment
kubectl rollout history deployment/myapp-deployment
```

---

**Q2.** Roll back Deployment `myapp-deployment` to the previous revision.

**Imperative:**
```bash
kubectl rollout undo deployment/myapp-deployment
# Or to a specific revision:
kubectl rollout undo deployment/myapp-deployment --to-revision=2
```

**Declarative:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp-deployment
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
        - name: nginx
          image: nginx:1.9.1
```

---

## 12. Services

**Q1.** Create a NodePort Service `myapp-service` exposing port 80 (targetPort 8080) on nodePort 30004 for Pods labeled `app=myapp`.

**Declarative:**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: myapp-service
spec:
  type: NodePort
  selector:
    app: myapp
  ports:
    - port: 80
      targetPort: 8080
      nodePort: 30004
```

**Imperative:**
```bash
kubectl expose deployment myapp-deployment --type=NodePort --port=80 --target-port=8080 --name=myapp-service
```

---

**Q2.** Compare ClusterIP, NodePort, and LoadBalancer Service types.

**Answer:**
| Type | Scope | Use case |
|------|-------|----------|
| ClusterIP (default) | Internal only | Pod-to-Pod communication |
| NodePort | 30000–32767 on every node | Dev/test external access |
| LoadBalancer | Cloud LB + NodePort | Production external access |

---

## 13. Namespaces & Resource Quotas

**Q1.** Create namespace `dev` and a ResourceQuota limiting CPU requests to 4, memory requests to 4Gi, CPU limits to 10, and memory limits to 10Gi.

**Imperative:**
```bash
kubectl create namespace dev
```

**Declarative:**
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: dev
---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: cpu-resource-quota
  namespace: dev
spec:
  hard:
    requests.cpu: "4"
    requests.memory: 4Gi
    limits.cpu: "10"
    limits.memory: 10Gi
```

---

**Q2.** What is the purpose of the `kube-system` namespace?

**Answer:** Houses **system components** — control plane Pods (apiserver, scheduler, etcd), CoreDNS, kube-proxy, Metrics Server, etc.

---

## 14. Imperative vs Declarative

**Q1.** Which kubectl command is idempotent and stores last-applied configuration?

**Answer:** **`kubectl apply -f`** — idempotent and stores config in annotation `kubectl.kubernetes.io/last-applied-configuration`. `kubectl create` and `kubectl replace` are **not** idempotent.

**Imperative:**
```bash
kubectl apply -f manifest.yaml    # declarative, idempotent
kubectl create -f manifest.yaml   # fails if exists
kubectl replace -f manifest.yaml  # requires full object
```

---

**Q2.** Create a Deployment imperatively with 3 replicas.

**Imperative:**
```bash
kubectl create deployment web --image=nginx --replicas=3
```

---

## 15. How `kubectl apply` Works

**Q1.** Explain the three-way merge used by `kubectl apply`.

**Answer:** kubectl merges three sources:
1. **Local YAML** (desired state from file)
2. **Last applied configuration** (stored in annotation)
3. **Live object** in cluster

The result is sent as a JSON patch to the apiserver.

---

**Q2.** Which annotation stores the last-applied configuration?

**Answer:** `kubectl.kubernetes.io/last-applied-configuration`

```bash
kubectl get pod mypod -o yaml | grep last-applied
```

---

## 16. Scheduling Overview

**Q1.** Name four scheduling constraint mechanisms covered in this chapter.

**Answer:** Manual scheduling (`nodeName`/Binding), **Labels & Selectors**, **Taints & Tolerations**, **Node Selector / Node Affinity**, **Resource requests/limits**, **DaemonSets**, **Static Pods**, **Priority Classes**, **Multiple schedulers**.

---

**Q2.** Who assigns Pods to nodes by default?

**Answer:** **kube-scheduler** automatically assigns Pods when `nodeName` is empty and no custom `schedulerName` is set.

---

## 17. Manual Scheduling

**Q1.** Schedule Pod `nginx` onto `node02` at creation time.

**Declarative:**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx
spec:
  containers:
    - name: nginx
      image: nginx
  nodeName: node02
```

---

**Q2.** Bind an existing unscheduled Pod `nginx` to `node02` using the Binding API.

**Declarative:**
```yaml
apiVersion: v1
kind: Binding
metadata:
  name: nginx
target:
  apiVersion: v1
  kind: Node
  name: node02
```

**Imperative:**
```bash
kubectl apply -f binding.yaml
```

---

## 18. Labels & Selectors

**Q1.** Add label `status=active` to Pod `mypod`, then list all Pods with `env=dev` and `tier=frontend`.

**Imperative:**
```bash
kubectl label pods mypod status=active
kubectl get pods -l env=dev,tier=frontend
kubectl get pods --selector env=dev
```

---

**Q2.** Remove label `status` from Pod `mypod`.

**Imperative:**
```bash
kubectl label pods mypod status-
```

---

## 19. Taints & Tolerations

**Q1.** Taint `node1` with `app=blue:NoSchedule`. Create a Pod that tolerates this taint.

**Imperative:**
```bash
kubectl taint nodes node1 app=blue:NoSchedule
```

**Declarative:**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: blue-app
spec:
  tolerations:
    - key: app
      operator: Equal
      value: blue
      effect: NoSchedule
  containers:
    - name: nginx
      image: nginx
```

---

**Q2.** Compare `NoSchedule`, `PreferNoSchedule`, and `NoExecute` taint effects.

**Answer:**
| Effect | Behavior |
|--------|----------|
| NoSchedule | Pod not scheduled unless it tolerates |
| PreferNoSchedule | Scheduler tries to avoid the node |
| NoExecute | Not scheduled; existing Pods without toleration are **evicted** |

---

## 20. Node Selectors & Node Affinity

**Q1.** Schedule a Pod only on nodes labeled `size=Large`.

**Declarative (nodeSelector):**
```yaml
spec:
  nodeSelector:
    size: Large
  containers:
    - name: nginx
      image: nginx
```

**Imperative:**
```bash
kubectl label nodes node01 size=Large
```

---

**Q2.** Require node affinity for `size` In `[Large, Medium]` and prefer `disktype=ssd`.

**Declarative:**
```yaml
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
          - matchExpressions:
              - key: size
                operator: In
                values:
                  - Large
                  - Medium
      preferredDuringSchedulingIgnoredDuringExecution:
        - weight: 1
          preference:
            matchExpressions:
              - key: disktype
                operator: In
                values:
                  - ssd
  containers:
    - name: nginx
      image: nginx
```

---

## 21. Resource Requests, Limits & Quotas

**Q1.** Create a Pod with requests `cpu: 2`, `memory: 1Gi` and limits `cpu: 2`, `memory: 2Gi`.

**Declarative:**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: resource-pod
spec:
  containers:
    - name: nginx
      image: nginx
      resources:
        requests:
          memory: "1Gi"
          cpu: "2"
        limits:
          memory: "2Gi"
          cpu: "2"
```

---

**Q2.** What is the difference between `500m` CPU and `1Gi` memory notation?

**Answer:** CPU: `500m` = 0.5 core (millicores). Memory: `1Gi` = 1024-based (binary); `1G` = 1000-based (decimal). Scheduler uses **requests**; runtime enforces **limits**.

---

## 22. DaemonSets

**Q1.** Deploy a DaemonSet `elasticsearch` in `kube-system` with label `app=elasticsearch`.

**Declarative:**
```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: elasticsearch
  namespace: kube-system
spec:
  selector:
    matchLabels:
      app: elasticsearch
  template:
    metadata:
      labels:
        app: elasticsearch
    spec:
      containers:
        - name: fluentd-elasticsearch
          image: registry.k8s.io/fluentd-elasticsearch:1.20
```

**Imperative:**
```bash
kubectl apply -f daemonset.yaml
kubectl get ds -n kube-system
```

---

**Q2.** When would you use a DaemonSet instead of a Deployment?

**Answer:** When you need **one Pod per node** — log collectors (fluentd), monitoring (node-exporter), networking agents (kube-proxy), storage agents.

---

## 23. Static Pods

**Q1.** How are static Pods managed and where is their manifest path configured?

**Answer:** Managed directly by **kubelet** (not scheduler/controllers). Manifest path: `--pod-manifest-path=/etc/kubernetes/manifests` or `staticPodPath` in kubelet config. Mirror Pods appear in API with suffix `-<nodeName>`.

---

**Q2.** Which control plane components run as static Pods with kubeadm?

**Answer:** kube-apiserver, kube-controller-manager, kube-scheduler, and etcd.

```bash
ls /etc/kubernetes/manifests/
kubectl get pods -n kube-system -o wide
```

---

## 24. Priority Classes & Preemption

**Q1.** Create PriorityClass `high-priority` with value `1000000000` and assign it to a Pod.

**Declarative:**
```yaml
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: high-priority
value: 1000000000
description: "Priority class for mission-critical pods"
preemptionPolicy: PreemptLowerPriority
---
apiVersion: v1
kind: Pod
metadata:
  name: critical-pod
spec:
  priorityClassName: high-priority
  containers:
    - name: nginx
      image: nginx
```

**Imperative:**
```bash
kubectl get priorityclasses
```

---

**Q2.** What does `preemptionPolicy: Never` do?

**Answer:** The Pod will **never preempt** lower-priority Pods. Default `PreemptLowerPriority` allows higher-priority Pods to evict lower-priority ones when resources are scarce.

---

## 25. Multiple Schedulers & Profiles

**Q1.** Assign Pod `nginx` to a custom scheduler named `my-custom-scheduler`.

**Declarative:**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx
spec:
  schedulerName: my-custom-scheduler
  containers:
    - name: nginx
      image: nginx
```

---

**Q2.** Name the default scheduling framework phases and one plugin in each.

**Answer:**
| Phase | Example plugin |
|-------|----------------|
| Queue sort | PrioritySort |
| Filter | NodeResourceFit, NodeName |
| Score | NodeResourceFit, ImageLocality |
| Bind | DefaultBinder |

---

## 26. Admission Controllers

**Q1.** Where do admission controllers sit in the request flow?

**Answer:** After **authentication** and **authorization**, **before** persistence in etcd. Mutating controllers run before validating ones.

---

**Q2.** Name three built-in admission controllers and their purpose.

**Answer:**
| Controller | Purpose |
|------------|---------|
| NamespaceLifecycle | Prevents ops in terminating namespaces |
| LimitRanger | Enforces LimitRange defaults/min/max |
| ResourceQuota | Enforces namespace quotas |
| PodSecurity | Enforces Pod Security Standards |

Enable via `--enable-admission-plugins` on kube-apiserver.

---

## 27. Useful Commands Cheat Sheet

**Q1.** Set default namespace to `dev` for the current context and list all Pods across namespaces.

**Imperative:**
```bash
kubectl config set-context $(kubectl config current-context) --namespace=dev
kubectl get pods --all-namespaces
kubectl get pods,rs,deploy,svc
```

---

**Q2.** Explain `pod.spec.containers` recursively and export a Pod YAML.

**Imperative:**
```bash
kubectl explain pod.spec.containers --recursive
kubectl get pod <name> -o yaml > exported.yaml
kubectl api-resources
```

---

## 28. Docs & Resources

**Q1.** Where do you find official YAML examples for Deployments, Services, and DaemonSets?

**Answer:** [kubernetes.io/docs](https://kubernetes.io/docs/) — Concepts and Tasks sections. Key pages: Deployments, Service networking, DaemonSet, Scheduling, Resource Management, Static Pods, Admission Controllers.

---

## Mixed Topic Questions

**Q1.** Deploy a 3-replica nginx Deployment in namespace `prod`, expose it as NodePort Service on port 30080, and verify Pods are running.

**Imperative:**
```bash
kubectl create namespace prod
kubectl create deployment nginx --image=nginx --replicas=3 -n prod
kubectl expose deployment nginx --type=NodePort --port=80 --target-port=80 -n prod
kubectl get deploy,svc,pods -n prod
```

**Declarative:**
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: prod
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx
  namespace: prod
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
        - name: nginx
          image: nginx
          ports:
            - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: nginx
  namespace: prod
spec:
  type: NodePort
  selector:
    app: nginx
  ports:
    - port: 80
      targetPort: 80
      nodePort: 30080
```

---

**Q2.** A Pod stays Pending. It has `nodeSelector: disktype=ssd` but no nodes have that label. Fix it by labeling `node01` and ensuring the Pod schedules.

**Imperative:**
```bash
kubectl label nodes node01 disktype=ssd
kubectl describe pod <pod-name>
kubectl get pod <pod-name> -o wide
```

---

**Q3.** Taint the control plane node to prevent scheduling, then deploy a DaemonSet log collector that tolerates the control-plane taint.

**Imperative:**
```bash
kubectl describe node controlplane | grep -i taint
```

**Declarative:**
```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: log-collector
  namespace: kube-system
spec:
  selector:
    matchLabels:
      app: log-collector
  template:
    metadata:
      labels:
        app: log-collector
    spec:
      tolerations:
        - key: node-role.kubernetes.io/control-plane
          operator: Exists
          effect: NoSchedule
      containers:
        - name: fluentd
          image: fluent/fluentd:v1.16
```

---

**Q4.** Export existing Pod `webapp` YAML, change the image to `nginx:1.25`, apply declaratively, then roll back if broken using rollout history.

**Imperative:**
```bash
kubectl get pod webapp -o yaml > webapp.yaml
# Edit image in YAML
kubectl apply -f webapp.yaml
# If managed by Deployment:
kubectl rollout history deployment/webapp
kubectl rollout undo deployment/webapp
```

---

**Q5.** Create namespace `dev` with ResourceQuota (max 10 Pods, 4 CPU requests) and deploy a Pod with Guaranteed QoS (requests = limits).

**Declarative:**
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: dev
---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: dev-quota
  namespace: dev
spec:
  hard:
    pods: "10"
    requests.cpu: "4"
---
apiVersion: v1
kind: Pod
metadata:
  name: guaranteed-pod
  namespace: dev
spec:
  containers:
    - name: app
      image: nginx
      resources:
        requests:
          cpu: "500m"
          memory: "256Mi"
        limits:
          cpu: "500m"
          memory: "256Mi"
```

**Answer:** Guaranteed QoS requires **limits = requests** for all containers.

---

**Q6.** Manually schedule Pod `debug` on `node02`, verify kubelet started it, check logs, and delete it.

**Imperative:**
```bash
kubectl run debug --image=busybox --restart=Never --command -- sleep 3600 --overrides='{"spec":{"nodeName":"node02"}}'
kubectl get pod debug -o wide
kubectl logs debug
kubectl delete pod debug
```

**Declarative:**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: debug
spec:
  nodeName: node02
  containers:
    - name: busybox
      image: busybox
      command: ["sleep", "3600"]
```
