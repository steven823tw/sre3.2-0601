-- ============================================================================
-- V3.1 SRE Platform — Production PostgreSQL Schema
-- ============================================================================
-- PostgreSQL 16+ | UUID-OSSP or built-in gen_random_uuid()
-- Designed for: 10,000+ devices, 100K+ alerts/month, 10K+ operations/month
-- All timestamps are timestamptz (UTC). All identifiers are lowercase_snake_case.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 0. Extensions
-- ---------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";       -- uuid_generate_v4() fallback
CREATE EXTENSION IF NOT EXISTS "pg_trgm";          -- trigram index for LIKE/%text%
CREATE EXTENSION IF NOT EXISTS "btree_gin";        -- GIN index on scalar columns
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements"; -- query performance monitoring

-- Optional: TimescaleDB (uncomment if available)
-- CREATE EXTENSION IF NOT EXISTS timescaledb;

-- ---------------------------------------------------------------------------
-- 1. Custom Enum Types
-- ---------------------------------------------------------------------------

-- Asset types covering all supported platforms
CREATE TYPE asset_type AS ENUM (
    'vm',               -- Virtual machine (VMware, OpenStack, KVM)
    'physical_host',    -- Bare-metal server
    'storage_device',   -- SAN/NAS storage array
    'network_device',   -- Switch, router, firewall
    'container_host',   -- Kubernetes node
    'cluster',          -- vSphere/OpenStack/K8s cluster
    'datastore',        -- Storage pool / datastore
    'load_balancer'     -- L4/L7 load balancer
);

-- Asset operational status
CREATE TYPE asset_status AS ENUM (
    'active',
    'maintenance',
    'decommissioned',
    'unknown',
    'provisioning',
    'error'
);

-- Platform identifiers
CREATE TYPE platform_type AS ENUM (
    'vmware_vsphere',
    'openstack',
    'kubernetes',
    'physical',
    'fusion_sphere',
    'storage_array',
    'network'
);

-- Alert severity levels (mirrors Prometheus/Grafana)
CREATE TYPE alert_severity AS ENUM (
    'critical',
    'high',
    'medium',
    'low',
    'info'
);

-- Alert lifecycle status
CREATE TYPE alert_status AS ENUM (
    'firing',
    'acknowledged',
    'resolved',
    'silenced',
    'expired'
);

-- Operation (ticket) types
CREATE TYPE operation_type AS ENUM (
    'inspection',       -- Automated health inspection
    'change_request',   -- Planned change
    'incident',         -- Incident response
    'maintenance',      -- Scheduled maintenance
    'remediation',      -- AI-driven remediation
    'audit'             -- Compliance audit
);

-- Operation risk levels
CREATE TYPE risk_level AS ENUM (
    'critical',
    'high',
    'medium',
    'low',
    'none'
);

-- Operation lifecycle status
CREATE TYPE operation_status AS ENUM (
    'draft',
    'pending_approval',
    'approved',
    'executing',
    'completed',
    'failed',
    'cancelled',
    'rolled_back'
);

-- Operation step status
CREATE TYPE step_status AS ENUM (
    'pending',
    'running',
    'completed',
    'failed',
    'skipped',
    'rolled_back'
);

-- Audit action types
CREATE TYPE audit_action AS ENUM (
    'create',
    'read',
    'update',
    'delete',
    'execute',
    'login',
    'logout',
    'export',
    'import',
    'approve',
    'reject'
);

-- User roles
CREATE TYPE user_role AS ENUM (
    'admin',
    'operator',
    'viewer',
    'auditor',
    'ai_agent'
);

-- Conversation status
CREATE TYPE conversation_status AS ENUM (
    'active',
    'archived',
    'deleted'
);

-- Skill status
CREATE TYPE skill_status AS ENUM (
    'active',
    'disabled',
    'draft',
    'deprecated'
);

-- ---------------------------------------------------------------------------
-- 2. Core Tables
-- ---------------------------------------------------------------------------

-- ===== users =====
-- User accounts for the SRE platform. Supports both human and AI agent accounts.
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username        TEXT NOT NULL UNIQUE,
    email           TEXT UNIQUE,
    display_name    TEXT NOT NULL,
    password_hash   TEXT,                           -- NULL for SSO/API-key-only users
    role            user_role NOT NULL DEFAULT 'viewer',
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    last_login_at   TIMESTAMPTZ,
    api_key_hash    TEXT,                           -- Hashed API key for programmatic access
    preferences     JSONB NOT NULL DEFAULT '{}',    -- UI preferences, notification settings
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE users IS 'User accounts including human operators and AI agent service accounts';
COMMENT ON COLUMN users.api_key_hash IS 'SHA-256 hash of API key; plaintext never stored';
COMMENT ON COLUMN users.preferences IS 'JSONB blob for UI theme, notification channels, timezone';

