# CKA Practice — Scheduling

> Based on [enhanced_readme.md](./enhanced_readme.md)

---

## 1. Scheduling Overview

**Q1.** Describe the default Pod scheduling workflow from creation to running on a node.

**Answer:**
1. User creates Pod → apiserver stores it in etcd (no `nodeName`)
2. kube-scheduler watches unscheduled Pods
3. Scheduler **filters** nodes, **scores** them, **binds** best node
4. kubelet on chosen node pulls image and starts container

---

**Q2.** Name four categories of scheduling constraints from the scheduling mindmap.

**Answer:** **Manual** (nodeName, Binding), **Constraints** (labels, taints, node selector, affinity), **Resources** (requests, limits, LimitRange, ResourceQuota), **Special** (DaemonSets, static Pods, multiple schedulers, priority/preemption).

---

## 2. Manual Scheduling

**Q1.** Force Pod `nginx` onto `node02` at creation time, bypassing the scheduler.

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

**Imperative:**
```bash
kubectl run nginx --image=nginx --restart=Never --overrides='{"spec":{"nodeName":"node02"}}'
```

---

**Q2.** An unscheduled Pod `nginx` exists. Bind it to `node02` using the Binding API.

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

## 3. Labels & Selectors

**Q1.** Label node `node01` with `size=Large` and list all nodes showing labels.

**Imperative:**
```bash
kubectl label nodes node01 size=Large
kubectl get nodes --show-labels
kubectl describe node node01
```

---

**Q2.** Add label `tier=frontend` to Pod `mypod` and retrieve all Pods matching `env=dev,tier=frontend`.

**Imperative:**
```bash
kubectl label pods mypod tier=frontend
kubectl get pods -l env=dev,tier=frontend
kubectl get pods --selector env=dev
```

---

## 4. Taints & Tolerations

**Q1.** Taint `node1` with `app=blue:NoSchedule` and remove the control-plane taint from `controlplane`.

**Imperative:**
```bash
kubectl taint nodes node1 app=blue:NoSchedule
kubectl taint nodes controlplane node-role.kubernetes.io/control-plane:NoSchedule-
kubectl describe node node1 | grep -i taint
```

---

**Q2.** Create a Pod that tolerates `app=blue:NoSchedule` and the control-plane taint.

**Declarative:**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: tolerant-pod
spec:
  tolerations:
    - key: app
      operator: Equal
      value: blue
      effect: NoSchedule
    - key: node-role.kubernetes.io/control-plane
      operator: Exists
      effect: NoSchedule
  containers:
    - name: nginx
      image: nginx
```

**Answer:** Taints **repel** Pods; they do **not** attract Pods to a node — use **Node Affinity** for attraction.

---

## 5. Node Selectors & Node Affinity

**Q1.** Schedule a Pod only on nodes with `size=Large` using nodeSelector.

**Declarative:**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: large-only
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

**Q2.** Require affinity for `size` In `[Large, Medium]`, prefer `disktype=ssd`, and add pod anti-affinity so no two `app=web` Pods share a host.

**Declarative:**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: web
  labels:
    app: web
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
    podAntiAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        - labelSelector:
            matchExpressions:
              - key: app
                operator: In
                values:
                  - web
          topologyKey: kubernetes.io/hostname
  containers:
    - name: nginx
      image: nginx
```

**Answer:** `requiredDuringSchedulingIgnoredDuringExecution` = hard rule; label changes after scheduling are **ignored** (Pod stays). `requiredDuringSchedulingRequiredDuringExecution` would evict if labels change.

---

## 6. Resource Requests, Limits & Quotas

**Q1.** Create a Pod with Burstable QoS: requests `cpu: 500m, memory: 512Mi`, limits `cpu: 1, memory: 1Gi`.

**Declarative:**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: burstable-pod
spec:
  containers:
    - name: nginx
      image: nginx
      resources:
        requests:
          cpu: 500m
          memory: 512Mi
        limits:
          cpu: "1"
          memory: 1Gi
```

---

**Q2.** Create a LimitRange and ResourceQuota in namespace `dev`.

**Declarative:**
```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: cpu-resource-constraint
  namespace: dev
spec:
  limits:
    - default:
        cpu: 500m
        memory: 1Gi
      defaultRequest:
        cpu: 500m
        memory: 1Gi
      max:
        cpu: "1"
        memory: 1Gi
      min:
        cpu: 100m
        memory: 500Mi
      type: Container
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
    pods: "10"
