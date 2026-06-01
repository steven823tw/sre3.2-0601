"""Chat service — intent recognition and recommendation generation.

Implements rule-based intent recognition that maps natural language
to structured operation recommendations.  No LLM dependency.
"""
from __future__ import annotations

import re
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

import structlog

from app.core.registry import AtomicOperation, registry
from app.schemas.chat import ChatResponse, RecommendationStep

logger = structlog.get_logger(__name__)

# Risk level descriptions for user-facing messages
RISK_DESCRIPTIONS: dict[str, str] = {
    "low": "低风险 — 可安全执行，无需审批",
    "medium": "中风险 — 建议确认后执行",
    "high": "高风险 — 需要审批，可能影响服务",
    "critical": "严重风险 — 必须审批，可能造成不可逆影响",
}


@dataclass
class RecognizedIntent:
    """Result of intent recognition."""
    intent: str
    target: str | None = None
    confidence: float = 1.0
    params: dict[str, Any] = field(default_factory=dict)


class IntentRecognizer:
    """Map natural language to structured intents using regex patterns.

    Patterns are tried in order; the first match wins.
    Each pattern must have named groups for extraction.
    """

    PATTERNS: list[tuple[str, str, list[str]]] = [
        # (intent, regex, [operation_ids])

        # --- Service management (must precede generic restart/shutdown patterns) ---
        ("service_restart", r"(?:重启|重新启动)\s*(?P<target>\S+)\s*(?:上的|的)\s*(?P<service>\S+)\s*(?:服务|service)", ["maintenance.service_restart"]),
        ("service_status", r"(?:查看|检查)\s*(?P<target>\S+)\s*(?:上的|的)\s*(?P<service>\S+)\s*(?:服务|service)\s*(?:状态|情况)", ["maintenance.service_status"]),

        # --- Infrastructure diagnostics ---
        ("diagnose", r"(?P<target>\S+)\s*(?:连接超时|不通|宕机|挂了|有问题|怎么了|连不上|无法访问)", ["infra.ping", "compute.vm_status"]),
        ("restart", r"重启\s*(?P<target>\S+)", ["compute.vm_restart"]),
        ("restart", r"(?P<target>\S+)\s*重启", ["compute.vm_restart"]),
        ("shutdown", r"(?:关机|关闭)\s*(?P<target>\S+)", ["compute.vm_stop"]),
        ("power_on", r"(?:开机|启动)\s*(?P<target>\S+)", ["compute.vm_start"]),
        ("power_on", r"(?P<target>\S+)\s*(?:开机|启动)", ["compute.vm_start"]),
        ("snapshot", r"(?:创建|做)\s*(?P<target>\S+)\s*(?:快照|备份快照)", ["compute.vm_snapshot"]),
        ("check_alerts", r"(?:查看|看看|有什么)\s*(?:告警|报警|告警信息)", []),
        ("check_resources", r"(?:查看|看看)\s*(?:集群|资源|设备|服务器)", []),
        ("disk_usage", r"(?P<target>\S+)\s*(?:磁盘|硬盘|存储)\s*(?:空间|容量|满了|不足)", ["storage.disk_usage"]),
        ("network_check", r"(?P<target>\S+)\s*(?:网络|ping|连通)", ["infra.ping", "infra.traceroute"]),
        ("check_status", r"(?:查看|检查|看看)\s*(?P<target>\S+)\s*(?:状态|情况)", ["compute.vm_status", "compute.host_status"]),
        ("help", r"(?:帮助|你能做什么|怎么用|使用说明)", []),

        # --- Database operations ---
        ("db_status", r"(?:查看|检查)\s*(?P<target>\S+)\s*(?:数据库|db|DB)\s*(?:状态|健康|连接)", ["database.status", "database.connection_pool"]),
        ("db_slow_queries", r"(?P<target>\S+)\s*(?:数据库|db|DB)\s*(?:慢查询|慢SQL|性能)", ["database.slow_queries"]),
        ("db_replication", r"(?P<target>\S+)\s*(?:数据库|db|DB)\s*(?:复制|同步|主从|延迟)", ["database.replication_lag"]),
        ("db_backup", r"(?P<target>\S+)\s*(?:数据库|db|DB)\s*(?:备份|恢复)", ["database.backup_status"]),

        # --- Backup operations ---
        ("backup_create", r"(?:创建|做|执行)\s*(?P<target>\S+)\s*(?:备份|全量备份|增量备份)", ["backup.create"]),
        ("backup_restore", r"(?:恢复|还原)\s*(?P<target>\S+)\s*(?:备份|数据)", ["backup.restore"]),
        ("backup_verify", r"(?:验证|检查)\s*(?P<target>\S+)\s*(?:备份|完整性)", ["backup.verify"]),

        # --- Security operations ---
        ("security_scan", r"(?:扫描|漏洞扫描|安全扫描)\s*(?P<target>\S+)", ["security.vulnerability_scan"]),
        ("patch_check", r"(?P<target>\S+)\s*(?:补丁|更新|patch)\s*(?:状态|情况|检查)", ["security.patch_status"]),
        ("cert_check", r"(?P<target>\S+)\s*(?:证书|SSL|TLS|https)\s*(?:过期|到期|检查|状态)", ["infra.cert_check"]),
        ("cert_renew", r"(?:续签|更新|重新申请)\s*(?P<target>\S+)\s*(?:证书|SSL)", ["security.cert_renew"]),

        # --- Log and monitoring ---
        ("log_search", r"(?:查看|搜索|查)\s*(?P<target>\S+)\s*(?:日志|log|错误日志)", ["monitoring.log_search"]),
        ("performance_check", r"(?P<target>\S+)\s*(?:性能|CPU|内存|负载)\s*(?:查看|检查|监控)", ["compute.cpu_usage", "compute.memory_usage"]),
        ("metric_query", r"(?:查看|查询)\s*(?P<target>\S+)\s*(?:指标|metric|监控数据)", ["monitoring.metric_query"]),

        # --- VM migration and lifecycle ---
        ("migrate", r"(?:迁移|漂移)\s*(?P<target>\S+)", ["compute.vm_migrate"]),
        ("maintenance_mode", r"(?P<target>\S+)\s*(?:进入|进入维护模式|维护)", ["compute.host_maintenance"]),

        # --- Network operations ---
        ("firewall_list", r"(?:查看|列出)\s*(?P<target>\S+)\s*(?:防火墙|firewall)\s*(?:规则|策略)", ["network.firewall_rule_list"]),
        ("dns_check", r"(?:DNS|域名解析|域名)\s*(?:检查|查看)\s*(?P<target>\S+)", ["infra.dns_check"]),
    ]

    def recognize(self, message: str) -> RecognizedIntent:
        """Recognize intent from a natural language message.

        Args:
            message: The user's input message.

        Returns:
            RecognizedIntent with detected intent and extracted parameters.
        """
        message = message.strip()
        if not message:
            return RecognizedIntent(intent="empty", target=None)

        for intent, pattern, ops in self.PATTERNS:
            match = re.search(pattern, message)
            if match:
                target = match.groupdict().get("target")
                logger.info("intent_recognized", intent=intent, target=target, message=message[:50])
                return RecognizedIntent(
                    intent=intent,
                    target=target,
                    params=match.groupdict(),
                )

        # Fallback: treat as general query
        logger.info("intent_recognized", intent="general", message=message[:50])
        return RecognizedIntent(intent="general", target=None)


