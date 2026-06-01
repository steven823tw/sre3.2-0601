# V3.1 SRE Platform — Database Architecture

## Overview

Production-grade PostgreSQL 16+ schema designed for large-scale SRE operations:

- **10,000+ devices** across multiple platforms (VMware, OpenStack, K8s, physical)
- **100,000+ alerts/month** from Prometheus, Grafana, vCenter
- **10,000+ operations/month** with full execution tracking
- **100+ concurrent operations** with proper locking

## Files

| File | Purpose |
|------|---------|
| `schema.sql` | Complete DDL — tables, indexes, enums, functions, roles, partition management |
| `migrations/001_initial.py` | Alembic migration equivalent of schema.sql |
| `seeds/generate_test_data.py` | Python script to generate realistic test data |

## Entity Relationship

```
users ──────────────┬──── platforms ──── assets ──── asset_metrics
                    │        │              │
                    │        │              ├── asset_relations (self-ref)
                    │        │              │
                    │        └────── operations ── operation_steps
                    │                    │
                    ├──── alerts         │
                    │                    │
                    ├──── audit_logs     │
                    │                    │
                    ├──── skills ────────┘
                    │
                    └──── conversations
```

## Tables

### Core Tables

| Table | Rows (expected) | Partitioned | Description |
|-------|----------------|-------------|-------------|
| `users` | ~50 | No | User accounts (human + AI agents) |
| `platforms` | ~10 | No | Platform adapter connections |
| `assets` | 10,000+ | No | Unified asset registry |
| `asset_relations` | 20,000+ | No | Asset dependency graph |
| `alerts` | 100K+/month | Yes (monthly) | Alert records from monitoring |
| `operations` | 10K+/month | No | Operations/tickets |
| `operation_steps` | 50K+/month | No | Steps within operations |
| `audit_logs` | 50K+/month | Yes (monthly) | Immutable audit trail |
| `asset_metrics` | 500K+/month | Yes (monthly) | Time-series metrics |
| `skills` | ~50 | No | YAML skill definitions |
| `conversations` | 1,000+ | No | AI Agent chat history |

### Partitioned Tables

Three tables use native PostgreSQL range partitioning by month:

- **`alerts`** — partitioned on `created_at`
- **`audit_logs`** — partitioned on `created_at`
- **`asset_metrics`** — partitioned on `recorded_at`

Partitions are created 6 months ahead. Old partitions are dropped per retention policy:

| Table | Retention |
|-------|-----------|
| `asset_metrics` | 6 months |
| `alerts` | 12 months |
| `audit_logs` | 24 months |

### Partition Maintenance

Run monthly via pg_cron or external scheduler:

```sql
-- Create future partitions (3 months ahead)
SELECT create_monthly_partitions('alerts', 3);
SELECT create_monthly_partitions('audit_logs', 3);
SELECT create_monthly_partitions('asset_metrics', 3);

-- Drop old partitions per retention policy
SELECT drop_old_partitions('asset_metrics', 6);
SELECT drop_old_partitions('alerts', 12);
SELECT drop_old_partitions('audit_logs', 24);
```

## Enum Types

All status/type fields use PostgreSQL enum types (not varchar):

| Enum | Values |
|------|--------|
| `asset_type` | vm, physical_host, storage_device, network_device, container_host, cluster, datastore, load_balancer |
| `asset_status` | active, maintenance, decommissioned, unknown, provisioning, error |
| `platform_type` | vmware_vsphere, openstack, kubernetes, physical, fusion_sphere, storage_array, network |
| `alert_severity` | critical, high, medium, low, info |
| `alert_status` | firing, acknowledged, resolved, silenced, expired |
| `operation_type` | inspection, change_request, incident, maintenance, remediation, audit |
| `operation_status` | draft, pending_approval, approved, executing, completed, failed, cancelled, rolled_back |
| `risk_level` | critical, high, medium, low, none |
| `audit_action` | create, read, update, delete, execute, login, logout, export, import, approve, reject |
| `user_role` | admin, operator, viewer, auditor, ai_agent |

## Index Strategy

### Asset Search (Dashboard < 200ms target)

