@echo off
setlocal enabledelayedexpansion

set NAMESPACE=%1
if "%NAMESPACE%"=="" set NAMESPACE=default

echo Cleaning up test resources...
echo Namespace: %NAMESPACE%
echo =============================

kubectl delete pod postgres-test-pod -n %NAMESPACE%
kubectl delete configmap postgres-config -n %NAMESPACE%
kubectl delete secret postgres-secret -n %NAMESPACE%

echo Cleanup complete!