-- ===== platforms =====
-- Platform adapter configurations (vCenter connections, OpenStack endpoints, etc.)
CREATE TABLE platforms (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL,                  -- Human-readable name: "Prod vCenter"
    platform_type   platform_type NOT NULL,
    endpoint        TEXT NOT NULL,                  -- API endpoint URL
    credentials     JSONB NOT NULL DEFAULT '{}',    -- Encrypted credentials (app-level encryption)
    config          JSONB NOT NULL DEFAULT '{}',    -- Platform-specific config (skip TLS verify, etc.)
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    last_sync_at    TIMESTAMPTZ,
    sync_status     TEXT,                           -- 'success', 'failed', 'in_progress'
    sync_error      TEXT,                           -- Last sync error message
    created_by      UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE platforms IS 'Platform adapter connection configs (vCenter, OpenStack, K8s, etc.)';
COMMENT ON COLUMN platforms.credentials IS 'Encrypted at application layer; never expose via API';

-- ===== assets =====
-- Unified asset registry. All infrastructure objects across all platforms.
-- Designed for 10,000+ rows with fast search by name, IP, platform, status.
CREATE TABLE assets (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_id     TEXT,                           -- Platform-specific ID (vCenter MOID, K8s UID, etc.)
    name            TEXT NOT NULL,                  -- Display name
    asset_type      asset_type NOT NULL,
    platform_id     UUID REFERENCES platforms(id) ON DELETE SET NULL,
    platform_type   platform_type NOT NULL,
    status          asset_status NOT NULL DEFAULT 'active',

    -- Network identifiers
    ip_addresses    TEXT[] DEFAULT '{}',            -- Array of IPs for multi-homed hosts
    mac_addresses   TEXT[] DEFAULT '{}',

    -- Hierarchy
    cluster_name    TEXT,                           -- Parent cluster name
    datacenter      TEXT,                           -- Datacenter name
    folder_path     TEXT,                           -- vSphere folder path or K8s namespace

    -- Hardware specs (populated by discovery)
    cpu_cores       SMALLINT,
    memory_mb       INTEGER,
    disk_gb         INTEGER,
    os_type         TEXT,                           -- 'linux', 'windows', 'esxi', 'other'
    os_version      TEXT,

    -- Flexible metadata per asset type
    metadata        JSONB NOT NULL DEFAULT '{}',    -- Vendor-specific fields, custom tags

    -- Lifecycle
    discovered_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- Prevent duplicate assets from same platform
    UNIQUE (platform_id, external_id)
);

COMMENT ON TABLE assets IS 'Unified asset registry for all infrastructure objects across all platforms';
COMMENT ON COLUMN assets.external_id IS 'Platform-specific identifier: vCenter MOID, K8s UID, etc.';
COMMENT ON COLUMN assets.metadata IS 'Vendor-specific fields, custom tags, warranty info, etc.';
COMMENT ON COLUMN assets.ip_addresses IS 'Array of IPs; use array contains (@>) for search';

-- ===== asset_relations =====
-- Asset dependency / containment relationships (host runs VM, VM uses datastore, etc.)
CREATE TABLE asset_relations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_asset_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    target_asset_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    relation_type   TEXT NOT NULL,                  -- 'runs_on', 'uses', 'contains', 'connects_to'
    metadata        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE (source_asset_id, target_asset_id, relation_type)
);

COMMENT ON TABLE asset_relations IS 'Directed dependency graph between assets (host->VM, VM->datastore, etc.)';

-- ===== alerts =====
-- Alert records from monitoring systems (Prometheus, Grafana, vCenter alarms).
-- Partitioned by created_at for time-range queries and retention management.
CREATE TABLE alerts (
    id              UUID NOT NULL DEFAULT gen_random_uuid(),
    external_id     TEXT,                           -- Source system alert ID
    source          TEXT NOT NULL,                  -- 'prometheus', 'grafana', 'vcenter', 'manual'
    title           TEXT NOT NULL,
    description     TEXT,
    severity        alert_severity NOT NULL,
    status          alert_status NOT NULL DEFAULT 'firing',

    -- Resource association
    asset_id        UUID REFERENCES assets(id) ON DELETE SET NULL,
    resource_name   TEXT,                           -- Denormalized for fast display
    resource_type   TEXT,

    -- Alert metadata
    labels          JSONB NOT NULL DEFAULT '{}',    -- Prometheus labels or vCenter alarm fields
    annotations     JSONB NOT NULL DEFAULT '{}',    -- Description, runbook URL, etc.
    value           DOUBLE PRECISION,               -- Threshold value that triggered alert
    threshold       DOUBLE PRECISION,               -- Configured threshold

    -- Lifecycle
    firing_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    acknowledged_at TIMESTAMPTZ,
    acknowledged_by UUID REFERENCES users(id) ON DELETE SET NULL,
    resolved_at     TIMESTAMPTZ,
    resolved_by     UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),  -- Partition key

    -- Composite PK required for partitioned tables
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

