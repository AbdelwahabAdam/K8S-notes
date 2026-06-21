## Application Lifecycle Management - Section Introduction

----
## Rolling updates and rollbacks 

- see status of roolout:

`kubectl rollout status deployment/<deployment-name>`

- to see the rollout history

`kubectl rollout history deployment/<deployment-name>`


we have two deployment stratregies:

- Recreate
- Rolling Update (defaults)


ex:

```yaml

apiVersion: apps/v1
kind: Deployment
metadata:
    name: myapp-deployment
    labels:
        app: myapp
        type: front-end
spec:
    template:
        metadata:
            name: myapp-pod
            labels:
                app: myapp
                type: front-end
        spec:
            containers:
                - name: nginx-container
                  image: nginx:1.7.1
    replicas: 3
    selector:
        matchLabels:
            app: myapp
            type: front-end
```
two ways of rollout:

- if we create this deployment, then apply a change (ex: image:nginx:latest) then we run `kubectl apply -f .`
a new rollout is triggered (this is the best way of doing a rollout)

- we can update the image using this command: (but this will make mimatch between the running deployment and it's deployment file)

`kubectl set image deployment/<dployment-name> nginx=nginx:latest`

NOTE:
for mulitple containers: 
OPTION 1: Single command: (single rollout)

`kubectl set image deployment/myapp-deployment container-1=nginx:latest container-2=busybox:latest`

OPTION 2: sperate command: (multiple rollout)
### Update first container
kubectl set image deployment/myapp-deployment container-1=nginx:latest

### Update second container (separate command)
kubectl set image deployment/myapp-deployment container-2=busybox:latest


### Commands -summary

- Create
`kubectl create -f deployment-definition.yaml`

- Get
`kubectl get deployments`

- Update
`kubectl apply -f deployment-definition.yaml`
`kubectl set image deployment/<dployment-name> nginx=nginx:latest`



- status
`kubectl rollout status deployment/<deployment-name>`
`kubectl rollout history deployment/<deployment-name>`


- Rollback
`kubectl rollout undo deployment/<deployment-name>`






## Configuration Applications

#### command and arguments in Docker

- `docker run ubuntu`

- `docker run ubuntu [CMD]`

After building the docker file
```Dockerfile
FROM ubuntu
CMD sleep 5   ## CMD ["sleep", "5"]
```

- build the docker image
`docker build -t ubuntu-sleeper .`

- run the container
`docker run ubuntu-sleeper`

to pass the sleep time in the command >> ENTRYPOINT

```Dockerfile
FROM ubuntu
ENTRYPOINT ["sleep"]
```

so when we run `docker run ubuntu-sleeper 10`  > the 10 is appendded to the sleep


to put default value if value is not passed

```Dockerfile
FROM ubuntu
ENTRYPOINT ["sleep"]
CMD ["5"]
```

`docker run ubuntu-sleeper`  > that will use the 5
`docker run ubuntu-sleeper 10`  > that will use the passed 10


we can overwrite it using command:

`docker run --entrypoint sleep2.0   ubuntu-sleeper 10`  >> this will replace the Entrypoint from sleep to sleep2.0



--------
#### Commands and Arguments


create a pod with command

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: ubunto-sleeper-pod
  labels:
    app: myapp
spec:
  containers:
    - name: ubunto-sleeper
      image: ubunto-sleeper
      args: ["10"]
      command: ["sleep2.0"]
```
NOTE:
command in pod >>. overwrite >>> Entrypoint in docker file
args in pod >>. overwrite >>> CMD in docker file




### environment vars
we have 3 ways of setting env vars:
- plain key value
- configMap
- Secrests




#### Plain key Value
we can set it in pod file container
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: ubunto-sleeper-pod
  labels:
    app: myapp
spec:
  containers:
    - name: ubunto-sleeper
      image: ubunto-sleeper
      env:
        - name: App_color
          value: pink
        - name: header_color
          value: green

```

#### ConfigMap

there is no way to create a config map file

- Imperative

`kubectl create configmap <config-name> --from-litreal=<key>=<value>`
`kubectl create configmap app-config --from-litreal=APP_COLOR=blue --from-litreal=APP_MODE=prod`

or

`kubectl create configmap <config-name> --from-file=<path-to-file>`
`kubectl create configmap app-config --from-file=/home/appconfig.properties`



- declarative

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
    APP_COLOR: blue
    APP_MODE: prod
```
then
`kubectl create -f cofig-map.yaml`



- to view config maps

`kubectl get configmap`


--- configMap in pods
pod file
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: ubunto-sleeper-pod
  labels:
    app: myapp
spec:
  containers:
    - name: ubunto-sleeper
      image: ubunto-sleeper
      envfrom:
            - configMapRef:
                name: app-config
```

we have other cases:

- env
```yaml
      envfrom:
            - configMapRef:
                name: app-config

```

- single env
```yaml
      envfrom:
            - configMapKeyRef:
                name: app-config
                key: APP_COLOR

```


- volume

```yaml
      envfrom:
            - configMap:
                name: app-config

```
----

#### Secrets
used to store sensitve info

- create a sencret
- inject to pod

to create a secret


- Imperative

`kubectl create secret generic <secret-name> --from-litreal=<key>=<value>`
`kubectl create secret generic app-secret --from-litreal=DB_HOST=mysql`

or

`kubectl create secret generic <secret-name> --from-file=<path-to-file>`
`kubectl create secret generic app-config --from-file=/home/appconfig.properties`


- declarative

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secret
data:
    DB_HOST: mysql
    DB_USER: root
    DB_PASSWORD: passwrd
```
but we should provide those sensitive info as a hash coded

`echo -n "mysql" | base64  `
`echo -n "root" | base64  `
`echo -n "passwrd" | base64  `

then the file will be:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secret
data:
    DB_HOST: bx1zcww=
    DB_USER: cm9vda==
    DB_PASSWORD: cGFzd3Jk
```


to view secrets

`kubectl get secrests`

to view attr:

`kubectl describe secrests`

to view values:

`kubectl get secret app-secret -o yaml`
but those are coded,


to decoded:

`echo -n 'bx1zcww=' | base64 --decode`



- confiuring secret with pods:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: ubunto-sleeper-pod
  labels:
    app: myapp
spec:
  containers:
    - name: ubunto-sleeper
      image: ubunto-sleeper
      envfrom:
            - secretRef:
                name: app-secret
```



ther other way to inject sercrets:

- Env
- single Env
- vlume











```yaml
      env:
        - name: APP_COLOR
          valueFrom:
            SecretKeyRef:
```



------

### Encrypting Secret Data at Rest

if we accessed etcd using:

```cmd
ETCDCTL_API=3 etcdctl \
   --cacert=/etc/kubernetes/pki/etcd/ca.crt   \
   --cert=/etc/kubernetes/pki/etcd/server.crt \
   --key=/etc/kubernetes/pki/etcd/server.key  \
   get /registry/secrets/default/secret1 | hexdump -C
```
note: secret1 is your secret

we can see the secrets from the etcd, to prevent that we need to activate Encrypting Secret Data at Rest

and that by adding 
`--encryption-provider-config=/etc/kubernetes/enc/enc.yaml`  >> to `/etc/kubernetes/manifests/kube-apiserver.yaml` commands section
 >> this will let us see the secrents (no encreption)
then add this part in volumeMounts

```yaml
    volumeMounts:
    ...
    - name: enc                           # add this line
      mountPath: /etc/kubernetes/enc      # add this line
      readOnly: true                      # add this line

```

then this part in vloums:

```yaml
  volumes:
  ...
  - name: enc                             # add this line
    hostPath:                             # add this line
      path: /etc/kubernetes/enc           # add this line
      type: DirectoryOrCreate             # add this line

```
now if we added secret2
`kubectl create secret generic my-secret2 --from-literal=key2=topsecret`

and accessed the etcd for secrent2

```cmd
ETCDCTL_API=3 etcdctl \
   --cacert=/etc/kubernetes/pki/etcd/ca.crt   \
   --cert=/etc/kubernetes/pki/etcd/server.crt \
   --key=/etc/kubernetes/pki/etcd/server.key  \
   get /registry/secrets/default/secret2 | hexdump -C
```
Note: note /registry/secrets/default/secret2

we will not be able to see the secret, but we can see for secret1


```cmd
ETCDCTL_API=3 etcdctl \
   --cacert=/etc/kubernetes/pki/etcd/ca.crt   \
   --cert=/etc/kubernetes/pki/etcd/server.crt \
   --key=/etc/kubernetes/pki/etcd/server.key  \
   get /registry/secrets/default/secret | hexdump -C
```
>> here we can see the secret 

to apply the changes (encription) to all secrets

`kubectl get secrets --all-namespaces -o json | kubectl replace -f -`

now even secret1 is encripted



NOTE: to create a secret file:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: my-secret
data:
  key1: c3VwZXJzZWNyZXQ=

```
-----


### Multi contaienrs pods

- share the same lifecycle
- call each other with localhost 
- share the same storage and volume


```yaml
apiVersion: v1
kind: Pod
metadata:
  name: simple-webapp
  labels:
    app: myapp
spec:
  containers:
    - name: web-app
      image: web-app
      ports:
        - containerport: 8080
  containers:
    - name: main-app
      image: main-app
```



#### Design Patterns

- co-located containers     >>> no aplility to define which containers start first, start together and end together

- regular init containers   >>> start and end then the main app run
- Sidecar containers        >>> we can specify who start first



co-located containers 

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: simple-webapp
  labels:
    app: myapp
spec:
  containers:
    - name: web-app
      image: web-app
      ports:
        - containerport: 8080
  containers:
    - name: main-app
      image: main-app
```


regular init containers

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: simple-webapp
  labels:
    app: myapp
spec:
  containers:
    - name: web-app
      image: web-app
      ports:
        - containerport: 8080

  initContainers:
    - name: main-app
      image: main-app
      command: 'wait-for-db-to-start.sh'
    - name: api-checker
      image: busybox
      command: 'wait-for-another-api.sh'

```

Sidecar containers   

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: simple-webapp
  labels:
    app: myapp
spec:
  containers:
    - name: web-app
      image: web-app
      ports:
        - containerport: 8080

  initContainers:
    - name: main-app
      image: main-app
      command: 'wait-for-db-to-start.sh'
      restartPolicy: Always

```


ex: APP >> ElasticSeach >> Kibana


NOTES: for multi containers pods:

- If any main container (i.e., containers listed under spec.containers) exits and the Pod's restartPolicy is set to Always or OnFailure, all containers in the Pod are restarted.

- Kubernetes does not restart individual containers within a Pod. Instead, it treats the Pod as a single unit of execution and restarts the entire Pod if needed.

This applies only to main containers, not init containers


examples for init containers:
- A script that pulls code or binaries from a repository before the application starts.
- A script that waits for an external service (like a database) to become available.

>> I think this is like depend on in docker!!


what is init containers:

- An init container is a special container that runs before the main containers in a Pod. Each init container must succeed (exit 0) before the next one is started. Once all init containers complete, the regular containers start simultaneously.


NOTE: If any init container fails, the entire Pod is restarted and all init containers are rerun from the beginning.

ex:
```yaml

apiVersion: v1
kind: Pod
metadata:
  name: myapp-pod
  labels:
    app: myapp
spec:
  initContainers:
    - name: init-myservice
      image: busybox:1.31
      command: ["sh", "-c", "until nslookup myservice; do echo waiting for myservice; sleep 2; done;"]
    - name: init-mydb
      image: busybox:1.31
      command: ["sh", "-c", "until nslookup mydb; do echo waiting for mydb; sleep 2; done;"]
  containers:
    - name: myapp-container
      image: busybox:1.28
      command: ["sh", "-c", "echo The app is running! && sleep 3600"]

```


#### Native Sidecar Containers

Declared using the restartPolicy: Always field inside the initContainers block.
Kubernetes treats such containers as sidecars, ensuring they:
- Start before main containers.
- Run alongside them.
- Shut down after the main containers complete.

ex:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: sidecar-example
spec:
  initContainers:
    - name: sidecar-logger
      image: busybox:1.31
      restartPolicy: Always
      command: ["sh", "-c", "while true; do echo Sidecar running; sleep 10; done"]
  containers:
    - name: main-app
      image: busybox:1.31
      command: ["sh", "-c", "echo Main app starting; sleep 60"]

```

The sidecar-logger container behaves like a sidecar, though declared in initContainers.
It uses restartPolicy: Always to stay alive throughout the Pod lifecycle.
Kubernetes starts the sidecar first, waits for readiness, then starts the main app.


----

#### Self-Healing Applications

- Kubernetes supports self-healing applications through ReplicaSets and Replication Controllers. The replication controller helps ensure that a POD is re-created automatically when the application within the POD crashes. It helps in ensuring enough replicas of the application are running at all times.


- Kubernetes provides additional support to check the health of applications running within PODs and take necessary actions through Liveness and Readiness Probes.

-----
## Scale Applications

TODO: course for that! >. https://learn.kodekloud.com/user/courses/kubernetes-autoscaling
- 🆕Introduction to Autoscaling (2025 Updates)

- Horizontal POD Autoscaling    >> add more servers
- Vertical POd Autoscaling      >> add more resources




sclase workloads        >>> by adding more contaienrs 
- Horizontal scaling        > adding more pods
- Vertical Scaling          > increase resources in exsiting pods




scaling cluster infra 
- Horizontal scaling        > adding more nodes
- Vertical Scaling          > increase resources in exsiting nodes


Automated
- Cluster AutoScaler >> Horizontal Cluster infra
- Horizontal Pod Autoscaler (HPA) >> Horizontal Scaling pod (workload)
- Vertical Pod Autoscaler (VPA)>> Vertical Scaling pod (workload)



#### 🆕 Horizontal Pod Autoscaler (HPA)

- continusely mentor the metric
- add pods
- Balances thresholds
- track multiple matrics


ex: 
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  selector:
    matchLabels:
      app: my-app
  replicas: 1
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
        - name: nginx
          image: nginx
          resources:
            requests:
                cpu: "250m"
            limits:
                cpu: "500m"
```

to autoscale this deployment
`kubectl autoscale deployment my-app --cpu-percent=50 --min=1 --max=10`
- Metric server must be up

- to get all Horizontal Pod Autoscaler (HPA)
`kubectl get hpa`



we can create it using yaml


```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
    scaleTargetRef:
        apiVersion: app/v1
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

we can use the builtin metrics server or Custom mertics Adapter(workload, Deploytment)

and external workload adapters ex: DATADOG, Dynatrace



------

### In place pods resizing

any changes in resources definition in deployment pod section. this will close the pod and spawn a new one


to active thie features:

- `$FEATURE_GATES=InPlacePodVerticalScaling=true `

ex:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  selector:
    matchLabels:
      app: my-app
  replicas: 1
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
        - name: nginx
          image: nginx
          resizePolicy:
            - resourceName: cpu
              restartPolicy: NotRequired
            - resourceName: memnory
              restartPolicy: RestartContainer
          resources:
            requests:
                cpu: "1"
                memory: "256Mi"
            limits:
                cpu: "500m"
                memory: "512Mi"

```
now we can change the resources, CPU from 1 to 2, and the pod will not restart.

>> this is manually 


limitations:

- Only CPU and Memory resources can be changes
- Pod QoS class cannot be change
- init containers and Ephemeral containers cannot be resized
- Resources request and limits, cannot be removed once set
- Container memnort limit can't be set below the curret usage
- Windows pods cannot be resized

----

### Vertical Pod Autoscaling (VPA)

 >> not included by default, we must deploy it


- Contain observes metrics
- Add pods resources
- Balances thresholds

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  selector:
    matchLabels:
      app: my-app
  replicas: 1
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
        - name: nginx
          image: nginx
          resources:
            requests:
                cpu: "250m"
            limits:
                cpu: "500m"
```


to deploy it:

`kubectl apply -f https://github.com/kubernetes/autoscaler/releases/latest/download/vertical-pod-autoscaler.yaml`

the VPA consist of 3 components:

- VPA Admission Contoller       >> with the updater get the recommended data and deploy another one with the new size
- VPA Updater                   >> get data from recommender and terminate the pods 
- VPA recommender               >> monitor Mertics server and suggert changes



- we can do it only using a file:

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
    name: my-app
spec:
    targetRed:
        apiVersion: apps/v1
        king: Deployment
        name: my-app
    updatePolicy:
        updateMode: "Auto"
    resourcePolicy:
        containerPolicies:
            - contaienrName: "my-app"
              minAllowed:
                cpu: "250m"
              maxAllowed:
                cpu: "2"
             controllResources: ["cpu"]
```

we have 4 modes for VPA

- off           >> only recomment, does not change anything
- initial       >> only changes in POD creation. not later
- Recreate      >> Evicats pods if usgae goes beyond range
- Auto          >> update existing pods to recommend numbers, but when support for "in-place update of pod resources" is aviable, this mode will be preferred


we can get more info by:

`kubectl describe vpa vpa-name`




| Features | VPA (Vertical Scaling) | HPA (Horizontal Scaling)|
|----------|------------------------|-------------------------|
|Scaling Method| Increase CPU and Memory for existing Pods| Add/remove Pods based on load|
|Pod Behaviour| Restart Pods to apply new resources Values| Keeps Exsiting Pods running|
|Handling Traffix Spikes|No, because scaling restart Pods|Avoids unnecessary Idle pods|
|Best For|Stateful workloads, Memory-heavy apps (BDs, ML workloads)| Webapp, microservices, stateless services|
|Example Use case| Databasea (mysql, PosgtesSql), AL/MI workloads| Webservers (nginx, API services), message queues, microservices|


what is the diffrence between Stateful and stateless services?
!!


----

## Self-healing Applications !!