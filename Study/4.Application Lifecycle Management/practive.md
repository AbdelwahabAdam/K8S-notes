# CKA Practice — Application Lifecycle Management
> Based on [enhanced_readme.md](./enhanced_readme.md)

---

## Topic Questions

### 1. Rolling Updates & Rollbacks

**Q1.** A Deployment `web-app` runs 3 replicas with image `nginx:1.7.1`. Update the image to `nginx:1.25` and verify the rollout completes without downtime. Then roll back to the previous revision.

**Answer**

*Imperative:*
```bash
kubectl set image deployment/web-app nginx=nginx:1.25
kubectl rollout status deployment/web-app
kubectl rollout history deployment/web-app
kubectl rollout undo deployment/web-app
```

*Declarative:*
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: web-app
  template:
    metadata:
      labels:
        app: web-app
    spec:
      containers:
        - name: nginx
          image: nginx:1.25
```
```bash
kubectl apply -f deployment.yaml
kubectl rollout status deployment/web-app
```

**Q2.** Change Deployment `api` strategy from default `RollingUpdate` to `Recreate`. What is the trade-off?

**Answer**

*Declarative:*
```yaml
spec:
  strategy:
    type: Recreate
```

All old Pods terminate before new ones start — **downtime occurs**, but avoids running two versions simultaneously (useful when the app cannot tolerate mixed versions).

---

### 2. Commands & Arguments (Docker vs K8s)

**Q1.** An image `ubuntu-sleeper` has `ENTRYPOINT ["sleep"]` and `CMD ["5"]`. Create a Pod that runs `sleep2.0 10` instead.

**Answer**

*Declarative:*
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: ubuntu-sleeper-pod
spec:
  containers:
    - name: ubuntu-sleeper
      image: ubuntu-sleeper
      command: ["sleep2.0"]   # overrides ENTRYPOINT
      args: ["10"]            # overrides CMD
```

*Imperative:*
```bash
kubectl run ubuntu-sleeper-pod --image=ubuntu-sleeper \
  --command -- sleep2.0 10
```

**Q2.** Map Docker concepts to Kubernetes Pod spec fields: `CMD`, `ENTRYPOINT`, and `docker run image arg`.

**Answer**

| Docker | Kubernetes |
|--------|------------|
| `ENTRYPOINT` | `command` |
| `CMD` | `args` |
| `docker run image arg` | `args` only (ENTRYPOINT from image kept) |

---

### 3. Environment Variables

**Q1.** Create a Pod `color-pod` with env vars `APP_COLOR=pink` and `HEADER_COLOR=green`.

**Answer**

*Declarative:*
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: color-pod
spec:
  containers:
    - name: app
      image: nginx
      env:
        - name: APP_COLOR
          value: pink
        - name: HEADER_COLOR
          value: green
```

*Imperative:*
```bash
kubectl run color-pod --image=nginx \
  --env=APP_COLOR=pink --env=HEADER_COLOR=green
```

**Q2.** Name the three ways to inject configuration into a Pod and when to use each.

**Answer**

| Method | Use case |
|--------|----------|
| Plain `env` | Simple static key-value pairs |
| ConfigMap | Non-sensitive configuration |
| Secret | Sensitive credentials |

---

### 4. ConfigMaps

**Q1.** Create ConfigMap `app-config` with `APP_COLOR=blue` and `APP_MODE=prod`. Mount it as env vars in Pod `myapp`.

**Answer**

*Imperative:*
```bash
kubectl create configmap app-config \
  --from-literal=APP_COLOR=blue \
  --from-literal=APP_MODE=prod
```

*Declarative (ConfigMap):*
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  APP_COLOR: blue
  APP_MODE: prod
```

*Declarative (Pod — single key):*
```yaml
env:
  - name: APP_COLOR
    valueFrom:
      configMapKeyRef:
        name: app-config
        key: APP_COLOR
```

*Declarative (Pod — all keys):*
```yaml
envFrom:
  - configMapRef:
      name: app-config
```

**Q2.** Mount ConfigMap `app-config` as files at `/etc/config` in Pod `myapp`.

**Answer**

*Declarative:*
```yaml
spec:
  volumes:
    - name: config-vol
      configMap:
        name: app-config
  containers:
    - name: app
      image: nginx
      volumeMounts:
        - name: config-vol
          mountPath: /etc/config
```

---

### 5. Secrets

**Q1.** Create Secret `db-secret` with `DB_USER=root` and `DB_PASSWORD=password`. Inject `DB_PASSWORD` as an env var in Pod `api`.

