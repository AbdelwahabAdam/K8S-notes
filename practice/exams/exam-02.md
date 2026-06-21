# Exam 02

**Namespace:** `exam-2`

---

## Q1 — Pod creation

**Task:** Create a **multi-container** Pod named `sidecar-pod` in `exam-2`:
- Container `app`: image `nginx`
- Container `logger`: image `busybox`, command `sleep 3600`

Verify both containers are Ready (2/2).

### Answer

```bash
kubectl create namespace exam-2

cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: sidecar-pod
  namespace: exam-2
spec:
  containers:
    - name: app
      image: nginx
    - name: logger
      image: busybox
      command: ["sleep", "3600"]
EOF

kubectl get pod sidecar-pod -n exam-2
```

**Expected output:**

```
NAME          READY   STATUS    RESTARTS   AGE
sidecar-pod   2/2     Running   0          20s
```

---

## Q2 — ReplicaSet creation

**Task:** Create ReplicaSet `cache-rs` in `exam-2` with **2 replicas**, label `tier=cache`, image `redis:7-alpine`. Scale it to **5** replicas using a command.

### Answer

```bash
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: cache-rs
  namespace: exam-2
spec:
  replicas: 2
  selector:
    matchLabels:
      tier: cache
  template:
    metadata:
      labels:
        tier: cache
    spec:
      containers:
        - name: redis
          image: redis:7-alpine
EOF

kubectl scale rs cache-rs -n exam-2 --replicas=5
kubectl get rs cache-rs -n exam-2
```

**Expected output:**

```
NAME       DESIRED   CURRENT   READY   AGE
cache-rs   5         5         5       30s
```

---

## Q3 — Node behaviour

**Task:** Cordon **node03** (mark unschedulable). Create a new Pod and confirm it does **not** land on node03. Uncordon node03.

### Answer

```bash
kubectl cordon node03
kubectl run cordon-test -n exam-2 --image=nginx --restart=Never
kubectl get pod cordon-test -n exam-2 -o wide
kubectl uncordon node03
```

**Expected:** Pod on **node01** or **node02**, never node03 while cordoned.

```
NAME          NODE
cordon-test   node01   # or node02

node03   Ready,SchedulingDisabled   # while cordoned
node03   Ready                        # after uncordon
```

---

## Q4 — Scheduler

**Task:** Create 3 Pods (`spread-1`, `spread-2`, `spread-3`) with no scheduling constraints. Observe how the scheduler distributes them across node01–node03.

### Answer

```bash
for i in 1 2 3; do
  kubectl run spread-$i -n exam-2 --image=nginx --restart=Never
done
kubectl get pods -n exam-2 -o wide | grep spread
```

**Expected output (ideal spread):**

```
spread-1   node01
spread-2   node02
spread-3   node03
```

Scheduler scores nodes to spread Pods — exact placement may vary if nodes have different load.

---

## Q5 — Imperative vs Declarative

**Task:**
1. Create ReplicaSet `imp-rs` imperatively is not supported — instead create Deployment `imp-dep` with `kubectl create deployment` (2 replicas, nginx).
2. Export it to YAML.
3. Change replicas to 4 in the YAML and apply declaratively.

### Answer

```bash
kubectl create deployment imp-dep -n exam-2 --image=nginx --replicas=2
kubectl get deployment imp-dep -n exam-2 -o yaml > /tmp/imp-dep.yaml
# Edit spec.replicas to 4 in the file (remove status, resourceVersion, uid)
kubectl apply -f /tmp/imp-dep.yaml
kubectl get deployment imp-dep -n exam-2
```

**Expected output:**

```
NAME      READY   UP-TO-DATE   AVAILABLE   AGE
imp-dep   4/4     4            4           1m
```

Imperative = step-by-step commands. Declarative = desired state in YAML + `apply`.

---

## Q6 — Manual scheduling

**Task:** Create Pod `manual-node01` in `exam-2` without `nodeName` first — note its node. Delete it. Recreate using `nodeName: node01` and confirm placement.

### Answer

```bash
kubectl run manual-node01 -n exam-2 --image=nginx --restart=Never
kubectl get pod manual-node01 -n exam-2 -o wide
kubectl delete pod manual-node01 -n exam-2

cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: manual-node01
  namespace: exam-2
spec:
  nodeName: node01
  containers:
    - name: nginx
      image: nginx
EOF

kubectl get pod manual-node01 -n exam-2 -o wide
```

**Expected output:**

```
NAME            NODE
manual-node01   node01
```

---

## Q7 — Labels & selectors

**Task:**
1. Create Pods `red` and `blue` with labels `color=red` and `color=blue`.
2. Create a Service `color-svc` that selects only `color=red`.
3. Verify endpoints include only the red Pod.

### Answer

```bash
kubectl run red -n exam-2 --image=nginx --labels="color=red" --restart=Never
kubectl run blue -n exam-2 --image=nginx --labels="color=blue" --restart=Never

cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: color-svc
  namespace: exam-2
spec:
  selector:
    color: red
  ports:
    - port: 80
      targetPort: 80
EOF

kubectl get endpoints color-svc -n exam-2
```

**Expected output:**

```
NAME        ENDPOINTS          AGE
color-svc   10.244.x.x:80      5s
```

Only **one** endpoint IP (red Pod). Blue Pod excluded by selector.

---

## Q8 — Taints & tolerations

