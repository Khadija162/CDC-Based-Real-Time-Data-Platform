# CDC-Based Real-Time Data Platform

An end-to-end **local CDC streaming and observability prototype** using PostgreSQL logical replication, Debezium, Kafka-compatible Redpanda, Python, FastAPI, Streamlit, Docker, read-only AI analysis, and an Azure cloud blueprint.

> **Status:** Repository code and local Compose stack added. The CDC runtime, GitHub Actions result, Ollama inference and Azure deployment have not been independently verified. Cloud resources have **not** been provisioned.

## Architecture

```text
PostgreSQL orders (seeded synthetic CC0 data)
     │ WAL / pgoutput
     ▼
Debezium on Kafka Connect
     │ snapshot, inserts, updates, deletes
     ▼
Redpanda (Kafka API) -> Python CDC worker (offset-deduplicated SQLite)
                                         |
                                         ▼
                                 FastAPI metrics + AI
                                         |
                                         ▼
                                   Streamlit UI

Cloud roadmap: Azure PostgreSQL → CDC/Kafka → ADLS Gen2/Databricks/Delta → Container Apps
```

## Open data

The repository includes **12 original synthetic e-commerce orders**, released under CC0 at [data/public/orders.csv](data/public/orders.csv). The PostgreSQL initialization script loads equivalent example rows. No personal information or proprietary data is included. See [attribution](data/public/README.md).

## Run locally (Windows PowerShell + Docker Desktop)

```powershell
git clone https://github.com/Khadija162/CDC-Based-Real-Time-Data-Platform.git
cd CDC-Based-Real-Time-Data-Platform
docker compose up -d --build
```

Wait for Kafka Connect readiness, then register the Debezium PostgreSQL connector. **Run the next command only once** (subsequent registrations return HTTP 409 unless you update/delete the connector):

```powershell
Invoke-RestMethod -Uri http://localhost:8083/connectors -Method Post -ContentType "application/json" -InFile connectors/orders.json
```

Check its status:

```powershell
Invoke-RestMethod -Uri http://localhost:8083/connectors/orders-connector/status
```

A connector snapshot should emit the initial 12 rows. Subsequent changes in PostgreSQL should generate CDC events:

```powershell
docker compose exec postgres psql -U cdc -d orders -c "UPDATE public.orders SET status='paid', updated_at=NOW() WHERE order_id=1001;"
docker compose exec postgres psql -U cdc -d orders -c "INSERT INTO public.orders(order_id,customer_code,amount,status) VALUES (10013,'C013',149.99,'created');"
docker compose exec postgres psql -U cdc -d orders -c "DELETE FROM public.orders WHERE order_id=1002;"
```

View API at http://localhost:8000/docs and dashboard at http://localhost:8501. Metrics are empty until the connector and worker have consumed events.

### Run tests locally

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest -q
```

## AI incident analysis

POST `/api/ai/investigate` summarizes recorded CDC state. Default `LLM_MODE=mock` requires no GPU/API credentials. `LLM_MODE=ollama` supports locally hosted open-weight models such as Qwen 2.5 when Ollama is separately running and network-accessible. The Compose API currently runs in mock mode. The model never executes SQL or remediates incidents.

## Docker services

- `postgres`: PostgreSQL 16 with logical WAL, seeded public demo data
- `redpanda`: Kafka-compatible broker
- `connect`: Debezium PostgreSQL connector runtime (registration required)
- `worker`: CDC ingestion, SQLite materialized orders + event audit counts
- `api`: read-only FastAPI monitoring + AI
- `dashboard`: Streamlit web frontend

Demo passwords in Compose are **not suitable for production**. SQLite offsets deduplicate Kafka replays, but this is a single-node prototype with no production high availability, full DLQ, or durable connector configuration monitoring.

## Cloud deployment

Terraform in `infra/terraform/` defines only an **Azure resource group and ADLS Gen2 storage account**. The target deployment includes managed PostgreSQL, Debezium/Kafka, Event Hubs if connector-compatible, Azure Databricks Delta Lake processing, and secured Container Apps front/backend. Nothing has been deployed. See [architecture and roadmap](docs/architecture.md).

## Security and limitations

The API and Kafka Connect endpoints are localhost-bound and unauthenticated. Do not expose publicly. The CDC connector is configured for a development-only database. Review source schema changes, connector health, data retention, consumer delivery semantics, and least-privilege access before production usage.
