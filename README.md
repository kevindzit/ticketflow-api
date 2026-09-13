# TicketFlow API

A REST API service for my [TicketFlow](https://github.com/kevindzit/TicketFlow) project.
TicketFlow is my CS capstone - an AI ticket-triage system for MSP work (I work at an
MSP, so it solves a real problem I deal with). This is a separate service that exposes
the triage + assignment logic over a clean JSON API, containerized with Docker and
deployed on Kubernetes. It talks to the same MySQL database TicketFlow uses, so a ticket
created through the API shows up in the TicketFlow dashboard.

## What it does
- `POST` a support ticket -> it classifies the ticket (category + priority), auto-assigns
  a technician by skill / availability / workload, and saves it.
- Classification is **pluggable**: it uses Ollama / Llama 3.1 when that's available and
  falls back to rule-based logic when it isn't or returns invalid output, so it runs
  and tests anywhere.

## Stack
Python / Flask, SQLAlchemy, MySQL, gunicorn, Docker, Kubernetes, pytest, GitHub Actions.

## Endpoints
- `GET  /api/health` - health check (used by the Kubernetes probes)
- `POST /api/tickets` - create a ticket (classify + assign). Needs `X-API-Key`.
- `GET  /api/tickets`, `GET /api/tickets/{id}`
- `GET  /api/technicians`
- `GET  /docs` - Swagger UI

```
curl -X POST localhost:30080/api/tickets -H "X-API-Key: change-me" -H "Content-Type: application/json" \
  -d '{"client_name":"Acme Co","subject":"VPN is down","description":"office outage, urgent"}'
```

### Ticket input and classification

Send a JSON object with `subject`, `description`, and either `client_id` or `client_name`.
Subject and description must be nonempty strings. Text is trimmed before validation.
The subject limit is 200 characters and the client name limit is 100 characters,
matching the database columns. A supplied client ID must be an integer from 1 to
2147483647. Nulls, booleans, and numeric strings are not accepted as IDs.

If both client fields are supplied, both must be valid and `client_id` takes precedence.
Invalid input returns a JSON error with HTTP 400 before a client or ticket is created.
An unknown client ID returns HTTP 404.

Model output must contain a supported category, a supported priority, and a nonempty
text summary. Categories are Network, Hardware, Software, Security, Email, and Other.
Priorities are Low, Medium, High, and Critical. Surrounding whitespace is removed;
the labels must otherwise match these values. If validation fails, the existing
rules classify the original ticket instead. The response reports `classified_by`
as `rules` when this happens.

## Run locally
```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python scripts\seed_demo_data.py
python run.py
# http://localhost:8080/api/health
```
By default it uses a local SQLite file. To share TicketFlow's database, set
`DATABASE_URL` to your MySQL URL before running.

## Tests
```
pip install -r requirements.txt -r requirements-dev.txt
pytest
```
CI runs the tests on pushes and pull requests (`.github/workflows/ci.yml`). They use
a throwaway SQLite db and default to the rule-based classifier. Validation tests
also exercise the Ollama path with mocked responses, including valid output,
unsupported labels, missing fields, and unavailable models. No MySQL or Ollama
server is needed.

## Docker
```
docker build -t ticketflow-api:0.1.0 .
```

## Kubernetes (Docker Desktop)
Enable Kubernetes in Docker Desktop, then:
```
kubectl apply -f k8s/
kubectl get pods
curl localhost:30080/api/health
```
What gets deployed:
- the API as a **Deployment** (2 replicas) with readiness/liveness probes
- **MySQL** as a **StatefulSet** with a persistent volume
- a **ConfigMap** (config) and a **Secret** (DB creds + API key)
- a **NodePort Service** at `localhost:30080`
- a one-time **Job** that creates the tables and seeds demo data

Scale it:
```
kubectl scale deployment ticketflow-api --replicas=4
```
> Note: MySQL runs in the cluster here for local learning. In production this would be a
> managed database, not a StatefulSet.

## What I learned
- Containerizing a Flask app with Docker and running it on Kubernetes
- Deployments vs StatefulSets, and why MySQL needs a StatefulSet + PersistentVolume
- ConfigMaps vs Secrets for config and credentials
- Readiness vs liveness probes
- Scaling replicas and zero-downtime rolling updates
- Keeping the LLM optional behind a fallback so the service stays testable

## Notes / todo
- add Alembic migrations for the shared schema
- swap the NodePort for an Ingress
