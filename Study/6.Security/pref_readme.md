# Security — Pref Revision (CKA)

Quick exam revision. See [enhanced_readme.md](./enhanced_readme.md) for full detail.

---

## Security layers

1. **Host** — SSH keys, no password auth
2. **Authentication** — who are you?
3. **Authorization** — what can you do? (RBAC)
4. **TLS** — encrypt all component traffic
5. **NetworkPolicy** — restrict Pod traffic
6. **Secrets** — encrypt at rest in etcd

---

## Authentication

| Identity | How |
|----------|-----|
| Human | Certs, OIDC, LDAP — **not** K8s User objects |
| Workload | **ServiceAccount** |

Methods: client certs, bearer tokens, SA tokens, OIDC

---

## TLS essentials

- **CA** signs all cluster certs (`ca.crt`, `ca.key`)
- Server certs: apiserver, etcd, kubelet
- Client certs: admin, controller-manager, scheduler, kube-proxy
- Admin CSR needs `O=system:masters`
- Apiserver needs **SANs** for all DNS names + IPs

```bash
openssl x509 -in cert.crt -text -noout   # Subject, SAN, expiry
crictl logs <id>                         # if kubectl broken
```

Ports: apiserver **6443**, etcd **2379/2380**

---

## CSR flow

1. User: key + CSR → base64
2. Create `CertificateSigningRequest`
3. `kubectl certificate approve <name>`
4. Cert in CSR status

---

## Kubeconfig

`clusters` + `users` + `contexts` → `~/.kube/config`

```bash
kubectl config view/use-context/set-context
```

---

## Authorization modes

**RBAC** (standard), Node, Webhook, ABAC (legacy)

```bash
kubectl auth can-i create pods --as user -n ns
```

---

## RBAC

| Object | Scope |
|--------|-------|
| **Role** + **RoleBinding** | Namespace |
| **ClusterRole** + **ClusterRoleBinding** | Cluster |

```yaml
rules:
  - apiGroups: [""]
    resources: ["pods"]
    verbs: ["get", "list", "create"]
```

Namespaced: pods, deploy, svc, secrets, cm, roles  
Cluster: nodes, pv, ns, clusterroles, csr

---

## ServiceAccount

- For apps/bots — not humans
- Default SA auto-mounted
- Token: `/var/run/secrets/kubernetes.io/serviceaccount/`
- `kubectl create token <sa> --duration 2h`
- Bind via RoleBinding `kind: ServiceAccount`

---

## Image security

```yaml
imagePullSecrets:
  - name: regcred
```

```bash
kubectl create secret docker-registry regcred \
  --docker-server=... --docker-username=... --docker-password=...
```

---

## Security context

| Level | Examples |
|-------|----------|
| Pod | `runAsUser`, `fsGroup` |
| Container | `capabilities`, `readOnlyRootFilesystem` |

Pod Security: `privileged` / `baseline` / `restricted`

---

## NetworkPolicy

- Default = all Pods talk to all Pods
- Needs CNI support (Calico, etc.)
- **ingress** = incoming; **egress** = outgoing
- `podSelector` = which Pods policy applies to

---

## Exam tips

1. RBAC verbs: get, list, create, update, patch, delete, watch
2. `--as` and `--namespace` for can-i checks
3. CSR apiGroup: `certificates.k8s.io/v1`
4. RBAC apiGroup: `rbac.authorization.k8s.io/v1`
5. NetworkPolicy: `networking.k8s.io/v1`

---

## Kubernetes Docs — YAML Example Locations

| Topic | Official docs (YAML examples) |
|-------|-------------------------------|
| CSR | [Certificate Signing Requests](https://kubernetes.io/docs/reference/access-authn-authz/certificate-signing-requests/) |
| Kubeconfig | [Organize cluster access (kubeconfig)](https://kubernetes.io/docs/concepts/configuration/organize-cluster-access-kubeconfig/) |
| Role / RoleBinding | [RBAC — Role & RoleBinding](https://kubernetes.io/docs/reference/access-authn-authz/rbac/) |
| ClusterRole / ClusterRoleBinding | [RBAC — ClusterRole & ClusterRoleBinding](https://kubernetes.io/docs/reference/access-authn-authz/rbac/) |
| ServiceAccount | [Configure Service Accounts](https://kubernetes.io/docs/tasks/configure-pod-container/configure-service-account/) |
| imagePullSecrets | [Pull from Private Registry](https://kubernetes.io/docs/tasks/configure-pod-container/pull-image-private-registry/) |
| SecurityContext | [Security Context](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/) |
| NetworkPolicy | [Declare Network Policy](https://kubernetes.io/docs/tasks/administer-cluster/declare-network-policy/) |
| Encrypt secrets | [Encrypt Secret Data at Rest](https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/) |
