@echo off
REM Double-click to build the image and deploy to Kubernetes.
REM First: make sure Kubernetes is ENABLED in Docker Desktop (Settings > Kubernetes).
cd /d "%~dp0"

echo ============================================
echo  1/3  Building Docker image (ticketflow-api:0.1.0)
echo ============================================
docker build -t ticketflow-api:0.1.0 .
if errorlevel 1 ( echo. & echo BUILD FAILED - copy the error above and send it to Claude. & pause & exit /b 1 )

echo.
echo ============================================
echo  2/3  Applying Kubernetes manifests
echo ============================================
kubectl apply -f k8s/
if errorlevel 1 ( echo. & echo APPLY FAILED - is Kubernetes enabled in Docker Desktop? Send the error to Claude. & pause & exit /b 1 )

echo.
echo ============================================
echo  3/3  Current pods
echo ============================================
kubectl get pods

echo.
echo Done. MySQL takes a few minutes the first time.
echo Watch progress:   kubectl get pods -w
echo When pods are Ready, test:   curl.exe localhost:30080/api/health
echo.
pause
