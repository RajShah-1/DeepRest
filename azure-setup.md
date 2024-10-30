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


## Fresh Setup:

```
alias minikube="~/minikube"
```

```
minikube start --cpus 4 --memory 8192 --kubernetes-version=v1.20.1
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


## Trying to enable Jaegar and stuff
```
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

- How to expose Jaeger end-points (it does not unfortunately use a load-balancer)
- So Jaeger is currently failing...
azureuser@DR-1:~$ kubectl get jaeger jaeger-elasticsearch
NAME                   STATUS   VERSION   STRATEGY     STORAGE         AGE
jaeger-elasticsearch   Failed             production   elasticsearch   112m:
azureuser@DR-1:~$ kubectl get jaeger jaeger-elasticsearch
NAME                   STATUS   VERSION   STRATEGY     STORAGE         AGE
jaeger-elasticsearch   Failed             production   elasticsearch   112m

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



## Debugging Jaeger failure