COMMENT ON TABLE alerts IS 'Alert records from all monitoring sources; partitioned monthly by created_at';
COMMENT ON COLUMN alerts.labels IS 'Prometheus-style key-value labels for filtering';
COMMENT ON COLUMN alerts.source IS 'Monitoring system that generated this alert';

-- Create partitions for current year + next year (extend via cron job)
CREATE TABLE alerts_y2026m01 PARTITION OF alerts FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
CREATE TABLE alerts_y2026m02 PARTITION OF alerts FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');
CREATE TABLE alerts_y2026m03 PARTITION OF alerts FOR VALUES FROM ('2026-03-01') TO ('2026-04-01');
CREATE TABLE alerts_y2026m04 PARTITION OF alerts FOR VALUES FROM ('2026-04-01') TO ('2026-05-01');
CREATE TABLE alerts_y2026m05 PARTITION OF alerts FOR VALUES FROM ('2026-05-01') TO ('2026-06-01');
CREATE TABLE alerts_y2026m06 PARTITION OF alerts FOR VALUES FROM ('2026-06-01') TO ('2026-07-01');
CREATE TABLE alerts_y2026m07 PARTITION OF alerts FOR VALUES FROM ('2026-07-01') TO ('2026-08-01');
CREATE TABLE alerts_y2026m08 PARTITION OF alerts FOR VALUES FROM ('2026-08-01') TO ('2026-09-01');
CREATE TABLE alerts_y2026m09 PARTITION OF alerts FOR VALUES FROM ('2026-09-01') TO ('2026-10-01');
CREATE TABLE alerts_y2026m10 PARTITION OF alerts FOR VALUES FROM ('2026-10-01') TO ('2026-11-01');
CREATE TABLE alerts_y2026m11 PARTITION OF alerts FOR VALUES FROM ('2026-11-01') TO ('2026-12-01');
CREATE TABLE alerts_y2026m12 PARTITION OF alerts FOR VALUES FROM ('2026-12-01') TO ('2027-01-01');
CREATE TABLE alerts_y2027m01 PARTITION OF alerts FOR VALUES FROM ('2027-01-01') TO ('2027-02-01');
CREATE TABLE alerts_y2027m02 PARTITION OF alerts FOR VALUES FROM ('2027-02-01') TO ('2027-03-01');
CREATE TABLE alerts_y2027m03 PARTITION OF alerts FOR VALUES FROM ('2027-03-01') TO ('2027-04-01');
CREATE TABLE alerts_y2027m04 PARTITION OF alerts FOR VALUES FROM ('2027-04-01') TO ('2027-05-01');
CREATE TABLE alerts_y2027m05 PARTITION OF alerts FOR VALUES FROM ('2027-05-01') TO ('2027-06-01');
CREATE TABLE alerts_y2027m06 PARTITION OF alerts FOR VALUES FROM ('2027-06-01') TO ('2027-07-01');

-- Default partition catches anything outside defined ranges
CREATE TABLE alerts_default PARTITION OF alerts DEFAULT;

-- ===== operations =====
-- Operations/tickets: inspections, change requests, incidents, maintenance.
CREATE TABLE operations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title           TEXT NOT NULL,
    description     TEXT,
    operation_type  operation_type NOT NULL,
    risk_level      risk_level NOT NULL DEFAULT 'medium',
    status          operation_status NOT NULL DEFAULT 'draft',

    -- Target resources
    target_assets   UUID[] DEFAULT '{}',            -- Array of asset UUIDs this operation targets
    platform_id     UUID REFERENCES platforms(id) ON DELETE SET NULL,

    -- Execution details
    skill_id        UUID,                           -- Skill used for automated execution
    parameters      JSONB NOT NULL DEFAULT '{}',    -- Operation input parameters
    result          JSONB NOT NULL DEFAULT '{}',    -- Execution result summary
    error_message   TEXT,

    -- Scheduling
    scheduled_at    TIMESTAMPTZ,                    -- When to execute (NULL = immediate)
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,

    -- Ownership
    created_by      UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    approved_by     UUID REFERENCES users(id) ON DELETE SET NULL,
    approved_at     TIMESTAMPTZ,

    -- AI Agent context
    conversation_id UUID,                           -- Link to AI conversation that triggered this

    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE operations IS 'Operations/tickets: inspections, change requests, incidents, remediations';
