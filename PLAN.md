# Event Optimizer — 实现计划

## Context

玩家有一个随机数生成器（硬币 k=2、骰子 k=6 等），进行 n 次独立投掷。游戏有 m 个事件区间 `p₁ > p₂ > ... > p_m`，以及 f 个特征公式。每个公式计算"结果在维度 f 上得分 ≥ x 的概率" p_f(n,x)，稀有度值 = p_f(n,x)。若稀有度落入 `(p_{k+1}, p_k]`，则触发事件 k。

**问题**：事件阈值固定不可改，玩家只能调整 n。需要工具帮助玩家选择最优 n，最大化触发特定事件的概率。

**指标**："至少一个公式触发该事件的概率"（公式间按近似独立处理，小 n 可精确枚举）。

## 项目结构

```
GoChelper/
├── main.py                  # CLI 入口，交互式对话
├── core/
│   ├── __init__.py
│   ├── events.py            # 事件阈值管理、二分查找区间
│   ├── engine.py            # 核心计算引擎
│   └── utils.py             # 组合数 C(n,k)、缓存
├── generators/
│   ├── __init__.py
│   ├── base.py              # Formula 数据类定义
│   ├── coin.py              # 公平硬币 k=2，导出 formulas 列表
│   └── dice.py              # 公平骰子 k=6，导出 formulas 列表（占位）
```

## 模块设计

### 1. `generators/base.py` — Formula 数据结构

```python
@dataclass
class Formula:
    name: str                          # "At Least X Heads"
    description: str                   # 人类可读说明
    valid_x: Callable[[int], list[int]]  # 给定 n，返回所有合法 x 的有序列表
    compute: Callable[[int, int], int]  # 返回有利结果数（分子），分母 = k**n
```

- `valid_x(n)` 返回有序列表，例如连续型返回 `[1, 2, ..., n]`，回文（仅偶数）返回 `[2, 4, 6, ...]`
- `compute` 返回精确 `Fraction` 或 `float`
- 概率质量计算不再用 `x+1`，而是取 `valid_x` 列表中的下一个值 `x_next`：`mass = p(n, x) - p(n, x_next)`；列表最大值的 `x_next` 视为概率 0

### 2. `generators/coin.py` — 硬币公式（按解锁顺序）

| # | 公式 | x 范围 (valid_x) | 计算方式 |
|---|------|-----------------|---------|
| 1 | **至少 x 次正面** `AtLeastXHeads` | `[1, 2, ..., n]` | 有利结果数 = `∑_{i=x}^{n} C(n,i)` |
| 2 | **最长连续正面 ≥ x** `LongestRunHeads` | `[1, 2, ..., n]` | DP 递推（Schilling），计有利结果数 |
| 3 | **至少 x 段游程** `AtLeastXRuns` | `[1, 2, ..., n]` | 游程数分布：整序组合相关 |
| 4 | **存在长度 ≥ x 的回文子串** `PalindromeSubseq` | `[2, 4, 6, ...]`（仅偶数） | 组合/DP |


每个公式独立实现，注册到模块级 `FORMULAS: list[Formula]` 列表中。

### 3. `core/events.py` — 事件阈值

```python
class Events:
    def __init__(self, thresholds: list[float]):  # 从大到小
        self.thresholds = sorted(thresholds, reverse=True)  # p₁ > p₂ > ... > pₘ

    def find_interval(self, rarity: float) -> int | None:
        """返回事件编号 (1-indexed)，稀有度过大未触发返回 None"""
        if rarity > self.thresholds[0]:
            return None
        for i, t in enumerate(self.thresholds):
            if rarity > t:
                return i  # 在 (thresholds[i], thresholds[i-1]] 之间
        return len(self.thresholds)  # ≤ p_m，最高事件
```

### 4. `core/engine.py` — 核心引擎

**核心数据结构：**
```python
Result = dict[int, float]  # n -> P(触发事件 k)
```

**计算流程：**

最终只需要每个事件是否被触发（二进制），无需追踪中间态。对于给定 n：

```
对每个公式 f ∈ formulas[0:f]:
  x_vals = f.valid_x(n)
  # 通过二分查找，找到事件区间在 x 轴上的边界
  # 对于事件 k: p_f(n,x) 单调递减，区间 (p_{k+1}, p_k] 对应 x ∈ (x_high, x_low]
  # x_low  = min{x | p_f(n,x) ≤ p_k}
  # x_high = min{x | p_f(n,x) ≤ p_{k+1}}
  # 则 P(公式 f 触发事件 k) = p_f(n, x_low) - p_f(n, x_high)
  # 转为计数: count_f(k) = f.compute(n, x_low) - f.compute(n, x_high)
  
  # 仅当需要完整分布展示时，才遍历所有 x 统计每个区间
```

**"至少一次"合并（跨公式）：**
```
P(事件 k 触发) = 1 - ∏_f (1 - count_f(k) / k**n)
```

- 无需预先存储完整的 `P_f_k_num` 矩阵，按需计算
- 优化查询时只计算目标事件的概率，跳过无关事件

**小 n 精确模式（可选）：**
- 当 n ≤ 20 时，可枚举所有 2ⁿ 个序列
- 对每个序列计算所有公式的最优稀有度
- 精确统计触发概率
- 与近似结果对比展示

**优化查询：**
```python
def find_best_n(n_range, target_event):
    """对目标事件区间，返回最优 n（触发概率最大）"""
    best_n = max(n_range, key=lambda n: P_event(n, target_event))
    return best_n
```

### 5. `main.py` — CLI 入口

交互流程：
1. 列出可用生成器，用户选择
2. 显示该生成器的公式列表（按解锁顺序），用户输入已解锁数量 f
3. 输入 n 上限
4. 事件配置存储在 `events.json`，每项含 `name` 和 `probability`，从大到小排列
5. 用户选择要优化的目标事件区间
6. 输出最优 n
7. 可选：查看特定 n 的完整分布

### 6. `core/utils.py` — 工具函数

- `binomial(n, k)` — 组合数，返回 Python int，利用递推 `C(n,k) = C(n,k-1) * (n-k+1) // k` 避免中间浮点
- 所有概率以"有利结果数 / kⁿ"的整数形式存储和计算
- 与事件阈值比较时：`num > threshold * k**n`，一次整数乘法即可
- Python `int` 为任意精度，n 很大时（如 n=1000）`2^1000` 约 302 位十进制，乘法在微秒级完成

## 关键设计决策

1. **定点整数**：所有概率以 `int` 存有利结果数（分子），隐含分母 `kⁿ`。与阈值比较用 `num > threshold * kⁿ` 整数乘法，零浮点误差，零第三方依赖
2. **缓存**：组合数和公式结果按 (n, x) 缓存，避免重复计算
3. **可扩展性**：新增生成器只需在 `generators/` 下新增一个 `.py` 文件，导出 `FORMULAS` 列表即可


