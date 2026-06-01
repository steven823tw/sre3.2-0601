# V3.1 E2E 测试

## 技术栈

- **Playwright** — 跨浏览器 E2E 测试
- **@playwright/test** — 测试运行器

## 安装

```bash
cd tests/e2e
npm install
npx playwright install
```

## 运行

```bash
# 运行所有测试
npx playwright test

# 运行特定测试
npx playwright test chat.spec.ts

# 有头模式（调试）
npx playwright test --headed

# 查看报告
npx playwright show-report
```

## 测试场景

### 核心流程 (chat.spec.ts)

1. 首次访问 → 显示欢迎消息
2. 输入 "查看告警" → 显示告警列表
3. 输入 "重启 web-01" → 显示确认弹窗
4. 点击确认 → 显示操作进度
5. 操作完成 → 显示结果

### 告警管理 (alerts.spec.ts)

1. 访问告警页面 → 显示告警列表
2. 点击 P0 标签 → 只显示 P0 告警
3. 点击确认按钮 → 告警状态变为 "已确认"
4. 点击解决按钮 → 告警状态变为 "已解决"

### 资源管理 (resources.spec.ts)

1. 访问资源页面 → 显示 VM 列表
2. 切换到物理机标签 → 显示物理机列表
3. 搜索 "web" → 只显示名称包含 web 的资源
4. 选择多台资源 → 显示批量操作栏
5. 点击详情 → 右侧显示详情面板

### 仪表盘 (dashboard.spec.ts)

1. 访问仪表盘 → 显示 4 个统计卡片
2. 图表正确渲染 → CPU/内存趋势图可见
3. 告警分布图 → 饼图正确显示

## 配置

```typescript
// playwright.config.ts
export default defineConfig({
  testDir: './tests',
  timeout: 30000,
  retries: 2,
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  webServer: [
    {
      command: 'cd ../backend && uvicorn app.main:app --port 8688',
      port: 8688,
      reuseExistingServer: true,
    },
    {
      command: 'cd ../frontend && npm run dev',
      port: 5173,
      reuseExistingServer: true,
    },
  ],
});
```
