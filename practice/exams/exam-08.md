# Exam 08

**Namespace:** `exam-8`

---

## Q1 — Pod creation

**Task:** Create Pod `mem-test` with explicit resources: requests `memory: 512Mi`, limits `memory: 1Gi`, image nginx.

### Answer

```bash
kubectl create namespace exam-8

cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: mem-test
  namespace: exam-8
spec:
  containers:
    - name: nginx
      image: nginx
      resources:
        requests:
          memory: 512Mi
        limits:
          memory: 1Gi
EOF

kubectl describe pod mem-test -n exam-8 | grep -A6 "Limits:"
```

**Expected:**

```
    Limits:
      memory:  1Gi
    Requests:
      memory:  512Mi
QoS Class:  Burstable
```

---

## Q2 — ReplicaSet creation

**Task:** ReplicaSet `mem-rs`, 2 replicas, each container requests `256Mi` memory, image nginx.

### Answer

```bash
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: mem-rs
  namespace: exam-8
spec:
  replicas: 2
  selector:
    matchLabels:
      app: mem-rs
  template:
    metadata:
      labels:
        app: mem-rs
    spec:
      containers:
        - name: nginx
          image: nginx
          resources:
            requests:
              memory: 256Mi
EOF

kubectl get rs mem-rs -n exam-8
kubectl describe rs mem-rs -n exam-8 | grep -A2 "Pods Status"
```

**Expected:**

```
DESIRED 2  CURRENT 2  READY 2
```

---

## Q3 — Node behaviour

**Task:** Check which node has the **most** Pods running (all namespaces). Identify resource pressure.

### Answer

```bash
kubectl get pods -A -o wide --field-selector spec.nodeName=node01 --no-headers | wc -l
kubectl get pods -A -o wide --field-selector spec.nodeName=node02 --no-headers | wc -l
kubectl get pods -A -o wide --field-selector spec.nodeName=node03 --no-headers | wc -l
kubectl describe nodes | grep -A3 "Allocated resources"
```

**Expected:** Counts per node + allocation percentages for CPU/memory.

---

## Q4 — Scheduler

**Task:** Create Pod requesting `memory: 4Gi`. If Pending, check events. Reduce to `128Mi` and confirm scheduling.

### Answer

```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: big-mem
  namespace: exam-8
spec:
  containers:
    - name: nginx
      image: nginx
      resources:
        requests:
          memory: 4Gi
EOF

kubectl describe pod big-mem -n exam-8 | grep FailedScheduling
```

**Expected (if nodes < 4Gi allocatable):**

```
0/3 nodes are available: 3 Insufficient memory.
```

```bash
kubectl delete pod big-mem -n exam-8
kubectl run small-mem -n exam-8 --image=nginx --restart=Never \
  --overrides='{"spec":{"containers":[{"name":"small-mem","image":"nginx","resources":{"requests":{"memory":"128Mi"}}}]}}'
kubectl get pod small-mem -n exam-8
```

**Expected:** Running.

---

## Q5 — Imperative vs Declarative

**Task:** Create 2 replicas imperatively with `kubectl create deployment`. Scale to 4 imperatively. Then scale to 2 declaratively via YAML apply.

### Answer

```bash
kubectl create deployment imp-scale -n exam-8 --image=nginx --replicas=2
kubectl scale deployment imp-scale -n exam-8 --replicas=4
kubectl get deployment imp-scale -n exam-8

kubectl get deployment imp-scale -n exam-8 -o yaml > /tmp/imp-scale.yaml
# Set spec.replicas: 2, clean status/metadata noise
kubectl apply -f /tmp/imp-scale.yaml
kubectl get deployment imp-scale -n exam-8
```

**Expected:**

```
4/4  →  then  2/2
```

---

## Q6 — Manual scheduling

**Task:** Pin Pod `mem-test` to the node with **least** Pods (your choice from Q3) using `nodeName`.

### Answer

```bash
# Example if node03 has least Pods:
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: light-node
  namespace: exam-8
spec:
  nodeName: node03
  containers:
    - name: nginx
      image: nginx
EOF

kubectl get pod light-node -n exam-8 -o wide
```

**Expected:**

