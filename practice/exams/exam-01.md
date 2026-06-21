# Exam 01

**Namespace:** `exam-1`  
Create the namespace before starting.

---

## Q1 — Pod creation

**Task:** Create a Pod named `web-pod` in namespace `exam-1`. Use image `nginx:1.25`. Add labels `app=web` and `tier=frontend`. Verify it is Running.

### Answer

```bash
kubectl create namespace exam-1

cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: web-pod
  namespace: exam-1
  labels:
    app: web
    tier: frontend
spec:
  containers:
    - name: nginx
      image: nginx:1.25
EOF

kubectl get pod web-pod -n exam-1
```

**Expected output:**

```
NAME      READY   STATUS    RESTARTS   AGE
web-pod   1/1     Running   0          15s
```

---

## Q2 — ReplicaSet creation

**Task:** Create a ReplicaSet named `web-rs` in `exam-1` with **3 replicas**. Pods must have label `app=web-rs`. Use image `nginx`. Confirm 3 Pods are Running.

### Answer

```bash
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: web-rs
  namespace: exam-1
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web-rs
  template:
    metadata:
      labels:
        app: web-rs
    spec:
      containers:
        - name: nginx
          image: nginx
EOF

kubectl get rs web-rs -n exam-1
kubectl get pods -n exam-1 -l app=web-rs
```

**Expected output:**

```
NAME     DESIRED   CURRENT   READY   AGE
web-rs   3         3         3       20s

NAME           READY   STATUS    RESTARTS   AGE
web-rs-xxxxx   1/1     Running   0          20s
web-rs-yyyyy   1/1     Running   0          20s
web-rs-zzzzz   1/1     Running   0          20s
```

---

## Q3 — Node behaviour

**Task:** List all nodes. Identify which node is the control plane. Check why application Pods do **not** schedule on `master`.

### Answer

```bash
kubectl get nodes
kubectl describe node master | grep -i taint
```

**Expected output:**

```
NAME     STATUS   ROLES           AGE   VERSION
master   Ready    control-plane   ...   v1.xx.x
node01   Ready    <none>          ...   v1.xx.x
node02   Ready    <none>          ...   v1.xx.x
node03   Ready    <none>          ...   v1.xx.x

Taints: node-role.kubernetes.io/control-plane:NoSchedule
```

**Explanation:** Master has `NoSchedule` taint — normal Pods are rejected unless they have a matching toleration.

---

## Q4 — Scheduler

**Task:** Create a Pod named `sched-test` in `exam-1` (image `nginx`, no `nodeName`). Record which node the scheduler assigns. Check the Scheduled event.

### Answer

```bash
kubectl run sched-test -n exam-1 --image=nginx --restart=Never
kubectl get pod sched-test -n exam-1 -o wide
kubectl describe pod sched-test -n exam-1 | grep -A3 Events
```

**Expected output:**

```
NAME        READY   STATUS    RESTARTS   AGE   IP            NODE
sched-test  1/1     Running   0          10s   10.244.x.x    node0X

Events:
  Type    Reason     Age   Message
  Normal  Scheduled  10s   Successfully assigned exam-1/sched-test to node0X
```

`node0X` = one of **node01**, **node02**, or **node03** (scheduler filter → score → bind).

---

## Q5 — Imperative vs Declarative

**Task:**
1. Create Pod `imp-pod` in `exam-1` using an **imperative** command (image `busybox`, command `sleep 3600`).
2. Try creating the same Pod again with `kubectl create -f` — observe the error.
3. Update the Pod using `kubectl apply -f` with the same name.

### Answer

```bash
# Imperative
kubectl run imp-pod -n exam-1 --image=busybox --restart=Never -- sleep 3600

# Declarative create (fails — already exists)
cat <<EOF > /tmp/imp-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: imp-pod
  namespace: exam-1
spec:
  containers:
    - name: imp-pod
      image: busybox
      command: ["sleep", "3600"]
EOF
kubectl create -f /tmp/imp-pod.yaml
```

**Expected output (create fails):**

```
Error from server (AlreadyExists): pods "imp-pod" already exists
```

```bash
# apply works (idempotent)
kubectl apply -f /tmp/imp-pod.yaml
```

**Expected output:**

```
pod/imp-pod unchanged
```

| Method | Idempotent? |
|--------|-------------|
| `kubectl run` / `create -f` | No |
| `kubectl apply -f` | Yes |

---

## Q6 — Manual scheduling

**Task:** Create Pod `pinned-node02` in `exam-1` and force it onto **node02** using `nodeName`. Verify it never lands on another node.

### Answer

```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: pinned-node02
  namespace: exam-1
spec:
  nodeName: node02
  containers:
    - name: nginx
      image: nginx
EOF

kubectl get pod pinned-node02 -n exam-1 -o wide
```

**Expected output:**

```
NAME            READY   STATUS    RESTARTS   AGE   NODE
pinned-node02   1/1     Running   0          10s   node02
```

Scheduler is **bypassed** — `nodeName` only works at creation time.

---

## Q7 — Labels & selectors

**Task:**
1. Label Pod `web-pod` with `env=dev`.
2. List only Pods in `exam-1` that have **both** `env=dev` and `tier=frontend`.

### Answer

