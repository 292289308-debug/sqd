# 灵眸量化 (SmartQuant Dashboard)

> 面向个人投资者与量化研究员的"一站式"行情 + 策略 + 实盘看板
> 比同花顺更量化 · 比 JoinQuant 更轻量本地

**版本**: v0.1 立项稿
**日期**: 2026-06-19
**状态**: Phase 1 MVP 开发中

---

## 🎯 项目定位

| 维度 | 同花顺/通达信 | JoinQuant/BigQuant | **本项目 (SQD)** |
|---|---|---|---|
| 实时行情 | ★★★★★ | ★★ | ★★★★ |
| 技术指标 | ★★★★ | ★★★ | ★★★★★ |
| 量化回测 | ★ | ★★★★★ | ★★★★ |
| 本地部署 | ★ | ★★ | ★★★★★ |
| 开源/可定制 | × | × | ✓ |
| 学习曲线 | 平缓 | 陡峭 | 中等 |

---

## 📁 项目结构

```
sqd/
├── README.md                    # 本文件
├── docker-compose.yml           # 一键启动所有服务
├── .env.example                 # 环境变量模板
├── backend/                     # FastAPI 后端
│   ├── app/
│   │   ├── main.py              # 入口
│   │   ├── core/                # 配置 + 安全
│   │   ├── api/v1/endpoints/    # REST 路由
│   │   ├── models/              # SQLAlchemy 模型
│   │   └── services/            # 业务逻辑
│   ├── tests/                   # pytest
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                    # Vue 3 前端
│   ├── src/
│   │   ├── views/               # 页面
│   │   ├── components/          # 组件
│   │   └── main.ts
│   ├── package.json
│   └── Dockerfile
├── scripts/
│   ├── init_db.sql              # 数据库初始化
│   ├── prometheus.yml           # 监控配置
│   └── fetch_history.py         # 历史数据拉取
├── data/                        # 本地数据 (SQLite / 缓存)
└── docs/                        # 文档
    ├── 01_PRD.md                # 产品需求
    ├── 02_技术架构.md           # 架构设计
    ├── 03_数据库设计.md         # Schema 说明
    ├── 04_API规范.md            # REST 规范
    ├── 05_前端设计.md           # UI 线框
    ├── 06_策略开发指南.md       # 量化教程
    ├── 07_部署运维.md           # Docker 部署
    ├── 08_合规说明.md           # 法律风险
    └── 09_路线图.md             # 版本规划
```

---

## 🚀 快速开始

### 方式 A: Docker (推荐,需 Docker 环境)

```bash
# 1. 复制环境变量
cp .env.example .env
# 编辑 .env 填入 TUSHARE_TOKEN

# 2. 一键启动
docker compose up -d

# 3. 访问
# 前端: http://localhost:5173
# 后端 API: http://localhost:8000/docs
```

### 方式 B: 本地开发 (无需 Docker)

```bash
# 后端
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload

# 前端 (新开终端)
cd frontend
npm install
npm run dev
```

---

## 🛠 技术栈

| 层 | 选型 |
|---|---|
| 后端 | Python 3.11+ / FastAPI / SQLAlchemy 2.0 / asyncpg |
| 前端 | Vue 3 / TypeScript / Vite 5 / Pinia |
| K线图 | TradingView Lightweight Charts |
| 数据库 | TimescaleDB (时序) + PostgreSQL (业务) |
| 缓存 | Redis 7 |
| 任务队列 | Celery + APScheduler |
| 行情数据 | Tushare Pro / AkShare |
| 回测引擎 | backtrader (MVP) → 自研事件驱动 (V1.1) |
| 部署 | Docker Compose → Kubernetes |

---

## 📅 路线图

| 阶段 | 时长 | 内容 |
|---|---|---|
| **Phase 1 MVP** | 2 个月 | A 看盘 + B 回测 |
| V1.1 | +1 个月 | C 实盘 (华泰 CTP 模拟盘) |
| V1.2 | +1 个月 | D 资讯 (财联社 + 公告摘要) |
| Phase 2 | 持续 | AI 因子 / NLP / 移动端 |

详见 [`docs/09_路线图.md`](docs/09_路线图.md)

---

## 📊 Phase 1 MVP 交付清单

- [x] 项目结构 + Docker Compose
- [x] 数据库 schema (PostgreSQL + TimescaleDB)
- [ ] FastAPI 后端骨架 + 健康检查
- [ ] Vue 3 前端骨架 + K 线展示
- [ ] Tushare 数据接入 demo
- [ ] 双均线回测 PoC
- [ ] 前端线框图 (首页/自选股/K线/回测)
- [ ] 合规清单

---

## ⚖️ 合规声明

本项目定位为 **个人量化研究工具**:
- ✅ 自用看行情 + 回测: 无需任何资质
- ⚠️ 提供给第三方使用: 需"金融信息服务业务"资质
- ❌ 禁止"承诺收益" / "代客理财" / "非法荐股"

详见 [`docs/08_合规说明.md`](docs/08_合规说明.md)

---

## 📜 许可证

TBD (计划 MIT)

---

## 关联文档

- 详细规划: `../stock_quant_dashboard_plan.md`
- 立项决策: B+C+A+B+B+A (Q1~Q6)