@dataclass
class ConversationContext:
    """Tracks conversation state for parameter auto-fill.

    Attributes:
        recent_targets: Recently referenced targets (hosts, VMs, services).
        last_intent: The most recently recognized intent.
        user_preferences: User-specific preferences (e.g., default environment).
    """
    recent_targets: list[str] = field(default_factory=list)
    last_intent: str | None = None
    user_preferences: dict[str, Any] = field(default_factory=dict)

    def add_target(self, target: str | None) -> None:
        """Add a target to recent history, deduplicating."""
        if target and target not in self.recent_targets:
            self.recent_targets.insert(0, target)
            # Keep only the 5 most recent
            self.recent_targets = self.recent_targets[:5]

    def resolve_target(self, explicit_target: str | None) -> str | None:
        """Resolve target, falling back to most recent if not provided."""
        if explicit_target:
            return explicit_target
        if self.recent_targets:
            return self.recent_targets[0]
        return None


class ChatService:
    """AI Agent chat service with intent recognition and operation recommendation."""

    # Map intents to recommended atomic operations
    INTENT_TO_OPERATIONS: dict[str, list[str]] = {
        "diagnose": ["infra.ping", "compute.vm_status"],
        "restart": ["compute.vm_restart"],
        "shutdown": ["compute.vm_stop"],
        "power_on": ["compute.vm_start"],
        "snapshot": ["compute.vm_snapshot"],
        "check_alerts": ["monitoring.alert_check"],
        "check_resources": ["compute.host_status"],
        "disk_usage": ["storage.disk_usage"],
        "network_check": ["infra.ping", "infra.traceroute"],
        "check_status": ["compute.vm_status"],
        "db_status": ["database.status", "database.connection_pool"],
        "db_slow_queries": ["database.slow_queries"],
        "db_replication": ["database.replication_lag"],
        "db_backup": ["database.backup_status"],
        "backup_create": ["backup.create"],
        "backup_restore": ["backup.restore"],
        "backup_verify": ["backup.verify"],
        "security_scan": ["security.vulnerability_scan"],
        "patch_check": ["security.patch_status"],
        "cert_check": ["infra.cert_check"],
        "cert_renew": ["security.cert_renew"],
        "log_search": ["monitoring.log_search"],
        "performance_check": ["compute.cpu_usage", "compute.memory_usage"],
        "metric_query": ["monitoring.metric_query"],
        "migrate": ["compute.vm_migrate"],
        "maintenance_mode": ["compute.host_maintenance"],
        "firewall_list": ["network.firewall_rule_list"],
        "dns_check": ["infra.dns_check"],
        "service_restart": ["maintenance.service_restart"],
        "service_status": ["maintenance.service_status"],
    }

    # Human-readable response templates per intent
    RESPONSE_TEMPLATES: dict[str, str] = {
        "diagnose": "检测到 {target} 存在问题，建议按以下步骤诊断：",
        "restart": "将为您重启 {target}，建议先确认当前状态：",
        "shutdown": "将关闭 {target}，请确认操作影响：",
        "power_on": "将启动 {target}，检查当前状态：",
        "snapshot": "将为 {target} 创建快照，操作步骤如下：",
        "check_alerts": "以下是当前活跃的告警信息，建议按优先级处理：",
        "check_resources": "以下是集群资源概况：",
        "disk_usage": "检查 {target} 的磁盘使用情况：",
        "network_check": "将对 {target} 进行网络连通性检查：",
        "check_status": "查看 {target} 的运行状态：",
        "db_status": "检查 {target} 数据库状态和连接池：",
        "db_slow_queries": "查看 {target} 的慢查询情况：",
        "db_replication": "检查 {target} 的数据库复制状态：",
        "db_backup": "检查 {target} 的数据库备份状态：",
        "backup_create": "将为 {target} 创建备份：",
        "backup_restore": "将恢复 {target} 的备份数据，请确认：",
        "backup_verify": "验证 {target} 的备份完整性：",
        "security_scan": "对 {target} 进行安全漏洞扫描：",
        "patch_check": "检查 {target} 的补丁更新状态：",
        "cert_check": "检查 {target} 的 SSL/TLS 证书状态：",
        "cert_renew": "续签 {target} 的 SSL/TLS 证书：",
        "log_search": "搜索 {target} 的日志：",
        "performance_check": "查看 {target} 的性能指标：",
        "metric_query": "查询 {target} 的监控指标：",
        "migrate": "将迁移 {target}，此操作需要审批：",
        "maintenance_mode": "将 {target} 切换至维护模式：",
        "firewall_list": "查看 {target} 的防火墙规则：",
        "dns_check": "检查 {target} 的 DNS 解析：",
        "service_restart": "重启 {target} 上的服务：",
        "service_status": "查看 {target} 上的服务状态：",
        "help": "我是 Engineer Assist 智能运维助手，可以帮您：\n"
                "- 诊断故障：输入主机名+症状（如 web-01 连接超时）\n"
                "- 执行操作：重启/关机/开机 + 主机名\n"
                "- 查看告警：查看告警\n"
                "- 查看资源：查看集群/资源\n"
                "- 磁盘检查：主机名 + 磁盘空间不足\n"
                "- 网络检查：主机名 + 网络/ping\n"
                "- 数据库操作：数据库状态/慢查询/复制延迟\n"
                "- 备份管理：创建/恢复/验证备份\n"
                "- 安全检查：漏洞扫描/补丁状态/证书检查\n"
                "- 日志搜索：主机名 + 日志\n"
                "- 性能监控：主机名 + CPU/内存/负载\n"
                "- 迁移操作：迁移 + 主机名\n"
                "- 服务管理：重启/查看服务状态",
        "general": "我没有完全理解您的需求。您可以尝试：\n"
                   "- 描述故障现象（如 web-01 连接超时）\n"
                   "- 请求操作（如 重启 web-01）\n"
                   "- 查看告警/资源\n"
                   "- 输入 '帮助' 查看完整功能",
        "empty": "请输入您的问题或操作需求。",
    }

    MAX_CONTEXTS = 1000
    CONTEXT_TTL = timedelta(hours=2)

    def __init__(self) -> None:
        self._recognizer = IntentRecognizer()
        self._contexts: OrderedDict[int, tuple[datetime, ConversationContext]] = OrderedDict()

    def _get_context(self, conversation_id: int | None) -> ConversationContext:
        """Get or create conversation context with TTL-based eviction.

        Args:
            conversation_id: The conversation identifier.

        Returns:
            The ConversationContext for the given conversation.
        """
        if conversation_id is None:
            return ConversationContext()
        now = datetime.now(timezone.utc)
        # Evict expired entries
        expired = [k for k, (ts, _) in self._contexts.items() if now - ts > self.CONTEXT_TTL]
        for k in expired:
            del self._contexts[k]
        # LRU eviction if over capacity
        while len(self._contexts) >= self.MAX_CONTEXTS:
            self._contexts.popitem(last=False)
        # Get or create
        if conversation_id in self._contexts:
            ts, ctx = self._contexts.pop(conversation_id)
            self._contexts[conversation_id] = (now, ctx)
            return ctx
        ctx = ConversationContext()
        self._contexts[conversation_id] = (now, ctx)
        return ctx

    def _assess_risk(self, recommendations: list[RecommendationStep]) -> str:
        """Assess the overall risk of a set of recommendations.

        Args:
            recommendations: The list of recommendation steps.

        Returns:
            Risk description string.
        """
        if not recommendations:
            return "无操作推荐"

        risk_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        max_risk = max(
            risk_order.get(r.risk_level, 0) for r in recommendations
        )
        risk_label = [k for k, v in risk_order.items() if v == max_risk][0]
        return RISK_DESCRIPTIONS.get(risk_label, "未知风险等级")

    def _estimate_total_time(self, recommendations: list[RecommendationStep]) -> str:
        """Estimate total execution time for recommendations.

        Args:
            recommendations: The list of recommendation steps.

        Returns:
            Human-readable time estimate.
        """
        if not recommendations:
            return "无需执行操作"

        total_ms = sum(r.estimated_time_ms for r in recommendations)
        if total_ms < 1000:
            return f"预计耗时 {total_ms} 毫秒"
        elif total_ms < 60000:
            seconds = total_ms // 1000
            return f"预计耗时 {seconds} 秒"
        elif total_ms < 3600000:
            minutes = total_ms // 60000
            return f"预计耗时 {minutes} 分钟"
        else:
            hours = total_ms // 3600000
            minutes = (total_ms % 3600000) // 60000
            return f"预计耗时 {hours} 小时 {minutes} 分钟"

    def _auto_fill_params(
        self,
        op: AtomicOperation,
        recognized: RecognizedIntent,
        context: ConversationContext,
    ) -> dict[str, Any]:
        """Auto-fill operation parameters from recognized intent and context.

        Args:
            op: The atomic operation whose params to fill.
            recognized: The recognized intent with extracted parameters.
            context: The conversation context for fallback values.

        Returns:
            Populated parameter dictionary.
        """
        params = dict(op.params_schema)

        # Resolve target from explicit input or conversation history
        resolved_target = context.resolve_target(recognized.target)

        # Fill common parameter names from resolved target
        for param_name in ("target", "vm", "host", "instance", "hostname", "domain"):
            if param_name in params and resolved_target:
                params[param_name] = resolved_target

        # Fill service name from recognized params if available
        if "service" in params and recognized.params.get("service"):
            params["service"] = recognized.params["service"]

        # Fill additional params from recognized groups
        for key, value in recognized.params.items():
            if key != "target" and key in params and value:
                params[key] = value

        return params

    def process_message(
        self,
        message: str,
        conversation_id: int | None = None,
    ) -> ChatResponse:
        """Process a user message and return a structured response.

        Args:
            message: The user's input text.
            conversation_id: Optional existing conversation ID.

        Returns:
            ChatResponse with intent, recommendations, and message.
        """
        recognized = self._recognizer.recognize(message)
        context = self._get_context(conversation_id)

        # Resolve target using context for auto-fill
        resolved_target = context.resolve_target(recognized.target)

        # Build recommendations from registry
        recommendations: list[RecommendationStep] = []
        op_ids = self.INTENT_TO_OPERATIONS.get(recognized.intent, [])

        for step_num, op_id in enumerate(op_ids, start=1):
            op = registry.get(op_id)
            if op is None:
                logger.warning("operation_not_found", op_id=op_id)
                continue

            # Auto-fill params from intent and conversation context
            params = self._auto_fill_params(op, recognized, context)

            recommendations.append(
                RecommendationStep(
                    step=step_num,
                    action=op.id,
                    description=op.description,
                    params=params,
                    risk_level=op.risk_level.value,
                    estimated_time_ms=op.estimated_time_ms,
                )
            )

        # Update conversation context
        context.add_target(resolved_target)
        context.last_intent = recognized.intent

        # Generate response message
        template = self.RESPONSE_TEMPLATES.get(recognized.intent, "")
        response_message = template.format(
            target=resolved_target or "目标",
        )

        # Append risk and time estimates for actionable intents
        if recommendations:
            risk_desc = self._assess_risk(recommendations)
            time_est = self._estimate_total_time(recommendations)
            response_message += f"\n\n风险评估：{risk_desc}\n{time_est}"

        logger.info(
            "chat_processed",
            intent=recognized.intent,
            target=resolved_target,
            recommendation_count=len(recommendations),
            conversation_id=conversation_id,
        )

        return ChatResponse(
            success=True,
            conversation_id=conversation_id,
            intent=recognized.intent,
            recommendations=recommendations,
            message=response_message,
        )


# Module-level singleton
chat_service = ChatService()