```bash
kubectl label pod web-pod -n exam-1 env=dev
kubectl get pods -n exam-1 -l env=dev,tier=frontend
```

**Expected output:**

```
NAME      READY   STATUS    RESTARTS   AGE
web-pod   1/1     Running   0          5m
```

Pods without both labels are excluded.

---

## Q8 — Taints & tolerations

**Task:**
1. Add taint `workload=special:NoSchedule` to **node02**.
2. Create Pod `no-tol` (image `nginx`) — confirm it avoids node02.
3. Create Pod `with-tol` with a toleration for that taint — confirm it **can** run on node02.
4. Remove the taint when done.

### Answer

```bash
kubectl taint nodes node02 workload=special:NoSchedule

kubectl run no-tol -n exam-1 --image=nginx --restart=Never
kubectl get pod no-tol -n exam-1 -o wide
```

**Expected:** `no-tol` on **node01** or **node03**, NOT node02.

```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: with-tol
  namespace: exam-1
spec:
  tolerations:
    - key: workload
      operator: Equal
      value: special
      effect: NoSchedule
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
          - matchExpressions:
              - key: kubernetes.io/hostname
                operator: In
                values: [node02]
  containers:
    - name: nginx
      image: nginx
EOF

kubectl get pod with-tol -n exam-1 -o wide
```

**Expected output:**

```
NAME       NODE
with-tol   node02
```

```bash
kubectl taint nodes node02 workload=special:NoSchedule-
```

---

## Q9 — Node selectors & node affinity

**Task:**
1. Label **node01** with `size=large`.
2. Create Pod `large-only` with `nodeSelector: size: large`.
3. Create Pod `not-node01` with node affinity: hostname **NotIn** `node01`.

### Answer

```bash
kubectl label nodes node01 size=large --overwrite

cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: large-only
  namespace: exam-1
spec:
  nodeSelector:
    size: large
  containers:
    - name: nginx
      image: nginx
EOF

kubectl get pod large-only -n exam-1 -o wide
```

**Expected:**

```
NAME         NODE
large-only   node01
```

```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: not-node01
  namespace: exam-1
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
          - matchExpressions:
              - key: kubernetes.io/hostname
                operator: NotIn
                values: [node01]
  containers:
    - name: nginx
      image: nginx
EOF

kubectl get pod not-node01 -n exam-1 -o wide
```



**Expected:** `not-node01` on **node02** or **node03**.

---

## Q10 — Resource requests, limits & quotas

**Task:**
1. Create ResourceQuota in `exam-1`: max **10 pods**, max **2** CPU requests.
2. Create Pod `res-pod` with requests `cpu: 200m`, `memory: 256Mi` and limits `cpu: 400m`, `memory: 512Mi`.
3. Show quota usage.

### Answer

```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ResourceQuota
metadata:
  name: exam1-quota
  namespace: exam-1
spec:
  hard:
    pods: "10"
    requests.cpu: "2"
    requests.memory: 2Gi
EOF

cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: res-pod
  namespace: exam-1
spec:
  containers:
    - name: nginx
      image: nginx
      resources:
        requests:
          cpu: 200m
          memory: 256Mi
        limits:
          cpu: 400m
          memory: 512Mi
EOF

kubectl describe quota exam1-quota -n exam-1
kubectl describe pod res-pod -n exam-1 | grep -A6 "Limits:"
```

**Expected output:**

```
Resource         Used   Hard
--------         ----   ----
pods             X      10
requests.cpu     ...    2
```

```
    Limits:
      cpu:     400m
      memory:  512Mi
    Requests:
      cpu:     200m
      memory:  256Mi
QoS Class:  Burstable
```

---

## Q11 — DaemonSets

**Task:** Create DaemonSet `log-agent` in `exam-1` (image `busybox`, command `sleep 3600`, label `app=log-agent`). Verify one Pod runs on each **worker** (node01–node03).

### Answer

```bash
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: log-agent
  namespace: exam-1
spec:
  selector:
    matchLabels:
      app: log-agent
  template:
    metadata:
      labels:
        app: log-agent
    spec:
      containers:
        - name: agent
          image: busybox
          command: ["sleep", "3600"]
EOF

kubectl get ds log-agent -n exam-1
kubectl get pods -n exam-1 -l app=log-agent -o custom-columns=NAME:.metadata.name,NODE:.spec.nodeName
```

**Expected output:**

```
NAME         DESIRED   CURRENT   READY   UP-TO-DATE   AVAILABLE
log-agent    3         3         3       3            3

NAME              NODE
log-agent-xxxxx   node01
log-agent-yyyyy   node02
log-agent-zzzzz   node03
```

---

## Q12 — Static Pods

**Task:** On **master**, find where static Pod manifests live. List the 4 control-plane static Pods visible in `kube-system`.

### Answer

```bash
ssh master "sudo ls /etc/kubernetes/manifests/"
kubectl get pods -n kube-system -o wide | grep master
```

**Expected output:**

```
etcd.yaml
kube-apiserver.yaml
kube-controller-manager.yaml
kube-scheduler.yaml

etcd-master
kube-apiserver-master
kube-controller-manager-master
kube-scheduler-master
```

Static Pods are managed by **kubelet** on master — not by Deployment or scheduler.

---

## Cleanup

```bash
kubectl delete namespace exam-1
kubectl label nodes node01 size-
```
