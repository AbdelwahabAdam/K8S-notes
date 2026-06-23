# Kustomize
## Kustomize Problem Statement and Ideology

creating seperate yaml file for each env (dev-stg-prod) is not ideal

base ... overlays

base.yaml
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
spec:
  replicas: 1
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      name: nginx-2
      labels:
        app: nginx
    spec:
      containers:
        - name: nginx
          image: nginx
```

overlays/dev
```yaml
spec:
  replicas: 1
```

overlays/stg
```yaml
spec:
  replicas: 2
```

overlays/prod
```yaml
spec:
  replicas: 5
```


Folder Strucute

- k8s/
    - base/
        - kustomization.yaml
        - nginx-depl.yaml
        - service.yaml
        - redis.depl.yaml
    - overlays/
        - dev/
            - kustomization.ymal
            - config-map.yaml
        - stg/
            - kustomization.ymal
            - config-map.yaml
        - prod/
            - kustomization.ymal
            - config-map.yaml



- kustomize coms built-in with kuectl 


---------

## Kustomize vs Helm

## Installation/Setup Kustomize

`curl -s "https://raw.githubusercontent.com/kubernetes-sigs/kustomize/master/hack/install_kustomize.sh" | bash`

## The kustomization.yaml File

ex:


- k8s/
    - kustomization.yaml
    - nginx-deployment.yaml
    - nginx-service.yaml


in kustomization.yaml

```yaml
resources:
    nginx-deployment.yaml
    nginx-service.yaml
commonLabels:
    company: hopa
```


`kustomize build k8s/`  >> applies a lable to all resourses from resources and commonLabels
--------
## Kustomize Output



`kustomize build k8s/ | kubectl apply -f -`


to delete resources 

`kustomize build k8s/ | kubectl delete -f -`

------------
## Kustomize ApiVersion and Kind

```yaml



```
--------------------
## Managing Directories

- k8s/
    - api-deployment.yaml
    - api-service.yaml
    - db-deployment.yaml
    - db-service.yaml

- k8s/
    - api/
        - api-deployment.yaml
        - api-service.yaml
    - db/
        - db-deployment.yaml
        - db-service.yaml

to apply that
`kubectl apply -f k8s/api/`
`kubectl apply -f k8s/db/`

or we can use kustomize

- k8s/
    - kustomization.yaml
    - api/
        - api-deployment.yaml
        - api-service.yaml
    - db/
        - db-deployment.yaml
        - db-service.yaml

```yaml
resources:
    - api/api-deployment.yaml
    - api/api-service.yaml
    - db/db-deployment.yaml
    - db/db-service.yaml
```
to apply now: (one command)
`kustomize build k8s/ | kubectl apply -f -`
or
`kubectl apply -k ./k8s/`

and we can also specify the directory 

```yaml
resources:
    - api/
    - db/
```
and in each one we create another kustomization.yaml that contain the resources

--------

## Common Transformers

- allow us to make conf changes to all yaml files (all components)



we have 4 types:
- CommonLabel               >> adds a label to all kubernates resources
- namePrefix/Suffix         >> adds a common prefix-suffix to all resources names
- Namespace                 >> adds a common namespace to all resources
- commonAnnotations         >> adds an annotation to all resources


```yaml
commonLabels:
    ownername: hopa


namespace: lap

namePrefix: start-
nameSuffix: -end

commonAnnotations:
    branch: master
```

---------------------
## Image Transformers

modify an image in all resources file

```yaml
images:
    - name: nginx
      newName: haproxy
```
nginx >> haproxy

```yaml
images:
    - name: nginx
      newTag: 2.4
```
nginx >> nginx:2.4


```yaml
images:
    - name: nginx
      newName: haproxy
      newTag: 2.4
```
nginx >> haproxy:2.4

----------
## Patches Intro
- another method to modifying kubernates configs
- unlike common transoformers patches provide a more surgical approach to targeting one or more specific sections in kubernaters resources

- to create a patch we need 3 parametars
1. operation type: add, remove, replace
2. Target: what resource should this patch be applien on
    - Kind
    - Version/Group
    - Name
    - Namespace
    - label/selector
    - Annotation selector
3. value



kustomization.yaml
```yaml
patches:
    - taget: 
        kind: Deployment
        name: api-deployment
      patch: |-
            - op: replace
            path: /metadata/name
            value: web-deplyment
```
two type of patches:

- JSON 6902 Patch
- strategic merge patch

strategic merge patch:
```yaml
patches:
    - patch: |- 
        apiVersion: apps/v1
        kind: Deployment
        metadata:
            name: myapp-deployment
        spec:
            replicas: 6
```
--------------
## Different Types of Patches

we have two way to define a patch

- Inline

- Separate file


```yaml
patches:
    - path: replica-path.yaml
      target:
        kind: Deployment
        name: nginx-deployment
```

replica-path.yaml:
```yaml
- op: replace
    path: /metadata/name
    value: web-deplyment
```


------------

## Overlays

ENV:
1. dev
2. stg
3. prod

- k8s/
    - base/
        - kustomization.yaml
        - nginx-depl.yaml
        - service.yaml
        - redis.depl.yaml
    - overlays/
        - dev/
            - kustomization.ymal
            - config-map.yaml
        - stg/
            - kustomization.ymal
            - config-map.yaml
        - prod/
            - kustomization.ymal
            - config-map.yaml


/base/nginx-depl.yaml

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
    name: nginx-deployment
spec:
    replicas: 1
```

base/kustomization
```yaml
resources:
    - nginx-depl.yaml
    - service.yaml
    - redis-depl.yaml
```

overlays/dev/kustomization
```yaml
bases:
    - ../../base
patch: |-
    - op: replace
      path: /spec/replicas
      value: 2
```


overlays/prod/kustomization
```yaml
bases:
    - ../../base
patch: |-
    - op: replace
      path: /spec/replicas
      value: 3
```

NOTE: we cam also add a new resource in /prod

---------

## Components

- k8s/
    - base/
    - dev/          >> import db
    - premium/      >> import db
    - self hosted/  >> import caching
    - components/
        - caching/
        - db/






































































