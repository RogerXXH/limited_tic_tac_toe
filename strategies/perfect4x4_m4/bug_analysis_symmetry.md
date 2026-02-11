# train_xwin/train_ywin 对称变换 Bug 分析

**发现时间**: 2026-02-12
**问题**: AI 不会防守，只顾进攻

---

## 问题描述

测试发现 AI 存在严重缺陷：
- 作为**先手**时，如果后手发起进攻（能连成4子），AI 不会阻止
- 作为**后手**时，如果发起进攻，能正常获胜
- **结论**: AI 只知道如何"让己方赢"，但不知道如何"阻止对方赢"

这表明 `train_xwin.cpp` 和 `train_ywin.cpp` 分别训练时，`need` 数组的计算有误。

---

## 实现思路回顾

### train_xwin.cpp (X-win 训练器)

**目标**: 计算所有 X 能必胜的状态（包括能制胜和能延长状态）

**核心概念**:
- **Type A**: X 有制胜手（能走到某个 Type B），`dp[0] = 1`
- **Type B**: Y 的所有走法均通向 Type A，`dp[1] = 1`
- **终局 X-win**: Type B，深度 = 0

**四个阶段**:
1. **Phase 1**: 枚举所有标准型，标记终局 X-win 状态
2. **Phase 2**: 计算每个非终局状态的 y 后继数量 → 初始化 `need[]`
3. **Phase 3**: 无边 BFS 传播 X-win 的 Type A 和 Type B
4. **Phase 4**: 保存结果到 `xwin_4x4_m4.data`

**文件格式**:
```
[记录数: 8字节]
[state_code: 8B | dp0: 1B | dp1: 1B | depth0: 2B | depth1: 2B] × N
```

### train_ywin.cpp (Y-win 训练器)

完全对称：
- **Type A'**: Y 有制胜手，`dp[1] = -1`
- **Type B'**: X 的所有走法均通向 Type A'，`dp[0] = -1`
- 输出到 `ywin_4x4_m4.data`

### merge_training_data.cpp (合并工具)

**双指针合并法**:
- 两个输入文件都已排序
- 同时读取，按 `state_code` 大小顺序写入输出
- 内存消耗：~28MB（两个缓冲区各约 14MB）
- 输出到 `game_tree_4x4_m4.data`

---

## 根因分析

### 问题所在：`need` 数组计算错误

**Phase 2: 计算 `need[]`**
```cpp
// 对每个状态 (x, y) 计算其 y 后继数量
get_y_succs(x, lx, y, ly, succ_buf);
need[i] = (uint8_t)ns;  // ns = y 后继的数量
```

**`get_y_succs` 的实现**:
```cpp
// 从 (x, y) 出发，枚举 Y 走一步得到的所有 (x, y_new)
for (pos=0; pos<CELLS; pos++) {
    if (occ & (1u<<pos)) continue;  // 跳过已占用位置
    // ... 构造 y_new ...
    add(canonicalize(x, lx, ynew, lnew));  // 标准化后加入
}
```

**Phase 3: BFS 传播**
```cpp
// 当 j 的某个 y 后继进入 Type A 时
for z in get_y_preds(j):
    need[z]--;  // z 的一个 y 后继进入 Type A
    if (need[z] == 0) {
        // z 的所有 y 后继均已是 Type A → z 成为 Type B
        dp_flags[z] |= 2;
        bfs.push(z);
    }
}
```

**`get_y_preds` 的实现**（反向推导）:
```cpp
// 无溢出: y_prev = y[:-1]
add(canonicalize(x, lx, y, ly-1));

// 有溢出: y_prev = [fallen] + y[:-1]
yprev[0] = f;
add(canonicalize(x, lx, yprev, ly));
```

### 核心问题：`canonicalize` 破坏了前驱/后继的对应关系

**`canonicalize` 的行为**:
```cpp
static uint64_t canonicalize(const int* x, int lx, const int* y, int ly) {
    uint64_t best = UINT64_MAX;
    for (int t = 0; t < 8; t++) {  // 试 8 种对称变换
        // ... 应用变换 t ...
        uint64_t c = encode_state(xt, lx, yt, ly);
        if (c < best) best = c;  // 取最小 code
    }
    return best;  // 只返回最小编码，没有返回用了哪个变换！
}
```

**关键矛盾**:

假设有两个状态：
- **状态 A**: `(x1, y1)` → 经过变换 **T3** 变成标准型 `code_min1`
- **状态 B**: `(x2, y2)` → 经过变换 **T1** 变成标准型 `code_min2`

如果 B 是 A 的一个 y 后继，我们希望：
```
need[code_min1]--  当 code_min2 进入 Type A 时
```

但当前实现是：