**Answer**

*Imperative:*
```bash
kubectl create secret generic db-secret \
  --from-literal=DB_USER=root \
  --from-literal=DB_PASSWORD=password
```

*Declarative:*
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-secret
type: Opaque
stringData:
  DB_USER: root
  DB_PASSWORD: password
---
apiVersion: v1
kind: Pod
metadata:
  name: api
spec:
  containers:
    - name: api
      image: my-api
      env:
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: DB_PASSWORD
```

**Q2.** Decode the value of key `DB_PASSWORD` from Secret `db-secret`.

**Answer**

```bash
kubectl get secret db-secret -o jsonpath='{.data.DB_PASSWORD}' | base64 --decode
echo
```

---

### 6. Encrypting Secrets at Rest

**Q1.** Secrets are stored base64-encoded in etcd by default. What must you configure on kube-apiserver to encrypt them at rest?

**Answer**

1. Create `/etc/kubernetes/enc/enc.yaml`:
```yaml
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
  - resources:
      - secrets
    providers:
      - aescbc:
          keys:
            - name: key1
              secret: <32-byte-base64-key>
      - identity: {}
```

2. Edit static Pod `/etc/kubernetes/manifests/kube-apiserver.yaml`:
```yaml
command:
  - --encryption-provider-config=/etc/kubernetes/enc/enc.yaml
volumeMounts:
  - name: enc
    mountPath: /etc/kubernetes/enc
    readOnly: true
volumes:
  - name: enc
    hostPath:
      path: /etc/kubernetes/enc
      type: DirectoryOrCreate
```

3. Re-encrypt existing Secrets:
```bash
kubectl get secrets --all-namespaces -o json | kubectl replace -f -
```

**Q2.** After enabling encryption at rest, how do you verify Secrets are no longer stored in plaintext in etcd?

**Answer**

Use `etcdctl get` against a Secret key — the value should be encrypted (not readable base64 plaintext). Compare before/after enabling the encryption provider.

---

### 7. Multi-Container Pods

**Q1.** Create Pod `simple-webapp` with container `web-app` (nginx on port 8080) and `log-collector` (busybox tailing `/var/log/app.log`) sharing an `emptyDir` volume.

**Answer**

*Declarative:*
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: simple-webapp
spec:
  containers:
    - name: web-app
      image: nginx
      ports:
        - containerPort: 8080
      volumeMounts:
        - name: logs
          mountPath: /var/log
    - name: log-collector
      image: busybox
      command: ["sh", "-c", "tail -f /var/log/app.log"]
      volumeMounts:
        - name: logs
          mountPath: /var/log
  volumes:
    - name: logs
      emptyDir: {}
```

**Q2.** If one container in a multi-container Pod exits and `restartPolicy` is `Always`, what happens?

**Answer**

The **entire Pod restarts** — Kubernetes does not restart individual containers independently when `restartPolicy` is Always or OnFailure.

---

### 8. Init & Sidecar Containers

**Q1.** Create Pod `myapp-pod` with two init containers that wait for DNS resolution of `myservice` and `mydb` before starting the main `busybox` container.

**Answer**

*Declarative:*
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: myapp-pod
spec:
  initContainers:
    - name: init-myservice
      image: busybox:1.31
      command: ['sh', '-c', 'until nslookup myservice; do sleep 2; done']
    - name: init-mydb
      image: busybox:1.31
      command: ['sh', '-c', 'until nslookup mydb; do sleep 2; done']
  containers:
    - name: myapp-container
      image: busybox:1.28
      command: ['sh', '-c', 'echo Running! && sleep 3600']
```

**Q2.** Create a native sidecar (K8s 1.28+) logger that runs alongside the main app container.

**Answer**

*Declarative:*
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-with-sidecar
spec:
  initContainers:
    - name: sidecar-logger
      image: busybox:1.31
      restartPolicy: Always
      command: ['sh', '-c', 'while true; do echo logging; sleep 10; done']
  containers:
    - name: main-app
      image: busybox:1.31
      command: ['sh', '-c', 'sleep 3600']
```

Init containers run sequentially; a native sidecar uses `restartPolicy: Always` on an init container to stay running alongside main containers.

---

### 9. Self-Healing & Probes

**Q1.** Add liveness, readiness, and startup HTTP probes to Deployment `api` on port 8080 (`/healthz`, `/ready`, `/startup`).

**Answer**