COMMENT ON COLUMN operations.target_assets IS 'Array of asset UUIDs targeted by this operation';
COMMENT ON COLUMN operations.parameters IS 'JSONB input parameters for the operation skill';

-- ===== operation_steps =====
-- Individual steps within an operation. Provides granular execution tracking.
CREATE TABLE operation_steps (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    operation_id    UUID NOT NULL REFERENCES operations(id) ON DELETE CASCADE,
    step_number     SMALLINT NOT NULL,
    name            TEXT NOT NULL,
    description     TEXT,
    status          step_status NOT NULL DEFAULT 'pending',
    command         TEXT,                           -- Command or API call executed
    output          TEXT,                           -- stdout / response
    error_output    TEXT,                           -- stderr / error
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    duration_ms     INTEGER,                        -- Execution time in milliseconds
    metadata        JSONB NOT NULL DEFAULT '{}',

    UNIQUE (operation_id, step_number)
);

COMMENT ON TABLE operation_steps IS 'Granular execution steps within an operation';

-- ===== audit_logs =====
-- Complete audit trail for all actions. Partitioned by created_at.
CREATE TABLE audit_logs (
    id              UUID NOT NULL DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id) ON DELETE SET NULL,
    username        TEXT,                           -- Denormalized for display after user deletion
    action          audit_action NOT NULL,
    resource_type   TEXT NOT NULL,                  -- 'asset', 'alert', 'operation', 'user', etc.
    resource_id     UUID,
    resource_name   TEXT,                           -- Denormalized resource name

    -- Change tracking
    old_values      JSONB,                          -- Previous state (for updates)
    new_values      JSONB,                          -- New state (for creates/updates)

    -- Request context
    ip_address      INET,
    user_agent      TEXT,
    request_id      UUID,                           -- Correlation ID for distributed tracing

    -- Result
    success         BOOLEAN NOT NULL DEFAULT TRUE,
    error_message   TEXT,
    duration_ms     INTEGER,

    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),  -- Partition key

    -- Composite PK required for partitioned tables
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

COMMENT ON TABLE audit_logs IS 'Immutable audit trail for all platform actions; partitioned monthly';
COMMENT ON COLUMN audit_logs.old_values IS 'Previous resource state for update actions';

-- Create partitions
CREATE TABLE audit_logs_y2026m01 PARTITION OF audit_logs FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
CREATE TABLE audit_logs_y2026m02 PARTITION OF audit_logs FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');
CREATE TABLE audit_logs_y2026m03 PARTITION OF audit_logs FOR VALUES FROM ('2026-03-01') TO ('2026-04-01');
CREATE TABLE audit_logs_y2026m04 PARTITION OF audit_logs FOR VALUES FROM ('2026-04-01') TO ('2026-05-01');
CREATE TABLE audit_logs_y2026m05 PARTITION OF audit_logs FOR VALUES FROM ('2026-05-01') TO ('2026-06-01');
CREATE TABLE audit_logs_y2026m06 PARTITION OF audit_logs FOR VALUES FROM ('2026-06-01') TO ('2026-07-01');
CREATE TABLE audit_logs_y2026m07 PARTITION OF audit_logs FOR VALUES FROM ('2026-07-01') TO ('2026-08-01');
CREATE TABLE audit_logs_y2026m08 PARTITION OF audit_logs FOR VALUES FROM ('2026-08-01') TO ('2026-09-01');
CREATE TABLE audit_logs_y2026m09 PARTITION OF audit_logs FOR VALUES FROM ('2026-09-01') TO ('2026-10-01');
CREATE TABLE audit_logs_y2026m10 PARTITION OF audit_logs FOR VALUES FROM ('2026-10-01') TO ('2026-11-01');
CREATE TABLE audit_logs_y2026m11 PARTITION OF audit_logs FOR VALUES FROM ('2026-11-01') TO ('2026-12-01');
CREATE TABLE audit_logs_y2026m12 PARTITION OF audit_logs FOR VALUES FROM ('2026-12-01') TO ('2027-01-01');
CREATE TABLE audit_logs_y2027m01 PARTITION OF audit_logs FOR VALUES FROM ('2027-01-01') TO ('2027-02-01');
CREATE TABLE audit_logs_y2027m02 PARTITION OF audit_logs FOR VALUES FROM ('2027-02-01') TO ('2027-03-01');
CREATE TABLE audit_logs_y2027m03 PARTITION OF audit_logs FOR VALUES FROM ('2027-03-01') TO ('2027-04-01');
CREATE TABLE audit_logs_y2027m04 PARTITION OF audit_logs FOR VALUES FROM ('2027-04-01') TO ('2027-05-01');
CREATE TABLE audit_logs_y2027m05 PARTITION OF audit_logs FOR VALUES FROM ('2027-05-01') TO ('2027-06-01');
CREATE TABLE audit_logs_y2027m06 PARTITION OF audit_logs FOR VALUES FROM ('2027-06-01') TO ('2027-07-01');

