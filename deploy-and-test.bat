@echo off
setlocal enabledelayedexpansion

echo Deploying PostgreSQL connectivity test pod...
echo ============================================

:: Default values
set NAMESPACE=default
set ENABLE_PVC=false
set MANUAL_TESTS=false
set POSTGRES_SERVER=

:: Parse command line arguments
:parse_args
if "%~1"=="" goto end_parse
if /i "%~1"=="--namespace" (
    set NAMESPACE=%~2
    shift
    shift
    goto parse_args
) else if /i "%~1"=="-n" (
    set NAMESPACE=%~2
    shift
    shift
    goto parse_args
) else if /i "%~1"=="--server" (
    set POSTGRES_SERVER=%~2
    shift
    shift
    goto parse_args
) else if /i "%~1"=="-s" (
    set POSTGRES_SERVER=%~2
    shift
    shift
    goto parse_args
) else if /i "%~1"=="--enable-pvc" (
    set ENABLE_PVC=true
    shift
    goto parse_args
) else if /i "%~1"=="--manual-tests" (
    set MANUAL_TESTS=true
    shift
    goto parse_args
) else if /i "%~1"=="--help" (
    goto show_help
) else if /i "%~1"=="-h" (
    goto show_help
) else (
    echo Unknown parameter: %~1
    echo Use --help for usage information
    exit /b 1
)
:end_parse

echo Namespace: %NAMESPACE%

:: Check if image exists locally
docker images | findstr /C:"connectivity-tester" | findstr /C:"latest" >nul
if errorlevel 1 (
    echo Building connectivity tester image first...
    call build-image.bat
)

:: Create namespace if it doesn't exist
echo Ensuring namespace exists...
kubectl create namespace %NAMESPACE% --dry-run=client -o yaml | kubectl apply -f -

:: Apply configurations
echo Applying PostgreSQL ConfigMap...
kubectl apply -f postgres-configmap.yaml -n %NAMESPACE%

echo Applying PostgreSQL Secret...
kubectl apply -f postgres-secret.yaml -n %NAMESPACE%

echo Applying Azure Services Secret...
kubectl apply -f azure-services-secret.yaml -n %NAMESPACE%

:: Apply PVC if enabled
if "%ENABLE_PVC%"=="true" (
    echo PVC testing enabled - creating PVC...
    kubectl apply -f test-pvc.yaml -n %NAMESPACE%
    kubectl apply -f pvc-configmap.yaml -n %NAMESPACE%
    
    :: Wait for PVC to be bound
    echo Waiting for PVC to be bound...
    kubectl wait --for=condition=Bound pvc/test-pvc --timeout=60s -n %NAMESPACE%
    
    :: Deploy pod with PVC enabled
    kubectl apply -f postgres-test-pod-extended.yaml -n %NAMESPACE%
    kubectl set env pod/postgres-test-pod TEST_PVC=true -n %NAMESPACE%
) else (
    echo PVC testing disabled ^(use --enable-pvc to enable^)
    kubectl apply -f postgres-test-pod-extended.yaml -n %NAMESPACE%
)

:: Wait for pod to be ready
echo Waiting for pod to be ready...
kubectl wait --for=condition=Ready pod/postgres-test-pod --timeout=60s -n %NAMESPACE%

if !errorlevel!==0 (
    echo Pod is ready!
    echo.
    
    if "%MANUAL_TESTS%"=="true" if not "%POSTGRES_SERVER%"=="" (
        echo Running manual connectivity tests...
        echo ====================================
        
        echo.
        echo Test 1: DNS Resolution
        echo ----------------------
        kubectl exec postgres-test-pod -n %NAMESPACE% -- nslookup %POSTGRES_SERVER%.postgres.database.azure.com
        
        echo.
        echo Test 2: Network Connectivity
        echo ----------------------------
        kubectl exec postgres-test-pod -n %NAMESPACE% -- nc -zv %POSTGRES_SERVER%.postgres.database.azure.com 5432
        
        echo.
        echo Test 3: PostgreSQL Connection
        echo -----------------------------
        kubectl exec postgres-test-pod -n %NAMESPACE% -- psql -c "SELECT version();"
        
        echo.
        echo Test 4: List databases
        echo ----------------------
        kubectl exec postgres-test-pod -n %NAMESPACE% -- psql -c "\l"
        
        echo.
        echo Test 5: Connect to keycloak database
        echo ------------------------------------
        kubectl exec postgres-test-pod -n %NAMESPACE% -- psql -d keycloak -c "SELECT current_database(), current_user, inet_server_addr(), inet_server_port();"
        
        echo.
        echo ================================================
        echo Manual tests complete!
        echo.
        echo To manually connect to the database, run:
        echo kubectl exec -it postgres-test-pod -n %NAMESPACE% -- psql -d keycloak
    ) else (
        echo Viewing automated test results...
        echo =================================
        kubectl logs postgres-test-pod -n %NAMESPACE% -f
    )
) else (
    echo Pod failed to become ready
    echo Pod status:
    kubectl describe pod postgres-test-pod -n %NAMESPACE%
)

echo.
echo To clean up resources, run:
echo cleanup.bat %NAMESPACE%
exit /b 0

:show_help
echo Usage: %0 [options]
echo Options:
echo   --namespace, -n ^<namespace^>  Kubernetes namespace ^(default: default^)
echo   --server, -s ^<server^>        PostgreSQL server name ^(for manual tests^)
echo   --enable-pvc                 Enable PVC testing
echo   --manual-tests               Run manual connectivity tests
echo   --help, -h                   Show this help message
exit /b 0