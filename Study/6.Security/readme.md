# Security 

- k8s seurity Primitives
- Security Persistent key value store
- Authentication and Authorization
- Security Context
- TLS Certificates For cluster components
- Image Security
- Network Polices

------

## Kubernetes Security Primitives

- Secure Hosts
>> No password auth
>> only ssh

first line of defence, is controlling the access to the kube-apiserver it self

Who can access?
- Static Token File
- Certificates
- External Authentication Providers - LDAP
- Service Accounts

what thet can do?
- RBAC Authorization
- ABAC Authorization
- Node Authorization
- Webhook Mode

all communication between the diffrent components are secured by `TLS Certificates`

- by default, all pods can access each other in the cluster, we can restrict that using `Network Policies`

--------

### Authentication in K8s Cluster

who can access the cluster?

- Admins                        
- Developers                    
- Therid parties (Bots)         >>> Service Account
- Users                         >>> User Authentication are managed by the apps it self, so we will not handle that


in K8s we cant create users, but we can  create a service account

all users access is managed by the kube-apiserver, for each request, Kube-apiserver authenticate it before processing it


how kube-apiserver authenticate?
- Static Token File
- Certificase
- Identity Services                     >>> LDAP


----------

### TLS Certificates (Transport Layer Security)

- what are TLS Certificates
- How to generate them?
- How to view them?
- How does k8s use certificates?
- How to configure them?
- How to troubleshoot issues related to certificates?




a Certificate is used to guarantee truest between two parties during a transaction

- Certificate Authority (CA) 
    - Symantec
    - digicert
    - global sign



- To encrypt messages, we use asymertic encryption with a pair of public and private key
- an admin uses a pair of keys to secure the ssh connectivity to the server, the server uses a pair of keys to secure https traffic
- But for this the server furst sends a certificate signing request to a CA, the CA uses it's private key to sign the CSR
> NOTE: all the users have a copy of the CA's public key
- the sign certificate is then sent back to the server
- The server configures the web app with the signed certificate.
- whenever a user accesses the web app, the server send the certificate with it's public key 
the user'browser  reads the certificate and uses the CA'public key to validate and retrieve the server's public key
- then it generate a symmetric key that it wishes to use going forward for all communication, the symetric key is encripted using the server's public key and sent back to the server
- the server uses it's private key to decrypt the message and retrieve the symmertic key
...etc



we can encrypt data with a key and decrypt with the other  (pricate and public key)

- certificate with publickey usualy called (.pem, .crt)
- certificate with privatekey usualy called (-key.pem, .key)

----------

### TLS in Kubernetes

- webserver >> Privatekey, Certificate (public key) <<< Server Certificates
- Certificate Authority (CA)    >> Private, public key <<< Root Certificates
- User  >> Client Cerrificates


k8s consist of master and worker nodes, all connection between them must be secured and encrypted
communication between all k8s components must be secured and encrypted


#### Server Certificates for servers


ALL CERTIFICATES USED IN THE CLUSTER:

first the server components in the cluster:
- Kube-apiserver            >>>> apiserver.crt , apiserver.key
- Etcd server               >>>> etcd-server.crt, etcd-server.key
- kubelet server               >>>> kubelet-server.crt, kubelet-server.key

the client components:

- Admin                         >>>> admin.crt, admin.key
- kube-scheduler                >>>> scheduler.crt, scheduler.key
- kube-controller manager       >>>> controller-manager.crt, controller-manager.key
- kube-proxy                >>>> kube-proxy.crt, kube-proxy.key

the kube-apiserver is the only components interact with the etcd, to it is a client for the etcd, we can use the same keys, or generate a new one for this communication

- apiserver-etcd-client            >>>>  apiserver-etcd-client.cert,   apiserver-etcd-client.key

the same for the kubelet

- apiserver-kubelet-client            >>>>  apiserver-kubelet-client.cert,   apiserver-kubelet-client.key



k8s must have at least 1 CA (certificate authority) for the cluster
- ca.crt
- ca.key
----

TO generate a cettificates:

1. CA (certificate authority)

ca.key          >>>         `opensssl genrsa -out ca.key 2048`                                          >>> Generate Keys

ca.csr          >>>         `opensssl req  -new -key ca.key -subj "/CN=KUBERNATES-CA" -out ca.csr`      >>> Certificate Signing Request

ca.crt          >>>         `openssl x509 -req -in ca.csr -signkey ca.key -out ca.crt`                  >>> Sign Certificates


2. Admin User

