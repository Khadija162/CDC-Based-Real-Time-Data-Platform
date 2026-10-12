# CDC design and Azure roadmap

Local reference architecture: PostgreSQL logical WAL (`pgoutput`) → Debezium PostgreSQL connector → Redpanda Kafka-compatible topic → Python at-least-once consumer → transactional SQLite snapshot and metrics → FastAPI → Streamlit. A small original CC0 orders CSV and matching SQL seed data are included.

The connector takes an initial snapshot and subsequently emits create/update/delete changes. The consumer deduplicates by Kafka topic/partition/offset and commits the Kafka offset only after materializing the record. This is a single-node demonstration, not a production exactly-once service; malformed events require a dead-letter queue to prevent repeated stalls.

Cloud design (not provisioned): Azure Database for PostgreSQL with verified logical-replication permissions; Debezium Connect running on dedicated managed compute; Kafka/Event Hubs after validating compatibility; ADLS Gen2 Bronze data, Databricks Delta Lake Silver/Gold, Azure Container Apps for API/dashboard, Entra ID + Key Vault + Azure Monitor, read-only open-weight AI incident analyst.

Production milestones: persist broker/Connect volumes; secure credentials and TLS; configure logical slot WAL retention monitoring; offset recovery; schema registry; retry/DLQ; snapshot restart; idempotent data replay; tenant authorization and operational metrics. Terraform example creates only resource group and storage; applying it can incur costs.
