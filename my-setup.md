## Azure Setup

Refer [azure-setup.md](./azure-setup.md)

## PACE Exploration (Inactive)

```
(INACTIVE ice cluster does not support containers, only HIVE and PHOENIX support)
ssh rshah647@login-ice.pace.gatech.edu 
cd ~/scratch

# git clone https://github.com/RajShah-1/DeepRest.git
cd DeepRest
cd minikube-openebs/minikube-openiscsi/
```


## Useful Commands:
```
kubectl describe pods --namespace social-network
minikube service list

kubectl logs <pod> -n <namespace>

kubectl config set-context --current --namespace=social-network

# Start a dashboard
minikube dashboard

```

## Local Setup:
### Problems and Solution Attempts

- Translate oc commands to corresponding minikube commands
- Started minikube with `minikube start`
- Enabled OpenEBS
    ```sh
    kubectl apply -f https://openebs.github.io/charts/openebs-operator.yaml
    ```
- cd DeepRest/social-network
- kubectl apply -f social-network-deploy/k8s-yaml/init/
    ```
    namespace/social-network created
    persistentvolumeclaim/compose-post-redis-pvc created
    persistentvolumeclaim/home-timeline-redis-pvc created
    persistentvolumeclaim/media-config-pvc created
    persistentvolumeclaim/media-mongodb-pvc created
    persistentvolumeclaim/nginx-config-pvc created
    persistentvolumeclaim/post-storage-mongodb-pvc created
    persistentvolumeclaim/social-graph-mongodb-pvc created
    persistentvolumeclaim/social-graph-redis-pvc created
    persistentvolumeclaim/url-shorten-mongodb-pvc created
    persistentvolumeclaim/user-mongodb-pvc created
    persistentvolumeclaim/user-timeline-mongodb-pvc created
    persistentvolumeclaim/user-timeline-redis-pvc created
    pod/centos created
    ```
- pod/centos is not working properly though (working now : )) 
- kubectl describe pods --namespace social-network
    - shows errors

- pod/centos is working now! After changing PVCs to use the openebs storageclass
- Ran the following:
    ```
    kubectl cp social-network-deploy/assets/media-frontend/ social-network/centos:/media-config
    kubectl cp social-network-deploy/assets/nginx-web-server/ social-network/centos:/nginx-config
    kubectl cp social-network-deploy/assets/gen-lua/ social-network/centos:/nginx-config
    ```
- Deleted the pod centos with the following command (was that really a good idea? -> Yup, instructions say so):
    ```
    kubectl delete -f social-network-deploy/k8s-yaml/init/02-frontend-initializer.yaml
    ```
- Did the following to get the setup up and running:
	```
	kubectl apply -f social-network-deploy/k8s-yaml/
	```
- One service is still failing:
- Enabling metric-server in minikube:
	```
	minikube addons enable metrics-server
	```

- Cleanup steps:
	```
	$ kubectl delete -f social-network-deploy/k8s-yaml/
	$ kubectl delete pvc --all -n social-network
	$ for pv in $(kubectl get pv -o jsonpath='{.items[*].metadata.name}'); do
		echo $pv
		kubectl patch pv $pv -p '{"metadata":{"finalizers":null}}';
	  done
	$ kubectl delete pv --all --grace-period=0 --force
	# Stop and delete the minikube container
	$ minikube stop
    $ minikube delete
	```
- 

## Fresh Setup:

```
$ minikube start --cpus 4 --memory 4096
$ kubectl apply -f https://openebs.github.io/charts/openebs-operator.yaml
$ cd $DEEPREST_DIR/social-network
$ kubectl apply -f social-network-deploy/k8s-yaml/init/
$ kubectl cp social-network-deploy/assets/media-frontend/ social-network/centos:/media-config
$ kubectl cp social-network-deploy/assets/nginx-web-server/ social-network/centos:/nginx-config
$ kubectl cp social-network-deploy/assets/gen-lua/ social-network/centos:/nginx-config
$ kubectl delete -f social-network-deploy/k8s-yaml/init/02-frontend-initializer.yaml
$ kubectl apply -f social-network-deploy/k8s-yaml/
```

