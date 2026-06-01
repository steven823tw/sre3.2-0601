"""Tests for ChatService intent recognition and recommendation.

Comprehensive tests covering:
- 15+ intent patterns
- Parameter auto-fill from context
- Risk assessment
- Estimated time
- Conversation context tracking
"""
from __future__ import annotations

import pytest

from app.services.chat_service import (
    ChatService,
    ConversationContext,
    IntentRecognizer,
    chat_service,
)


class TestIntentRecognizer:
    """Test the IntentRecognizer pattern matching."""

    def setup_method(self):
        self.recognizer = IntentRecognizer()

    # --- Original patterns ---
    def test_diagnose_timeout(self):
        result = self.recognizer.recognize("web-01 连接超时")
        assert result.intent == "diagnose"
        assert result.target == "web-01"

    def test_diagnose_down(self):
        result = self.recognizer.recognize("db-01 宕机了")
        assert result.intent == "diagnose"
        assert result.target == "db-01"

    def test_diagnose_broken(self):
        result = self.recognizer.recognize("app-server 挂了")
        assert result.intent == "diagnose"
        assert result.target == "app-server"

    def test_diagnose_unreachable(self):
        result = self.recognizer.recognize("web-01 连不上")
        assert result.intent == "diagnose"
        assert result.target == "web-01"

    def test_restart_prefix(self):
        result = self.recognizer.recognize("重启 web-01")
        assert result.intent == "restart"
        assert result.target == "web-01"

    def test_restart_suffix(self):
        result = self.recognizer.recognize("web-01 重启")
        assert result.intent == "restart"
        assert result.target == "web-01"

    def test_shutdown(self):
        result = self.recognizer.recognize("关机 db-01")
        assert result.intent == "shutdown"
        assert result.target == "db-01"

    def test_shutdown_close(self):
        result = self.recognizer.recognize("关闭 web-01")
        assert result.intent == "shutdown"
        assert result.target == "web-01"

    def test_power_on_start(self):
        result = self.recognizer.recognize("启动 web-01")
        assert result.intent == "power_on"
        assert result.target == "web-01"

    def test_power_on_boot(self):
        result = self.recognizer.recognize("开机 db-01")
        assert result.intent == "power_on"
        assert result.target == "db-01"

    def test_snapshot(self):
        result = self.recognizer.recognize("创建 web-01 快照")
        assert result.intent == "snapshot"
        assert result.target == "web-01"

    def test_check_alerts(self):
        result = self.recognizer.recognize("查看告警")
        assert result.intent == "check_alerts"

    def test_check_alerts_variant(self):
        result = self.recognizer.recognize("有什么告警")
        assert result.intent == "check_alerts"

    def test_check_resources(self):
        result = self.recognizer.recognize("看看集群")
        assert result.intent == "check_resources"

    def test_disk_usage(self):
        result = self.recognizer.recognize("db-01 磁盘空间不足")
        assert result.intent == "disk_usage"
        assert result.target == "db-01"

    def test_help(self):
        result = self.recognizer.recognize("帮助")
        assert result.intent == "help"

    def test_help_variant(self):
        result = self.recognizer.recognize("你能做什么")
        assert result.intent == "help"

    def test_general_fallback(self):
        result = self.recognizer.recognize("hello world")
        assert result.intent == "general"

    def test_empty_input(self):
        result = self.recognizer.recognize("")
        assert result.intent == "empty"

    # --- New database patterns ---
    def test_db_status(self):
        result = self.recognizer.recognize("检查 mysql-01 数据库状态")
        assert result.intent == "db_status"
        assert result.target == "mysql-01"

    def test_db_slow_queries(self):
        result = self.recognizer.recognize("db-01 数据库慢查询")
        assert result.intent == "db_slow_queries"
        assert result.target == "db-01"

    def test_db_replication(self):
        result = self.recognizer.recognize("pg-01 数据库复制延迟")
        assert result.intent == "db_replication"
        assert result.target == "pg-01"

    def test_db_backup(self):
        result = self.recognizer.recognize("mysql-01 数据库备份")
        assert result.intent == "db_backup"
        assert result.target == "mysql-01"

    # --- New backup patterns ---
    def test_backup_create(self):
        result = self.recognizer.recognize("创建 web-01 全量备份")
        assert result.intent == "backup_create"
        assert result.target == "web-01"

    def test_backup_restore(self):
        result = self.recognizer.recognize("恢复 db-01 数据")
        assert result.intent == "backup_restore"
        assert result.target == "db-01"

    def test_backup_verify(self):
        result = self.recognizer.recognize("验证 web-01 备份完整性")
        assert result.intent == "backup_verify"
        assert result.target == "web-01"

    # --- New security patterns ---
    def test_security_scan(self):
        result = self.recognizer.recognize("漏洞扫描 web-01")
        assert result.intent == "security_scan"
        assert result.target == "web-01"

    def test_patch_check(self):
        result = self.recognizer.recognize("web-01 补丁状态")
        assert result.intent == "patch_check"
        assert result.target == "web-01"

    def test_cert_check(self):
        result = self.recognizer.recognize("web-01 证书过期")
        assert result.intent == "cert_check"
        assert result.target == "web-01"

    def test_cert_renew(self):
        result = self.recognizer.recognize("续签 web-01 SSL证书")
        assert result.intent == "cert_renew"
        assert result.target == "web-01"

    # --- New log and monitoring patterns ---
    def test_log_search(self):
        result = self.recognizer.recognize("查看 web-01 日志")
        assert result.intent == "log_search"
        assert result.target == "web-01"

    def test_performance_check(self):
        result = self.recognizer.recognize("web-01 CPU 监控")
        assert result.intent == "performance_check"
        assert result.target == "web-01"

    def test_metric_query(self):
        result = self.recognizer.recognize("查看 web-01 指标")
        assert result.intent == "metric_query"
        assert result.target == "web-01"

    # --- New VM lifecycle patterns ---
    def test_migrate(self):
        result = self.recognizer.recognize("迁移 web-01")
        assert result.intent == "migrate"
        assert result.target == "web-01"

    def test_maintenance_mode(self):
        result = self.recognizer.recognize("esxi-01 维护")
        assert result.intent == "maintenance_mode"
        assert result.target == "esxi-01"

    # --- New network patterns ---
    def test_firewall_list(self):
        result = self.recognizer.recognize("查看 web-01 防火墙规则")
        assert result.intent == "firewall_list"
        assert result.target == "web-01"

    def test_dns_check(self):
        result = self.recognizer.recognize("DNS 检查 web-01")
        assert result.intent == "dns_check"
        assert result.target == "web-01"

    # --- New service management patterns ---
    def test_service_restart(self):
        result = self.recognizer.recognize("重启 web-01 上的 nginx 服务")
        assert result.intent == "service_restart"
        assert result.target == "web-01"

    def test_service_status(self):
        result = self.recognizer.recognize("检查 web-01 的 nginx 服务状态")
        assert result.intent == "service_status"
        assert result.target == "web-01"


