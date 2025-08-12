#!/bin/bash

echo "Building connectivity tester Docker image..."
docker build -t connectivity-tester:latest .

if [ $? -eq 0 ]; then
    echo "Docker image built successfully!"
    echo "To use in Kubernetes, you may need to:"
    echo "  - Push to a registry: docker tag connectivity-tester:latest <registry>/connectivity-tester:latest"
    echo "  - Or for local testing with kind/minikube: kind load docker-image connectivity-tester:latest"
else
    echo "Failed to build Docker image"
    exit 1
fi