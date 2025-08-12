# PostgreSQL Connectivity Test Pod for AKS

This test pod helps validate connectivity between a pod in AKS and an Azure Flexible PostgreSQL server.

## Prerequisites

- kubectl configured to connect to your AKS cluster
- Azure Flexible PostgreSQL server details
- Docker installed and running (for building custom test image)

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
   - For Secondary PostgreSQL Server:
     - Set `postgres-host-secondary` (e.g., replica-server.postgres.database.azure.com)
     - Set `postgres-port-secondary` (default: 5432)
     - Set `postgres-database-secondary` (optional, defaults to primary database)
     - Set `postgres-user-secondary` (optional, defaults to primary user)  
     - Set `postgres-password-secondary` (optional, defaults to primary password)
   - For Custom Hostname Testing:
     - Set `custom-host-1` through `custom-host-10` (e.g., internal-api.company.com, https://api.example.com)
     - Set `custom-host-1-name` through `custom-host-10-name` for display names (e.g., "Internal API", "My Service")

2. **Deploy with automated tests** (includes Azure service tests if configured):
   ```bash
   ./deploy-and-test.sh
   ```

The automated tests will:
- Always test Primary PostgreSQL connectivity (required)
  - Lists all available databases with sizes
  - Shows installed extensions for each accessible database
  - Displays available (but not installed) extensions
- Test Secondary PostgreSQL if configured (optional)
  - Same database and extension discovery as primary
  - Useful for primary/replica setups or multiple database servers
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
  - Atlassian (id.atlassian.com/login)
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

## Docker Image Build Requirements

The connectivity tester uses a custom Docker image that must be built before deployment. The build scripts handle this automatically, but you should be aware of the requirements:

### **System Requirements:**
- **Docker installed and running** - Docker Desktop (Windows/Mac) or Docker Engine (Linux)
- **Internet access** - To download base image and dependencies
- **Sufficient disk space** - ~200MB for image and build cache
- **Docker permissions** - User must be able to run Docker commands

### **Required Files:**
These files must be present in the project directory for the build to succeed:
- `Dockerfile` - Container definition
- `requirements.txt` - Python dependencies
- `test_connectivity.py` - Main connectivity test script

### **Architecture Considerations:**

**For local clusters (kind/minikube):**
```bash
# Build and load into cluster
./build-image.sh
kind load docker-image connectivity-tester:latest
```

**For cloud clusters (AKS/EKS/GKE):**
```bash
# Build for correct architecture (if on Apple Silicon)
docker build --platform linux/amd64 -t connectivity-tester:latest .

# Push to container registry
docker tag connectivity-tester:latest your-registry/connectivity-tester:latest
docker push your-registry/connectivity-tester:latest

# Update pod YAML to use your registry image
```

### **Corporate Network Issues:**
If you're behind a corporate firewall:
- Configure Docker to use corporate proxy settings
- Use internal container registry instead of Docker Hub
- Contact IT about accessing python package repositories (PyPI)

### **Dependencies Installed:**
The image includes:
- `python:3.11-slim` base image (Debian-based)
- `postgresql-client` - For PostgreSQL connectivity
- `curl` - For HTTP requests  
- Python packages: `psycopg2-binary`, `requests`, `urllib3`

## Container Image Versioning

The project uses automated Docker image builds via GitHub Actions with intelligent version tagging:

### **Automatic Image Tags:**

**Latest Development:**
- `ghcr.io/davidpacold/connectivity-tester:latest` - Always the newest version from main branch

**Version Releases:**
When you create a git tag like `v1.2.3`, multiple image tags are automatically created:
- `ghcr.io/davidpacold/connectivity-tester:1.2.3` - Exact version
- `ghcr.io/davidpacold/connectivity-tester:1.2` - Latest patch in 1.2.x series  
- `ghcr.io/davidpacold/connectivity-tester:1` - Latest minor in 1.x series

### **Creating Version Releases:**

```bash
# Create and push a version tag
git tag v1.0.0
git push origin v1.0.0

# This triggers automatic build of all version tags
# Available immediately after build completes
```

### **Using Specific Versions:**

**For development/testing (default):**
```yaml
image: ghcr.io/davidpacold/connectivity-tester:latest
imagePullPolicy: Always
```

**For production deployments:**
```yaml
image: ghcr.io/davidpacold/connectivity-tester:1.0.0  # Pin to exact version
imagePullPolicy: IfNotPresent
```

### **Version History:**
All built versions remain available indefinitely in GitHub Container Registry, allowing:
- **Rollbacks** to previous versions if issues arise
- **Testing** with specific versions
- **Staging** environments with pinned versions

### **Automatic Builds:**
Images are automatically built when you:
- Push changes to `main` branch (creates new `latest`)
- Push version tags like `v1.0.0` (creates version-specific tags)
- Modify Docker-related files (`Dockerfile`, `requirements.txt`, `test_connectivity.py`)

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