CREATE TABLE audit_logs_default PARTITION OF audit_logs DEFAULT;

-- ===== asset_metrics =====
-- Time-series metrics (CPU, memory, disk, network). Heaviest table.
-- Partitioned monthly. Consider TimescaleDB hypertable for automatic management.
CREATE TABLE asset_metrics (
    id              UUID NOT NULL DEFAULT gen_random_uuid(),
    asset_id        UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    metric_name     TEXT NOT NULL,                  -- 'cpu_usage_pct', 'memory_usage_pct', 'disk_usage_pct', etc.
    value           DOUBLE PRECISION NOT NULL,
    unit            TEXT NOT NULL DEFAULT '%',      -- '%', 'MB', 'Mbps', 'ms', 'count'
    labels          JSONB NOT NULL DEFAULT '{}',    -- Additional labels (interface name, mount point)
    recorded_at     TIMESTAMPTZ NOT NULL DEFAULT now(),  -- Partition key

    PRIMARY KEY (id, recorded_at)
) PARTITION BY RANGE (recorded_at);

COMMENT ON TABLE asset_metrics IS 'Time-series metrics for all assets; partitioned monthly by recorded_at';
COMMENT ON COLUMN asset_metrics.metric_name IS 'Standard metric names: cpu_usage_pct, memory_usage_pct, disk_read_mb, etc.';

-- Create partitions
CREATE TABLE asset_metrics_y2026m01 PARTITION OF asset_metrics FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
CREATE TABLE asset_metrics_y2026m02 PARTITION OF asset_metrics FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');
CREATE TABLE asset_metrics_y2026m03 PARTITION OF asset_metrics FOR VALUES FROM ('2026-03-01') TO ('2026-04-01');
CREATE TABLE asset_metrics_y2026m04 PARTITION OF asset_metrics FOR VALUES FROM ('2026-04-01') TO ('2026-05-01');
CREATE TABLE asset_metrics_y2026m05 PARTITION OF asset_metrics FOR VALUES FROM ('2026-05-01') TO ('2026-06-01');
CREATE TABLE asset_metrics_y2026m06 PARTITION OF asset_metrics FOR VALUES FROM ('2026-06-01') TO ('2026-07-01');
CREATE TABLE asset_metrics_y2026m07 PARTITION OF asset_metrics FOR VALUES FROM ('2026-07-01') TO ('2026-08-01');
CREATE TABLE asset_metrics_y2026m08 PARTITION OF asset_metrics FOR VALUES FROM ('2026-08-01') TO ('2026-09-01');
CREATE TABLE asset_metrics_y2026m09 PARTITION OF asset_metrics FOR VALUES FROM ('2026-09-01') TO ('2026-10-01');
CREATE TABLE asset_metrics_y2026m10 PARTITION OF asset_metrics FOR VALUES FROM ('2026-10-01') TO ('2026-11-01');
CREATE TABLE asset_metrics_y2026m11 PARTITION OF asset_metrics FOR VALUES FROM ('2026-11-01') TO ('2026-12-01');
CREATE TABLE asset_metrics_y2026m12 PARTITION OF asset_metrics FOR VALUES FROM ('2026-12-01') TO ('2027-01-01');
CREATE TABLE asset_metrics_y2027m01 PARTITION OF asset_metrics FOR VALUES FROM ('2027-01-01') TO ('2027-02-01');
CREATE TABLE asset_metrics_y2027m02 PARTITION OF asset_metrics FOR VALUES FROM ('2027-02-01') TO ('2027-03-01');
CREATE TABLE asset_metrics_y2027m03 PARTITION OF asset_metrics FOR VALUES FROM ('2027-03-01') TO ('2027-04-01');
CREATE TABLE asset_metrics_y2027m04 PARTITION OF asset_metrics FOR VALUES FROM ('2027-04-01') TO ('2027-05-01');
CREATE TABLE asset_metrics_y2027m05 PARTITION OF asset_metrics FOR VALUES FROM ('2027-05-01') TO ('2027-06-01');
CREATE TABLE asset_metrics_y2027m06 PARTITION OF asset_metrics FOR VALUES FROM ('2027-06-01') TO ('2027-07-01');