class TestConversationContext:
    """Test the ConversationContext parameter tracking."""

    def test_add_target_dedup(self):
        ctx = ConversationContext()
        ctx.add_target("web-01")
        ctx.add_target("web-01")
        assert ctx.recent_targets.count("web-01") == 1

    def test_add_target_ordering(self):
        ctx = ConversationContext()
        ctx.add_target("web-01")
        ctx.add_target("db-01")
        assert ctx.recent_targets[0] == "db-01"
        assert ctx.recent_targets[1] == "web-01"

    def test_add_target_limit(self):
        ctx = ConversationContext()
        for i in range(10):
            ctx.add_target(f"host-{i}")
        assert len(ctx.recent_targets) == 5
        assert ctx.recent_targets[0] == "host-9"

    def test_resolve_explicit_target(self):
        ctx = ConversationContext()
        ctx.add_target("db-01")
        assert ctx.resolve_target("web-01") == "web-01"

    def test_resolve_fallback_to_recent(self):
        ctx = ConversationContext()
        ctx.add_target("db-01")
        assert ctx.resolve_target(None) == "db-01"

    def test_resolve_no_context(self):
        ctx = ConversationContext()
        assert ctx.resolve_target(None) is None

    def test_add_none_target_ignored(self):
        ctx = ConversationContext()
        ctx.add_target(None)
        assert len(ctx.recent_targets) == 0

    def test_add_empty_target_ignored(self):
        ctx = ConversationContext()
        ctx.add_target("")
        assert len(ctx.recent_targets) == 0