admin.key           >>>     `openssl genrsa -out admin.key 2048`                                                                    >>> Generate Keys
admin.csr           >>>     `openssl req -new -key admin.key -subj "/CN=kube-admin/OU=system:masters" -out admin.csr`               >>> Certificate Siging Request
admin.crt           >>>     `openssl x509 -req -in admin.csr -CA ca.crt -CAkey ca.key -out admin.crt `                              >>> sign Certificates

to diffrentiate this user (admin) from any other user, we have to add the admin user to systemmaster group 


in order to use those certificates:
- use them in api call
```
curl https://kube-apiserver:6443/api/v1/pods --key admin.key --cert admin.crt --cacert ca.crt 
```

- use them in kube-config.yaml file

```yaml
apiVersion: v1
clusters:
    - cluster:
        certificate-authority: ca.cart
        server: https://kube-apiserver:6443
    name: kubernates
kind: Config
users:
    - name: kubernates-admin
      user:
        client-certificate: admin.crt
        client-key: admin.key
```

NOTE:
- we need to specify the CA cert for all components


3. etcd servers

- follow the same approach to generate the 

certificate >>>>  etcdserver.crt
key         >>>>  etcdserver.key

BUT: etcd can be deployed as a cluster between multiple servers as a high availability environment, so we will have to generate the keys and cert for each

certificate >>>>  etcdserver.crt, etcdpeer1.crt ...etc
key         >>>>  etcdserver.key, etcdpeer1.key ...etc

after all certificate are generated, we have to specify them while starting the etcd server

cat etcd.yaml
```
- etcd
    - --key-file=/path-to-certs/etcdserver.key
    - --cert-file=/path-to-certs/etcdserver.crt
    - --peer-cert-file=/path-to-certs/etcdpeer1.crt
    - --peer-client-cert-auth=true
    - --peer-key-file=/etc/kubernates/pki/etcd/ca.crt
    - --trusted-ca-file=/etc/kubernates/pki/etcd/ca.crt
```


4. kube-apiserver

the issue here is that kube-apiserver, has multiple names, so when we generate the Certificate Siging Request, we have to put all of those names

apiserver.key           >>>     `openssl genrsa -out apiserver.key 2048`                                                                        >>> Generate Keys
apiserver.csr           >>>     `openssl req -new -key apiserver.key -subj "/CN=kube-apiserver" -out apiserver.csr`                             >>> Certificate Siging Request
we have to create a openssl.conf file, to put all names:
```cnf
[req]
req=extensions= v3_req
distinguished_name= req_distinguished_name
[ v3_req ]
basicConstraints= CA:FALSE
keyUsage = nonRepuiation
subjectAltName= @alt_names
[alt_names]
DNS.1 = Kubernates
DNS.2 = Kubernates.defaults
DNS.3 = Kubernates.defaults.svc
DNS.4 = Kubernates.defaults.svc.cluster.local
Ip.1 = 10.96.0.1
Ip.2 = 172.17.0.87
```
apiserver.csr           >>>     `openssl req -new -key apiserver.key -subj "/CN=kube-apiserver" -out apiserver.csr -config openss.cnf`               >>> Certificate Siging Request

apiserver.crt           >>>     `openssl x509 -req -in apiserver.csr -CA ca.crt -CAkey ca.key -out apiserver.crt `                                  >>> sign Certificates

-----
#### View Certificate Details

in order to know the path for the certificates:

view the manifests file: /etc/kubernates/manifest/kube-apiserver.yaml

ex:  `- --tls-cert-file=/etc/kubernates/pki/apiserver.crt`


to view the certificate after knowing the path:
`openssl x509 -in /etc/kubernates/pki/apiserver.crt -text -noout`       >> to decode it and view it's content

- subject               >> the name of the crt
- Alternative Name      >> other names to be used
- Not After             >> expiration date
- Issuer                >> the issuer for it


NOTE:
in some cases, it kube-apiserver or etcd server had an issue, the `kubectrl` may not work, so we go one lever down, and view logs by

- crictl ps -a
- crictl log <container-id>


NOTE:
etcd uses port 2379 for client communication

etcd uses port 2380 for peer-to-peer communication


-----

### Certificates API

- Create CertificateSigningRequest Object
- Review Request
- Arrove Request
- Share Cert to Users


A user geneerate a key, then generate the Certificate Siging Request, and sent it to the admin,
the admin generate the Certificate Siging Request yaml file