CREATE TABLE asset_metrics_default PARTITION OF asset_metrics DEFAULT;

-- ===== skills =====
-- Skill/workflow definitions (YAML-based automation).
CREATE TABLE skills (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL UNIQUE,
    display_name    TEXT NOT NULL,
    description     TEXT,
    category        TEXT NOT NULL DEFAULT 'general', -- 'inspection', 'remediation', 'verification', 'context'
    version         TEXT NOT NULL DEFAULT '1.0.0',
    status          skill_status NOT NULL DEFAULT 'active',

    -- Skill definition
    yaml_content    TEXT NOT NULL,                  -- Full YAML skill definition
    parameters      JSONB NOT NULL DEFAULT '{}',    -- Input parameter schema (JSON Schema)
    output_schema   JSONB NOT NULL DEFAULT '{}',    -- Output schema

    -- Execution config
    timeout_seconds INTEGER NOT NULL DEFAULT 300,
    max_retries     SMALLINT NOT NULL DEFAULT 0,
    requires_approval BOOLEAN NOT NULL DEFAULT FALSE,
    risk_level      risk_level NOT NULL DEFAULT 'medium',

    -- Metadata
    author          TEXT,
    tags            TEXT[] DEFAULT '{}',
    platform_types  platform_type[] DEFAULT '{}',   -- Supported platforms

    created_by      UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE skills IS 'YAML-based automation skill definitions for inspections and remediations';
COMMENT ON COLUMN skills.yaml_content IS 'Complete YAML skill definition including steps, conditions, rollback';

-- ===== conversations =====
-- AI Agent conversation history. Supports multi-turn dialogues.
CREATE TABLE conversations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title           TEXT,
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status          conversation_status NOT NULL DEFAULT 'active',

    -- Context
    platform_id     UUID REFERENCES platforms(id) ON DELETE SET NULL,
    target_assets   UUID[] DEFAULT '{}',
    operation_id    UUID REFERENCES operations(id) ON DELETE SET NULL,

    -- Messages stored as JSONB array for efficient retrieval
    messages        JSONB NOT NULL DEFAULT '[]',    -- [{role, content, timestamp, tokens}]
    message_count   INTEGER NOT NULL DEFAULT 0,
    total_tokens    INTEGER NOT NULL DEFAULT 0,

    -- Model info
    model_id        TEXT,                           -- 'claude-3.5-sonnet', 'gpt-4', etc.
    system_prompt   TEXT,

    metadata        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE conversations IS 'AI Agent multi-turn conversation history';
COMMENT ON COLUMN conversations.messages IS 'Array of {role, content, timestamp, token_count} objects';


-- ---------------------------------------------------------------------------
-- 3. Indexes
-- ---------------------------------------------------------------------------

-- ===== users =====
-- (username, email already have UNIQUE indexes)

-- ===== platforms =====
CREATE INDEX idx_platforms_type ON platforms(platform_type);
CREATE INDEX idx_platforms_active ON platforms(is_active) WHERE is_active = TRUE;

-- ===== assets =====
-- Primary search patterns: name, IP, platform, status, cluster, type
CREATE INDEX idx_assets_name ON assets(name);
CREATE INDEX idx_assets_name_trgm ON assets USING gin(name gin_trgm_ops);  -- LIKE/ILIKE support
CREATE INDEX idx_assets_type ON assets(asset_type);
CREATE INDEX idx_assets_status ON assets(status);
CREATE INDEX idx_assets_platform_id ON assets(platform_id);
CREATE INDEX idx_assets_platform_type ON assets(platform_type);
CREATE INDEX idx_assets_cluster ON assets(cluster_name) WHERE cluster_name IS NOT NULL;
CREATE INDEX idx_assets_datacenter ON assets(datacenter) WHERE datacenter IS NOT NULL;
CREATE INDEX idx_assets_ip ON assets USING gin(ip_addresses);  -- Array contains search
CREATE INDEX idx_assets_external_id ON assets(platform_id, external_id); -- Duplicate check + lookup
CREATE INDEX idx_assets_last_seen ON assets(last_seen_at);
CREATE INDEX idx_assets_metadata ON assets USING gin(metadata jsonb_path_ops);  -- JSONB search

-- ===== asset_relations =====
CREATE INDEX idx_asset_relations_source ON asset_relations(source_asset_id);
CREATE INDEX idx_asset_relations_target ON asset_relations(target_asset_id);
CREATE INDEX idx_asset_relations_type ON asset_relations(relation_type);

-- ===== alerts =====
-- Filter patterns: severity, status, resource, time range
CREATE INDEX idx_alerts_severity ON alerts(severity);
CREATE INDEX idx_alerts_status ON alerts(status);
CREATE INDEX idx_alerts_asset_id ON alerts(asset_id);
CREATE INDEX idx_alerts_source ON alerts(source);
CREATE INDEX idx_alerts_firing_at ON alerts(firing_at);
CREATE INDEX idx_alerts_created_at ON alerts(created_at);
-- Composite for dashboard queries: active alerts by severity
CREATE INDEX idx_alerts_status_severity ON alerts(status, severity) WHERE status = 'firing';
-- For alert deduplication
CREATE INDEX idx_alerts_external_source ON alerts(source, external_id) WHERE external_id IS NOT NULL;

-- ===== operations =====
-- Filter patterns: status, type, risk level, time range
CREATE INDEX idx_operations_type ON operations(operation_type);
CREATE INDEX idx_operations_status ON operations(status);
CREATE INDEX idx_operations_risk ON operations(risk_level);
CREATE INDEX idx_operations_created_by ON operations(created_by);
CREATE INDEX idx_operations_platform ON operations(platform_id);
CREATE INDEX idx_operations_scheduled ON operations(scheduled_at) WHERE scheduled_at IS NOT NULL;
CREATE INDEX idx_operations_created_at ON operations(created_at);
-- Composite for dashboard: active operations
CREATE INDEX idx_operations_active ON operations(status, created_at) WHERE status IN ('draft', 'pending_approval', 'approved', 'executing');

-- ===== operation_steps =====
CREATE INDEX idx_operation_steps_op ON operation_steps(operation_id);
CREATE INDEX idx_operation_steps_status ON operation_steps(status);

-- ===== audit_logs =====
-- Search patterns: user, action, resource, time range
CREATE INDEX idx_audit_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_action ON audit_logs(action);
CREATE INDEX idx_audit_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_created_at ON audit_logs(created_at);
CREATE INDEX idx_audit_request_id ON audit_logs(request_id) WHERE request_id IS NOT NULL;

-- ===== asset_metrics =====
-- Primary query: asset + metric + time range
CREATE INDEX idx_metrics_asset_time ON asset_metrics(asset_id, recorded_at DESC);
CREATE INDEX idx_metrics_name ON asset_metrics(metric_name);
CREATE INDEX idx_metrics_recorded_at ON asset_metrics(recorded_at);
-- Composite for latest-value queries
CREATE INDEX idx_metrics_asset_name_time ON asset_metrics(asset_id, metric_name, recorded_at DESC);

-- ===== skills =====
CREATE INDEX idx_skills_category ON skills(category);
CREATE INDEX idx_skills_status ON skills(status) WHERE status = 'active';
CREATE INDEX idx_skills_tags ON skills USING gin(tags);
CREATE INDEX idx_skills_platforms ON skills USING gin(platform_types);

-- ===== conversations =====
CREATE INDEX idx_conversations_user ON conversations(user_id);
CREATE INDEX idx_conversations_status ON conversations(status) WHERE status = 'active';
CREATE INDEX idx_conversations_operation ON conversations(operation_id) WHERE operation_id IS NOT NULL;
CREATE INDEX idx_conversations_created_at ON conversations(created_at);


-- ---------------------------------------------------------------------------
-- 4. Utility Functions
-- ---------------------------------------------------------------------------

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at trigger to all tables with updated_at column
CREATE TRIGGER trg_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_platforms_updated_at BEFORE UPDATE ON platforms
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_assets_updated_at BEFORE UPDATE ON assets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_operations_updated_at BEFORE UPDATE ON operations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_skills_updated_at BEFORE UPDATE ON skills
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_conversations_updated_at BEFORE UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Auto-update message_count on conversations
CREATE OR REPLACE FUNCTION update_conversation_stats()
RETURNS TRIGGER AS $$
BEGIN
    NEW.message_count = jsonb_array_length(NEW.messages);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_conversations_stats BEFORE INSERT OR UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION update_conversation_stats();


-- ---------------------------------------------------------------------------
-- 5. Partition Maintenance (run via pg_cron or external scheduler)
-- ---------------------------------------------------------------------------

-- Function to create future partitions (call monthly)
CREATE OR REPLACE FUNCTION create_monthly_partitions(
    p_table_name TEXT,
    p_months_ahead INTEGER DEFAULT 3
)
RETURNS VOID AS $$
DECLARE
    v_start DATE;
    v_end DATE;
    v_partition_name TEXT;
    v_month DATE;
BEGIN
    FOR i IN 0..p_months_ahead LOOP
        v_month := date_trunc('month', CURRENT_DATE) + (i || ' months')::INTERVAL;
        v_start := v_month;
        v_end := v_month + INTERVAL '1 month';
        v_partition_name := p_table_name || '_y' || to_char(v_month, 'YYYY') || 'm' || to_char(v_month, 'MM');

        -- Skip if partition already exists
        IF NOT EXISTS (
            SELECT 1 FROM pg_class WHERE relname = v_partition_name
        ) THEN
            EXECUTE format(
                'CREATE TABLE IF NOT EXISTS %I PARTITION OF %I FOR VALUES FROM (%L) TO (%L)',
                v_partition_name, p_table_name, v_start, v_end
            );
            RAISE NOTICE 'Created partition: %', v_partition_name;
        END IF;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Function to drop old partitions (retention policy)
CREATE OR REPLACE FUNCTION drop_old_partitions(
    p_table_name TEXT,
    p_retention_months INTEGER
)
RETURNS VOID AS $$
DECLARE
    v_cutoff DATE;
    v_rec RECORD;
BEGIN
    v_cutoff := date_trunc('month', CURRENT_DATE) - (p_retention_months || ' months')::INTERVAL;

    FOR v_rec IN
        SELECT tablename FROM pg_tables
        WHERE schemaname = 'public'
        AND tablename LIKE p_table_name || '_y%'
        AND tablename < p_table_name || '_y' || to_char(v_cutoff, 'YYYY') || 'm' || to_char(v_cutoff, 'MM')
    LOOP
        EXECUTE format('DROP TABLE IF EXISTS %I', v_rec.tablename);
        RAISE NOTICE 'Dropped partition: %', v_rec.tablename;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Example maintenance schedule (run monthly via pg_cron):
-- SELECT create_monthly_partitions('alerts', 3);
-- SELECT create_monthly_partitions('audit_logs', 3);
-- SELECT create_monthly_partitions('asset_metrics', 3);
-- SELECT drop_old_partitions('asset_metrics', 6);   -- Keep 6 months of metrics
-- SELECT drop_old_partitions('alerts', 12);          -- Keep 1 year of alerts
-- SELECT drop_old_partitions('audit_logs', 24);      -- Keep 2 years of audit logs


-- ---------------------------------------------------------------------------
-- 6. Row Level Security (RLS) — Enable for multi-tenant deployments
-- ---------------------------------------------------------------------------

-- Uncomment and customize for multi-tenant setups:
-- ALTER TABLE assets ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY assets_tenant_isolation ON assets
--     USING (platform_id IN (
--         SELECT p.id FROM platforms p
--         JOIN users u ON u.id = (SELECT auth.uid())
--         WHERE u.role = 'admin' OR p.created_by = u.id
--     ));


-- ---------------------------------------------------------------------------
-- 7. Application Roles
-- ---------------------------------------------------------------------------

-- Create application role with least privilege
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'sre_app') THEN
        CREATE ROLE sre_app LOGIN PASSWORD 'CHANGE_ME_IN_PRODUCTION';
    END IF;