```

**Answer:** QoS classes: **Guaranteed** (limits = requests), **Burstable** (requests set, limits differ), **BestEffort** (no requests/limits).

---

## 7. DaemonSets

**Q1.** Deploy DaemonSet `elasticsearch` in `kube-system` that tolerates control-plane taints.

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
      tolerations:
        - key: node-role.kubernetes.io/control-plane
          operator: Exists
          effect: NoSchedule
      containers:
        - name: fluentd-elasticsearch
          image: registry.k8s.io/fluentd-elasticsearch:1.20
```

**Imperative:**
```bash
kubectl apply -f daemonset.yaml
kubectl get daemonset -n kube-system
kubectl get pods -n kube-system -l app=elasticsearch
```

---

**Q2.** When is a DaemonSet preferred over a Deployment?

**Answer:** When you need **exactly one Pod per matching node** — log collection (fluentd), monitoring (node-exporter), networking (kube-proxy), storage agents (Ceph/GlusterFS).

---

## 8. Static Pods

**Q1.** How do you create a static Pod and how does it appear in the API?

**Answer:** Place a manifest in kubelet's manifest path (`/etc/kubernetes/manifests` or `staticPodPath` in kubelet config). kubelet creates and monitors it directly. A **mirror Pod** appears in the API with name suffix `-<nodeName>`.

```bash
# On the node:
cp my-static-pod.yaml /etc/kubernetes/manifests/
crictl pods
kubectl get pods -n kube-system
```

---

**Q2.** Who manages static Pods — scheduler, Deployment controller, or kubelet?

**Answer:** **kubelet** only. Static Pods bypass the scheduler and workload controllers. Control plane components (apiserver, etcd, scheduler, controller-manager) are static Pods with kubeadm.

---

## 9. Priority Classes & Preemption

**Q1.** Create PriorityClass `high-priority` (value 1000000000) and a Pod using it.

**Declarative:**
```yaml
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: high-priority
value: 1000000000
globalDefault: false
description: "Mission-critical pods"
preemptionPolicy: PreemptLowerPriority
---
apiVersion: v1
kind: Pod
metadata:
  name: critical-app
spec:
  priorityClassName: high-priority
  containers:
    - name: nginx
      image: nginx
```

**Imperative:**
```bash
kubectl get priorityclasses
kubectl get pc
```

---

**Q2.** What is the valid priority range and default Pod priority?

**Answer:** Range: **-2,147,483,648** to **1,000,000,000**. Default Pod priority is **0**. `PreemptLowerPriority` evicts lower-priority Pods; `Never` disables preemption.

---

## 10. Multiple Schedulers & Profiles

**Q1.** Deploy a custom scheduler Pod and assign a workload to scheduler `my-scheduler`.

**Declarative (scheduler config):**
```yaml
apiVersion: kubescheduler.config.k8s.io/v1
kind: KubeSchedulerConfiguration
profiles:
  - schedulerName: my-scheduler
    plugins:
      score:
        enabled:
          - name: NodeResourcesFit
        disabled:
          - name: ImageLocality
leaderElection:
  leaderElect: true
  resourceNamespace: kube-system
  resourceName: lock-object-my-scheduler
```

**Declarative (Pod using custom scheduler):**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx
spec:
  schedulerName: my-scheduler
  containers:
    - name: nginx
      image: nginx
```

---

**Q2.** Name the scheduling framework phases and example plugins.

**Answer:**
| Phase | Example plugins |
|-------|-----------------|
| Queue sort | PrioritySort |
| PreFilter / Filter | NodeResourceFit, NodeName, TaintToleration |
| PreScore / Score | NodeResourceFit, ImageLocality |
| Bind | DefaultBinder |

Custom plugins register at **Extension Points**.

---

## 11. Admission Controllers

**Q1.** Where do admission controllers fit in the API request path?

**Answer:** After **authentication** and **authorization**, before **etcd** persistence. **Mutating** admission runs before **validating** admission.

---

**Q2.** Which admission controllers enforce LimitRange defaults and namespace quotas?

**Answer:**
- **LimitRanger** — enforces LimitRange default/min/max on Pods and containers
- **ResourceQuota** — enforces namespace ResourceQuota limits
- **NamespaceLifecycle** — blocks operations in terminating namespaces
- **PodSecurity** — enforces Pod Security Standards

Configure via `--enable-admission-plugins` on kube-apiserver.

---

## 12. Cheat Sheet & Resources

**Q1.** Safely drain `node-1` for maintenance, then return it to service.

**Imperative:**
```bash
kubectl cordon node-1
kubectl drain node-1 --ignore-daemonsets --delete-emptydir-data
# Perform maintenance...
kubectl uncordon node-1
```

---

**Q2.** Check node resource usage and explore Pod affinity fields.

**Imperative:**
```bash
kubectl top nodes
kubectl top pods
kubectl explain pod.spec.affinity --recursive
kubectl get nodes --show-labels
```

---

## Mixed Topic Questions

**Q1.** Node `node01` must run only large SSD workloads. Label it, taint it `dedicated=large:NoSchedule`, and deploy a Pod with node affinity, toleration, and resource requests.

**Imperative:**
```bash
kubectl label nodes node01 size=Large disktype=ssd
kubectl taint nodes node01 dedicated=large:NoSchedule
```

**Declarative:**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: large-ssd-app
spec:
  tolerations:
    - key: dedicated
      operator: Equal
      value: large
      effect: NoSchedule
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
          - matchExpressions:
              - key: size
                operator: In
                values:
                  - Large
              - key: disktype
                operator: In
                values:
                  - ssd
  containers:
    - name: app
      image: nginx
      resources:
        requests:
          cpu: "1"
          memory: 1Gi
        limits:
          cpu: "2"
          memory: 2Gi
```

