# NEtworking

### Prerequisite Switching, Routing, Gateways CNI in kubernetes

1. Switching and routing
- switching
- routing
- Default Gateway

2. DNS
- DNS configuration on linux
- CoreDNS intro
3. Network Namespaces
4. Docker Networking


---------------
- interface
- ipv4 ipv6
- ip add, subnet mask
- routing table, ARP table
- DNS and default DNS
- Domain Name
- Records Types  (A, AAAA, CNAME) >> nslookup, dig
- CoreDNS
- default dns port port 53
-  /etc/hosts
- to list interface: `ip link`
- arp table:
`arp`


Network Namespaces
- process Namespaces
- create network NS `ip netns add red`
- to list them: `ip netns`
- to find interfaces inside the namespace
`ip netns exec red ip link`
or
`ip -n red lin`

to link two namespaces!

`ip link add veth-red rtype ceth peer name veth-blue`
`ip link set veth-red netns red`
`ip link set veth-blue netns blue`
`ip -n red addr add 192.168.15.1 dev veth-red`
`ip -n blue addr add 192.168.15.2 dev veth-blue`
`ip -n red link set veth-red up`
`ip -n blue link set veth-blue up`


Linux Bridge
- create new interface type Bridge
`ip link add v-net-0 type bridge`

- up
`ip link set dev v-net-0 up`


--------
## Docker Networking


when we create a container, it is created with interface eth0 with ip: 192.168.1.10

network has some types:

- None: no one can reach it from outside world, and the container can't reach any one there too
- HOST: the container is attached to the host machine. (ex, if we deployed a webpp on port 80 in the container, then it will be avialable in port 80 in the host machine too)
> if we run another process that lisiten on the same port, then it will not work.
- Bridge: intrenal private network is created, the host and the container are attached to the same network.
> network ip: 172.17.0.0 (each device connected to the network, get his own private netwrork ip)

---------
## CNI (Container Networking Interface)

- Brdige
- VLAN
- IPVLAN
- MACVLAN
- WINDOWS
- HOSTLOCAL
- DHCP

- flannel
- clilium
- vmware nsx
- calico

docker has it's own CNM (container Network Model)

-----------------

## Cluster Networking

K8s has at least two nodes, master and worker nodes

each node must have at least 1 interface connected to a network and each interface must have an address configured, the host must have a unique hostname and mac address

>> NOTE: make sure to take care of that, if you clone VMS to create the nodes 

- Master should accept connection on 6443 port (for kube-apiserver)
- kubelet lisiten on port (10250) on both master and worker
- kube scheduler on master lisiten on port (10259)
- kube controll manager on master lisiten on port (10257)
- services on worker nodes are exported on ports from (30000-32767)
- etcd server listen on (2379)
- if we have multiple masters, all of the above must be open, and port (23780) for etcd client to connect to each other

-------------------

## Commands:

- `ip link`     >> interfaces
- `ip addr`     >> get ip address
- `ip route`
- `ip addr add 192.168.1.10/24 dev eth0`
- `ip route add 192.168.1.0/24 via 192.168.2.1`
- `netstat -plant`
- `arp`
- `route`
- `cat /proc/sys/net/ipv4/ip_forward`




----------------
## Pod Networking

cni!

add interface 
add routing?

----------------
## CNI in kubernetes


how to configurte contaienr run time to use a plugin?

ex plugin:
- flannel
- cilium
- nsx-t
all pulgin are installed on /opt/cni/bin
and that's where the containerruntime find the plugins


plugin configuration files are located in:
/etc/cni/net.d
ex:
- bridge.conflist
- flannel.conflist

CNI contain:

1- Create Veth pair
2- attach veth pair
3- assign IP address
4- Being Up Interface


-----------
## ipam (ip address mangments)

-------------
## Service Networking




































