#!/bin/bash

NAMESPACE=${1:-default}

echo "Cleaning up test resources..."
echo "Namespace: $NAMESPACE"
echo "============================="

kubectl delete pod postgres-test-pod -n $NAMESPACE
kubectl delete configmap postgres-config -n $NAMESPACE
kubectl delete secret postgres-secret -n $NAMESPACE

echo "Cleanup complete!"