*Declarative:*
```yaml
spec:
  template:
    spec:
      containers:
        - name: api
          image: my-api
          ports:
            - containerPort: 8080
          livenessProbe:
            httpGet:
              path: /healthz
              port: 8080
            initialDelaySeconds: 15
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /ready
              port: 8080
            periodSeconds: 5
          startupProbe:
            httpGet:
              path: /startup
              port: 8080
            failureThreshold: 30
            periodSeconds: 10
```

**Q2.** What happens when each probe type fails?

**Answer**

| Probe | Action on failure |
|-------|-------------------|
| **Liveness** | Container is restarted |
| **Readiness** | Pod removed from Service endpoints (no traffic) |
| **Startup** | Other probes disabled until startup succeeds; then normal probing resumes |

---

### 10. Scaling Applications

**Q1.** Scale Deployment `frontend` from 2 to 5 replicas imperatively and verify.

**Answer**

*Imperative:*
```bash
kubectl scale deployment frontend --replicas=5
kubectl get deployment frontend
kubectl get pods -l app=frontend
```

*Declarative:*
```yaml
spec:
  replicas: 5
```
```bash
kubectl apply -f deployment.yaml
```

**Q2.** Compare horizontal vs vertical scaling at the workload and cluster level.

**Answer**

| Type | Method |
|------|--------|
| Horizontal (workload) | More Pod replicas — HPA |
| Vertical (workload) | More CPU/memory per Pod — VPA |
| Horizontal (cluster) | More nodes — Cluster Autoscaler |
| Vertical (cluster) | Bigger nodes |

---

### 11. Horizontal Pod Autoscaler (HPA)

**Q1.** Create HPA `my-app-hpa` for Deployment `my-app`: min 1, max 10, target CPU 50%.

**Answer**

*Imperative:*
```bash
kubectl autoscale deployment my-app --cpu-percent=50 --min=1 --max=10
```

*Declarative:*
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: my-app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-app
  minReplicas: 1
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 50
```

**Q2.** HPA shows `<unknown>` for metrics. What prerequisite is likely missing?

**Answer**

**Metrics Server** is not installed or not reachable. HPA needs resource metrics from Metrics Server for CPU-based autoscaling.

```bash
kubectl top pods
kubectl get apiservice v1beta1.metrics.k8s.io
```

---

### 12. Vertical Pod Autoscaler (VPA)

**Q1.** Create VPA `my-app-vpa` for Deployment `my-app` in `Auto` mode, controlling CPU for container `nginx` (min 250m, max 2 cores).

**Answer**

*Declarative:*
```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: my-app-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-app
  updatePolicy:
    updateMode: "Auto"
  resourcePolicy:
    containerPolicies:
      - containerName: nginx
        minAllowed:
          cpu: 250m
        maxAllowed:
          cpu: "2"
        controlledResources: ["cpu"]
```

**Q2.** When should you choose VPA over HPA for a stateless web API?

**Answer**

Prefer **HPA** for stateless web/API workloads — it adds Pods during traffic spikes without restarting existing ones. Use **VPA** for memory-heavy or stateful workloads where right-sizing per-Pod resources matters more than replica count.

---

### 13. In-Place Pod Resizing

**Q1.** Configure container `nginx` for in-place CPU resize without restart, but memory resize requiring container restart. Enable feature gate `InPlacePodVerticalScaling`.

**Answer**

*Declarative:*
```yaml
spec:
  containers:
    - name: nginx
      image: nginx
      resizePolicy:
        - resourceName: cpu
          restartPolicy: NotRequired
        - resourceName: memory
          restartPolicy: RestartContainer
      resources:
        requests:
          cpu: "1"
          memory: 256Mi
        limits:
          cpu: "2"
          memory: 512Mi
```

**Q2.** List two limitations of in-place Pod resizing.

**Answer**

- Only **CPU and memory** can be resized in place
- Cannot change **QoS class** (e.g., Guaranteed → Burstable)
- **Windows** nodes not supported

---

## Mixed Topic Questions

### Scenario 1 — Config-Driven Rolling Deploy

Deployment `shop` (3 replicas, `nginx:1.7`) must read `APP_MODE` from ConfigMap `shop-config` (`APP_MODE=staging`) and `DB_PASSWORD` from Secret `shop-db`. Update image to `nginx:1.25` with zero downtime (`maxUnavailable: 0`, `maxSurge: 1`). Roll back if the rollout fails.

**Answer**

```bash
kubectl create configmap shop-config --from-literal=APP_MODE=staging
kubectl create secret generic shop-db --from-literal=DB_PASSWORD=s3cret
```

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: shop
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: shop
  template:
    metadata:
      labels:
        app: shop
    spec:
      containers:
        - name: nginx
          image: nginx:1.25
          env:
            - name: APP_MODE
              valueFrom:
                configMapKeyRef:
                  name: shop-config
                  key: APP_MODE
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: shop-db
                  key: DB_PASSWORD
          readinessProbe:
            httpGet:
              path: /
              port: 80
            periodSeconds: 5
```

