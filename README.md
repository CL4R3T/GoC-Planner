# 🎲 GoC-Planner — Event Optimizer

概率事件触发优化器。帮助玩家在给定随机数生成器（硬币、骰子等）下，选择最优的试验次数 **n**，最大化触发特定稀有度事件的概率。

## Quick Start

```bash
git clone <repo-url> && cd GoC-Planner
uv sync
```

### Web GUI（推荐）

```bash
uv run python app.py
# 浏览器打开 http://localhost:5000
```

左侧配置面板选择生成器、公式数、目标事件、n 上限 → 点击 Optimize → 右侧显示概率曲线和事件分布图。

### CLI

```bash
uv run python main.py
```

交互式对话：生成器 → 公式数 → 目标事件 → n 上限 → 输出最优 n 及概率表。

## How It Works

玩家有一个随机数生成器（硬币 k=2，骰子 k=6 等），进行 **n** 次独立试验。

- **m 个事件区间** `p₁ > p₂ > ... > pₘ` — 按稀有度从常见到极稀有排列
- **f 个特征公式** — 每个公式对结果序列计算得分 x，稀有度 = `有利结果数 / kⁿ`
- 若稀有度落入区间 `(p_{k+1}, p_k]`，则触发事件 k

**核心指标**：至少一个公式触发目标事件的概率（公式间按独立近似处理）。

```
P(事件 k 触发) = 1 - ∏_f (1 - count_f(k) / kⁿ)
```

## Project Structure

```
GoC-Planner/
├── app.py                    # Flask 后端（Web GUI）
├── main.py                   # CLI 入口
├── pyproject.toml            # uv 项目配置
├── events.json               # 事件阈值配置
├── core/
│   ├── events.py             # 事件阈值管理
│   ├── engine.py             # 核心计算引擎
│   └── utils.py              # 组合数 C(n, k)
├── generators/
│   ├── base.py               # Formula 数据结构
│   └── coin.py               # 公平硬币 (k=2) 公式集
└── templates/
    └── index.html            # Web GUI 前端 (Chart.js)
```

## Generators

| 生成器 | k | 公式 |
|--------|---|------|
| **coin** | 2 | At Least X, Exact Count, Longest Streak, Alternating, Prime Count |

添加新生成器：在 `generators/` 下新建 `.py` 文件，导出 `K` 和 `FORMULAS: list[Formula]`，在 `generators/__init__.py` 中注册即可。

## Events

事件配置存储在 `events.json`，按概率从大到小排列。格式：

```json
[
  { "name": "... being left-handed.", "probability": "1/10" },
  { "name": "... having blue eyes.",   "probability": 0.95 }
]
```

`probability` 支持浮点数或 `"1/N"` 字符串格式。

## API Endpoints

| 端点 | 方法 | 说明 |
|------|------|------|
| `/` | GET | Web GUI 页面 |
| `/api/config` | GET | 返回生成器、公式、事件配置 |
| `/api/optimize` | POST | 运行优化，返回概率曲线 + 分布 |
| `/api/distribution` | POST | 查询指定 n 的完整事件分布 |

## Dependencies

- **Python** ≥ 3.12
- **Flask** ≥ 3.0（Web GUI）
- **Chart.js** 4.x（前端，CDN 加载）
- 无其他第三方依赖 — 核心计算使用 Python 任意精度整数，零浮点误差
