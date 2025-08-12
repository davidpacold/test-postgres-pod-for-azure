@echo off
setlocal enabledelayedexpansion

set NAMESPACE=%1
if "%NAMESPACE%"=="" set NAMESPACE=default

echo Cleaning up test resources...
echo Namespace: %NAMESPACE%
echo =============================

kubectl delete pod postgres-test-pod -n %NAMESPACE% --ignore-not-found=true
kubectl delete configmap postgres-config -n %NAMESPACE% --ignore-not-found=true
kubectl delete secret postgres-secret -n %NAMESPACE% --ignore-not-found=true
kubectl delete secret azure-services-secret -n %NAMESPACE% --ignore-not-found=true
kubectl delete pvc test-pvc -n %NAMESPACE% --ignore-not-found=true
kubectl delete configmap pvc-config -n %NAMESPACE% --ignore-not-found=true

echo Cleanup complete!