```bash
kubectl apply -f deployment.yaml
kubectl rollout status deployment/shop || kubectl rollout undo deployment/shop
```

---

### Scenario 2 — Init + Sidecar Logging Stack

Pod `analytics` needs: (1) init container waiting for `redis` DNS, (2) main `app` container, (3) sidecar log shipper sharing `/var/log` via `emptyDir`. Main app must not start until Redis resolves.

**Answer**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: analytics
spec:
  initContainers:
    - name: wait-redis
      image: busybox:1.31
      command: ['sh', '-c', 'until nslookup redis; do sleep 2; done']
    - name: log-shipper
      image: fluent/fluent-bit
      restartPolicy: Always
      volumeMounts:
        - name: logs
          mountPath: /var/log
  containers:
    - name: app
      image: my-analytics:latest
      volumeMounts:
        - name: logs
          mountPath: /var/log
  volumes:
    - name: logs
      emptyDir: {}
```

---

### Scenario 3 — Probe Tuning for Slow Startup

App takes up to 5 minutes to start. Configure startup probe (30 failures × 10s = 300s), then liveness/readiness on `/health` port 8080. Scale with HPA at 60% CPU, 2–8 replicas.

**Answer**

```yaml
# Deployment excerpt
startupProbe:
  httpGet:
    path: /health
    port: 8080
  failureThreshold: 30
  periodSeconds: 10
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  periodSeconds: 10
readinessProbe:
  httpGet:
    path: /health
    port: 8080
  periodSeconds: 5
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: analytics-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: analytics
  minReplicas: 2
  maxReplicas: 8
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 60
```

---

### Scenario 4 — Multi-Container Command Override

Image `ubuntu-sleeper` has `ENTRYPOINT ["sleep"]` and `CMD ["5"]`. In a 2-container Pod, `worker-a` runs `sleep 30`, `worker-b` runs `sleep2.0 60`. Both share a ConfigMap volume at `/config`.

**Answer**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: dual-sleeper
spec:
  volumes:
    - name: cfg
      configMap:
        name: worker-config
  containers:
    - name: worker-a
      image: ubuntu-sleeper
      args: ["30"]
      volumeMounts:
        - name: cfg
          mountPath: /config
    - name: worker-b
      image: ubuntu-sleeper
      command: ["sleep2.0"]
      args: ["60"]
      volumeMounts:
        - name: cfg
          mountPath: /config
```

---

### Scenario 5 — Secret Encryption + ConfigMap Volume

Enable encryption at rest for Secrets (exam: edit apiserver static Pod). Create Secret `api-key` and ConfigMap `api-config`. Mount ConfigMap as files; inject Secret key as env var. Verify Secret value is not plaintext in etcd.

**Answer**

1. Configure `EncryptionConfiguration` and apiserver flag (see Section 6).
2. Create resources:
```bash
kubectl create secret generic api-key --from-literal=TOKEN=abc123
kubectl create configmap api-config --from-literal=LOG_LEVEL=debug
kubectl get secrets --all-namespaces -o json | kubectl replace -f -
```
3. Pod spec combines `env` from Secret and volume from ConfigMap (see Sections 4–5).
4. Verify with `etcdctl` that stored value is encrypted.

---

### Scenario 6 — HPA + VPA Decision & Scale

Deployment `batch-processor` is memory-bound (8 Gi per Pod, few replicas). Deployment `api-gateway` is CPU-bound under load. Configure appropriate autoscaling for each and explain your choice.

**Answer**

**api-gateway** — HPA (stateless, traffic spikes):
```bash
kubectl autoscale deployment api-gateway --cpu-percent=50 --min=2 --max=20
```

**batch-processor** — VPA in `Recreate` or `Auto` mode (memory-heavy):
```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: batch-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: batch-processor
  updatePolicy:
    updateMode: "Recreate"
  resourcePolicy:
    containerPolicies:
      - containerName: processor
        controlledResources: ["memory"]
        minAllowed:
          memory: 4Gi
        maxAllowed:
          memory: 16Gi
```

Do **not** run HPA and VPA on the same Deployment for the same resource — they conflict. Use HPA for replica scaling; VPA for right-sizing memory per Pod.