<BASE64_ENCODED_CSR>         >>> `cat jana.csr | base64`
```yaml
apiVersion: certificates.k8s.io/v1
kind: CertificateSigingRequest
metadata:
    name: jana-csr
spec:
    signatureName: kubernates.io/kube-apiserver-client
    expirationSeconds: 600 #seconds
    usage:
        - clent auth
    request: <BASE64_ENCODED_CSR>
```


get all Certificates request:
`kubectl get csr`

approve a request:
`kubecrl certificate approve jana`

view certificate:
`kubectl get csr jana -o yaml`
then 
`echo "<BASE64_ENCODED_CSR>" | base64 --decode`


CONTROLLER manager: CSR-approving, CSR-Signing


`cat /etc/kubetnates/manifest/kube-contoll-manager.yaml`
we can find

```yaml
    - --cluster-signing-cert-file=/etc/kubernetes/pki/ca.crt
    - --cluster-signing-key-file=/etc/kubernetes/pki/ca.key
```



---------

### KubeConfig

now if we have the three files 
- ca.crt
- admin.key
- admin.crt

we can send requests to the kibe-apiserver.
and we can also do that from kubectl

ex:
`kubectl get pods  --server my-kube-playground:6443 --clinet-key admin.key --clinet-certificate admin.crt --certificate-authrity ca.crt`

but providing them each request or command is not easy, so we move then in config file

```config
--server my-kube-playground:6443 
--clinet-key admin.key 
--clinet-certificate admin.crt 
--certificate-authrity ca.crt
```

and do:
`kubectl get pods --kubeconfig config`

config file has 3 sections:

- Clusters >>> Dev, prod, google

- Contexts  >>> define which user account will access which cluster

- Users >>> Admin, dev user, prod user


```yaml

apiVersion: v1 
kind: Config
current-context: dev-iser@google ##!!
clusters:
    - name: my-kube-playground
    cluster:
        certificate-authority: ca.crt
        server: https://my-kube-playground: 6443
contexts:
    - name: my-kube-admin@my-kube-playground 
    context:
        cluster: my-kube-playground 
        user: my-kube-admin
    namespace: finance
users:
    - name: my-kube-admin
      user:
        client-certificate: admin.crt 
        client-key: admin.key
```
NOTE: no kubectl apply here >> location ~/.kube/config

to view the file:
`kubdectl config view`

to change context:
`kubectl config use-context prod-user@production`

to view all attr

`kubectl config -h`


Certificates in kubeconfig

-----------------

### API Group

- metric
- healthz
- version
- api
- apis
...etc


the API is 2:
- api: Core
>> v1 >>> that contain all

- nodes
- pods
- namespaces
- events
- pv
- pvc
...etc



- apis
caontains:

- /apps
- /extensions
- /networking.k8s.io
- /storage.k8s.io
- /authentication.k8s.io
- /certificates.k8s.io


each container resources
ex:

/apps:
- /deployment
- /replicaset
- /statefulsets

and in each we have
- list
- get
- create
- delete
- update
- watch


same for 
- /networking.k8s.io
contains:

- /v1 >> /networkpolicies


and same for 
- /certificates.k8s.io
contains:
- /v1 >>> /certificatesigningrequests



we can use 
`kubectl proxy` in order to address the api server without passing the certificates

or we will have to pass them

NOTE:
kube-apiserver run on port: 6443

--------

kube-proxy VS kubectl proxy (not the same)

------------------


### Authorization


Authorization Mechanisms

- Node Authorizer:


- RBAC (role based access controll):
we define a role and set all users needed to that role


- webhook
ex: open policy agent


- AlwaysAllow

- Always Deny

those are set by the `--authorization-mode=AlwaysAllow` in the kube-apiserver

----
### Role-Based Access Controls (RBAC)

we create a row object (yaml)

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
    name: developer 

rules:
    - apiGroups: [""]
      resources: ["pods"]
      verbs: ["list", "get", "create", "update", "delete"]

    - apiGroups: [""]
      resources: ["ConfigMap"]
      verbs: ["create"]
```

create using
`kubectl apply -f developer-role.yaml`


then bind user to the role

```yaml

apiVersion: rbac.authorization.k8s.io/v1 
kind: RoleBinding
metadata:
    name: devuser-developer-binding
subjects:
    - kind: User
      name: dev-user
      apiGroup: rbac.authorization.k8s.io
    roleRef:
        kind: Role
        name: developer
        apiGroup: rbac.authorization.k8s.io

