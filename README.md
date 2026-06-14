# 社区旧物赠送流转记录

社区内旧物赠送与领取的简易流转记录系统（MVP）。

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + Naive UI + @vueuse/core + axios + date-fns，端口 **6101** |
| 后端 | Flask + SQLite（`backend/data/gift.db`），端口 **6000** |

## 功能

- 赠送记录列表（`n-data-table`）
- 新增 / 编辑弹窗表单（`n-form`）
- 字段：物品名、描述、赠送日期、赠送地点、接收方昵称、赠送人昵称、联系电话、是否已取走
- 首次启动自动写入 5 条 seed 数据

## 目录结构

```
├── .github/
│   └── workflows/
│       └── ci.yml       # 持续集成流水线
├── backend/             # Flask API
│   ├── app.py
│   ├── requirements.txt
│   └── data/            # SQLite 数据库（自动生成）
├── frontend/            # Vue 3 前端
│   ├── package.json
│   └── src/
└── scripts/
    └── health_check.sh  # 后端接口健康检查脚本
```

## 启动方式

### 1. 后端（一条命令）

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
python app.py
```

后端运行在 http://localhost:6000

### 2. 前端

另开终端，**任选一种方式**：

**方式 A — 在项目根目录：**
```powershell
npm install --prefix frontend
npm run dev
```

**方式 B — 在 frontend 目录：**
```powershell
cd frontend
npm install
npm run dev
```

前端默认运行在 http://localhost:6101（若端口被占用会自动尝试 6102、6103…，请看终端输出）。API 通过 Vite 代理转发至后端。

> 请先启动后端，否则页面能打开但列表会提示「加载失败」。

## 常见问题

| 现象 | 原因 / 处理 |
|------|-------------|
| `'vite' 不是内部或外部命令` | 未安装依赖，先执行 `npm install`（在 `frontend` 目录或根目录用 `--prefix frontend`） |
| `Missing script: "dev"` | 当前目录不对，应在项目根目录或 `frontend/` 下运行 |
| `npm run dev` 无报错但浏览器打不开 | 看终端里 Vite 输出的实际地址（可能不是 6101）；确认访问的是 `http://localhost:端口/` 而非直接打开 html 文件 |
| 页面空白或列表报错 | 后端未启动，先在 `backend` 目录运行 `python app.py` |
| PowerShell 不支持 `&&` | 请分行执行命令，或使用上面方式 A/B |
| 端口 6101 已被占用 | 已配置自动换端口；或关闭占用该端口的旧进程后重试 |

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/gifts` | 获取赠送记录列表（支持查询参数，见下方），返回包含 `location` 赠送地点字段 |
| GET | `/api/gifts/:id` | 获取单条记录，返回包含 `location` 赠送地点字段 |
| POST | `/api/gifts` | 新建记录，请求体及返回均包含 `location` 赠送地点字段 |
| PUT | `/api/gifts/:id` | 更新记录，请求体及返回均包含 `location` 赠送地点字段 |
| PUT | `/api/gifts/:id/mark-taken` | 快捷标记指定记录为已取走（无需提交完整表单） |
| DELETE | `/api/gifts/:id` | 删除记录 |
| GET | `/api/gifts/summary` | 轻量汇总统计（总记录数、已取走数、待取走数），返回字段见下方 |
| GET | `/api/gifts/export` | 导出赠送记录为 CSV 文件（支持与列表相同的查询参数），返回字段见下方 |
| GET | `/api/health` | 健康检查 |

**GET `/api/gifts` 可选查询参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `item_name` | string | 按物品名关键字模糊查询，不传则不过滤 |
| `is_taken` | int | 按是否已取走筛选：`1` 已取走，`0` 待取走，不传则不过滤 |

**GET `/api/gifts/summary` 返回字段：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `total_count` | int | 赠送记录总条数 |
| `taken_count` | int | 已标记为取走的记录条数 |
| `pending_count` | int | 待取走的记录条数（= 总条数 - 已取走数） |

**GET `/api/gifts/export` 可选查询参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `item_name` | string | 按物品名关键字模糊查询，不传则不过滤 |
| `is_taken` | int | 按是否已取走筛选：`1` 已取走，`0` 待取走，不传则不过滤 |

**GET `/api/gifts/export` 返回格式：**

- Content-Type：`text/csv; charset=utf-8-sig`
- 响应体为 UTF-8 BOM 开头的 CSV 文本文件，浏览器会触发下载
- 文件名格式：`gift_records_YYYYMMDD_HHmmss.csv`
- CSV 列顺序：物品名、描述、赠送日期、接收方昵称、是否已取走

## 持续集成（CI）

项目配置了 GitHub Actions 持续集成流水线（`.github/workflows/ci.yml`），在 **推送到 `main` 分支** 或 **向 `main` 发起 Pull Request** 时自动运行。

### 流水线内容

| 阶段 | 检查项 | 说明 |
|------|--------|------|
| 后端检查 | 依赖安装 | `pip install -r requirements.txt` |
| 后端检查 | 接口健康检查 | 启动 Flask 服务后请求 `/api/health`，验证返回正常 |
| 前端检查 | 依赖安装 | `npm ci`（基于 `package-lock.json` 做确定性安装） |
| 前端检查 | TypeScript 类型检查 | `vue-tsc --noEmit` |
| 前端检查 | 生产构建 | `npm run build` |

任一环节失败，流水线会标记为失败并在 PR 页面显示红叉。

### 本地等价命令

如需在本地手动执行与 CI 相同的检查，可运行以下命令：

**后端：**
```bash
cd backend
pip install -r requirements.txt
bash ../scripts/health_check.sh 6000
```

### 后端自动化测试

项目使用 `pytest` 作为轻量级单元测试框架，测试文件位于 `backend/tests/` 目录。测试使用独立临时数据库文件，不会污染正式数据。

**运行所有测试：**
```bash
cd backend
pip install -r requirements.txt
python -m pytest tests/ -v
```

**运行指定测试文件：**
```bash
cd backend
python -m pytest tests/test_gifts.py -v
```

**运行指定测试类：**
```bash
cd backend
python -m pytest tests/test_gifts.py::TestListGifts -v
```

**运行指定测试用例：**
```bash
cd backend
python -m pytest tests/test_gifts.py::TestListGifts::test_filter_by_item_name -v
```

**生成测试覆盖率报告：**
```bash
cd backend
pip install pytest-cov
python -m pytest tests/ --cov=. --cov-report=html
```

**测试覆盖场景：**

| 测试类 | 测试用例 | 说明 |
|--------|----------|------|
| `TestListGifts` | `test_filter_by_item_name` | 列表查询带物品名筛选 |
| `TestCreateGift` | `test_create_phone_empty` | 新建记录联系电话为空校验失败 |
| `TestCreateGift` | `test_create_phone_invalid_length` | 新建记录联系电话长度错误校验失败 |
| `TestCreateGift` | `test_create_phone_non_digits` | 新建记录联系电话含非数字校验失败 |
| `TestMarkGiftTaken` | `test_mark_taken_success` | 快捷标记已取走成功 |
| `TestMarkGiftTaken` | `test_mark_taken_duplicate` | 重复标记返回错误 |
| `TestMarkGiftTaken` | `test_mark_taken_idempotent_check` | 先成功标记后重复标记返回错误 |

**前端：**
```bash
cd frontend
npm ci
npx vue-tsc --noEmit
npm run build
```

> 提示：本地运行健康检查脚本前，请确保 6000 端口未被占用。脚本会自动启动并停止 Flask 服务。

## 环境要求

- Python 3.10+
- Node.js 18+（使用项目内 `npm install`，无需全局 pnpm/yarn）
