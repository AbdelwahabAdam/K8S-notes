# CKA Practice — Security
> Based on [enhanced_readme.md](./enhanced_readme.md)

---

## Topic Questions

### 1. Security Primitives Overview

**Q1.** List the defense-in-depth layers for Kubernetes cluster security.

**Answer**

| Layer | Mechanism |
|-------|-----------|
| Host security | SSH keys only, hardened OS |
| API access control | Authentication + Authorization |
| Transport security | TLS between all components |
| Authorization | RBAC (standard) |
| Network isolation | Network Policies |
| Data at rest | Secrets encryption in etcd |

**Q2.** What happens to every request reaching kube-apiserver before it is processed?

**Answer**

1. **Authentication** — verify identity (certs, tokens, OIDC, ServiceAccount)
2. **Authorization** — check permissions (RBAC, Node, Webhook)
3. **Admission controllers** — enforce policies (mutating/validating)

---

### 2. Authentication

**Q1.** How are human users vs in-cluster workloads authenticated differently?

**Answer**

| Identity type | Managed by |
|---------------|------------|
| Admin / developer | External — certs, OIDC, LDAP (not API objects) |
| Service account | Kubernetes API (`ServiceAccount` object) |
| Bots / workloads | ServiceAccount tokens mounted in Pods |

**Q2.** Name four authentication methods kube-apiserver supports.

**Answer**

1. **Client certificates** (X.509 signed by cluster CA)
2. **Static token file** (`--token-auth-file`, legacy)
3. **ServiceAccount tokens** (mounted in Pods)
4. **OIDC / LDAP / Webhook** (external identity providers)

---

### 3. TLS Certificates

**Q1.** Generate a cluster CA and an admin client certificate with group `system:masters`.

**Answer**

```bash
# CA
openssl genrsa -out ca.key 2048
openssl req -new -key ca.key -subj "/CN=KUBERNETES-CA" -out ca.csr
openssl x509 -req -in ca.csr -signkey ca.key -out ca.crt

# Admin user
openssl genrsa -out admin.key 2048
openssl req -new -key admin.key \
  -subj "/CN=kube-admin/O=system:masters" -out admin.csr
openssl x509 -req -in admin.csr -CA ca.crt -CAkey ca.key -out admin.crt
```

**Q2.** kube-apiserver certificate is expiring. How do you inspect it and which fields matter?

**Answer**

```bash
openssl x509 -in /etc/kubernetes/pki/apiserver.crt -text -noout
```

Check: **Subject**, **SANs** (must include `kubernetes`, service DNS names, cluster IP), **Not After** (expiry), **Issuer**.

If kubectl fails, debug static Pods:
```bash
crictl ps -a
crictl logs <container-id>
```

---

### 4. Certificate Signing Requests (CSR)

**Q1.** User `jane` submits a CSR. Create the CSR object, approve it, and extract the signed certificate.

**Answer**

```bash
openssl genrsa -out jane.key 2048
openssl req -new -key jane.key -subj "/CN=jane" -out jane.csr
cat jane.csr | base64 | tr -d '\n'   # paste into YAML
```

*Declarative:*
```yaml
apiVersion: certificates.k8s.io/v1
kind: CertificateSigningRequest
metadata:
  name: jane-csr
spec:
  signerName: kubernetes.io/kube-apiserver-client
  expirationSeconds: 86400
  usages:
    - client auth
  request: <BASE64_ENCODED_CSR>
```

*Imperative:*
```bash
kubectl apply -f jane-csr.yaml
kubectl get csr
kubectl certificate approve jane-csr
kubectl get csr jane-csr -o jsonpath='{.status.certificate}' | base64 --decode > jane.crt
```

**Q2.** Which control plane component signs approved CSRs, and what flags configure it?

**Answer**

**kube-controller-manager** runs CSR approving and signing controllers.

```yaml
--cluster-signing-cert-file=/etc/kubernetes/pki/ca.crt
--cluster-signing-key-file=/etc/kubernetes/pki/ca.key
```