END
$$;

GRANT CONNECT ON DATABASE sre_platform TO sre_app;
GRANT USAGE ON SCHEMA public TO sre_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO sre_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO sre_app;
-- Grant EXECUTE on functions
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO sre_app;

-- Read-only role for dashboards / reporting
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'sre_readonly') THEN
        CREATE ROLE sre_readonly LOGIN PASSWORD 'CHANGE_ME_IN_PRODUCTION';
    END IF;
END
$$;

GRANT CONNECT ON DATABASE sre_platform TO sre_readonly;
GRANT USAGE ON SCHEMA public TO sre_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO sre_readonly;


-- ---------------------------------------------------------------------------
-- 8. Performance Settings (apply via ALTER SYSTEM or postgresql.conf)
-- ---------------------------------------------------------------------------

-- Recommended PostgreSQL configuration for this workload:
-- shared_buffers = 4GB                    (25% of RAM for 16GB server)
-- effective_cache_size = 12GB             (75% of RAM)
-- work_mem = 64MB                         (for complex sorts/hashes)
-- maintenance_work_mem = 1GB              (for VACUUM, CREATE INDEX)
-- max_parallel_workers_per_gather = 4     (parallel query)
-- max_parallel_workers = 8
-- random_page_cost = 1.1                  (for SSD storage)
-- effective_io_concurrency = 200          (for SSD)
-- wal_buffers = 64MB
-- max_wal_size = 4GB
-- checkpoint_completion_target = 0.9
-- autovacuum_max_workers = 4
-- autovacuum_naptime = 30s                (more frequent for high-write tables)
-- Enable pg_stat_statements: shared_preload_libraries = 'pg_stat_statements'


-- ============================================================================
-- End of schema.sql
-- ============================================================================
