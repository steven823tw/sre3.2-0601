# V3.1 监控指标

## 应用指标

### API 指标

```
http_requests_total{method, path, status} — 请求总数
http_request_duration_seconds{method, path} — 请求耗时
http_requests_in_flight — 当前并发请求数
```

### 数据库指标

```
db_pool_size — 连接池大小
db_pool_checked_out — 已借出连接数
db_pool_overflow — 溢出连接数
db_query_duration_seconds{operation} — 查询耗时
```

### 业务指标

```
active_operations — 当前执行中的操作数
alerts_by_severity{severity} — 按严重级别统计的告警数
assets_by_type{type} — 按类型统计的资产数
chat_requests_total — Chat 请求总数
```

## 告警规则

### API 员警

```yaml
groups:
  - name: api_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "API 错误率超过 5%"
          
      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "API P95 延迟超过 1 秒"
```

### 数据库告警

```yaml
groups:
  - name: db_alerts
    rules:
      - alert: DatabaseConnectionPoolExhausted
        expr: db_pool_checked_out / db_pool_size > 0.9
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "数据库连接池使用率超过 90%"
          
      - alert: SlowQueries
        expr: rate(db_query_duration_seconds_sum[5m]) / rate(db_query_duration_seconds_count[5m]) > 0.5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "数据库平均查询耗时超过 500ms"
```

## Grafana Dashboard

### API Dashboard

- 请求速率 (QPS)
- 错误率
- 延迟分布 (P50/P95/P99)
- 并发请求数

### 数据库 Dashboard

- 连接池使用率
- 查询耗时分布
- 慢查询列表
- 表大小统计

### 业务 Dashboard

- 活跃告警数
- 操作成功率
- 资产在线率
- Chat 使用统计