```
light-node   node03   Running
```

(Your node choice may differ based on Q3 counts.)

---

## Q7 — Labels & selectors

**Task:** Label all Pods in `exam-8` with `exam=8` using single command on namespace resources.

### Answer

```bash
kubectl label pods -n exam-8 --all exam=8
kubectl get pods -n exam-8 -l exam=8 --no-headers | wc -l
```

**Expected:** Count equals total Pods in exam-8.

---

## Q8 — Taints & tolerations

**Task:** Create toleration using `operator: Exists` (no value) for key `special`. Taint node02 `special=:NoSchedule` (empty value with Exists taint).

### Answer

```bash
kubectl taint nodes node02 special:NoSchedule
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: exists-tol
  namespace: exam-8
spec:
  tolerations:
    - key: special
      operator: Exists
      effect: NoSchedule
  nodeName: node02
  containers:
    - name: nginx
      image: nginx
EOF

kubectl get pod exists-tol -n exam-8
kubectl taint nodes node02 special:NoSchedule-
```

**Expected:** `exists-tol` Running on node02.

---

## Q9 — Node selectors & node affinity

**Task:** Use `Gt` operator: label node01 `cores=2`, node02 `cores=4`. Schedule Pod with affinity `cores Gt 3`.

### Answer

```bash
kubectl label nodes node01 cores=2 --overwrite
kubectl label nodes node02 cores=4 --overwrite

cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: gt-cores
  namespace: exam-8
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
          - matchExpressions:
              - key: cores
                operator: Gt
                values: ["3"]
  containers:
    - name: nginx
      image: nginx
EOF

kubectl get pod gt-cores -n exam-8 -o wide
```

**Expected:** NODE = **node02** (cores=4 > 3).

---

## Q10 — Resource requests, limits & quotas

**Task:** Full setup:
- ResourceQuota: `requests.memory: 1Gi`, `limits.memory: 2Gi`
- LimitRange: max memory per container `512Mi`
- Create Pod within both limits

### Answer

```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ResourceQuota
metadata:
  name: mem-quota
  namespace: exam-8
spec:
  hard:
    requests.memory: 1Gi
    limits.memory: 2Gi
---
apiVersion: v1
kind: LimitRange
metadata:
  name: mem-lr
  namespace: exam-8
spec:
  limits:
    - type: Container
      max:
        memory: 512Mi
EOF

cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: valid-mem
  namespace: exam-8
spec:
  containers:
    - name: nginx
      image: nginx
      resources:
        requests:
          memory: 256Mi
        limits:
          memory: 512Mi
EOF

kubectl get pod valid-mem -n exam-8
kubectl describe quota mem-quota -n exam-8
```

**Expected:** Pod Running. Quota shows `requests.memory: 256Mi/1Gi`.

---

## Q11 — DaemonSets

**Task:** DaemonSet with resource requests `cpu: 50m` per Pod. Verify 3 Pods on workers and check total CPU requested.

### Answer

```bash
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: cpu-ds
  namespace: exam-8
spec:
  selector:
    matchLabels:
      app: cpu-ds
  template:
    metadata:
      labels:
        app: cpu-ds
    spec:
      containers:
        - name: nginx
          image: nginx
          resources:
            requests:
              cpu: 50m
EOF

kubectl get ds cpu-ds -n exam-8
kubectl get pods -n exam-8 -l app=cpu-ds --no-headers | wc -l
```

**Expected:**

```
DESIRED 3
3 Pods — total 150m CPU requested by DaemonSet
```

---

## Q12 — Static Pods

**Task:** Verify etcd static Pod uses host network or not. Check if it's managed by kubelet on master only.

### Answer

```bash
kubectl get pod etcd-master -n kube-system -o wide
kubectl get pod etcd-master -n kube-system -o jsonpath='{.spec.nodeName}{"\n"}{.metadata.ownerReferences}'; echo
```

**Expected:**

```
master
# no ownerReferences

NODE: master only
```

etcd runs exclusively on control plane node as static Pod.

---

## Cleanup

```bash
kubectl delete namespace exam-8
kubectl label nodes node01 cores-
kubectl label nodes node02 cores-
```
