# V3.1 测试策略

## 测试金字塔

```
        ┌───────────┐
        │   E2E     │  ← 5-10 个核心流程
        │ (Playwright)
        ├───────────┤
        │ Integration│  ← API 端点测试
        │ (pytest)  │  ← 数据库操作测试
        ├───────────┤
        │   Unit    │  ← 业务逻辑测试
        │ (pytest/  │  ← 组件渲染测试
        │  Vitest)  │  ← 工具函数测试
        └───────────┘
```

## 后端测试

### 单元测试 (`tests/unit/`)

**目标覆盖率**: > 80%

```bash
# 运行
cd backend && pytest tests/unit/ -v --cov=app --cov-report=html

# 必须测试
- IntentRecognizer: 10+ 自然语言输入 → 意图匹配
- AssetService: 过滤、分页、排序逻辑
- AlertService: 状态转换 (active → acknowledged → resolved)
- OperationService: 工作流状态机
- 所有 Pydantic schema 验证
```

### 集成测试 (`tests/integration/`)

```bash
# 运行 (需要测试数据库)
cd backend && pytest tests/integration/ -v --tb=short

# 必须测试
- 所有 API 端点的请求/响应格式
- 数据库 CRUD 操作
- 分页查询的正确性
- 错误响应的格式
- 认证/授权
```

### 测试 Fixtures

```python
# tests/conftest.py
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

@pytest.fixture
async def db_session():
    """提供测试数据库会话，测试后回滚"""
    engine = create_async_engine("postgresql+asyncpg://test:test@localhost:5432/test")
    async with AsyncSession(engine) as session:
        yield session
        await session.rollback()

@pytest.fixture
async def client(db_session):
    """提供测试 HTTP 客户端"""
    app = create_app(override_db=db_session)
    async with AsyncClient(app=app, base_url="http://test") as c:
        yield c
```

---

## 前端测试

### 单元测试 (Vitest + Testing Library)

```bash
# 运行
cd frontend && npm run test

# 必须测试
- 所有 UI 组件渲染
- 用户交互 (点击、输入、键盘)
- 状态管理 (Zustand stores)
- 工具函数 (formatTime, cn, etc.)
```

### 组件测试模式

```typescript
// AlertCard.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { AlertCard } from './AlertCard';

const mockAlert = {
  id: '1',
  title: 'Test Alert',
  severity: 'P0',
  status: 'active',
  // ...
};

describe('AlertCard', () => {
  it('renders alert title', () => {
    render(<AlertCard alert={mockAlert} />);
    expect(screen.getByText('Test Alert')).toBeInTheDocument();
  });

  it('shows P0 severity styling', () => {
    render(<AlertCard alert={mockAlert} />);
    const card = screen.getByRole('article');
    expect(card).toHaveClass('border-l-red-500');
  });

  it('calls onAcknowledge when button clicked', () => {
    const onAcknowledge = vi.fn();
    render(<AlertCard alert={mockAlert} onAcknowledge={onAcknowledge} />);
    fireEvent.click(screen.getByText('确认'));
    expect(onAcknowledge).toHaveBeenCalledWith('1');
  });
});
```

---

## E2E 测试 (Playwright)

### 核心流程

```typescript
// tests/e2e/chat.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Chat Flow', () => {
  test('send message and receive recommendation', async ({ page }) => {
    await page.goto('/chat');
    
    // 输入消息
    await page.fill('textarea', '查看告警');
    await page.click('button:has-text("发送")');
    
    // 等待响应
    await page.waitForSelector('[data-testid="recommendation-card"]');
    
    // 验证响应
    const response = page.locator('[data-testid="agent-message"]').last();
    await expect(response).toContainText('告警');
  });

  test('confirm operation shows progress', async ({ page }) => {
    await page.goto('/chat');
    
    await page.fill('textarea', '重启 web-01');
    await page.click('button:has-text("发送")');
    
    // 等待确认按钮
    await page.waitForSelector('button:has-text("确认执行")');
    await page.click('button:has-text("确认执行")');
    
    // 验证进度显示
    await page.waitForSelector('[data-testid="progress-card"]');
    await expect(page.locator('[data-testid="step-status"]')).toBeVisible();
  });
});
```

### 测试配置

```typescript
// playwright.config.ts
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  timeout: 30000,
  retries: 2,
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  webServer: [
    {
      command: 'cd backend && uvicorn app.main:app --port 8688',
      port: 8688,
      reuseExistingServer: true,
    },
    {
      command: 'cd frontend && npm run dev',
      port: 5173,
      reuseExistingServer: true,
    },
  ],
});
```

---

## 质量门禁

每个 PR 必须通过:

```bash
# 后端
cd backend && pytest --cov=app --cov-fail-under=80
cd backend && mypy app/ --strict
cd backend && ruff check app/

# 前端
cd frontend && npm run test
cd frontend && npx tsc --noEmit
cd frontend && npm run lint

# E2E (每个阶段完成时)
cd tests/e2e && npx playwright test
```

## 测试数据

- 单元测试: 使用 mock/factory，不依赖数据库
- 集成测试: 使用测试数据库，每个测试后回滚
- E2E 测试: 使用 seed 数据，每个测试前重置