**Task:**
1. Taint **node01** with `storage=ssd:NoSchedule`.
2. Create Pod without toleration — verify Pending or scheduled elsewhere.
3. Add toleration and affinity to force it on node01.
4. Remove taint.

### Answer

```bash
kubectl taint nodes node01 storage=ssd:NoSchedule

kubectl run store-pod -n exam-2 --image=nginx --restart=Never
kubectl get pod store-pod -n exam-2 -o wide
```

**Expected:** NOT on node01.

```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: store-tol
  namespace: exam-2
spec:
  tolerations:
    - key: storage
      operator: Equal
      value: ssd
      effect: NoSchedule
  nodeName: node01
  containers:
    - name: nginx
      image: nginx
EOF

kubectl get pod store-tol -n exam-2 -o wide
kubectl taint nodes node01 storage=ssd:NoSchedule-
```

**Expected:**

```
NAME        NODE
store-tol   node01
```

---

## Q9 — Node selectors & node affinity

**Task:**
1. Label node02 `zone=east`, node03 `zone=west`.
2. Pod `east-pod`: nodeSelector `zone: east`.
3. Pod `west-or-east`: affinity `zone In [east, west]` with **preferred** weight on `west`.

### Answer

```bash
kubectl label nodes node02 zone=east --overwrite
kubectl label nodes node03 zone=west --overwrite

cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: east-pod
  namespace: exam-2
spec:
  nodeSelector:
    zone: east
  containers:
    - name: nginx
      image: nginx
EOF

cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: west-or-east
  namespace: exam-2
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
          - matchExpressions:
              - key: zone
                operator: In
                values: [east, west]
      preferredDuringSchedulingIgnoredDuringExecution:
        - weight: 100
          preference:
            matchExpressions:
              - key: zone
                operator: In
                values: [west]
  containers:
    - name: nginx
      image: nginx
EOF

kubectl get pods east-pod west-or-east -n exam-2 -o wide
```

**Expected:**

```
east-pod      node02
west-or-east  node03   # preferred, but node02 also valid
```

---

## Q10 — Resource requests, limits & quotas

**Task:**
1. Create LimitRange in `exam-2`: default request `cpu: 100m`, `memory: 128Mi`; max `cpu: 500m`, `memory: 512Mi`.
2. Create Pod `default-res` with **no** resources defined — verify defaults applied.
3. Try Pod `too-big` with limit `cpu: 2` — verify rejection.

### Answer

```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: LimitRange
metadata:
  name: exam2-lr
  namespace: exam-2
spec:
  limits:
    - type: Container
      default:
        cpu: 200m
        memory: 256Mi
      defaultRequest:
        cpu: 100m
        memory: 128Mi
      max:
        cpu: 500m
        memory: 512Mi
EOF

kubectl run default-res -n exam-2 --image=nginx --restart=Never
kubectl describe pod default-res -n exam-2 | grep -A4 Requests
```

**Expected:**

```
    Requests:
      cpu:     100m
      memory:  128Mi
```

```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: too-big
  namespace: exam-2
spec:
  containers:
    - name: nginx
      image: nginx
      resources:
        limits:
          cpu: "2"
EOF
kubectl describe pod too-big -n exam-2 | grep -i forbidden
```

**Expected:**

```
Error creating: maximum cpu usage per Container is 500m, but limit is 2
```

---

## Q11 — DaemonSets

**Task:** Create DaemonSet `node-exporter` in `exam-2` that runs only on nodes labeled `zone=east` or `zone=west` (node02 and node03). Image: `busybox`, `sleep 3600`.

### Answer

```bash
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: zone-agent
  namespace: exam-2
spec:
  selector:
    matchLabels:
      app: zone-agent
  template:
    metadata:
      labels:
        app: zone-agent
    spec:
      nodeSelector:
        zone: east
      containers:
        - name: agent
          image: busybox
          command: ["sleep", "3600"]
EOF
```

Only node02 has `zone=east` — adjust or add second DaemonSet for west, OR use affinity In [east, west]:

```bash
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: zone-agent
  namespace: exam-2
spec:
  selector:
    matchLabels:
      app: zone-agent
  template:
    metadata:
      labels:
        app: zone-agent
    spec:
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
              - matchExpressions:
                  - key: zone
                    operator: In
                    values: [east, west]
      containers:
        - name: agent
          image: busybox
          command: ["sleep", "3600"]
EOF

kubectl get pods -n exam-2 -l app=zone-agent -o wide
```

**Expected:** 2 Pods on **node02** and **node03**.

---

## Q12 — Static Pods

**Task:** Explain the difference between Pod `kube-apiserver-master` and a normal Pod created with `kubectl run`. Verify kube-apiserver is not owned by a ReplicaSet.

### Answer

```bash
kubectl get pod kube-apiserver-master -n kube-system -o yaml | grep -E "ownerReferences|nodeName"
kubectl get rs -n kube-system | grep apiserver
```

**Expected:**

```
nodeName: master
# no ownerReferences (or empty)
# no ReplicaSet named kube-apiserver
```

| Normal Pod | Static Pod |
|------------|------------|
| Created via apiserver/kubectl | Created by kubelet from manifest file |
| Managed by controllers | Managed only by kubelet on that node |
| Name you choose | Mirror name: `<name>-<nodeName>` |

---

## Cleanup

```bash
kubectl delete namespace exam-2
kubectl label nodes node02 zone-
kubectl label nodes node03 zone-
kubectl taint nodes node01 storage=ssd:NoSchedule- 2>/dev/null
```
