#!/bin/bash

echo "Deploying PostgreSQL connectivity test pod..."
echo "============================================"

# Default values
NAMESPACE="default"
ENABLE_PVC=false
MANUAL_TESTS=false
POSTGRES_SERVER=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --namespace|-n)
            NAMESPACE="$2"
            shift 2
            ;;
        --server|-s)
            POSTGRES_SERVER="$2"
            shift 2
            ;;
        --enable-pvc)
            ENABLE_PVC=true
            shift
            ;;
        --manual-tests)
            MANUAL_TESTS=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --namespace, -n <namespace>  Kubernetes namespace (default: default)"
            echo "  --server, -s <server>        PostgreSQL server name (for manual tests)"
            echo "  --enable-pvc                 Enable PVC testing"
            echo "  --manual-tests               Run manual connectivity tests"
            echo "  --help, -h                   Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown parameter: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo "Namespace: $NAMESPACE"

# Check if image exists locally
if ! docker images | grep -q "connectivity-tester.*latest"; then
    echo "Building connectivity tester image first..."
    ./build-image.sh
fi

# Create namespace if it doesn't exist
echo "Ensuring namespace exists..."
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Apply configurations
echo "Applying PostgreSQL ConfigMap..."
kubectl apply -f postgres-configmap.yaml -n $NAMESPACE

echo "Applying PostgreSQL Secret..."
kubectl apply -f postgres-secret.yaml -n $NAMESPACE

echo "Applying Azure Services Secret..."
kubectl apply -f azure-services-secret.yaml -n $NAMESPACE

# Apply PVC if enabled
if [ "$ENABLE_PVC" = true ]; then
    echo "PVC testing enabled - creating PVC..."
    kubectl apply -f test-pvc.yaml -n $NAMESPACE
    kubectl apply -f pvc-configmap.yaml -n $NAMESPACE
    
    # Wait for PVC to be bound
    echo "Waiting for PVC to be bound..."
    kubectl wait --for=condition=Bound pvc/test-pvc --timeout=60s -n $NAMESPACE
    
    # Deploy pod with PVC enabled
    kubectl apply -f postgres-test-pod-extended.yaml -n $NAMESPACE
    kubectl set env pod/postgres-test-pod TEST_PVC=true -n $NAMESPACE
else
    echo "PVC testing disabled (use --enable-pvc to enable)"
    kubectl apply -f postgres-test-pod-extended.yaml -n $NAMESPACE
fi

# Wait for pod to be ready
echo "Waiting for pod to be ready..."
kubectl wait --for=condition=Ready pod/postgres-test-pod --timeout=60s -n $NAMESPACE

if [ $? -eq 0 ]; then
    echo "Pod is ready!"
    echo ""
    
    if [ "$MANUAL_TESTS" = true ] && [ -n "$POSTGRES_SERVER" ]; then
        echo "Running manual connectivity tests..."
        echo "===================================="
        
        echo ""
        echo "Test 1: DNS Resolution"
        echo "----------------------"
        kubectl exec postgres-test-pod -n $NAMESPACE -- nslookup ${POSTGRES_SERVER}.postgres.database.azure.com
        
        echo ""
        echo "Test 2: Network Connectivity"
        echo "----------------------------"
        kubectl exec postgres-test-pod -n $NAMESPACE -- nc -zv ${POSTGRES_SERVER}.postgres.database.azure.com 5432
        
        echo ""
        echo "Test 3: PostgreSQL Connection"
        echo "-----------------------------"
        kubectl exec postgres-test-pod -n $NAMESPACE -- psql -c "SELECT version();"
        
        echo ""
        echo "Test 4: List databases"
        echo "----------------------"
        kubectl exec postgres-test-pod -n $NAMESPACE -- psql -c "\l"
        
        echo ""
        echo "Test 5: Connect to keycloak database"
        echo "------------------------------------"
        kubectl exec postgres-test-pod -n $NAMESPACE -- psql -d keycloak -c "SELECT current_database(), current_user, inet_server_addr(), inet_server_port();"
        
        echo ""
        echo "================================================"
        echo "Manual tests complete!"
        echo ""
        echo "To manually connect to the database, run:"
        echo "kubectl exec -it postgres-test-pod -n $NAMESPACE -- psql -d keycloak"
    else
        echo "Viewing automated test results..."
        echo "================================="
        kubectl logs postgres-test-pod -n $NAMESPACE -f
    fi
else
    echo "Pod failed to become ready"
    echo "Pod status:"
    kubectl describe pod postgres-test-pod -n $NAMESPACE
fi

echo ""
echo "To clean up resources, run:"
echo "./cleanup.sh $NAMESPACE"