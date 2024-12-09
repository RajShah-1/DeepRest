- Installed docker, started using systemctl, installed minikube.
- `minikube start --cpus 4 --memory 8192 --kubernetes-version=v1.20.1`
- `minikube dashboard`
- established a tunnel from minikube dashboard port to the local machine's port 8001
    `ssh -L 8001:127.0.0.1:37211 azureuser@<your-azure-vm-ip`

## Installation

```
sudo apt update
sudo apt install docker.io
sudo systemctl start docker

sudo usermod -aG docker $USER

# log out and log back in for group addition to take place
docker info
docker run hello-world

sudo snap install kubectl --classic
curl -Lo minikube https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64 && chmod +x minikube

echo 'alias minikube="~/minikube"' >> ~/.bashrc
source ~/.bashrc
```

## Mounting a disk in azure

- Find out which disk to attach:
```
lsblk -o NAME,HCTL,SIZE,MOUNTPOINT | grep -i "sd"
```
- Prepare
```
sudo parted /dev/sdc --script mklabel gpt mkpart xfspart xfs 0% 100%
sudo mkfs.xfs /dev/sdc1
sudo partprobe /dev/sdc1
```
- Actually mount the disk
```
mkdir data
sudo mount /dev/sdc1 ~/data
sudo chown -R azureuser:azureuser data/
```

## Symlink /var/lib/docker to ~/data/docker
```
# elevate
sudo su -
mv /var/lib/docker ~/data
ln -snf ~/data/docker /var/lib/docker
exit
```

## Fresh Setup:

```
git clone https://github.com/RajShah-1/DeepRest.git
git checkout local-setup


minikube start --cpus 4 --memory 12288 --kubernetes-version=v1.20.1
minikube mount /run/udev:/run/udev &
kubectl apply -f https://openebs.github.io/charts/openebs-operator.yaml


cd $DEEPREST_DIR/social-network
kubectl apply -f social-network-deploy/k8s-yaml/init/
kubectl cp social-network-deploy/assets/media-frontend/ social-network/centos:/media-config
kubectl cp social-network-deploy/assets/nginx-web-server/ social-network/centos:/nginx-config
kubectl cp social-network-deploy/assets/gen-lua/ social-network/centos:/nginx-config
kubectl delete -f social-network-deploy/k8s-yaml/init/02-frontend-initializer.yaml
# Enable Jaeger first!
# kubectl apply -f social-network-deploy/k8s-yaml/
```

(optional, but recommended for easy metric scrapping, otherwise need to write a custom python metric scrapper daemon)
```
# Install helm and prometheus
sudo snap install helm --classic
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts

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


## Trying to enable Jaegar and friends
```

kubectl create clusterrole jaeger-operator --verb=get,list,watch --resource=namespaces
kubectl create clusterrolebinding jaeger-operator --clusterrole=jaeger-operator --serviceaccount=default:jaeger-operator


kubectl apply -f social-network-deploy/k8s-yaml/tracing/init/

# Wait for a while before running the below!
kubectl apply -f social-network-deploy/k8s-yaml/tracing/run.yaml
kubectl apply -f social-network-deploy/k8s-yaml/ephemeral-mongodb/
kubectl apply -f social-network-deploy/k8s-yaml/
```

## Exposing the services

- Using the load-balancer (tunneling) method
- run `minikube tunnel` in a separate terminal
- Use port-forwarding to port-forward ip:port to localhost:new-port. Example below:
```
ssh -i ~/.ssh/deeprest.pem -L 8082:10.98.32.24:8080 -L 8083:10.107.33.22:8080 azureuser@20.120.245.199
```




127.0.0.1:46521

ssh -i ~/.ssh/deeprest.pem -L 8082:10.109.33.14:8080 -L 8083:10.100.74.229:8080 -L 8084:46521 azureuser@20.120.245.199



- How to expose Jaeger end-points (it does not unfortunately use a load-balancer)
- So Jaeger is currently failing...
```
azureuser@DR-1:~$ kubectl get jaeger jaeger-elasticsearch
NAME                   STATUS   VERSION   STRATEGY     STORAGE         AGE
jaeger-elasticsearch   Failed             production   elasticsearch   112m:
azureuser@DR-1:~$ kubectl get jaeger jaeger-elasticsearch
NAME                   STATUS   VERSION   STRATEGY     STORAGE         AGE
jaeger-elasticsearch   Failed             production   elasticsearch   112m
```

- Useful command to check the logs of jaeger-operator
$ kubectl logs -f deployment/jaeger-operator

- Resolving type-1 error:
```
# Create a ClusterRole
kubectl create clusterrole jaeger-operator --verb=get,list,watch --resource=namespaces
# Create a ClusterRoleBinding
kubectl create clusterrolebinding jaeger-operator --clusterrole=jaeger-operator --serviceaccount=default:jaeger-operator
# Delete the pods for the changes to be reflected in logs
kubectl delete pod -l name=jaeger-operator
# Check logs
kubectl logs -f deployment/jaeger-operator
```
- For type-2, had to change kubernetes version with minikube
minikube start --kubernetes-version=v1.20.1


## Scrapping Prep:

- Get the metric server
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
- Add kubelet-insecure-tls in `kubectl edit deployment metrics-server -n kube-system`
```
args:
  - --cert-dir=/tmp
  - --secure-port=10250
  - --kubelet-preferred-address-types=InternalIP,ExternalIP,Hostname
  - --kubelet-use-node-status-port
  - --metric-resolution=15s
  - --kubelet-insecure-tls
```
- Mount /run/udev to minikube for openebs ndm
 to work
`minikube mount /run/udev:/run/udev`




## Important Notes

- We need to follow some steps to mount the attached disk on azure:
	- Refer: https://learn.microsoft.com/en-us/azure/virtual-machines/windows/attach-managed-disk-portal#initialize-a-new-data-disk
- Jaeger UI is attached to jaeger-elasticsearch-query service. Expose using minikube service and not through kube ingress (kube ingress is setup specific to OpenShift, and does not currently work on minikube)
- Jaeger UI takes some time to load the traces. Be patient. 

## Running the load sim

