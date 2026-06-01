"""001_initial — V3.1 SRE Platform initial schema migration.

Creates all core tables, enum types, indexes, partition management functions,
and utility triggers. Designed for PostgreSQL 16+.

Revision ID: 001_initial
Create Date: 2026-05-30
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import (
    UUID, JSONB, INET, ARRAY, ENUM
)

# revision identifiers
revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


# ---------------------------------------------------------------------------
# Enum type definitions (created separately so they can be referenced)
# ---------------------------------------------------------------------------
ASSET_TYPE = ENUM(
    "vm", "physical_host", "storage_device", "network_device",
    "container_host", "cluster", "datastore", "load_balancer",
    name="asset_type", create_type=True
)

ASSET_STATUS = ENUM(
    "active", "maintenance", "decommissioned", "unknown",
    "provisioning", "error",
    name="asset_status", create_type=True
)

PLATFORM_TYPE = ENUM(
    "vmware_vsphere", "openstack", "kubernetes", "physical",
    "fusion_sphere", "storage_array", "network",
    name="platform_type", create_type=True
)

ALERT_SEVERITY = ENUM(
    "critical", "high", "medium", "low", "info",
    name="alert_severity", create_type=True
)

ALERT_STATUS = ENUM(
    "firing", "acknowledged", "resolved", "silenced", "expired",
    name="alert_status", create_type=True
)

OPERATION_TYPE = ENUM(
    "inspection", "change_request", "incident",
    "maintenance", "remediation", "audit",
    name="operation_type", create_type=True
)

RISK_LEVEL = ENUM(
    "critical", "high", "medium", "low", "none",
    name="risk_level", create_type=True
)

OPERATION_STATUS = ENUM(
    "draft", "pending_approval", "approved", "executing",
    "completed", "failed", "cancelled", "rolled_back",
    name="operation_status", create_type=True
)

STEP_STATUS = ENUM(
    "pending", "running", "completed", "failed",
    "skipped", "rolled_back",
    name="step_status", create_type=True
)

AUDIT_ACTION = ENUM(
    "create", "read", "update", "delete", "execute",
    "login", "logout", "export", "import", "approve", "reject",
    name="audit_action", create_type=True
)

USER_ROLE = ENUM(
    "admin", "operator", "viewer", "auditor", "ai_agent",
    name="user_role", create_type=True
)

CONVERSATION_STATUS = ENUM(
    "active", "archived", "deleted",
    name="conversation_status", create_type=True
)

SKILL_STATUS = ENUM(
    "active", "disabled", "draft", "deprecated",
    name="skill_status", create_type=True
)


def _create_partitioned_table(table_name, columns_def, partition_col, pk_cols):
    """Helper to create a range-partitioned table with monthly partitions.

    Args:
        table_name: Name of the parent table.
        columns_def: SQLAlchemy Column objects (without PK constraint in columns_def).
        partition_col: Column name to partition by (must be timestamptz).
        pk_cols: List of column names for composite primary key.
    """
    # Partitioned tables require composite PK that includes the partition key.
    # We build the CREATE TABLE manually to support this.
    pass  # Actual creation done via op.execute() in upgrade()


def upgrade() -> None:
    # -----------------------------------------------------------------------
    # Extensions
    # -----------------------------------------------------------------------
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "btree_gin"')

    # -----------------------------------------------------------------------
    # Enum types
    # -----------------------------------------------------------------------
    ASSET_TYPE.create(op.get_bind(), checkfirst=True)
    ASSET_STATUS.create(op.get_bind(), checkfirst=True)
    PLATFORM_TYPE.create(op.get_bind(), checkfirst=True)
    ALERT_SEVERITY.create(op.get_bind(), checkfirst=True)
    ALERT_STATUS.create(op.get_bind(), checkfirst=True)
    OPERATION_TYPE.create(op.get_bind(), checkfirst=True)
    RISK_LEVEL.create(op.get_bind(), checkfirst=True)
    OPERATION_STATUS.create(op.get_bind(), checkfirst=True)
    STEP_STATUS.create(op.get_bind(), checkfirst=True)
    AUDIT_ACTION.create(op.get_bind(), checkfirst=True)
    USER_ROLE.create(op.get_bind(), checkfirst=True)
    CONVERSATION_STATUS.create(op.get_bind(), checkfirst=True)
    SKILL_STATUS.create(op.get_bind(), checkfirst=True)

    # -----------------------------------------------------------------------
    # users
    # -----------------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("username", sa.Text, nullable=False, unique=True),
        sa.Column("email", sa.Text, unique=True),
        sa.Column("display_name", sa.Text, nullable=False),
        sa.Column("password_hash", sa.Text),
        sa.Column("role", USER_ROLE, nullable=False, server_default="viewer"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("TRUE")),
        sa.Column("last_login_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("api_key_hash", sa.Text),
        sa.Column("preferences", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.execute("COMMENT ON TABLE users IS 'User accounts including human operators and AI agent service accounts'")

    # -----------------------------------------------------------------------
    # platforms
    # -----------------------------------------------------------------------
    op.create_table(
        "platforms",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("platform_type", PLATFORM_TYPE, nullable=False),
        sa.Column("endpoint", sa.Text, nullable=False),
        sa.Column("credentials", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("config", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("TRUE")),
        sa.Column("last_sync_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("sync_status", sa.Text),
        sa.Column("sync_error", sa.Text),
        sa.Column("created_by", UUID, sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.execute("COMMENT ON TABLE platforms IS 'Platform adapter connection configs (vCenter, OpenStack, K8s, etc.)'")

    # -----------------------------------------------------------------------
    # assets
    # -----------------------------------------------------------------------
    op.create_table(
        "assets",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("external_id", sa.Text),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("asset_type", ASSET_TYPE, nullable=False),
        sa.Column("platform_id", UUID, sa.ForeignKey("platforms.id", ondelete="SET NULL")),
        sa.Column("platform_type", PLATFORM_TYPE, nullable=False),
        sa.Column("status", ASSET_STATUS, nullable=False, server_default="active"),
        sa.Column("ip_addresses", ARRAY(sa.Text), server_default=sa.text("'{}'::text[]")),
        sa.Column("mac_addresses", ARRAY(sa.Text), server_default=sa.text("'{}'::text[]")),
        sa.Column("cluster_name", sa.Text),
        sa.Column("datacenter", sa.Text),
        sa.Column("folder_path", sa.Text),
        sa.Column("cpu_cores", sa.SmallInteger),
        sa.Column("memory_mb", sa.Integer),
        sa.Column("disk_gb", sa.Integer),
        sa.Column("os_type", sa.Text),
        sa.Column("os_version", sa.Text),
        sa.Column("metadata", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("discovered_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("last_seen_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("platform_id", "external_id", name="uq_assets_platform_external"),
    )
    op.execute("COMMENT ON TABLE assets IS 'Unified asset registry for all infrastructure objects across all platforms'")

    # -----------------------------------------------------------------------
    # asset_relations
    # -----------------------------------------------------------------------
    op.create_table(
        "asset_relations",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("source_asset_id", UUID, sa.ForeignKey("assets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_asset_id", UUID, sa.ForeignKey("assets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("relation_type", sa.Text, nullable=False),
        sa.Column("metadata", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("source_asset_id", "target_asset_id", "relation_type",
                            name="uq_asset_relations_triple"),
    )
    op.execute("COMMENT ON TABLE asset_relations IS 'Directed dependency graph between assets'")

    # -----------------------------------------------------------------------
    # alerts (partitioned)
    # -----------------------------------------------------------------------
    # Partitioned tables cannot use op.create_table() easily — use raw DDL
    op.execute("""
        CREATE TABLE alerts (
            id              UUID NOT NULL DEFAULT gen_random_uuid(),
            external_id     TEXT,
            source          TEXT NOT NULL,
            title           TEXT NOT NULL,
            description     TEXT,
            severity        alert_severity NOT NULL,
            status          alert_status NOT NULL DEFAULT 'firing',
            asset_id        UUID REFERENCES assets(id) ON DELETE SET NULL,
            resource_name   TEXT,
            resource_type   TEXT,
            labels          JSONB NOT NULL DEFAULT '{}'::jsonb,
            annotations     JSONB NOT NULL DEFAULT '{}'::jsonb,
            value           DOUBLE PRECISION,
            threshold       DOUBLE PRECISION,
            firing_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
            acknowledged_at TIMESTAMPTZ,
            acknowledged_by UUID REFERENCES users(id) ON DELETE SET NULL,
            resolved_at     TIMESTAMPTZ,
            resolved_by     UUID REFERENCES users(id) ON DELETE SET NULL,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
            PRIMARY KEY (id, created_at)
        ) PARTITION BY RANGE (created_at)
    """)
    op.execute("COMMENT ON TABLE alerts IS 'Alert records from all monitoring sources; partitioned monthly'")

    # Create 18 monthly partitions (current + next year + 6 months buffer)
    for year in [2026, 2027]:
        for month in range(1, 13):
            if year == 2027 and month > 6:
                break
            start = f"{year}-{month:02d}-01"
            if month == 12:
                end = f"{year + 1}-01-01"
            else:
                end = f"{year}-{month + 1:02d}-01"
            pname = f"alerts_y{year}m{month:02d}"
            op.execute(
                f"CREATE TABLE {pname} PARTITION OF alerts "
                f"FOR VALUES FROM ('{start}') TO ('{end}')"
            )
    op.execute("CREATE TABLE alerts_default PARTITION OF alerts DEFAULT")

    # -----------------------------------------------------------------------
    # operations
    # -----------------------------------------------------------------------
    op.create_table(
        "operations",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("operation_type", OPERATION_TYPE, nullable=False),
        sa.Column("risk_level", RISK_LEVEL, nullable=False, server_default="medium"),
        sa.Column("status", OPERATION_STATUS, nullable=False, server_default="draft"),
        sa.Column("target_assets", ARRAY(UUID), server_default=sa.text("'{}'::uuid[]")),
        sa.Column("platform_id", UUID, sa.ForeignKey("platforms.id", ondelete="SET NULL")),
        sa.Column("skill_id", UUID),
        sa.Column("parameters", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("result", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("error_message", sa.Text),
        sa.Column("scheduled_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("started_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("created_by", UUID, sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("approved_by", UUID, sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("approved_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("conversation_id", UUID),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.execute("COMMENT ON TABLE operations IS 'Operations/tickets: inspections, change requests, incidents, remediations'")

    # -----------------------------------------------------------------------
    # operation_steps
    # -----------------------------------------------------------------------
    op.create_table(
        "operation_steps",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("operation_id", UUID, sa.ForeignKey("operations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("step_number", sa.SmallInteger, nullable=False),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("status", STEP_STATUS, nullable=False, server_default="pending"),
        sa.Column("command", sa.Text),
        sa.Column("output", sa.Text),
        sa.Column("error_output", sa.Text),
        sa.Column("started_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("duration_ms", sa.Integer),
        sa.Column("metadata", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.UniqueConstraint("operation_id", "step_number", name="uq_operation_steps_number"),
    )
    op.execute("COMMENT ON TABLE operation_steps IS 'Granular execution steps within an operation'")

    # -----------------------------------------------------------------------
    # audit_logs (partitioned)
    # -----------------------------------------------------------------------
    op.execute("""
        CREATE TABLE audit_logs (
            id              UUID NOT NULL DEFAULT gen_random_uuid(),
            user_id         UUID REFERENCES users(id) ON DELETE SET NULL,
            username        TEXT,
            action          audit_action NOT NULL,
            resource_type   TEXT NOT NULL,
            resource_id     UUID,
            resource_name   TEXT,
            old_values      JSONB,
            new_values      JSONB,
            ip_address      INET,
            user_agent      TEXT,
            request_id      UUID,
            success         BOOLEAN NOT NULL DEFAULT TRUE,
            error_message   TEXT,
            duration_ms     INTEGER,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
            PRIMARY KEY (id, created_at)
        ) PARTITION BY RANGE (created_at)
    """)
    op.execute("COMMENT ON TABLE audit_logs IS 'Immutable audit trail for all platform actions; partitioned monthly'")

    for year in [2026, 2027]:
        for month in range(1, 13):
            if year == 2027 and month > 6:
                break
            start = f"{year}-{month:02d}-01"
            if month == 12:
                end = f"{year + 1}-01-01"
            else:
                end = f"{year}-{month + 1:02d}-01"
            pname = f"audit_logs_y{year}m{month:02d}"
            op.execute(
                f"CREATE TABLE {pname} PARTITION OF audit_logs "
                f"FOR VALUES FROM ('{start}') TO ('{end}')"
            )
    op.execute("CREATE TABLE audit_logs_default PARTITION OF audit_logs DEFAULT")

    # -----------------------------------------------------------------------
    # asset_metrics (partitioned)
    # -----------------------------------------------------------------------
    op.execute("""
        CREATE TABLE asset_metrics (
            id              UUID NOT NULL DEFAULT gen_random_uuid(),
            asset_id        UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
            metric_name     TEXT NOT NULL,
            value           DOUBLE PRECISION NOT NULL,
            unit            TEXT NOT NULL DEFAULT '%',
            labels          JSONB NOT NULL DEFAULT '{}'::jsonb,
            recorded_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
            PRIMARY KEY (id, recorded_at)
        ) PARTITION BY RANGE (recorded_at)
    """)
    op.execute("COMMENT ON TABLE asset_metrics IS 'Time-series metrics for all assets; partitioned monthly'")

    for year in [2026, 2027]:
        for month in range(1, 13):
            if year == 2027 and month > 6:
                break
            start = f"{year}-{month:02d}-01"
            if month == 12:
                end = f"{year + 1}-01-01"
            else:
                end = f"{year}-{month + 1:02d}-01"
            pname = f"asset_metrics_y{year}m{month:02d}"
            op.execute(
                f"CREATE TABLE {pname} PARTITION OF asset_metrics "
                f"FOR VALUES FROM ('{start}') TO ('{end}')"
            )
    op.execute("CREATE TABLE asset_metrics_default PARTITION OF asset_metrics DEFAULT")

    # -----------------------------------------------------------------------
    # skills
    # -----------------------------------------------------------------------
    op.create_table(
        "skills",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.Text, nullable=False, unique=True),
        sa.Column("display_name", sa.Text, nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("category", sa.Text, nullable=False, server_default="general"),
        sa.Column("version", sa.Text, nullable=False, server_default="1.0.0"),
        sa.Column("status", SKILL_STATUS, nullable=False, server_default="active"),
        sa.Column("yaml_content", sa.Text, nullable=False),
        sa.Column("parameters", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("output_schema", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("timeout_seconds", sa.Integer, nullable=False, server_default=sa.text("300")),
        sa.Column("max_retries", sa.SmallInteger, nullable=False, server_default=sa.text("0")),
        sa.Column("requires_approval", sa.Boolean, nullable=False, server_default=sa.text("FALSE")),
        sa.Column("risk_level", RISK_LEVEL, nullable=False, server_default="medium"),
        sa.Column("author", sa.Text),
        sa.Column("tags", ARRAY(sa.Text), server_default=sa.text("'{}'::text[]")),
        sa.Column("platform_types", ARRAY(PLATFORM_TYPE), server_default=sa.text("'{}'::platform_type[]")),
        sa.Column("created_by", UUID, sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.execute("COMMENT ON TABLE skills IS 'YAML-based automation skill definitions'")

    # -----------------------------------------------------------------------
    # conversations
    # -----------------------------------------------------------------------
    op.create_table(
        "conversations",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("title", sa.Text),
        sa.Column("user_id", UUID, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", CONVERSATION_STATUS, nullable=False, server_default="active"),
        sa.Column("platform_id", UUID, sa.ForeignKey("platforms.id", ondelete="SET NULL")),
        sa.Column("target_assets", ARRAY(UUID), server_default=sa.text("'{}'::uuid[]")),
        sa.Column("operation_id", UUID, sa.ForeignKey("operations.id", ondelete="SET NULL")),
        sa.Column("messages", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("message_count", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("total_tokens", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("model_id", sa.Text),
        sa.Column("system_prompt", sa.Text),
        sa.Column("metadata", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.execute("COMMENT ON TABLE conversations IS 'AI Agent multi-turn conversation history'")

    # -----------------------------------------------------------------------
    # Indexes
    # -----------------------------------------------------------------------

    # -- platforms
    op.create_index("idx_platforms_type", "platforms", ["platform_type"])
    op.execute("CREATE INDEX idx_platforms_active ON platforms(is_active) WHERE is_active = TRUE")

    # -- assets
    op.create_index("idx_assets_name", "assets", ["name"])
    op.execute("CREATE INDEX idx_assets_name_trgm ON assets USING gin(name gin_trgm_ops)")
    op.create_index("idx_assets_type", "assets", ["asset_type"])
    op.create_index("idx_assets_status", "assets", ["status"])
    op.create_index("idx_assets_platform_id", "assets", ["platform_id"])
    op.create_index("idx_assets_platform_type", "assets", ["platform_type"])
    op.execute("CREATE INDEX idx_assets_cluster ON assets(cluster_name) WHERE cluster_name IS NOT NULL")
    op.execute("CREATE INDEX idx_assets_datacenter ON assets(datacenter) WHERE datacenter IS NOT NULL")
    op.execute("CREATE INDEX idx_assets_ip ON assets USING gin(ip_addresses)")
    op.create_index("idx_assets_external_id", "assets", ["platform_id", "external_id"])
    op.create_index("idx_assets_last_seen", "assets", ["last_seen_at"])
    op.execute("CREATE INDEX idx_assets_metadata ON assets USING gin(metadata jsonb_path_ops)")

    # -- asset_relations
    op.create_index("idx_asset_relations_source", "asset_relations", ["source_asset_id"])
    op.create_index("idx_asset_relations_target", "asset_relations", ["target_asset_id"])
    op.create_index("idx_asset_relations_type", "asset_relations", ["relation_type"])

    # -- alerts (on partitioned table — indexes propagate to partitions)
    op.create_index("idx_alerts_severity", "alerts", ["severity"])
    op.create_index("idx_alerts_status", "alerts", ["status"])
    op.create_index("idx_alerts_asset_id", "alerts", ["asset_id"])
    op.create_index("idx_alerts_source", "alerts", ["source"])
    op.create_index("idx_alerts_firing_at", "alerts", ["firing_at"])
    op.create_index("idx_alerts_created_at", "alerts", ["created_at"])
    op.execute(
        "CREATE INDEX idx_alerts_status_severity ON alerts(status, severity) "
        "WHERE status = 'firing'"
    )
    op.execute(
        "CREATE INDEX idx_alerts_external_source ON alerts(source, external_id) "
        "WHERE external_id IS NOT NULL"
    )

    # -- operations
    op.create_index("idx_operations_type", "operations", ["operation_type"])
    op.create_index("idx_operations_status", "operations", ["status"])
    op.create_index("idx_operations_risk", "operations", ["risk_level"])
    op.create_index("idx_operations_created_by", "operations", ["created_by"])
    op.create_index("idx_operations_platform", "operations", ["platform_id"])
    op.execute("CREATE INDEX idx_operations_scheduled ON operations(scheduled_at) WHERE scheduled_at IS NOT NULL")
    op.create_index("idx_operations_created_at", "operations", ["created_at"])
    op.execute(
        "CREATE INDEX idx_operations_active ON operations(status, created_at) "
        "WHERE status IN ('draft', 'pending_approval', 'approved', 'executing')"
    )

    # -- operation_steps
    op.create_index("idx_operation_steps_op", "operation_steps", ["operation_id"])
    op.create_index("idx_operation_steps_status", "operation_steps", ["status"])

    # -- audit_logs
    op.create_index("idx_audit_user_id", "audit_logs", ["user_id"])
    op.create_index("idx_audit_action", "audit_logs", ["action"])
    op.create_index("idx_audit_resource", "audit_logs", ["resource_type", "resource_id"])
    op.create_index("idx_audit_created_at", "audit_logs", ["created_at"])
    op.execute("CREATE INDEX idx_audit_request_id ON audit_logs(request_id) WHERE request_id IS NOT NULL")

    # -- asset_metrics
    op.execute("CREATE INDEX idx_metrics_asset_time ON asset_metrics(asset_id, recorded_at DESC)")
    op.create_index("idx_metrics_name", "asset_metrics", ["metric_name"])
    op.create_index("idx_metrics_recorded_at", "asset_metrics", ["recorded_at"])
    op.execute("CREATE INDEX idx_metrics_asset_name_time ON asset_metrics(asset_id, metric_name, recorded_at DESC)")

    # -- skills
    op.create_index("idx_skills_category", "skills", ["category"])
    op.execute("CREATE INDEX idx_skills_status ON skills(status) WHERE status = 'active'")
    op.execute("CREATE INDEX idx_skills_tags ON skills USING gin(tags)")
    op.execute("CREATE INDEX idx_skills_platforms ON skills USING gin(platform_types)")

    # -- conversations
    op.create_index("idx_conversations_user", "conversations", ["user_id"])
    op.execute("CREATE INDEX idx_conversations_status ON conversations(status) WHERE status = 'active'")
    op.execute("CREATE INDEX idx_conversations_operation ON conversations(operation_id) WHERE operation_id IS NOT NULL")
    op.create_index("idx_conversations_created_at", "conversations", ["created_at"])

    # -----------------------------------------------------------------------
    # Triggers
    # -----------------------------------------------------------------------
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """)

    for tbl in ["users", "platforms", "assets", "operations", "skills", "conversations"]:
        op.execute(
            f"CREATE TRIGGER trg_{tbl}_updated_at BEFORE UPDATE ON {tbl} "
            f"FOR EACH ROW EXECUTE FUNCTION update_updated_at()"
        )

    op.execute("""
        CREATE OR REPLACE FUNCTION update_conversation_stats()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.message_count = jsonb_array_length(NEW.messages);
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """)

    op.execute(
        "CREATE TRIGGER trg_conversations_stats BEFORE INSERT OR UPDATE ON conversations "
        "FOR EACH ROW EXECUTE FUNCTION update_conversation_stats()"
    )

    # -----------------------------------------------------------------------
    # Partition maintenance functions
    # -----------------------------------------------------------------------
    op.execute("""
        CREATE OR REPLACE FUNCTION create_monthly_partitions(
            p_table_name TEXT, p_months_ahead INTEGER DEFAULT 3
        ) RETURNS VOID AS $$
        DECLARE
            v_start DATE; v_end DATE; v_partition_name TEXT; v_month DATE;
        BEGIN
            FOR i IN 0..p_months_ahead LOOP
                v_month := date_trunc('month', CURRENT_DATE) + (i || ' months')::INTERVAL;
                v_start := v_month;
                v_end := v_month + INTERVAL '1 month';
                v_partition_name := p_table_name || '_y' || to_char(v_month, 'YYYY') || 'm' || to_char(v_month, 'MM');
                IF NOT EXISTS (SELECT 1 FROM pg_class WHERE relname = v_partition_name) THEN
                    EXECUTE format('CREATE TABLE IF NOT EXISTS %I PARTITION OF %I FOR VALUES FROM (%L) TO (%L)',
                                   v_partition_name, p_table_name, v_start, v_end);
                    RAISE NOTICE 'Created partition: %', v_partition_name;
                END IF;
            END LOOP;
        END;
        $$ LANGUAGE plpgsql
    """)

    op.execute("""
        CREATE OR REPLACE FUNCTION drop_old_partitions(
            p_table_name TEXT, p_retention_months INTEGER
        ) RETURNS VOID AS $$
        DECLARE v_cutoff DATE; v_rec RECORD;
        BEGIN
            v_cutoff := date_trunc('month', CURRENT_DATE) - (p_retention_months || ' months')::INTERVAL;
            FOR v_rec IN
                SELECT tablename FROM pg_tables
                WHERE schemaname = 'public' AND tablename LIKE p_table_name || '_y%'
                AND tablename < p_table_name || '_y' || to_char(v_cutoff, 'YYYY') || 'm' || to_char(v_cutoff, 'MM')
            LOOP
                EXECUTE format('DROP TABLE IF EXISTS %I', v_rec.tablename);
                RAISE NOTICE 'Dropped partition: %', v_rec.tablename;
            END LOOP;
        END;
        $$ LANGUAGE plpgsql
    """)

    # -----------------------------------------------------------------------
    # Application roles
    # -----------------------------------------------------------------------
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'sre_app') THEN
                CREATE ROLE sre_app LOGIN PASSWORD 'CHANGE_ME_IN_PRODUCTION';
            END IF;
            IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'sre_readonly') THEN
                CREATE ROLE sre_readonly LOGIN PASSWORD 'CHANGE_ME_IN_PRODUCTION';
            END IF;
        END
        $$;
    """)
    op.execute("GRANT USAGE ON SCHEMA public TO sre_app")
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO sre_app")
    op.execute("GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO sre_app")
    op.execute("GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO sre_app")
    op.execute("GRANT USAGE ON SCHEMA public TO sre_readonly")
    op.execute("GRANT SELECT ON ALL TABLES IN SCHEMA public TO sre_readonly")


def downgrade() -> None:
    # Drop in reverse dependency order
    op.execute("DROP TABLE IF EXISTS conversations CASCADE")
    op.execute("DROP TABLE IF EXISTS skills CASCADE")
    op.execute("DROP TABLE IF EXISTS asset_metrics DEFAULT")
    op.execute("DROP TABLE IF EXISTS audit_logs DEFAULT")
    op.execute("DROP TABLE IF EXISTS operation_steps CASCADE")
    op.execute("DROP TABLE IF EXISTS operations CASCADE")
    op.execute("DROP TABLE IF EXISTS alerts DEFAULT")
    op.execute("DROP TABLE IF EXISTS asset_relations CASCADE")
    op.execute("DROP TABLE IF EXISTS assets CASCADE")
    op.execute("DROP TABLE IF EXISTS platforms CASCADE")
    op.execute("DROP TABLE IF EXISTS users CASCADE")

    # Drop partition maintenance functions
    op.execute("DROP FUNCTION IF EXISTS create_monthly_partitions")
    op.execute("DROP FUNCTION IF EXISTS drop_old_partitions")
    op.execute("DROP FUNCTION IF EXISTS update_conversation_stats")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at")

    # Drop roles
    op.execute("DROP ROLE IF EXISTS sre_app")
    op.execute("DROP ROLE IF EXISTS sre_readonly")

    # Drop enum types
    for enum_name in [
        "skill_status", "conversation_status", "user_role", "audit_action",
        "step_status", "operation_status", "risk_level", "operation_type",
        "alert_status", "alert_severity", "platform_type", "asset_status", "asset_type"
    ]:
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
