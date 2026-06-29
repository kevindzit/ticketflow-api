@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ================================================================
echo  TicketFlow API  -  deploy on a local Kubernetes cluster (kind)
echo  Uses your Docker ENGINE (healthy) and skips Docker Desktop's
echo  broken built-in Kubernetes entirely.
echo ================================================================
echo.

REM --- 0. Docker engine reachable? ---
docker version >nul 2>&1
if errorlevel 1 (
  echo [X] Docker engine not responding.
  echo     Open Docker Desktop, wait for "Engine running" green at the bottom, then re-run this.
  pause & exit /b 1
)

REM --- 1. kubectl present? ---
where kubectl >nul 2>&1
if errorlevel 1 (
  echo [X] kubectl not found on PATH. Docker Desktop normally installs it.
  echo     Send this message to Claude and we'll sort it out.
  pause & exit /b 1
)

REM --- 2. Get kind.exe (latest) if we don't have it ---
set "KIND=kind"
where kind >nul 2>&1
if errorlevel 1 (
  if not exist kind.exe (
    echo Downloading kind ^(latest^) ...
    curl.exe -Lo kind.exe https://github.com/kubernetes-sigs/kind/releases/latest/download/kind-windows-amd64
    if errorlevel 1 ( echo [X] Could not download kind. Check internet/VPN and retry. & pause & exit /b 1 )
  )
  set "KIND=kind.exe"
)

REM --- 3. Create the cluster (maps localhost:30080) if it isn't there ---
%KIND% get clusters 2>nul | findstr /x "ticketflow" >nul
if errorlevel 1 (
  echo Creating kind cluster "ticketflow" ...
  %KIND% create cluster --name ticketflow --config kind-config.yaml
  if errorlevel 1 ( echo [X] Cluster create failed - copy the error and send it to Claude. & pause & exit /b 1 )
) else (
  echo Cluster "ticketflow" already exists - reusing it.
)

REM --- 4. Build the image ---
echo.
echo Building image ticketflow-api:0.1.0 ...
docker build -t ticketflow-api:0.1.0 .
if errorlevel 1 ( echo [X] Build failed - copy the error and send it to Claude. & pause & exit /b 1 )

REM --- 5. Load the image into the cluster ---
echo.
echo Loading image into the cluster ...
%KIND% load docker-image ticketflow-api:0.1.0 --name ticketflow
if errorlevel 1 ( echo [X] Image load failed - copy the error and send it to Claude. & pause & exit /b 1 )

REM --- 6. Apply the manifests ---
echo.
echo Applying Kubernetes manifests ...
kubectl apply -f k8s/
if errorlevel 1 ( echo [X] kubectl apply failed - copy the error and send it to Claude. & pause & exit /b 1 )

REM --- 7. Show what's running ---
echo.
echo Done applying. Pods ^(MySQL takes a few minutes the first time^):
kubectl get pods
echo.
echo  Watch live:    kubectl get pods -w
echo  When all pods say Running / READY, test it:
echo     curl.exe localhost:30080/api/health
echo.
pause
