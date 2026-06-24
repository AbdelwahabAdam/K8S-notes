# CKA Practice — Logging and Monitoring

> Based on [enhanced_readme.md](./enhanced_readme.md)

---

## 1. Monitoring Overview

**Q1.** Does Kubernetes ship a full monitoring solution out of the box? What should you monitor at each layer?

**Answer:** **No** — Kubernetes does not include a complete monitoring stack. You add observability tools.

| Layer | What to monitor |
|-------|-----------------|
| Cluster components | apiserver, etcd, scheduler, controller-manager, kubelet, kube-proxy |
| Nodes | CPU, memory, disk, network |
| Applications | Pod logs, resource usage, health probes |
| Control plane | Static Pod logs in `kube-system` |

---

**Q2.** Draw the data flow from application containers to an admin viewing metrics.

**Answer:** Application Pods → stdout/stderr → kubelet log files → apiserver → `kubectl logs`. Container metrics: kubelet/cAdvisor → Metrics Server → `kubectl top`. External stacks (Prometheus, ELK) scrape or collect separately.

---

## 2. Metrics Server

**Q1.** Deploy Metrics Server and verify node and Pod CPU/memory usage.

**Imperative:**
```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
kubectl get pods -n kube-system | grep metrics-server
kubectl top nodes
kubectl top pods
kubectl top pods -n kube-system
kubectl top pod <pod-name> --containers
```

---

**Q2.** `kubectl top pods` returns "Metrics API not available." What are the most likely causes?

**Answer:**
1. **Metrics Server not deployed** or Pod not running
2. Metrics Server cannot reach kubelets (TLS, network, firewall)
3. RBAC missing for `metrics.k8s.io` API
4. kubelet not exposing stats to Metrics Server

```bash
kubectl get apiservice v1beta1.metrics.k8s.io
kubectl logs -n kube-system -l k8s-app=metrics-server
kubectl get pods -n kube-system | grep metrics-server
```

---

## 3. Heapster vs Metrics Server

**Q1.** Which metrics aggregator is current and which is deprecated?

**Answer:**
| Feature | Heapster | Metrics Server |
|---------|----------|----------------|
| Status | **Deprecated** | **Current standard** |
| Storage | Forwarded to backends | **In-memory only** (no history) |
| HPA | Old versions | Required for resource-based HPA |

---

**Q2.** Can Metrics Server store historical metrics for Grafana dashboards?

**Answer:** **No.** Metrics Server holds metrics **in-memory** only. For historical data and dashboards, use **Prometheus** (or another time-series backend) scraping kubelet/cAdvisor or a metrics exporter.

---

## 4. cAdvisor & kubelet Metrics

**Q1.** What is cAdvisor and where does it run?

**Answer:** **cAdvisor (Container Advisor)** is embedded in the **kubelet** on every node. It collects per-container CPU, memory, filesystem, and network metrics.

---

**Q2.** How do you access cAdvisor metrics on a node for debugging?

**Imperative:**
```bash
# On the node:
curl -k https://localhost:10250/metrics/cadvisor
crictl stats
```

**Answer:** kubelet exposes metrics on port **10250** (HTTPS). Metrics Server reads resource usage summaries from kubelets. For deep monitoring, **Prometheus** scrapes `/metrics/cadvisor`.

---

## 5. Viewing Metrics

**Q1.** Show CPU and memory usage for all Pods in namespace `prod` and for a specific container in a multi-container Pod.

**Imperative:**
```bash
kubectl top pods -n prod
kubectl top pod multi-app -n prod --containers
kubectl top node
kubectl top nodes
```

---

**Q2.** What prerequisite must be met before `kubectl top` works?

**Answer:** **Metrics Server** must be running and the `metrics.k8s.io` API must be available. RBAC must allow the user to access metrics resources.

```bash
kubectl get apiservice | grep metrics
kubectl api-resources | grep metrics
```

---

## 6. Application Logs