```sql
-- Name search with trigram (ILIKE support)
CREATE INDEX idx_assets_name_trgm ON assets USING gin(name gin_trgm_ops);

-- IP array containment
CREATE INDEX idx_assets_ip ON assets USING gin(ip_addresses);

-- JSONB metadata search
CREATE INDEX idx_assets_metadata ON assets USING gin(metadata jsonb_path_ops);

-- Filter indexes
CREATE INDEX idx_assets_type ON assets(asset_type);
CREATE INDEX idx_assets_status ON assets(status);
CREATE INDEX idx_assets_platform_type ON assets(platform_type);
CREATE INDEX idx_assets_cluster ON assets(cluster_name) WHERE cluster_name IS NOT NULL;
```

### Alert Filtering (List < 100ms target)

```sql
-- Composite for dashboard: active alerts by severity
CREATE INDEX idx_alerts_status_severity ON alerts(status, severity) WHERE status = 'firing';

-- Time range queries
CREATE INDEX idx_alerts_created_at ON alerts(created_at);
CREATE INDEX idx_alerts_firing_at ON alerts(firing_at);

-- Deduplication
CREATE INDEX idx_alerts_external_source ON alerts(source, external_id) WHERE external_id IS NOT NULL;
```

### Metric Queries (Asset + Time Range)

```sql
-- Primary: latest metrics for an asset
CREATE INDEX idx_metrics_asset_time ON asset_metrics(asset_id, recorded_at DESC);

-- Specific metric over time
CREATE INDEX idx_metrics_asset_name_time ON asset_metrics(asset_id, metric_name, recorded_at DESC);
```

### Query Examples

```sql
-- Dashboard: asset summary by platform and status (uses idx_assets_platform_type)
SELECT platform_type, status, count(*)
FROM assets
GROUP BY platform_type, status;

-- Search assets by name prefix (uses idx_assets_name_trgm)
SELECT id, name, asset_type, status
FROM assets
WHERE name ILIKE '%web-prod%'
ORDER BY name
LIMIT 50;

-- Find VMs by IP (uses idx_assets_ip)
SELECT id, name, status
FROM assets
WHERE '10.1.5.100' = ANY(ip_addresses);

-- Active critical alerts (uses idx_alerts_status_severity)
SELECT id, title, severity, firing_at, resource_name
FROM alerts
WHERE status = 'firing' AND severity = 'critical'
ORDER BY firing_at DESC
LIMIT 20;

-- Asset metrics for last 24h (uses idx_metrics_asset_time)
SELECT metric_name, value, unit, recorded_at
FROM asset_metrics
WHERE asset_id = '...'
  AND recorded_at >= now() - interval '24 hours'
ORDER BY recorded_at DESC;

-- Audit trail for a user (uses idx_audit_user_id)
SELECT action, resource_type, resource_name, created_at
FROM audit_logs
WHERE user_id = '...'
  AND created_at >= now() - interval '7 days'
ORDER BY created_at DESC;
```

## Design Decisions

### UUID Primary Keys

All tables use `gen_random_uuid()` (built into PostgreSQL 16+, no extension needed). This provides:

- Globally unique IDs across distributed systems
- No sequence management overhead
- Safe for client-side ID generation

**Note**: UUIDv7 (time-ordered) would be ideal for B-tree performance but requires PostgreSQL 18 or a custom function. Migration path is documented below.

### JSONB for Flexible Metadata

Used on `assets.metadata`, `operations.parameters`, `operations.result`, `alerts.labels`, `alerts.annotations`, `conversations.messages`. Indexed with `jsonb_path_ops` for containment queries.

### Array Columns

- `assets.ip_addresses` — TEXT[] for multi-homed hosts
- `operations.target_assets` — UUID[] for multi-asset operations
- `skills.tags` — TEXT[] for skill categorization

Arrays are indexed with GIN for `@>` (contains) and `ANY` queries.

### Partitioned Composite Primary Key

Partitioned tables (`alerts`, `audit_logs`, `asset_metrics`) use composite PKs `(id, created_at)` because PostgreSQL requires the partition key to be part of any unique constraint. This means:

- Foreign key references to these tables must include the partition key
- Application code should pass both `id` and `created_at` for lookups
- Alternatively, use the non-unique `id` column for lookups (slightly slower but simpler)

### Soft Deletes

Not implemented at the schema level. Assets with `status = 'decommissioned'` are retained for audit. Alert resolution is tracked via `resolved_at`/`resolved_by`. Deleted conversations use `status = 'deleted'`.

## Performance Tuning

### Recommended PostgreSQL Configuration

