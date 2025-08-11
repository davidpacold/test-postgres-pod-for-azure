#!/bin/bash

# Check if namespace is provided as second argument
NAMESPACE=${2:-default}
SERVER=$1

if [ -z "$SERVER" ]; then
    echo "Usage: ./deploy-and-test.sh <postgres-server> [namespace]"
    echo "Example: ./deploy-and-test.sh airia-postgresql-mvp my-namespace"
    exit 1
fi

echo "Deploying PostgreSQL connectivity test pod to AKS..."
echo "Namespace: $NAMESPACE"
echo "================================================"

# Create namespace if it doesn't exist
echo "0. Ensuring namespace exists..."
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Apply the configurations
echo "1. Creating ConfigMap..."
kubectl apply -f postgres-configmap.yaml -n $NAMESPACE

echo "2. Creating Secret..."
kubectl apply -f postgres-secret.yaml -n $NAMESPACE

echo "3. Creating test pod..."
kubectl apply -f postgres-test-pod.yaml -n $NAMESPACE

# Wait for pod to be ready
echo "4. Waiting for pod to be ready..."
kubectl wait --for=condition=ready pod/postgres-test-pod -n $NAMESPACE --timeout=60s

echo ""
echo "Pod deployed! Running connectivity tests..."
echo "============================================"

# Test DNS resolution
echo ""
echo "Test 1: DNS Resolution"
echo "----------------------"
kubectl exec postgres-test-pod -n $NAMESPACE -- nslookup $SERVER.postgres.database.azure.com

# Test network connectivity
echo ""
echo "Test 2: Network Connectivity (ping alternative using nc)"
echo "---------------------------------------------------------"
kubectl exec postgres-test-pod -n $NAMESPACE -- nc -zv $SERVER.postgres.database.azure.com 5432

# Test PostgreSQL connection
echo ""
echo "Test 3: PostgreSQL Connection"
echo "------------------------------"
kubectl exec postgres-test-pod -n $NAMESPACE -- psql -c "SELECT version();"

echo ""
echo "Test 4: List databases"
echo "----------------------"
kubectl exec postgres-test-pod -n $NAMESPACE -- psql -c "\l"

echo ""
echo "Test 5: Connect to keycloak database"
echo "-------------------------------------"
kubectl exec postgres-test-pod -n $NAMESPACE -- psql -d keycloak -c "SELECT current_database(), current_user, inet_server_addr(), inet_server_port();"

echo ""
echo "================================================"
echo "Tests complete!"
echo ""
echo "To manually connect to the database, run:"
echo "kubectl exec -it postgres-test-pod -n $NAMESPACE -- psql -d keycloak"
echo ""
echo "To clean up resources, run:"
echo "./cleanup.sh $NAMESPACE"