**Q1.** View live logs from container `nginx` in Pod `multi-app`, and retrieve logs from a crashed container.

**Imperative:**
```bash
kubectl logs multi-app -c nginx
kubectl logs -f multi-app -c nginx
kubectl logs multi-app --previous
kubectl logs -l app=nginx
kubectl logs multi-app --since=1h --tail=100
```

---

**Q2.** Create a multi-container Pod and fetch logs from each container separately.

**Declarative:**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: multi-app
spec:
  containers:
    - name: nginx
      image: nginx
    - name: sidecar
      image: busybox
      command: ["sh", "-c", "while true; do echo sidecar; sleep 5; done"]
```

**Imperative:**
```bash
kubectl apply -f multi-app.yaml
kubectl logs multi-app -c nginx
kubectl logs -f multi-app -c sidecar
```

**Answer:** Containers write to **stdout/stderr**. kubelet collects logs; kubectl reads them via the apiserver.

---

## 7. Cluster Component Logs

**Q1.** Retrieve logs for kube-apiserver, etcd, and kube-scheduler on a kubeadm cluster.

**Imperative:**
```bash
kubectl get pods -n kube-system
kubectl logs -n kube-system kube-apiserver-<control-plane-node>
kubectl logs -n kube-system etcd-<node>
kubectl logs -n kube-system kube-scheduler-<node>
kubectl logs -n kube-system kube-controller-manager-<node>
```

---

**Q2.** On a worker node, how do you view kubelet logs and container logs without kubectl?

**Imperative:**
```bash
journalctl -u kubelet
crictl ps -a
crictl logs <container-id>
```

**Answer:** Control plane components run as **static Pods** in `kube-system`. kubelet logs via **systemd** (`journalctl`). Pod log files on disk: `/var/log/pods/kube-system_<component>-*`.

---

## 8. Monitoring Solutions

**Q1.** Match each solution to its primary use case.

**Answer:**
| Solution | Type | Notes |
|----------|------|-------|
| Metrics Server | Built-in metrics API | `kubectl top`, HPA CPU |
| Prometheus | Time-series metrics | De facto K8s monitoring |
| Elastic Stack (EFK) | Logs + metrics | Fluentd + ES + Kibana |
| Grafana | Dashboards | Often paired with Prometheus |
| Datadog / Dynatrace | SaaS APM | Agent as DaemonSet |

---

**Q2.** Add liveness and readiness probes to a Pod running on port 8080.

**Declarative:**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: probed-app
spec:
  containers:
    - name: app
      image: myapp:1.0
      ports:
        - containerPort: 8080
      livenessProbe:
        httpGet:
          path: /healthz
          port: 8080
        initialDelaySeconds: 3
        periodSeconds: 10
      readinessProbe:
        httpGet:
          path: /ready
          port: 8080
        periodSeconds: 5
```

**Answer:** **Liveness** — restart if unhealthy. **Readiness** — remove from Service endpoints if not ready.

---

## 9. Cheat Sheet & Resources

**Q1.** Provide a one-liner workflow to deploy Metrics Server, confirm it works, and tail application logs.

**Imperative:**
```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
kubectl get pods -n kube-system | grep metrics-server
kubectl top nodes && kubectl top pods -A
kubectl logs -f <pod-name> -c <container>
kubectl logs <pod-name> --previous
```

---

**Q2.** Where are official docs for the resource metrics pipeline and logging architecture?

