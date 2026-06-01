# SRE Platform V3.2 — 完整程式碼審查報告

> **專案**: Engineer Assist SRE Platform  
> **版本**: 3.2.0  
> **審查日期**: 2026-06-01  
> **審查範圍**: 全端（Python FastAPI 後端 + React/TypeScript 前端 + 基礎設施配置 + 測試）

---

## 目錄

1. [摘要](#1-摘要)
2. [關鍵安全漏洞](#2-關鍵安全漏洞)
3. [關鍵運行時錯誤](#3-關鍵運行時錯誤)
4. [後端程式碼審查](#4-後端程式碼審查)
5. [前端程式碼審查](#5-前端程式碼審查)
6. [基礎設施配置審查](#6-基礎設施配置審查)
7. [測試覆蓋率審查](#7-測試覆蓋率審查)
8. [產品維度分析](#8-產品維度分析)
9. [改進建議](#9-改進建議)
10. [總結](#10-總結)

---

## 1. 摘要

| 類別 | 後端 | 前端 | 基礎設施 |
|------|------|------|---------|
| 審查檔案數 | 52 個 .py 檔案 | 60+ 個 .ts/.tsx/.css 檔案 | 6 個配置文件 |
| 關鍵安全漏洞 | 4 | 1 (CSS變量洩露) | 0 |
| 關鍵運行時錯誤 | 2 | 5 | 1 |
| 中級問題 | 15+ | 20+ | 3 |
| 程式碼重複 | 少 | 大量 | 少 |

---

## 2. 關鍵安全漏洞 (CRITICAL)

### 🔴 CRITICAL-01: 平台密碼明文儲存

**檔案**: `backend/app/api/v1/platforms.py` (第 155, 191 行), `backend/app/models/platform.py`

**說明**: 儘管資料庫欄位命名為 `encrypted_password`，但 `create_platform` 和 `update_platform` 直接將明文密碼存入資料庫，未進行任何加密。

```python
# platforms.py line 155 — 直接儲存明文密碼
platform = PlatformConnection(
    name=req.name,
    type=req.type,
    host=req.host,
    port=req.port,
    username=req.username,
    encrypted_password=req.password,  # ⚠️ 明文儲存！
    ...
)
```

**風險**: 任何具有資料庫存取權限的人均可取得所有虛擬化平台的管理員憑證。

**建議**: 使用 `cryptography.fernet` 或類似機制對密碼進行對稱加密，並在執行操作時解密。

---

### 🔴 CRITICAL-02: Shell 命令注入

**檔案**: `backend/app/services/operation_executor.py` (第 229-266 行)

**說明**: `_execute_real` 方法使用 f-string 拼接使用者輸入到 shell 命令中，未做任何清理。

```python
# 使用者提供的 target 直接嵌入命令字串
f"ping -c 3 {target}"         # 命令注入！
f"nc -zv {target} 22 80 443"  # 命令注入！
f"nslookup {target}"          # 命令注入！
f"traceroute -m 15 {target}"  # 命令注入！
```

**風險**: 如果攻擊者能控制 `params.target`，可執行任意系統命令。

**建議**: 使用 `shlex.quote()` 轉義所有使用者輸入，或使用 `asyncio.create_subprocess_exec()` 傳遞參數列表。

---

### 🔴 CRITICAL-03: FusionSphere 協議降級

**檔案**: `backend/app/platforms/fusionsphere/adapter.py` (第 40 行)

```python
scheme = "https" if config.verify_ssl else "http"
```

**說明**: 當 `verify_ssl=False` 時，連線降級為 HTTP（明文），包括登入時傳輸的密碼。

**風險**: 密碼在網路中以明文傳輸，可被中間人攻擊竊取。

**建議**: 始終使用 HTTPS，僅控制憑證驗證，不控制協議方案。

---

### 🔴 CRITICAL-04: 敏感 API 無認證保護

**檔案**: 多個 API 路由檔案

| 端點 | 缺失認證 |
|------|---------|
| `/api/v1/platforms/*` | ❌ 無 `CurrentUser` 依賴 |
| `/api/v1/migration/*` | ❌ 無 `CurrentUser` 依賴 |
| `/api/v1/dashboard/*` | ❌ 無 `CurrentUser` 依賴 |
| `/api/v1/chat` | ✅ 有意為之（工程師助手） |
| `/api/v1/atomics/*` | ❌ 無 `CurrentUser` 依賴 |

**風險**: 任何人無需登入即可管理平台連線、執行遷移、查看儀表板。

---

## 3. 關鍵運行時錯誤 (CRITICAL)

### 🔴 CRITICAL-05: NameError — 引用未匯入的類別

**檔案**: `backend/app/services/operation_executor.py` (第 286 行)

```python
except asyncio.TimeoutError:
    status = ExecutionStatus.FAILED
    error = str(exc)
    error_code = "TIMEOUT"
    raise OperationFailedError(...)  # 💥 NameError! 此類別未定義
```

**說明**: `OperationFailedError` 在該檔案中既未定義也未匯入。正確的類別名稱為 `OperationFailedException`（定義於 `exceptions.py`）。

**風險**: 當 infra 操作超時時，此程式碼將拋出 `NameError`，導致 500 錯誤。

---

### 🔴 CRITICAL-06: 遷移引擎命令不可執行

**檔案**: `backend/app/migration/engine.py` (第 151 行)

**說明**: `execute_migration` 使用 `asyncio.create_subprocess_shell(step.command, ...)` 執行 shell 命令，但 `step.command` 中包含描述性字串（如 `"export OVA from vSphere"`、`"download disk image"`、`"create VM from converted disk"`），這些不是有效的 shell 命令，執行時必定失敗。

**風險**: 整個 VM 遷移功能不可用。

---

## 4. 後端程式碼審查

### 4.1 架構評分

| 維度 | 評分 | 說明 |
|------|------|------|
| 分層架構 | ⭐⭐⭐⭐⭐ | 清晰的 API → Service → Repository 分層，依賴單向 |
| 型別安全 | ⭐⭐⭐⭐ | Pydantic v2 + type hints，少數 cast 使用 |
| 非同步設計 | ⭐⭐⭐⭐ | 全面 async/await，但部分 blocking call 包在 thread pool |
| 錯誤處理 | ⭐⭐⭐ | 有自定義異常層級，但部分 broad except |
| 可測試性 | ⭐⭐⭐⭐ | 依賴注入良好，但部分 singleton 模式使測試困難 |

### 4.2 主要問題

#### 高優先級

| 檔案 | 問題 | 影響 |
|------|------|------|
| `platforms/base.py` | `ConnectionError` 遮蔽 builtins.ConnectionError | 捕獲 socket 錯誤時行為異常 |
| `asset_repo.py` | LIKE 查詢未跳脫 SQL wildcard | 搜尋 `%` 或 `_` 時匹配過多結果 |
| `kvm/adapter.py` | XML 透過 f-string 拼接未跳轉 | 快照名稱含 `<` 或 `>` 時 XML 解析失敗 |
| `audit.py` | 請求 body 儲存於 audit log（含敏感資料） | 合規性問題 — 密碼/token 明文存於日誌 |
| `dashboard_service.py` | CPU / Memory 趨勢永遠回傳 0 | 儀表板圖表無實際資料 |
| `asset_service.py` | `execute_action` 為 stub | VM 操作功能不可用 |

#### 中度問題

| 檔案 | 問題 |
|------|------|
| `database.py` | 用 global 變數做 lazy init，無法使用 DI 覆蓋 |
| `base.py` (models) | `updated_at` 的 `onupdate` 僅在 Python 層生效 |
| `chat_service.py` | `_contexts` 使用 dict 存 conversation context，無 TTL 或清理機制，memory leak |
| `registry.py` | 796 行的單一檔案，所有 operation 寫死在 `_seed_operations()` 中 |
| `migration/engine.py` | 所有計劃存於記憶體，重啟後遺失 |
| `platform_repo.py` | `get_by_id` 無需 override base class |

---

## 5. 前端程式碼審查

### 5.1 架構評分

| 維度 | 評分 | 說明 |
|------|------|------|
| 元件化 | ⭐⭐⭐⭐ | 良好元件拆分，UI library 獨立 |
| 型別安全 | ⭐⭐⭐ | strict mode + 介面定義良好，但大量 type cast |
| 狀態管理 | ⭐⭐⭐ | React Query + Zustand 雙軌並存，部分 redundant |
| 測試覆蓋 | ⭐⭐⭐ | 有 Unit + E2E，但整合測試偏少 |
| 可維護性 | ⭐⭐ | 大量 duplicate code，雙目錄結構混亂 |

### 5.2 主要問題

#### Bug 類

| 檔案 | Bug |
|------|-----|
| `DashboardView.tsx` | `AlertSummary` 的 `statusCounts={undefined}` — 「By Status」永遠顯示 0 |
| `ChatView.tsx` | "Select Execute" 忽略選中的 ID，行為與 "Execute All" 一致 |
| `OperationsView.tsx` | `onApprove` 和 `onReject` 從未傳遞給 `OperationCard`，審批按鈕不可用 |
| `ResourcesView.tsx` | 所有批次操作 handler 為 `() => {}`（no-op），按鈕點擊沒反應 |
| `AlertsView.tsx` | "全部" Tab 計數顯示的是已篩選數量，非總數 |
| `PlatformWizard.tsx` | Test connection 發送硬編碼字串 `'test'` 而非實際配置 |

#### 程式碼重複

以下函數存在兩份實作，且行為不完全一致：

| 函數 | `lib/utils.ts` | `utils/` 目錄 | 差異 |
|------|---------------|---------------|------|
| `formatBytes` | `decimals=2` | `decimals=1` | 預設小數位數不同 |
| `formatRelativeTime` | "minutes ago" | "m ago" | 顯示格式不同 |
| `cn` | ✅ | ✅ | 實作相同（重複） |
| `formatDuration` | ✅ | ✅ | 實作相同（重複） |

CSS 主題也重複：
- `index.css` 定義了一份 CSS custom properties + 動畫
- `styles/theme.css` 定義了另一份，部分重疊、部分衝突

#### 型別衝突

```typescript
// constants.ts
type Platform = "vmware" | "kvm" | "fusioncompute" | "bare-metal";

// types/platform.ts
interface Platform { id: string; name: string; type: string; host: string; ... }
```

兩個完全不同的型別同名 `Platform`，`Asset.platform` 使用 `constants.ts` 的 string union，而 `PlatformManager` 使用 `types/platform.ts` 的 interface。

#### HTTP Client 不一致

| 層 | 檔案 | 認證 | 重試 | 錯誤處理 |
|-----|------|------|------|---------|
| `httpClient` | `api/client.ts` | ✅ 自動注入 token | ✅ 指數退避 | ✅ 結構化 `ApiError` |
| `fetchJSON` | `api/platforms.ts` | ❌ 無 | ❌ 無 | ❌ 僅 throw Error |

平台管理 API 無認證、無重試、錯誤處理不一致。

---

## 6. 基礎設施配置審查

### 6.1 Docker Compose

| 問題 | 詳情 |
|------|------|
| `version: "3.9"` | 已過時，Docker Compose v2 不需此欄位 |
| 硬編碼密碼 | `v32_dev_password` 寫在 docker-compose.yml 中 |
| 開發環境洩露 | `JWT_SECRET_KEY: dev-secret-key` 硬編碼 |
| 前端 volume mount | `./frontend:/app` 將整個原始碼 mount 進 container，適合 dev 但非 prod 模式 |
| 無 network 隔離 | 所有服務在同一個 default network，未定義自定義 network |

### 6.2 Dockerfile（未直接讀取但常見問題）

**建議**: 確保 production Dockerfile 使用 multi-stage build，distroless 基礎映像。

### 6.3 部署腳本

**建議**: `deploy-linux.sh` 和 `deploy-windows.ps1` 應處理 secret 管理（如 vault / environment-specific .env）。

---

## 7. 測試覆蓋率審查

| 測試層 | 檔案數 | 品質 | 說明 |
|--------|--------|------|------|
| 後端單位測試 | 11 | ⭐⭐⭐⭐⭐ | 測試品質優秀，chat_service 有 60+ 測試方法 |
| 前端元件測試 | 12 | ⭐⭐⭐ | 能驗證 render，但缺 interaction 測試 |
| E2E Playwright | 6 | ⭐⭐⭐ | 基本 smoke test，缺真實資料驗證 |

### 缺失的測試場景

1. **安全性測試**: 無 SQL injection / command injection / XSS 測試
2. **並發測試**: 無 race condition / 同時操作測試
3. **平台配接器整合測試**: 使用 mock 而非真實 SDK
4. **效能/壓力測試**: 無
5. **前端 mutation 失敗場景**: mutation error handler 未測試
6. **遷移引擎**: 無實際命令驗證（因命令無法執行）

---

## 8. 產品維度分析

### 8.1 產品定位

Engineer Assist 是面向 SRE 團隊的**智慧運維平台**，核心價值為：
1. **自然語言驅動的運維操作** — 透過聊天介面執行運維任務
2. **多虛擬化平台統一管理** — vSphere / KVM / FusionSphere 單一入口
3. **跨平台 VM 遷移** — 協助資料中心遷移或平台轉換

### 8.2 功能完整性

| 功能模塊 | 完成度 | 評估 |
|---------|--------|------|
| Chat 智慧助手 | 🟡 75% | Intent recognition 完善，但缺少 LLM 整合、對話歷史持久化 |
| 資產管理 (CRUD) | 🟢 90% | 完整 CRUD + 搜尋篩選，但批量操作未實作 |
| 告警管理 | 🟢 85% | 完整生命週期，但 WebSocket 即時推送未完成 |
| 儀表板 | 🟡 60% | 基本統計有，但趨勢資料為 stub (回傳 0) |
| 平台納管 | 🟡 65% | 配接器架構良好，但密碼明文儲存為安全紅旗 |
| VM 遷移 | 🔴 40% | 命令不可執行，引擎為 prototype 階段 |
| 操作執行 | 🟡 70% | 工作流程完整，但真實執行依賴未實作的平台操作 |
| 用戶認證 | 🟡 60% | JWT 實作良好，但多數端點未啟用認證 |

### 8.3 使用者體驗

**優點**:
- 繁體中文自然語言輸入，降低 SRE 使用門檻
- 操作風險分級（Low/Medium/High/Critical），幫助判斷
- 操作需要審批的高風險操作設計
- 響應式佈局，支援行動裝置

**缺點**:
- 無 LLM 整合，語意理解受限於 regex pattern
- 對話歷史無持久化（重整頁面即遺失）
- 無即時資料更新（WebSocket 整合未完成）
- 多處功能為 placeholder / stub
- 部分元件 CSS 風格不一致（Tailwind vs CSS custom properties）

### 8.4 可擴展性

**優秀設計**:
- PlatformAdapter 抽象類別設計，新增平台只需實作 3 個方法
- 109 個 Atomic Operation 的註冊表設計，便於擴充操作
- Repository 泛型 CRUD 基底類別
- 自定義異常層級架構

**待改進**:
- Operation registry 的 796 行寫死在程式碼中，應使用 decorator 或檔案載入
- Migration engine 無持久化
- 過度依賴 global singleton（registry, chat_service, _engine）
- 部分功能依賴系統命令（ping, nslookup, virt-v2v），缺乏 container 環境相容性

---

## 9. 改進建議

### P0 — 立即修復（安全與穩定）

| # | 建議 | 難度 | 影響 |
|---|------|------|------|
| 1 | 平台密碼使用 Fernet 對稱加密儲存 | 低 | 🔴 安全 |
| 2 | shell 命令使用 `shlex.quote()` 或 `create_subprocess_exec` | 低 | 🔴 安全 |
| 3 | FusionSphere adapter 移除協議降級邏輯 | 低 | 🔴 安全 |
| 4 | 所有敏感 API 加入 JWT 認證 | 中 | 🔴 安全 |
| 5 | 修復 `OperationFailedError` NameError | 低 | 🔴 Runtime |
| 6 | Migration engine 命令重寫為有效命令 | 高 | 🔴 功能 |

### P1 — 短期改進（功能與品質）

| # | 建議 | 難度 |
|---|------|------|
| 7 | 統一前端 HTTP client，platform API 改用 `httpClient` | 中 |
| 8 | 解決 CSS 主題重複（`index.css` vs `theme.css`） | 低 |
| 9 | 解決 `formatBytes`/`formatRelativeTime` 等 duplicate util | 低 |
| 10 | 解決 Frontend `Platform` type 衝突（constants.ts vs types/platform.ts） | 低 |
| 11 | DashboardView 傳遞 `statusCounts` 給 AlertSummary | 低 |
| 12 | 修復 ChatView "Select Execute" 行為 | 中 |
| 13 | 修復 OperationsView approve/reject 未接通問題 | 中 |
| 14 | 修復 PlatformWizard test connection 發送錯誤資料 | 高 |
| 15 | 修復 AssetsView 批次操作 handler | 中 |
| 16 | 前端搜尋加入 debounce（alertFilters, filterBar） | 低 |
| 17 | Audit log 中過濾敏感欄位（密碼、token） | 低 |

### P2 — 中期改進（架構與效能）

| # | 建議 | 難度 |
|---|------|------|
| 18 | 引入 LLM 或 ML 替代 regex-based intent recognition | 高 |
| 19 | WebSocket 即時推送告警/操作狀態 | 中 |
| 20 | Route-level code splitting (React.lazy) | 低 |
| 21 | 對話歷史持久化（資料庫） | 中 |
| 22 | Migration engine 改為 DB 持久化 | 中 |
| 23 | Operation registry 改為 decorator-based 自動註冊 | 中 |
| 24 | Dashboard 趨勢資料接入真實 metric | 高 |
| 25 | 全域 loading spinner / Suspense boundary | 低 |

### P3 — 長期改進（產品化）

| # | 建議 | 難度 |
|---|------|------|
| 26 | RBAC 權限模型實作 | 高 |
| 27 | 多租戶支援 | 高 |
| 28 | 操作審計報表匯出 | 中 |
| 29 | 自定義 Dashboard widget | 高 |
| 30 | i18n 國際化 | 中 |
| 31 | 效能測試與壓力測試 | 中 |
| 32 | CI/CD pipeline（GitHub Actions） | 中 |
| 33 | 健康檢查與自我監控 | 中 |

---

## 10. 總結

### 優點

1. **架構設計優秀**: 分層清晰（API → Service → Repository），抽象化平台配接器模式利於擴展
2. **型別安全意識強**: Pydantic v2 + TypeScript strict mode，錯誤預防在前
3. **操作安全設計**: Atomic operation 的風險分級、審批流程設計合理
4. **文檔完整**: 有 ARCHITECTURE.md、API_CONTRACT.md、DEPLOYMENT.md 等專業文檔
5. **測試品質佳**: 後端測試特別是 chat_service 測試覆蓋率高
6. **技術棧現代**: FastAPI + React 18 + Vite + TanStack Query + Zustand

### 需要立即關注的風險

- 🔴 **4 個安全漏洞**（密碼明文、命令注入、協議降級、無認證）
- 🔴 **2 個運行時錯誤**（NameError、遷移命令失效）
- 🟡 **大量前端 Bug**（逾 10 個已知功能未正確串接）
- 🟡 **程式碼重複問題**（工具函數雙目錄、CSS 主題衝突）

### 總體評價

這是一個**架構基礎良好但產品化程度不足**的專案。後端的分層架構和配接器模式設計讓人印象深刻，但安全問題和未完成的 stub 功能使其距離生產就緒還有一定距離。前端有多個明顯的 bug（如元件間的 props 未正確傳遞）和架構問題（重複代碼、型別衝突），建議優先解決安全漏洞和 P0/P1 問題後再進行功能擴展。

---

*報告由 QoderWork 自動生成*