---

### 5. Kubeconfig

**Q1.** Create a kubeconfig for user `dev-user` accessing cluster `my-cluster` at `https://my-cluster:6443` with client cert `admin.crt`/`admin.key` and CA `ca.crt`. Set default namespace to `finance`.

**Answer**

*Declarative:*
```yaml
apiVersion: v1
kind: Config
current-context: dev-user@my-cluster
clusters:
  - name: my-cluster
    cluster:
      certificate-authority: ca.crt
      server: https://my-cluster:6443
contexts:
  - name: dev-user@my-cluster
    context:
      cluster: my-cluster
      user: dev-user
      namespace: finance
users:
  - name: dev-user
    user:
      client-certificate: admin.crt
      client-key: admin.key
```

*Imperative:*
```bash
kubectl config set-cluster my-cluster --server=https://my-cluster:6443 --certificate-authority=ca.crt
kubectl config set-credentials dev-user --client-certificate=admin.crt --client-key=admin.key
kubectl config set-context dev-user@my-cluster --cluster=my-cluster --user=dev-user --namespace=finance
kubectl config use-context dev-user@my-cluster
```

**Q2.** Where is the default kubeconfig located? Can you apply it with `kubectl apply`?

**Answer**

Default: `~/.kube/config`. **No** — kubeconfig is a client-side file, not a Kubernetes API object. Use `kubectl config` commands or edit the file directly.

---

### 6. API Groups

**Q1.** Which API group contains Deployments? Which contains NetworkPolicies? Which contains Roles?

**Answer**

| Resource | API Group |
|----------|-----------|
| Deployments | `apps/v1` → `/apis/apps/v1` |
| NetworkPolicies | `networking.k8s.io/v1` |
| Roles | `rbac.authorization.k8s.io/v1` |
| Pods, Services, Secrets | Core → `/api/v1` |

```bash
kubectl api-resources
```

**Q2.** How can you explore the API locally without client certificates?

**Answer**

```bash
kubectl proxy
# Then browse http://localhost:8001/api/v1/...
```

Runs on the machine where kubectl is configured — uses your kubeconfig credentials.

---

### 7. Authorization

**Q1.** List authorization modes available in Kubernetes and identify the standard production mode.

**Answer**

| Mode | Description |
|------|-------------|
| **RBAC** | Role-based — **standard** |
| **Node** | kubelet access to its own resources |
| **Webhook** | External policy (OPA, etc.) |
| **ABAC** | Legacy attribute-based |
| **AlwaysAllow / AlwaysDeny** | Testing only |

Set on kube-apiserver: `--authorization-mode=Node,RBAC`

**Q2.** A request passes authentication but is denied. What component rejected it and what do you check next?

**Answer**

**Authorization** rejected it. Check RBAC:
```bash
kubectl auth can-i <verb> <resource> --as <user> -n <namespace>
kubectl describe rolebinding -n <namespace>
```

---

### 8. RBAC — Roles & Bindings

**Q1.** Create Role `developer` in namespace `default` allowing full Pod CRUD and ConfigMap create. Bind it to user `dev-user`.

**Answer**

*Imperative:*
```bash
kubectl create role developer -n default \
  --verb=get,list,create,update,delete --resource=pods
kubectl create role developer -n default \
  --verb=create --resource=configmaps
# Or combine in YAML for cleaner rules

kubectl create rolebinding devuser-developer-binding -n default \
  --role=developer --user=dev-user
```

*Declarative:*
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: developer
  namespace: default