```
shared_buffers = 4GB                     # 25% of RAM (for 16GB server)
effective_cache_size = 12GB              # 75% of RAM
work_mem = 64MB                          # Complex sorts/hashes
maintenance_work_mem = 1GB               # VACUUM, CREATE INDEX
max_parallel_workers_per_gather = 4
max_parallel_workers = 8
random_page_cost = 1.1                   # SSD storage
effective_io_concurrency = 200           # SSD
wal_buffers = 64MB
max_wal_size = 4GB
checkpoint_completion_target = 0.9
autovacuum_max_workers = 4
autovacuum_naptime = 30s                 # More frequent for high-write tables
shared_preload_libraries = 'pg_stat_statements'
```

### Monitoring Queries

```sql
-- Top slow queries
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Table sizes
SELECT relname, pg_size_pretty(pg_total_relation_size(relid))
FROM pg_stat_user_tables
ORDER BY pg_total_relation_size(relid) DESC;

-- Unused indexes (candidates for removal)
SELECT indexrelname, idx_scan, idx_tup_read
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY pg_relation_size(indexrelid) DESC;

-- Partition sizes
SELECT tablename, pg_size_pretty(pg_total_relation_size(tablename::regclass))
FROM pg_tables
WHERE tablename LIKE 'alerts_y%' OR tablename LIKE 'audit_logs_y%' OR tablename LIKE 'asset_metrics_y%'
ORDER BY tablename;
```

## Security

### Application Roles

| Role | Purpose | Permissions |
|------|---------|-------------|
| `sre_app` | Application service account | SELECT, INSERT, UPDATE, DELETE on all tables |
| `sre_readonly` | Dashboards, reporting | SELECT only |

**Production**: Change default passwords immediately. Consider connection pooling (PgBouncer) with `transaction` pooling mode.

### Row Level Security

RLS is not enabled by default (this is a self-hosted platform, not multi-tenant SaaS). For multi-tenant deployments, enable RLS on sensitive tables and create policies using `(SELECT auth.uid())` pattern.

## Migration Strategy

### Alembic Setup

```bash
cd Inspection_V2
pip install alembic psycopg2-binary

# Initialize (already done)
alembic init alembic

# Run initial migration
alembic upgrade head

# Generate future migrations
alembic revision --autogenerate -m "description"
```

### Migration Naming Convention

```
001_initial.py          — Core schema (tables, indexes, enums, functions)
002_seed_data.py        — Test data insertion
003_add_indexes.py      — Additional indexes based on query analysis
004_rls_policies.py     — Row Level Security (when needed)
```

### UUIDv7 Migration Path

When PostgreSQL 18 is available (or via `pg_uuidv7` extension):

```sql
-- 1. Install extension
CREATE EXTENSION pg_uuidv7;

-- 2. Add UUIDv7 column
ALTER TABLE assets ADD COLUMN id_v7 UUID DEFAULT uuid_generate_v7();

-- 3. Backfill
UPDATE assets SET id_v7 = uuid_generate_v7() WHERE id_v7 IS NULL;

-- 4. Swap primary key (requires maintenance window)
-- ... (detailed migration script needed)
```

## Seed Data

Generate realistic test data:

```bash
# Print SQL to stdout
python seeds/generate_test_data.py

# Write to file
python seeds/generate_test_data.py --output seeds/seed.sql

# Execute directly
python seeds/generate_test_data.py --execute --dsn "postgresql://sre_app:password@localhost:5432/sre_platform"
```

Test data includes:
- 5 users (admin, 2 operators, viewer, AI agent)
- 5 platform connections
- 135 assets (100 VMs, 20 hosts, 10 storage, 5 network)
- Asset relationships (host->VM, VM->datastore)
- 50 alerts (mixed severity/status)
- 20 operations with steps
- 100 audit log entries
- 24h of metrics for 5 sample assets
- 3 skill definitions
- 5 AI conversations

## Comparison with V1/V2

| Aspect | V1/V2 | V3.1 |
|--------|-------|------|
| Primary keys | `varchar(50)` | `UUID` |
| Timestamps | `varchar(50)` | `timestamptz` |
| Status fields | `varchar(1)` | Enum types |
| Foreign keys | None | Full FK with ON DELETE |
| Indexes | None | 30+ targeted indexes |
| Partitioning | None | Monthly range on 3 tables |
| JSONB | None | Flexible metadata |
| Audit trail | None | Full audit_logs table |
| Roles | Single postgres | sre_app + sre_readonly |
| Constraints | None | CHECK, UNIQUE, NOT NULL |
