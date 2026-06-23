# Helm


what helm is?
is a packet manager, it make us treat our k8s apps, as apps no as an objects

- `helm install workpress`
- single location to change anything
- upgrade in single command
- `help upgrade wordpress`
- `help rollback wordpress`
- `help uninstall wordpress`

--------

## Installation and Configuration

`sudo snap install heml --classic`
`curl https:`



--------
## A quick note about Helm2 vs Helm3

diffrences:
helm 2

- helm cli
- we had to install tiller
- tiller had Root permissions (that was not good)
- any update or roolback create a new revision

helm3 
- no tiller
- no middle layer
- 3-way stategic metric (see the live states-even if it is not dont by helm-)
- preserve live state on upgrade
-----------------
## Helm Components

- chart >> files contain all instuction needed
we can find helm charts online too (same as docker hub)

- metadata (data about data!)
save the metadata as secret on the cluster

Charts: 
a collection of files, and they contain all instructions that helm needs to know and be able to create the collection of objects that we need in k8s cluster



`helm install <relase-name> <chart-name>`
`helm install my-site bitnami/wordpress`

Helm Repositories
- Appscode
- TrueCharts
- Bitnami
- Community operators

and all list theier charts in helm app (artifact hub)


any chart contain chart.yaml

```yaml
apiVersion: v1
appVersion: 5.8.1           ## app version
version: 12.1.27            ## chart version
name: wordpress
description: 
type: application
dependencies:
    - condition: mariadb.enabled
      name: mariadb
      repository:  https://charts.bitnami.com/bitnami
      version: 9.x.x
keywords:
    - application
    - blog
    - wordpress
maintainers:
    - email: 
      name:
home:
icon: 
```
helm search hub wordpress

deploy the app:

- helm repo add bitnami https://charts.bitnami.com/bitnami
- helm install my-release bitnami/workpress


the chart is deployed as release

`helm list`

- delete app
`helm unistall my-release`

- `helm repo`
add, remove, update a repo

- `helm repo list`

- `helm repo update`

--------------

## Customizing chart parameters


`helm install --set wordpressBlogName="helm tutorials" my-release bitnami/wordpress `
`helm install --values custom-values.yaml my-release bitnami/wordpress `

```yaml
wordpressBlogName: "helm tutorials"

```

to get all files and edit it.
`helm pull bitnami/wordpress`
`helm pull --untar bitnami/wordpress`

`helm install my-release ./wordpress`
--------------------
## Lifecycle management with Helm
when we rum helm install, we create a new release


`helm list`  to list all relases

`helm history nginx-release`



chart hooks!












