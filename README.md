# PostgreSQL Connectivity Test Pod for AKS

This test pod helps validate connectivity between a pod in AKS and an Azure Flexible PostgreSQL server.

## Prerequisites

- kubectl configured to connect to your AKS cluster
- Azure Flexible PostgreSQL server details

## Setup

1. **Update the connection details** in `postgres-configmap.yaml`:
   - Replace `<YOUR-POSTGRES-SERVER>` with your PostgreSQL server name
   - Replace `<YOUR-USERNAME>` with your database username

2. **Update the password** in `postgres-secret.yaml`:
   - Replace `<YOUR-PASSWORD>` with your database password

3. **Make scripts executable**:
   ```bash
   chmod +x deploy-and-test.sh cleanup.sh
   ```

## Usage

### Deploy and test connectivity:

#### Linux/macOS/WSL:
```bash
# Deploy to specific namespace
./deploy-and-test.sh <YOUR-POSTGRES-SERVER> <namespace>

# Deploy to default namespace
./deploy-and-test.sh <YOUR-POSTGRES-SERVER>

# Example
./deploy-and-test.sh airia-postgresql-mvp my-namespace
```

#### Windows (Command Prompt/PowerShell):
```cmd
# Deploy to specific namespace
deploy-and-test.bat <YOUR-POSTGRES-SERVER> <namespace>

# Deploy to default namespace
deploy-and-test.bat <YOUR-POSTGRES-SERVER>

# Example
deploy-and-test.bat airia-postgresql-mvp my-namespace
```

The script will:
1. Create namespace if it doesn't exist
2. Deploy the ConfigMap, Secret, and test pod
3. Wait for the pod to be ready
4. Run connectivity tests:
   - DNS resolution
   - Network connectivity (port 5432)
   - PostgreSQL connection test
   - List databases
   - Connect to keycloak database

### Manual testing:
```bash
# Connect to the pod (add -n <namespace> if using custom namespace)
kubectl exec -it postgres-test-pod -n <namespace> -- /bin/sh

# Inside the pod, test with psql
psql -d keycloak

# Or run specific commands
psql -d keycloak -c "SELECT NOW();"
```

### Cleanup:

#### Linux/macOS/WSL:
```bash
# Clean up specific namespace
./cleanup.sh <namespace>

# Clean up default namespace
./cleanup.sh
```

#### Windows:
```cmd
# Clean up specific namespace
cleanup.bat <namespace>

# Clean up default namespace
cleanup.bat
```

## Troubleshooting

If connectivity fails, check:

1. **Network policies**: Ensure no network policies are blocking the connection
2. **Firewall rules**: Verify Azure PostgreSQL firewall allows AKS subnet
3. **SSL/TLS**: Azure PostgreSQL may require SSL. Add to connection if needed:
   ```bash
   psql "sslmode=require"
   ```
4. **Service endpoints/Private endpoints**: Ensure proper network configuration between AKS and PostgreSQL

## Files

- `postgres-test-pod.yaml` - Test pod with PostgreSQL client
- `postgres-configmap.yaml` - Database connection configuration
- `postgres-secret.yaml` - Database password (keep secure!)
- `deploy-and-test.sh` - Deployment and test script (Linux/macOS/WSL)
- `deploy-and-test.bat` - Deployment and test script (Windows)
- `cleanup.sh` - Resource cleanup script (Linux/macOS/WSL)
- `cleanup.bat` - Resource cleanup script (Windows)