```

create using
`kubectl apply -f binding-dev-role.yaml`

to get all roles

`kubectl get roles`

to get rolebinding

`kubectl get rolebindings`

to desctive a role

`kubectl describe role developer`



to check if u  have role to do something

`kubectl auth can-i create deployment`

or as user

`kubectl auth can-i create pods --as dev-user`

also we can add the namespace

`kubectl auth can-i create pods --as dev-user --namespace dololo`


NOTE: role and role binding, are namespaced

------
## Cluster Roles and Cluster Roles binding



NAME SPACED Scoes:
- pods
- replicasets
- jobs
- deployments
- services
- secrets
- roles
- pvc
- configmaps
- rolebindings


Cluster Scopes:
- nodes
- PV
- clusterroles
- clusterRolesBindings
- certificaressigningrequests
- namespaces




to create a cluster role:


```yaml

apiVersion: rbac.authorization.k8s.io/v1 
kind: ClusterRole
metadata:
    name: cluster-adminitrator
rules:
    - apiGroups: [""]
      resources: ["nodes"]
      verbs: ["list", "get", "create", "delete"]
```
we can use command:
`kubectl create clusterrole storage-admin --resource=persistentvolumes,storageclasses --verb=*`

and to attache a user to this cluter role, we create cluster binding


```yaml

apiVersion: rbac.authorization.k8s.io/v1 
kind: ClusterRoleBinding
metadata:
    name: cluster-admin-role-binding
subjects:
    - kind: User
      name: cluster-admin
      apiGroup: rbac.authorization.k8s.io
roleRef:
    kind: ClusterRole
    name: cluster-administator
    apiGroup: rbac.authorization.k8s.io
```

we can use command:

` kubectl create clusterrolebinding michelle-storage-admin --clusterrole storage-admin  --user=michelle`


-----------

## Service Accounts (bots)

ex: promethous, jinkins


to list all service accounts
`kubectl get serviceaccount`

it is mounted as projecting volume within the pod!
location: /var/run/secrests/kubernaties.io/serviceaccount   >>TOKEN inside

to create a service account

`kubectl create serviceaccount dashboard-sa`

or

```yaml

apiVersion: v1
kind: ServiceAccount
metadata:
    name: dashboard-sa
    namespace: default
```

to assosiate a service account to a pod, we pass it in the pod defination file

```yaml

apiVersion: v1
kind: Pod
metadata:
    name: my-kubeernates-dashboard-pod
spec:
    containers:
        - name: my-kubernates-container
          image: my-kubernates-image
    serviceAccountName: dashboard-sa
```


to create a token:

- `kubectl create token dashboard-sa --duration 2h`

we can use this token to send REST api request to the kube-apiserever


NOTES:

- Every namespace has a default servide account
- the default service account is automaticlly attached to the pod on creation
- to attach a service account to a pod use serviceAccountName Files
- when service account is attached to a pod, k8s:
        - automaticlly creates a token and mounts as a projected volume
        - automatticlly rotates token
        - automatticlly expires the token when the pod is deleted

-----
## Image Security

```yaml

apiVersion: v1
kind: Pod
metadata:
    name: nginx
spec:
    containers:
        - name: nginx
          image: nginx
```

the default: docker.io/library/nginx        >>> all public images

how to make private registery



```yaml

apiVersion: v1
kind: Pod
metadata:
    name: nginx
spec:
    containers:
        - name: nginx
          image: private-registery.io/apps/internal-app
    imagePullSecrets:
        - name: regcred
```

we have to create a sercret
```
kubectl create secret docker-registry regcred 
    --docker-server= private-registery.io
    --docker-username= regitery-user
    --docker-password= regirery-password
    --docker-email= registery-user@org.com
```



------------
## Prerequisite - Security in Docker
TODO: add 
## Security Contexts


```yaml
apiVersion: v1
kind: Pod
metadata:
    name: web-pod
spec:
    containers:
        - name: ubuntu
          image: ubuntu
          command: ["sleep", "3600"]
        securityContext:
            runAsUser: 1000
            capabilities:
                add: ["SYS_TIME"]
```

ex:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: multi-pod
spec:
  securityContext:
    runAsUser: 1001
  containers:
  -  image: ubuntu
     name: web
     command: ["sleep", "5000"]
     securityContext:
      runAsUser: 1002

  -  image: ubuntu
     name: sidecar
     command: ["sleep", "5000"]

```


-----------

### Network Policies

- Ingress: incoming
- Egress: outgoing


### Developing Network Policies

