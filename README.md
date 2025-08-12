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
# Show help
./deploy-and-test.sh --help

# Basic deployment (automated tests)
./deploy-and-test.sh

# Deploy with manual connectivity tests
./deploy-and-test.sh --manual-tests --server <YOUR-POSTGRES-SERVER>

# Deploy to specific namespace
./deploy-and-test.sh --namespace my-namespace

# Deploy with PVC testing enabled
./deploy-and-test.sh --enable-pvc

# Example with all options
./deploy-and-test.sh --namespace prod --server airia-postgresql-mvp --manual-tests --enable-pvc
```

#### Windows (Command Prompt/PowerShell):
```cmd
# Show help
deploy-and-test.bat --help

# Basic deployment (automated tests)
deploy-and-test.bat

# Deploy with manual connectivity tests
deploy-and-test.bat --manual-tests --server <YOUR-POSTGRES-SERVER>

# Deploy to specific namespace
deploy-and-test.bat --namespace my-namespace

# Deploy with PVC testing enabled
deploy-and-test.bat --enable-pvc

# Example with all options
deploy-and-test.bat --namespace prod --server airia-postgresql-mvp --manual-tests --enable-pvc
```

### Deployment Options:
- `--namespace, -n <namespace>` - Kubernetes namespace (default: default)
- `--server, -s <server>` - PostgreSQL server name (required for manual tests)
- `--enable-pvc` - Enable persistent volume claim testing
- `--manual-tests` - Run manual connectivity tests instead of automated tests
- `--help, -h` - Show usage information

The script will:
1. Build the connectivity tester Docker image if not present
2. Create namespace if it doesn't exist
3. Deploy the ConfigMap, Secret, Azure services secret, and test pod
4. Wait for the pod to be ready
5. Run either:
   - **Automated tests** (default): Shows continuous pod logs with all test results
   - **Manual tests** (with --manual-tests and --server): Runs specific connectivity tests:
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

## Extended Testing with Azure Services (Optional)

The test pod supports optional connectivity tests for Azure services:
- Azure OpenAI
- Azure Document Intelligence
- Persistent Volume Claims (PVC)

### Setup for Azure Service Tests:

1. **Configure AI services** in `azure-services-secret.yaml` (optional):
   - For Azure OpenAI:
     - Set `azure-openai-endpoint` (e.g., https://your-resource.openai.azure.com/)
     - Set `azure-openai-api-key`
     - Set `azure-openai-deployment` (e.g., gpt-35-turbo)
   - For Azure Document Intelligence:
     - Set `azure-docintel-endpoint` (e.g., https://your-resource.cognitiveservices.azure.com/)
     - Set `azure-docintel-api-key`
   - For Ollama:
     - Set `ollama-endpoint` (e.g., http://your-ollama-server:11434)
     - Set `ollama-model` (e.g., llama2, mistral, codellama)
   - For OpenAI-compatible endpoints:
     - Set `openai-compatible-endpoint` (e.g., https://api.openai.com, https://api.together.xyz/v1)
     - Set `openai-compatible-api-key` (optional for some self-hosted endpoints)
     - Set `openai-compatible-model` (e.g., gpt-3.5-turbo, meta-llama/Llama-2-7b-chat-hf)
   - For Custom Hostname Testing:
     - Set `custom-host-1` through `custom-host-10` (e.g., internal-api.company.com, https://api.example.com)
     - Set `custom-host-1-name` through `custom-host-10-name` for display names (e.g., "Internal API", "My Service")

2. **Deploy with automated tests** (includes Azure service tests if configured):
   ```bash
   ./deploy-and-test.sh
   ```

The automated tests will:
- Always test PostgreSQL connectivity (required)
- Test Azure OpenAI if configured (optional)
- Test Azure Document Intelligence if configured (optional)
- Test Ollama if configured (optional)
- Test OpenAI-compatible endpoints if configured (optional)
- Test custom hostnames if configured (optional)
- Test Persistent Volume Claim if enabled with --enable-pvc (optional)
- Test connectivity to external services (optional):
  - Office 365 (login.microsoftonline.com)
  - Google Drive (accounts.google.com)
  - Notion (notion.so)
  - Box (account.box.com)
  - Dropbox (dropbox.com)
  - ServiceNow (servicenow.com)
  - Amazon S3 (aws.amazon.com/s3)
  - Confluence (atlassian.com/software/confluence)
- Continue running for manual testing after automated tests complete

### Custom Hostname Testing:

You can configure up to 10 custom hostnames to test connectivity to internal APIs, custom services, or specific external endpoints:

**Examples:**
```yaml
# In azure-services-secret.yaml
custom-host-1: "internal-api.company.com"
custom-host-1-name: "Internal API"
custom-host-2: "https://api.example.com/health"
custom-host-2-name: "External API Health Check"
custom-host-3: "my-service.internal:8080"
custom-host-3-name: "Internal Microservice"
```

**Features:**
- Supports hostnames, URLs with full paths, and custom ports
- Automatically tries HTTPS first, then HTTP if HTTPS fails
- Handles SSL errors gracefully
- Provides detailed status information for each host

**To disable custom hostname tests:**
```bash
kubectl set env pod/postgres-test-pod TEST_CUSTOM_HOSTNAMES=false -n <namespace>
```

### Disabling External Service Tests:

If you want to disable the external service connectivity tests (e.g., in restricted environments):

```bash
# Set environment variable before deployment
kubectl set env pod/postgres-test-pod TEST_EXTERNAL_SERVICES=false -n <namespace>
```

### Testing Persistent Volume Claims (PVC):

To test PVC functionality in your AKS cluster:

1. **Configure storage class** in `pvc-configmap.yaml` (optional):
   - Default uses `managed-csi` (Azure Disk CSI driver)
   - Other options: `managed-csi-premium`, `azurefile-csi`, `azurefile-csi-premium`

2. **Deploy with PVC testing enabled**:
   ```bash
   # Linux/macOS/WSL
   ./deploy-and-test.sh --enable-pvc
   
   # Windows
   deploy-and-test.bat --enable-pvc
   ```

This will:
- Create a 1GB PVC using the configured storage class
- Mount it to the pod at `/mnt/test-storage`
- Test read/write permissions
- Check storage capacity
- Create a persistence marker file for validation

## Files

- `postgres-test-pod.yaml` - Original test pod with PostgreSQL client only
- `postgres-test-pod-extended.yaml` - Extended test pod with Azure service tests
- `postgres-configmap.yaml` - Database connection configuration
- `postgres-secret.yaml` - Database password (keep secure!)
- `azure-services-secret.yaml` - Azure service credentials (optional)
- `deploy-and-test.sh` - Deployment and test script (Linux/macOS/WSL)
- `deploy-and-test.bat` - Deployment and test script (Windows)
- `cleanup.sh` - Resource cleanup script (Linux/macOS/WSL)
- `cleanup.bat` - Resource cleanup script (Windows)
- `Dockerfile` - Custom test container image
- `requirements.txt` - Python dependencies
- `test_connectivity.py` - Python script for connectivity tests
- `build-image.sh` - Docker image build script (Linux/macOS/WSL)
- `build-image.bat` - Docker image build script (Windows)
- `test-pvc.yaml` - Persistent Volume Claim for storage testing
- `pvc-configmap.yaml` - PVC storage class configuration