## Debugging Crash-loop in nginx-thrift and media-frontend-ui

- Very helpful command: `kubectl logs nginx-thrift-7b9f58c5cf-8gxgs -n social-network`
```
2024/10/22 00:40:19 [emerg] 1#1: host not found in resolver "dns-default.openshift-dns.svc.cluster.local" in /usr/local/openresty/nginx/conf/nginx.conf:44
nginx: [emerg] host not found in resolver "dns-default.openshift-dns.svc.cluster.local" in /usr/local/openresty/nginx/conf/nginx.conf:44
```

- Oh, we need to change the resolver! we're not using openshift resolver in minikube
- changing that gave a new error about openresty's version being not supported on ARM. Need to do a version upgrade in media-frontend's docker image.
  - This is a bit tricky, it would be interesting/better if we could get this to work with emulation instead of building it for ARM, as jaeger-tracing also fails for ARM, and I was not able to find a fix for that without breaking a lot of other things.


- To do that, we need to rebuild media-frontend image as we're currently using KHChow's image.
- While rebuilding the image, running into the following issue:
```
Processing triggers for libgdk-pixbuf2.0-0:arm64 (2.32.2-1ubuntu1.6) ...
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100   169  100   169    0     0    312      0 --:--:-- --:--:-- --:--:--   312
  0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0
100 5184k  100 5184k    0     0  3621k      0  0:00:01  0:00:01 --:--:-- 3621k
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
  0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0
curl: (51) SSL: certificate subject name (giowm1295.siteground.biz) does not match target host name 'ftp.pcre.org'
```
- Fixed the above error by changing the link from ftp.pcre.org to source-forge with the same pcre version.
```
gcc -O2 -fPIC -I/usr/local/openresty/luajit/include/luajit-2.1 -c lbitlib.c -o lbitlib.o -Ic-api
gcc -shared -o bit32.so -L/usr/local/openresty/luajit/lib lbitlib.o
bit32 5.3.0-1 is now installed in /usr/local/openresty/luajit (license: MIT/X11)

long 2.0.0-0 is now installed in /usr/local/openresty/luajit (license: Apache 2.0)

 ---> Removed intermediate container e27c9c437e00
 ---> 0b92e0354a93
Step 46/50 : COPY lualongnumber /tmp/lualongnumber
 ---> 3227902c85c7
Step 47/50 : RUN cd /tmp/lualongnumber     && make     && make install
 ---> Running in d83866eb9997
gcc -o liblualongnumber.so       -shared -fPIC -g lualongnumber.c longnumberutils.c -I/usr/local/openresty/luajit/include/luajit-2.1
install liblualongnumber.so /usr/local/openresty/lualib
 ---> Removed intermediate container d83866eb9997
 ---> 19d49c9ebea0
Step 48/50 : COPY nginx.conf /usr/local/openresty/nginx/conf/nginx.conf
 ---> 747ce07d6adf
Step 49/50 : COPY nginx.vh.default.conf /etc/nginx/conf.d/default.conf
 ---> c0c499d78964
Step 50/50 : CMD ["/usr/local/openresty/bin/openresty", "-g", "daemon off;"]
 ---> Running in 62741f6a42c5
 ---> Removed intermediate container 62741f6a42c5
 ---> f26926783446
Successfully built f26926783446
```

- Tell minikube about this local image.
```
minikube image load local:media-frontend
```
There's one error left in media-frontend:

