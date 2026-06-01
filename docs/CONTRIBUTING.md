# V3.1 贡献指南

## 开发流程

### 1. 领取任务

从 `PRODUCT_PLAN.md` 中选择当前阶段的任务，确认：
- 任务未被他人认领
- 依赖任务已完成
- 有明确的验收标准

### 2. 创建分支

```bash
git checkout develop
git pull origin develop
git checkout -b feature/p1-api-bridge
```

### 3. 开发

```bash
# 后端
cd backend
source .venv/bin/activate
# 编写代码
# 编写测试
pytest tests/ -v

# 前端
cd frontend
npm install
# 编写代码
# 编写测试
npm run test
```

### 4. 提交

```bash
git add .
git commit -m "feat(chat): 实现意图识别引擎

- 添加 IntentRecognizer 类
- 支持 8 种自然语言模式
- 单元测试覆盖 10+ 场景

Closes #42"
```

### 5. 推送 & PR

```bash
git push origin feature/p1-api-bridge
# 在 GitHub 创建 PR → develop
```

### 6. 代码审查

PR 必须通过：
- [ ] 后端测试通过
- [ ] 前端测试通过
- [ ] 类型检查通过
- [ ] 代码风格检查通过
- [ ] 有测试覆盖新功能
- [ ] 文档已更新

### 7. 合并

```bash
# Squash merge to develop
git checkout develop
git merge --squash feature/p1-api-bridge
git commit -m "feat(chat): 实现意图识别引擎 (#42)"
```

## 分支策略

```
main          ← 生产就绪代码，只接受 develop 的 merge
├── develop   ← 开发主分支，所有 feature 合入这里
│   ├── feature/p1-api-bridge
│   ├── feature/p1-detail-fixes
│   ├── feature/p2-visualization
│   └── ...
└── hotfix/*  ← 紧急修复，从 main 创建
```

## Commit 规范

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type**: feat / fix / refactor / test / docs / chore

**Scope**: chat / assets / alerts / operations / dashboard / ui / api / db

**示例**:
```
feat(alerts): 添加告警确认/解决 API 端点

- PUT /alerts/{id}/acknowledge
- PUT /alerts/{id}/resolve
- 状态转换验证
- 审计日志记录

Closes #38
```

## 代码审查清单

### 后端
- [ ] 有类型提示
- [ ] 有 docstring
- [ ] 有错误处理
- [ ] 有日志记录
- [ ] 有测试覆盖
- [ ] 无 bare except
- [ ] 无 TODO/FIXME

### 前端
- [ ] 有 TypeScript props 接口
- [ ] 使用 cn() 拼接 className
- [ ] 有 aria-label
- [ ] 有 loading 状态
- [ ] 有 empty 状态
- [ ] 有 error 状态
- [ ] 无 any 类型
