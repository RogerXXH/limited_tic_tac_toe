# train_xwin 训练器设计方案

## 背景

原 C++ 训练器（`train_4x4_m4.cpp`）在运行到 26.2% 时被 OOM Kill，
根因是将所有边存入 `unordered_map`，导致内存需求约 15-20GB。

本方案彻底消除边的存储，改为**动态计算反向邻居**，分别处理 win 和 lose。

---

## 核心思路：动态计算前驱

给定一个标准型状态 `(x, y)`（x 为先手棋子列表，oldest→newest），
**不预存边**，而是在 BFS 时实时计算所有前驱状态：

### `get_x_predecessors(x, y)`：X 走到当前状态的前驱

| 条件 | 前驱 |
|------|------|
| `len(x) > len(y)`（无溢出） | `(x[:-1], y)` |
| `len(x) == 4`（有溢出） | `([fallen] + x[:-1], y)`，枚举所有空位 `fallen` |

### `get_y_predecessors(x, y)`：Y 走到当前状态的前驱

| 条件 | 前驱 |
|------|------|
| `len(y) >= 1`（无溢出） | `(x, y[:-1])` |
| `len(y) == 4`（有溢出） | `(x, [fallen] + y[:-1])`，枚举所有空位 `fallen` |

每个前驱都需要经过 `canonicalize` 标准化。

> 已有 Python 实现验证（`test_predecessors.py`，round-trip 2561 次全部通过）。

---

## win 状态的传播规则

### 两种 X-win 状态类型

| 类型 | 含义 | 对应 dp |
|------|------|---------|
| **Type B** | 终局（X 刚赢），或 Y 的所有走法均通向 Type A | `dp[s][1] = 1` |
| **Type A** | X 有制胜手（能走到某个 Type B 状态） | `dp[s][0] = 1` |

### 深度与类型的对应关系

| 深度 | 类型 | 来源 |
|------|------|------|
| 1 | Type B | 终局胜利状态（X 刚走赢） |
| 2 | Type A | Type B 深度1 的 x 前驱 |
| 3 | Type B | 所有 y 后继均为 Type A（深度2）的状态 |
| 4 | Type A | Type B 深度3 的 x 前驱 |
| … | … | … |

**关键约束**：检查"y 后继是否均为 X-win"时，只能查 **Type A** 状态（`dp[0]=1`），
不能混入 Type B，否则会误判。

### BFS 传播逻辑（对应原 `solve()` 的 win 传播）

```
queue ← 所有 terminal Type B 状态

while queue not empty:
    s = queue.pop()                     // s 是 Type B

    for each x_pred p of s:            // X 走到 s 的前驱
        if p already Type A: continue
        mark p as Type A
        depth[p] = depth[s] + 1

        for each y_pred q of p:        // Y 走到 p 的前驱
            need[q]--                  // q 的一个 y 后继进入 Type A
            if need[q] == 0:
                mark q as Type B
                depth[q] = depth[p] + 1
                queue.push(q)
```

`need[q]` 初始值 = q 的 y 后继总数（Phase 1 枚举时计算）。

---

## 代码方案：`train_xwin.cpp`

### Phase 1 — 枚举所有标准型

与 `count_canonical_4x4_m4.cpp` 逻辑相同，额外：

1. 统计每个状态的 **y 后继数量** → 初始化 `need[]`
2. 判断是否为**终局胜利状态** → 加入初始 BFS 队列
3. 枚举完成后，将所有 canonical codes **排序存入数组**，释放 hash set

内存峰值：约 2.5GB（枚举阶段 hash set）。

### Phase 2 — BFS 传播（无边）

**核心数组**（按排序后的下标索引，N ≈ 72,864,169）：

```
uint64_t codes[N]      // 排序后的 canonical code          583 MB
uint8_t  need[N]       // 尚未进入 Type A 的 y 后继数       73 MB
uint8_t  dp[N]         // 0=未知, 1=Type A, 2=Type B        73 MB
uint16_t depth[N]      // 制胜深度                         146 MB
                                                    合计  875 MB
```

BFS 队列存下标（`uint32_t`），最多 292MB。

**关键函数**（均在 BFS 阶段动态调用，不预存）：

- `decode(code)` → `(x[], y[])`
- `canonicalize(x[], y[])` → canonical code
- `get_x_predecessors(x, y)` → canonical codes 列表
- `get_y_predecessors(x, y)` → canonical codes 列表
- `get_y_successors(x, y)` → canonical codes 列表（用于 need 初始化）
- `binary_search(code)` → 下标（不存在返回 -1）
- `is_terminal_win(x, y)` → bool

### Phase 3 — 保存结果

输出格式与现有 `game_tree_4x4_m4.data` 兼容：

```
[记录数: 8字节 uint64]
[state_code: 8B | dp0: 1B | dp1: 1B | depth0: 2B | depth1: 2B] × N
```

仅保存 win 相关状态（Type A 或 Type B），其余 dp=0，depth=0。

### Phase 4 — Lose 处理（后续，对称）

Y-win（X 败）的传播逻辑完全对称：

- 终局败北状态为 Type B（`dp[s][0] = -1`）
- y 后继的 Type A（`dp[s][1] = -1`）通过 x 前驱传播
- 单独一个 pass，结果合并到同一文件

---

## 整体内存估算

| 阶段 | 峰值内存 |
|------|---------|
| Phase 1 枚举（hash set） | ~2.5 GB |
| Phase 2 BFS（数组 + 队列） | ~1.2 GB |
| 最终输出文件 | ~973 MB |

全程峰值不超过 **3 GB**，远低于 WSL 上限 9.7 GB。

---

## 文件清单

```
strategies/perfect4x4_m4/
├── train_xwin.cpp               # 本方案的 C++ 训练器（待实现）
├── test_predecessors.py         # 前驱函数 Python 验证（已完成）
├── perfect_strategy.py          # 核心策略（含 mmap 查询）
└── count_canonical_4x4_m4.cpp   # 标准型计数（可复用框架）

docs/
└── train_xwin_plan.md           # 本文档
```

---

## 参考：编码约定

```
基数：17
x_code = sum((pos+1) * 17^i for i, pos in enumerate(x_list))
         x_list[0] = 最老棋子（17^0），x_list[-1] = 最新棋子（17^(n-1)）
state_code = x_code * SEPARATOR + y_code
SEPARATOR = 17^4 = 83521

溢出规则：当 len(x) == max_move(=4) 时，新落子 → x = x[1:] + [new]
```
