@echo off
REM Pushes this project to GitHub as separate logical commits (a natural history).
REM BEFORE running: create an EMPTY repo named  ticketflow-api  on github.com
REM (do NOT add a README or .gitignore there - this project already has them).
cd /d "%~dp0"

echo This will commit the project in steps and push to:
echo   https://github.com/kevindzit/ticketflow-api.git
echo (Repo already created on GitHub. Pushing now...)

git init
git config user.name "Kevin Dzitkowski"
git config user.email "kevindzit@gmail.com"

git add app/__init__.py app/core/config.py app/core/__init__.py app/routes/health.py app/routes/__init__.py run.py requirements.txt .gitignore
git commit -m "scaffold flask app factory + health endpoint"

git add app/models.py app/core/database.py scripts/seed_demo_data.py
git commit -m "add db models matching ticketflow schema + seed script"

git add app/services/__init__.py app/services/classifier.py
git commit -m "add pluggable classifier (ollama + rule-based fallback)"

git add app/services/assignment.py app/core/auth.py app/routes/tickets.py app/routes/technicians.py app/routes/docs.py app/__init__.py
git commit -m "add ticket + technician endpoints, assignment, api-key auth, openapi docs"

git add tests pytest.ini requirements-dev.txt .github
git commit -m "add pytest suite + github actions ci"

git add Dockerfile .dockerignore k8s requirements.txt
git commit -m "add dockerfile + kubernetes manifests"

git add README.md
git commit -m "add readme"

git add -A
git commit -m "tidy up" 1>nul 2>nul

git branch -M main
git remote add origin https://github.com/kevindzit/ticketflow-api.git
git push -u origin main

echo.
echo If it asked you to sign in to GitHub, that is normal - approve it in the popup.
echo If anything errored, copy the output and send it to Claude.
pause
