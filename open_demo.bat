@echo off
cd /d "%~dp0"
echo ==================================================
echo  TicketFlow API - local access tunnel
echo  Leave this window OPEN while you use the API.
echo  Close it (or press Ctrl+C) to stop.
echo ==================================================
echo.
echo  Health: http://localhost:8080/api/health
echo  Docs:   http://localhost:8080/docs
echo.
kubectl port-forward service/ticketflow-api 8080:80