**计算 `need` 时**:
1. 从 A 出发，枚举 y 后继得到 B
2. 调用 `canonicalize(B)` → 它发现 T1 最优，返回 `code_min2`
3. 把 `code_min2` 加入 A 的 y 后继列表，`need[code_min1]` 包含 `code_min2`

**BFS 传播时**:
1. `code_min2` 进入 Type A
2. 调用 `get_y_preds(code_min2)` 来找它的前驱
3. 解码 `code_min2` 得到 `(x2, y2)`（这是 T1 变换后的标准型）
4. 假设去掉 `y2[-1]` 得到前驱 `(x2, y2[:-1])`
5. 调用 `canonicalize(x2, y2[:-1])`
6. **但这个 canonicalize 可能用 T2、T4... 任何变换得到最小编码！**

结果：
- `need` 初始化时：A 的 y 后继列表里是 `code_min2`（用 T1 变换得到的）
- BFS 传播时：`get_y_preds(code_min2)` 计算的前驱可能用 T2 变换，得到 `code_min1'`
- 如果 `code_min1' ≠ code_min1`（用了不同变换），那么 `need[code_min1]` 不会被减！

### 前驱计算可能"漏掉"某些节点

用户提出的问题：`get_y_preds` 是否可能漏掉某些前驱？

当前方法：
```
给定标准型 A，找 Y 走到 A 的所有前驱：
1. 解码 A 得到 (x, y)  —— 这是某个变换 T 下的标准型
2. 去掉 y[-1]，得到前驱 P = (x, y[:-1])
3. 调用 canonicalize(P)  —— 可能用不同的变换 T' 得到标准型 A'
4. 返回 A'
```

可能的问题场景：
```
状态 B 的某个 y 后继是 B'
B' 标准化后是 A
但用 get_y_preds(A) 找不到 B
```

这确实可能发生！因为：
- A 的 y 后继列表（Phase 2 计算）里包含的是用某种变换标准化后的 code
- A 的 y 前驱列表（get_y_preds 返回）包含的是用可能另一种变换标准化后的 code
- 两者可能不匹配

---

## 对比原始 Python 版本

### Python 版本（正确）

```python
# Phase 1: 预存所有边（标准化后的 state_code）
for state in all_states:
    for successor in get_successors(state):
        edge0_[successor].append(state)  # 存标准化后的 code

# Phase 2: BFS 传播
for y in edge0_[x]:  # y 是标准化后的 code
    for z in edge1_[y]:  # z 也是标准化后的 code
        need[z][1] -= 1  # 减同一个 code
```

**关键区别**：边已经存储了标准化后的 code，`edge1_[y]` 里的每个 z 都是同一个对称变换下的标准型。

### C++ 版本（有问题）

```cpp
// Phase 2: 计算 need[]（用某种变换标准化）
need[i] = count(get_y_succs(...))  // canonicalize 可能选任意变换

// Phase 3: BFS 传播
for z in get_y_preds(j):  // canonicalize 又可能选任意变换
    need[z]--;  // 减的可能是不同的 code！
```

前驱/后继的标准化没有保持一致的对称变换。

---

## 解决方案

需要确保前驱和后继使用**相同的对称变换**。

### 方案 A：记录变换 ID

修改 `canonicalize` 返回变换 ID：
```cpp
// 返回 (code, trans_id)
static std::pair<uint64_t, int> canonicalize_with_trans(...) {
    for (int t = 0; t < 8; t++) {
        uint64_t c = encode_state(...);
        if (c < best) { best = c; best_trans = t; }
    }
    return {best, best_trans};
}
```

然后在 `get_y_preds` 中使用相同的变换。

### 方案 B：预存变换映射

在 Phase 2 计算前驱/后继时，同时记录每个标准型用了哪个变换，建立映射表：
```
trans_map[code] = trans_id  // code 是用 trans_id 变换得到的标准型
```

在 BFS 传播时，使用这个映射表来反向查找。

### 方案 C：回到预存边的方案

回到原始 Python 版本的思路：预存所有边。虽然内存占用大，但逻辑简单正确。

---

## 待办

1. **选择解决方案**: 评估方案 A/B/C 的复杂度和可行性
2. **修复代码**: 重写 `train_xwin.cpp` 和 `train_ywin.cpp`
3. **重新训练**: 运行修复后的训练器
4. **验证测试**: 确保 AI 能正确防守
5. **问题总结**: 更新文档，记录修复过程

---

## 文件位置

- `train_xwin.cpp`: X-win 训练器（有 bug）
- `train_ywin.cpp`: Y-win 训练器（有 bug）
- `merge_training_data.cpp`: 合并工具
- `xwin_4x4_m4.data`: X-win 训练结果（约 102MB）
- `ywin_4x4_m4.data`: Y-win 训练结果（约 284MB）
- `game_tree_4x4_m4.data`: 合并后的训练数据（约 973MB）