class TestChatService:
    """Test the ChatService end-to-end processing."""

    def test_process_diagnose_message(self):
        response = chat_service.process_message("web-01 连接超时了")
        assert response.success is True
        assert response.intent == "diagnose"
        assert len(response.recommendations) >= 1
        assert response.recommendations[0].action == "infra.ping"

    def test_process_restart_message(self):
        response = chat_service.process_message("重启 web-01")
        assert response.success is True
        assert response.intent == "restart"
        assert any(r.action == "compute.vm_restart" for r in response.recommendations)

    def test_recommendations_have_params(self):
        response = chat_service.process_message("重启 web-01")
        restart_rec = next(r for r in response.recommendations if r.action == "compute.vm_restart")
        assert "vm" in restart_rec.params

    def test_recommendations_have_risk_level(self):
        response = chat_service.process_message("查看告警")
        for rec in response.recommendations:
            assert rec.risk_level in ("low", "medium", "high", "critical")

    def test_recommendations_have_estimated_time(self):
        response = chat_service.process_message("web-01 连接超时")
        for rec in response.recommendations:
            assert rec.estimated_time_ms > 0

    def test_conversation_id_passthrough(self):
        response = chat_service.process_message("帮助", conversation_id=42)
        assert response.conversation_id == 42

    def test_help_message_content(self):
        response = chat_service.process_message("帮助")
        assert "Engineer Assist" in response.message

    def test_general_message_content(self):
        response = chat_service.process_message("xyzzy")
        assert response.intent == "general"
        assert len(response.message) > 0

    # --- New intent processing tests ---
    def test_process_db_status_message(self):
        response = chat_service.process_message("检查 mysql-01 数据库状态")
        assert response.success is True
        assert response.intent == "db_status"
        assert any(r.action == "database.status" for r in response.recommendations)

    def test_process_backup_create_message(self):
        response = chat_service.process_message("创建 web-01 全量备份")
        assert response.success is True
        assert response.intent == "backup_create"
        assert any(r.action == "backup.create" for r in response.recommendations)

    def test_process_security_scan_message(self):
        response = chat_service.process_message("漏洞扫描 web-01")
        assert response.success is True
        assert response.intent == "security_scan"
        assert any(r.action == "security.vulnerability_scan" for r in response.recommendations)

    def test_process_log_search_message(self):
        response = chat_service.process_message("查看 web-01 日志")
        assert response.success is True
        assert response.intent == "log_search"
        assert any(r.action == "monitoring.log_search" for r in response.recommendations)

    def test_process_migrate_message(self):
        response = chat_service.process_message("迁移 web-01")
        assert response.success is True
        assert response.intent == "migrate"
        assert any(r.action == "compute.vm_migrate" for r in response.recommendations)

    def test_process_cert_check_message(self):
        response = chat_service.process_message("web-01 证书过期")
        assert response.success is True
        assert response.intent == "cert_check"
        assert any(r.action == "infra.cert_check" for r in response.recommendations)

    def test_process_dns_check_message(self):
        response = chat_service.process_message("DNS 检查 web-01")
        assert response.success is True
        assert response.intent == "dns_check"
        assert any(r.action == "infra.dns_check" for r in response.recommendations)

    # --- Risk assessment tests ---
    def test_response_includes_risk_assessment(self):
        response = chat_service.process_message("重启 web-01")
        assert "风险评估" in response.message

    def test_response_includes_time_estimate(self):
        response = chat_service.process_message("重启 web-01")
        assert "预计耗时" in response.message

    def test_low_risk_assessment(self):
        response = chat_service.process_message("查看告警")
        # alert_check is low risk
        assert "低风险" in response.message

    def test_high_risk_assessment(self):
        response = chat_service.process_message("关闭 web-01")
        # vm_stop is high risk
        assert "高风险" in response.message

    # --- Context auto-fill tests ---
    def test_context_preserves_target(self):
        svc = ChatService()
        svc.process_message("重启 web-01", conversation_id=1)
        # Second message without explicit target should reuse context
        response = svc.process_message("查看状态", conversation_id=1)
        # The target should be auto-filled from context
        for rec in response.recommendations:
            if "vm" in rec.params:
                assert rec.params["vm"] == "web-01"

    def test_context_different_conversations(self):
        svc = ChatService()
        svc.process_message("重启 web-01", conversation_id=1)
        svc.process_message("重启 db-01", conversation_id=2)
        # Conversation 1 should still remember web-01
        r1 = svc.process_message("查看状态", conversation_id=1)
        r2 = svc.process_message("查看状态", conversation_id=2)
        # Verify independent context
        for rec in r1.recommendations:
            if "vm" in rec.params:
                assert rec.params["vm"] == "web-01"
        for rec in r2.recommendations:
            if "vm" in rec.params:
                assert rec.params["vm"] == "db-01"

    def test_no_conversation_id_uses_ephemeral_context(self):
        response = chat_service.process_message("查看告警")
        assert response.success is True
        assert response.conversation_id is None