---

**Q2.** A namespace `staging` has a ResourceQuota allowing only 5 Pods. Three BestEffort Pods exist. Deploy two Guaranteed Pods with `cpu: 500m` requests/limits. What happens if you try a third?

**Answer:** Quota allows 5 Pods total — two more Guaranteed Pods fit (5 total). A sixth Pod would be **rejected** by the ResourceQuota admission controller.

**Declarative:**
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: staging
---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: pod-quota
  namespace: staging
spec:
  hard:
    pods: "5"
---
apiVersion: v1
kind: Pod
metadata:
  name: guaranteed-1
  namespace: staging
spec:
  containers:
    - name: app
      image: nginx
      resources:
        requests:
          cpu: 500m
          memory: 256Mi
        limits:
          cpu: 500m
          memory: 256Mi
```

---

**Q3.** Deploy a log-collecting DaemonSet on all nodes including control plane, using tolerations for control-plane and `NoExecute` taints.

**Declarative:**
```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: log-agent
  namespace: kube-system
spec:
  selector:
    matchLabels:
      app: log-agent
  template:
    metadata:
      labels:
        app: log-agent
    spec:
      tolerations:
        - key: node-role.kubernetes.io/control-plane
          operator: Exists
          effect: NoSchedule
        - operator: Exists
          effect: NoExecute
      containers:
        - name: fluentd
          image: fluent/fluentd:v1.16
```

**Imperative:**
```bash
kubectl apply -f log-agent-ds.yaml
kubectl get pods -n kube-system -l app=log-agent -o wide
```

---

**Q4.** Pod `orphan` is Pending with no events about scheduling. It was created without `nodeName`. Bind it to `node02`, verify placement, and confirm it is not managed by a Deployment.

**Imperative:**
```bash
kubectl describe pod orphan
kubectl apply -f binding.yaml   # Binding to node02
kubectl get pod orphan -o wide
kubectl get pod orphan -o jsonpath='{.metadata.ownerReferences}'
```

---

**Q5.** Create high-priority Pod `critical` and low-priority Pod `batch` on a full node. Explain preemption behavior.

**Answer:** If the node lacks resources, `critical` (high PriorityClass) with `PreemptLowerPriority` can **evict** `batch` (lower priority) to free resources. `preemptionPolicy: Never` on the PriorityClass prevents preemption.

**Declarative:**
```yaml
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: high-priority
value: 1000000
preemptionPolicy: PreemptLowerPriority
---
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: low-priority
value: 100
---
apiVersion: v1
kind: Pod
metadata:
  name: critical
spec:
  priorityClassName: high-priority
  containers:
    - name: app
      image: nginx
      resources:
        requests:
          cpu: "2"
          memory: 2Gi
---
apiVersion: v1
kind: Pod
metadata:
  name: batch
spec:
  priorityClassName: low-priority
  containers:
    - name: app
      image: nginx
      resources:
        requests:
          cpu: "2"
          memory: 2Gi
```

---

**Q6.** Cordon and drain `worker-2`, verify Pods rescheduled with anti-affinity spreading `app=web` across hosts, then uncordon.

**Imperative:**
```bash
kubectl cordon worker-2
kubectl drain worker-2 --ignore-daemonsets --delete-emptydir-data
kubectl get pods -l app=web -o wide
kubectl uncordon worker-2
```

**Declarative (anti-affinity Deployment):**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            - labelSelector:
                matchExpressions:
                  - key: app
                    operator: In
                    values:
                      - web
              topologyKey: kubernetes.io/hostname
      containers:
        - name: nginx
          image: nginx
```