**Answer:**
- [Resource metrics pipeline](https://kubernetes.io/docs/tasks/debug/debug-cluster/resource-metrics-pipeline/)
- [Logging architecture](https://kubernetes.io/docs/concepts/cluster-administration/logging/)
- [Metrics Server (GitHub)](https://github.com/kubernetes-sigs/metrics-server)
- [Troubleshoot clusters](https://kubernetes.io/docs/tasks/debug/debug-cluster/)

---

## Mixed Topic Questions

**Q1.** Metrics Server is missing. Deploy it, verify the API, check node/Pod usage, and diagnose a Pod using excessive CPU.

**Imperative:**
```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
kubectl wait -n kube-system --for=condition=Ready pod -l k8s-app=metrics-server --timeout=120s
kubectl get apiservice v1beta1.metrics.k8s.io
kubectl top nodes
kubectl top pods -A --sort-by=cpu
kubectl top pod <heavy-pod> --containers
kubectl describe pod <heavy-pod>
```

---

**Q2.** Pod `web-7x9k2` in namespace `prod` is CrashLoopBackOff. Investigate using logs from the current and previous container instance.

**Imperative:**
```bash
kubectl get pod web-7x9k2 -n prod
kubectl describe pod web-7x9k2 -n prod
kubectl logs web-7x9k2 -n prod
kubectl logs web-7x9k2 -n prod --previous
kubectl logs web-7x9k2 -n prod -c <container-name>
```

**Answer:** `--previous` retrieves logs from the **last terminated** container instance — essential for CrashLoopBackOff diagnosis.

---

**Q3.** Set up node-level log collection with a Fluentd DaemonSet and verify application logs reach stdout.

**Declarative:**
```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluentd
  namespace: kube-system
spec:
  selector:
    matchLabels:
      app: fluentd
  template:
    metadata:
      labels:
        app: fluentd
    spec:
      tolerations:
        - key: node-role.kubernetes.io/control-plane
          operator: Exists
          effect: NoSchedule
      containers:
        - name: fluentd
          image: fluent/fluentd-kubernetes-daemonset:v1.16
          volumeMounts:
            - name: varlog
              mountPath: /var/log
      volumes:
        - name: varlog
          hostPath:
            path: /var/log
```

**Imperative:**
```bash
kubectl apply -f fluentd-ds.yaml
kubectl get pods -n kube-system -l app=fluentd
kubectl logs -l app=myapp --tail=20
```

**Answer:** Pattern: **DaemonSet** on each node collects `/var/log` → forwards to Elasticsearch or cloud logging.

---

**Q4.** The API server is slow. Check control plane component logs and kubelet status on the master node.

**Imperative:**
```bash
kubectl get pods -n kube-system -o wide
kubectl logs -n kube-system kube-apiserver-<master-node> --tail=100
kubectl logs -n kube-system etcd-<master-node> --tail=50
# On the node:
journalctl -u kubelet --since "10 min ago"
crictl ps -a | grep kube-apiserver
crictl logs <apiserver-container-id>
```

---

**Q5.** Create a Pod with liveness probe failing on `/bad-path`. Observe restarts, fix the probe path, and confirm readiness.

**Declarative (broken):**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: probe-test
spec:
  containers:
    - name: nginx
      image: nginx
      ports:
        - containerPort: 80
      livenessProbe:
        httpGet:
          path: /bad-path
          port: 80
        initialDelaySeconds: 5
        periodSeconds: 5
```

**Declarative (fixed):**
```yaml
      livenessProbe:
        httpGet:
          path: /
          port: 80
        initialDelaySeconds: 5
        periodSeconds: 5
      readinessProbe:
        httpGet:
          path: /
          port: 80
        periodSeconds: 5
```

**Imperative:**
```bash
kubectl apply -f probe-test.yaml
kubectl describe pod probe-test   # RESTARTS increment
kubectl apply -f probe-test-fixed.yaml
kubectl get pod probe-test
```

---

**Q6.** Compare resource usage of all containers in namespace `kube-system`, then tail logs from metrics-server and a failing application Pod simultaneously.

**Imperative:**
```bash
kubectl top pods -n kube-system --containers
kubectl top pods -n kube-system --sort-by=memory
kubectl logs -n kube-system -l k8s-app=metrics-server -f &
kubectl logs -f <failing-pod> -n <namespace>
```

**Answer:** `kubectl top --containers` breaks down per-container usage in multi-container Pods. Combine with `kubectl logs -f` for live observability during incidents.