```
$ kubectl logs media-frontend-5f585b847-6d5mx -n social-network
2024/10/22 04:57:19 [error] 1#1: Failed to load tracing library /usr/local/lib/libjaegertracing_plugin.so: /usr/local/lib/libjaegertracing_plugin.so: cannot open shared object file: No such file or directory
nginx: [error] Failed to load tracing library /usr/local/lib/libjaegertracing_plugin.so: /usr/local/lib/libjaegertracing_plugin.so: cannot open shared object file: No such file or directory
```
- Building the image for AMD 64...
```
DOCKER_BUILDKIT=0 docker build --no-cache --platform linux/amd64 -t media-frontend-amd:local .
```
- Still seeing the below in the build output!
```
Step 33/50 : RUN cd /usr/local/lib     && curl -fSL https://github.com/jaegertracing/jaeger-client-cpp/releases/download/v${JAEGER_TRACING_VERSION}/libjaegertracing_plugin.linux_amd64.so -o libjaegertracing_plugin.so
 ---> [Warning] The requested image's platform (linux/amd64) does not match the detected host platform (linux/arm64/v8) and no specific platform was requested
 ---> Running in c92f35be9a92
 ```


## Trying to run docker with emulation!

export DOCKER_DEFAULT_PLATFORM=linux/amd64
minikube delete --all --purge
minikube start --cpus 4 --memory 4096 --base-image='gcr.io/k8s-minikube/kicbase:v0.0.45'

> Running the above commands lead to the following error.

💣  Error starting cluster: wait: /bin/bash -c "sudo env PATH="/var/lib/minikube/binaries/v1.31.0:$PATH" kubeadm init --config /var/tmp/minikube/kubeadm.yaml  --ignore-preflight-errors=DirAvailable--etc-kubernetes-manifests,DirAvailable--var-lib-minikube,DirAvailable--var-lib-minikube-etcd,FileAvailable--etc-kubernetes-manifests-kube-scheduler.yaml,FileAvailable--etc-kubernetes-manifests-kube-apiserver.yaml,FileAvailable--etc-kubernetes-manifests-kube-controller-manager.yaml,FileAvailable--etc-kubernetes-manifests-etcd.yaml,Port-10250,Swap,NumCPU,Mem,SystemVerification,FileContent--proc-sys-net-bridge-bridge-nf-call-iptables": Process exited with status 1
stdout:
[init] Using Kubernetes version: v1.31.0
[preflight] Running pre-flight checks

stderr:
W1022 18:33:21.530622    1916 common.go:101] your configuration file uses a deprecated API spec: "kubeadm.k8s.io/v1beta3" (kind: "ClusterConfiguration"). Please use 'kubeadm config migrate --old-config old.yaml --new-config new.yaml', which will write the new, similar spec using a newer API version.
W1022 18:33:21.531049    1916 common.go:101] your configuration file uses a deprecated API spec: "kubeadm.k8s.io/v1beta3" (kind: "InitConfiguration"). Please use 'kubeadm config migrate --old-config old.yaml --new-config new.yaml', which will write the new, similar spec using a newer API version.
        [WARNING Swap]: swap is supported for cgroup v2 only. The kubelet must be properly configured to use swap. Please refer to https://kubernetes.io/docs/concepts/architecture/nodes/#swap-memory, or disable swap on the node
        [WARNING Service-Kubelet]: kubelet service is not enabled, please run 'systemctl enable kubelet.service'
error execution phase preflight: [preflight] Some fatal errors occurred:
        [ERROR KubeletVersion]: couldn't get kubelet version: cannot execute 'kubelet --version': executable file not found in $PATH
[preflight] If you know what you are doing, you can make a check non-fatal with `--ignore-preflight-errors=...`
To see the stack trace of this error execute with --v=5 or higher

## Trying to enable Jaegar and stuff
kubectl apply -f social-network-deploy/k8s-yaml/tracing/init/
kubectl apply -f social-network-deploy/k8s-yaml/tracing/run.yaml
kubectl apply -f social-network-deploy/k8s-yaml/ephemeral-mongodb/
kubectl apply -f social-network-deploy/k8s-yaml/


## Could be useful in future; not working right now
kubectl expose deployment nginx-thrift --type=NodePort --name=nginx-thrift-service -n social-network
kubectl expose deployment media-frontend --type=NodePort --name=media-frontend-service -n social-network

minikube service nginx-thrift-service -n social-network
minikube service media-frontend-service -n social-network



## Links

https://gatech.service-now.com/home?id=kb_article_view&sysparm_article=KB0043494