rules:
  - apiGroups: [""]
    resources: ["pods"]
    verbs: ["list", "get", "create", "update", "delete"]
  - apiGroups: [""]
    resources: ["configmaps"]
    verbs: ["create"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: devuser-developer-binding
  namespace: default
subjects:
  - kind: User
    name: dev-user
    apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: developer
  apiGroup: rbac.authorization.k8s.io
```

**Q2.** Can user `dev-user` create Pods in namespace `dololo`?

**Answer**

```bash
kubectl auth can-i create pods --as dev-user --namespace dololo
# no — RoleBinding is in default namespace only
```

---

### 9. ClusterRoles & ClusterRoleBindings

**Q1.** Grant user `michelle` full access to PersistentVolumes and StorageClasses cluster-wide.

**Answer**

*Imperative:*
```bash
kubectl create clusterrole storage-admin \
  --resource=persistentvolumes,storageclasses --verb=*

kubectl create clusterrolebinding michelle-storage-admin \
  --clusterrole=storage-admin --user=michelle
```

*Declarative:*
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: storage-admin
rules:
  - apiGroups: [""]
    resources: ["persistentvolumes"]
    verbs: ["*"]
  - apiGroups: ["storage.k8s.io"]
    resources: ["storageclasses"]
    verbs: ["*"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: michelle-storage-admin
subjects:
  - kind: User
    name: michelle
    apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: storage-admin
  apiGroup: rbac.authorization.k8s.io
```

**Q2.** Name three cluster-scoped resources vs three namespaced resources.

**Answer**

| Namespaced | Cluster-scoped |
|------------|----------------|
| pods, deployments, secrets | nodes, persistentvolumes, namespaces |
| services, configmaps, roles | clusterroles, clusterrolebindings, csr |

---

### 10. Service Accounts

**Q1.** Create ServiceAccount `dashboard-sa`, generate a 2-hour token, and assign it to Pod `my-pod`.

**Answer**

*Imperative:*
```bash
kubectl create serviceaccount dashboard-sa
kubectl create token dashboard-sa --duration 2h
```

*Declarative:*
```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: dashboard-sa
  namespace: default
---
apiVersion: v1
kind: Pod
metadata:
  name: my-pod
spec:
  serviceAccountName: dashboard-sa
  containers:
    - name: app
      image: my-app
```

Token auto-mounted at `/var/run/secrets/kubernetes.io/serviceaccount/` unless `automountServiceAccountToken: false`.

**Q2.** Grant ServiceAccount `dashboard-sa` the `developer` Role in `default`.

**Answer**

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: dashboard-sa-developer
  namespace: default
subjects:
  - kind: ServiceAccount
    name: dashboard-sa
    namespace: default
roleRef:
  kind: Role
  name: developer
  apiGroup: rbac.authorization.k8s.io
```

---

### 11. Image Security

**Q1.** Pull image `private-registry.io/apps/internal-app` using credentials stored in Secret `regcred`.

**Answer**

*Imperative:*
```bash
kubectl create secret docker-registry regcred \
  --docker-server=private-registry.io \
  --docker-username=user \
  --docker-password=pass \
  --docker-email=user@org.com
```

*Declarative:*
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx
spec:
  containers:
    - name: nginx
      image: private-registry.io/apps/internal-app
  imagePullSecrets:
    - name: regcred
```

**Q2.** List three image security best practices.

**Answer**

1. **Scan images** for vulnerabilities
2. Use **minimal base images** and **pin digests** (not just tags)
3. Enforce policies via **admission controllers** (e.g., disallow `:latest`)

---

### 12. Security Contexts

**Q1.** Pod runs as UID 1001 (`fsGroup: 2000`). Container `web` overrides to UID 1002, adds `SYS_TIME` capability, disables privilege escalation, and uses read-only root filesystem.

**Answer**

*Declarative:*
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: multi-pod
spec:
  securityContext:
    runAsUser: 1001
    fsGroup: 2000
  containers:
    - name: web
      image: ubuntu
      command: ["sleep", "5000"]
      securityContext:
        runAsUser: 1002
        capabilities:
          add: ["SYS_TIME"]
        allowPrivilegeEscalation: false
        readOnlyRootFilesystem: true
```

**Q2.** What are the three Pod Security Standard levels and how are they enforced?

**Answer**

| Level | Description |
|-------|-------------|
| `privileged` | Unrestricted |
| `baseline` | Minimally restrictive, prevents known privilege escalations |
| `restricted` | Heavily restricted, follows hardening best practices |

Enforced via **Pod Security admission** on namespaces (labels: `pod-security.kubernetes.io/enforce`, etc.).

---

### 13. Network Policies

**Q1.** Create NetworkPolicy `db-policy` allowing ingress to Pods with `role=db` only from Pods with `role=api` on TCP 5432. Allow egress to DNS (UDP 53) only.

**Answer**

*Declarative:*
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: db-policy
  namespace: default
spec:
  podSelector:
    matchLabels:
      role: db
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              role: api
      ports:
        - protocol: TCP
          port: 5432
  egress:
    - to:
        - podSelector:
            matchLabels:
              role: dns
      ports:
        - protocol: UDP
          port: 53
```

**Q2.** Default network behavior in Kubernetes? What CNI feature is required for NetworkPolicies?

**Answer**

**Default: all Pods can communicate with all Pods** cluster-wide. NetworkPolicies require a CNI that supports them (e.g., **Calico**, **Cilium**, **Weave**). Flannel alone does **not** enforce NetworkPolicies.

---

## Mixed Topic Questions

### Scenario 1 — Onboard Developer with RBAC

User `jane` needs CSR-based access. After cert approval, she should list/get/create Pods and ConfigMaps in namespace `dev` only. Verify with `kubectl auth can-i`.

**Answer**

```bash
# CSR flow
openssl genrsa -out jane.key 2048
openssl req -new -key jane.key -subj "/CN=jane" -out jane.csr
# Create CSR, approve
kubectl certificate approve jane-csr
kubectl get csr jane-csr -o jsonpath='{.status.certificate}' | base64 --decode > jane.crt

# RBAC
kubectl create role developer -n dev \
  --verb=get,list,create --resource=pods,configmaps
kubectl create rolebinding jane-dev -n dev \
  --role=developer --user=jane

# Kubeconfig
kubectl config set-credentials jane --client-certificate=jane.crt --client-key=jane.key
kubectl config set-context jane@cluster --cluster=<cluster> --user=jane --namespace=dev
kubectl config use-context jane@cluster

# Verify
kubectl auth can-i create pods --as jane -n dev        # yes
kubectl auth can-i create pods --as jane -n default    # no
kubectl auth can-i delete pods --as jane -n dev      # no
```

---

### Scenario 2 — Secure Microservice Deployment

Deploy `api` Pod in namespace `backend`: private image from `registry.corp.io/api:v2`, ServiceAccount `api-sa` with Role allowing get/list Pods, `runAsNonRoot`, read-only root FS, NetworkPolicy allowing ingress only from `role=frontend` on port 8080.

**Answer**

```bash
kubectl create namespace backend
kubectl create sa api-sa -n backend
kubectl create secret docker-registry regcred -n backend \
  --docker-server=registry.corp.io --docker-username=deploy --docker-password=xxx
```

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: api-reader
  namespace: backend
rules:
  - apiGroups: [""]
    resources: ["pods"]
    verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: api-sa-binding
  namespace: backend
subjects:
  - kind: ServiceAccount
    name: api-sa
    namespace: backend
roleRef:
  kind: Role
  name: api-reader
  apiGroup: rbac.authorization.k8s.io
---
apiVersion: v1
kind: Pod
metadata:
  name: api
  namespace: backend
  labels:
    role: api
spec:
  serviceAccountName: api-sa
  imagePullSecrets:
    - name: regcred
  securityContext:
    runAsNonRoot: true
  containers:
    - name: api
      image: registry.corp.io/api:v2
      ports:
        - containerPort: 8080
      securityContext:
        readOnlyRootFilesystem: true
        allowPrivilegeEscalation: false
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-ingress
  namespace: backend
spec:
  podSelector:
    matchLabels:
      role: api
  policyTypes: [Ingress]
  ingress:
    - from:
        - podSelector:
            matchLabels:
              role: frontend
      ports:
        - protocol: TCP
          port: 8080
```

---

### Scenario 3 — TLS Certificate Expiry on API Server

`kubectl` returns TLS errors. apiserver cert expired. Inspect cert, identify expiry, and describe remediation (regenerate cert or `kubeadm certs renew`).

**Answer**

```bash
openssl x509 -in /etc/kubernetes/pki/apiserver.crt -text -noout | grep -A2 Validity

# kubeadm clusters
kubeadm certs renew apiserver
kubeadm certs renew all   # if multiple certs expired

# Restart static Pods
crictl ps | grep kube-apiserver
# kubelet auto-restarts static Pods after cert renewal

# Verify
kubectl get nodes
openssl x509 -in /etc/kubernetes/pki/apiserver.crt -text -noout | grep "Not After"
```

If SANs are wrong, regenerate CSR with correct `subjectAltName` entries for kubernetes service DNS and cluster IP.

---

### Scenario 4 — Namespace Isolation with NetworkPolicy + PSS

Namespace `production` enforces `restricted` Pod Security Standard. Only Pods with `tier=web` can reach Pods with `tier=db` on port 5432. No other traffic allowed to `tier=db`.

**Answer**

```bash
kubectl label namespace production \
  pod-security.kubernetes.io/enforce=restricted \
  pod-security.kubernetes.io/enforce-version=latest
```

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: db-isolation
  namespace: production
spec:
  podSelector:
    matchLabels:
      tier: db
  policyTypes: [Ingress]
  ingress:
    - from:
        - podSelector:
            matchLabels:
              tier: web
      ports:
        - protocol: TCP
          port: 5432
```

Pods must comply with `restricted` PSS (non-root, drop capabilities, no privileged, etc.) or admission will reject them.

---

### Scenario 5 — ClusterRole for Node Viewer + CSR Workflow

User `bob` needs cluster-wide read-only access to Nodes and Namespaces. Create ClusterRole, bind to `bob`, and verify. Also show CSR approval path if bob has no cert yet.

**Answer**

```bash
kubectl create clusterrole node-viewer \
  --verb=get,list,watch --resource=nodes,namespaces

kubectl create clusterrolebinding bob-node-viewer \
  --clusterrole=node-viewer --user=bob

kubectl auth can-i list nodes --as bob           # yes
kubectl auth can-i delete nodes --as bob         # no
kubectl auth can-i create pods --as bob -n default  # no
```

CSR path if no cert:
```bash
# bob generates key+csr → admin creates CSR → kubectl certificate approve bob-csr
# bob builds kubeconfig with signed cert
```

---

### Scenario 6 — End-to-End Security Audit

Audit checklist for namespace `payments`: (1) no default SA token mount, (2) Secrets encrypted at rest, (3) NetworkPolicy default-deny with explicit allows, (4) RBAC least privilege for SA `payment-processor`.

**Answer**

**1. Disable default SA token:**
```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: default
  namespace: payments
automountServiceAccountToken: false
```

**2. Secrets encryption** — verify apiserver `--encryption-provider-config` is set; re-encrypt:
```bash
kubectl get secrets -n payments -o json | kubectl replace -f -
```

**3. Default-deny NetworkPolicy:**
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny
  namespace: payments
spec:
  podSelector: {}
  policyTypes: [Ingress, Egress]
```
Then add explicit allow policies for required traffic only.

**4. Least-privilege RBAC for `payment-processor`:**
```bash
kubectl create role payment-role -n payments \
  --verb=get,list --resource=secrets
kubectl create rolebinding payment-sa-binding -n payments \
  --role=payment-role --serviceaccount=payments:payment-processor

kubectl auth can-i get secrets --as system:serviceaccount:payments:payment-processor -n payments  # yes
kubectl auth can-i get secrets --as system:serviceaccount:payments:payment-processor -n default    # no
```
