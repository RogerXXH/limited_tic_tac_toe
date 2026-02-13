# 图形界面说明 (display.py)

## 启动

```bash
python display.py
```

需要安装 pygame：`pip install pygame`

---

## 界面布局

```
┌──────────────────────────────────────────────┐
│ ┌─────────┐                            │
│ │Board    │                            │ 侧边菜单
│ │Config   │                            │
│ ├─────────┤                            │
│ │Board Size▼│                           │
│ │Max Move ▼│                           │
│ │Win Count▼│                           │
│ ├─────────┤                            │
│ │Piece    │                            │
│ │Style ▼ │                            │
│ ├─────────┤                            │
│ │Game Mode│                            │
│ │[PvP][PvAI]                          │
│ ├─────────┤                            │
│ │AI       │                            │
│ │Strategy▼│                            │
│ └─────────┘                            │
│                                        │
│       ┌─────────────────────────┐        │
│       │                       │        │  棋盘区域
│       │                       │        │
│       │   棋盘               │        │
│       │                       │        │
│       │                       │        │
│       └─────────────────────────┘        │
│                                        │
│     Round N | X' Turn | vs Player       │  状态栏
│                         [R]            │  重置按钮
└──────────────────────────────────────────────┘
```

---

## 侧边菜单

### Board Config（棋盘配置）

| 配置项 | 范围 | 说明 |
|--------|------|------|
| Board Size | 3-15 | 棋盘大小 |
| Max Move | 1-15 | 每位玩家最多保留的棋子数 |
| Win Count | 2-15 | 胜利所需的连珠数（通常 ≤ Max Move） |

### Piece Style（棋子样式）

- **X/O Style**: 经典的 X 和和 O 符号
- **Go Black/White**: 围棋黑白棋样式
- **Go with Border**: 带边框的围棋样式
- **Gradient Style**: 渐变色圆样式

### Game Mode（对战模式）

- **PvP**: 双人对弈模式，自动开始
- **PvAI**: 玩家与 AI 对战，需选择执 X 或 O

### AI Strategy（AI 策略）

| 策略 | 支持配置 | 描述 |
|------|---------|------|
| Player vs Player | 全部 | 双人对弈，无 AI |
| Random AI | 全部 | 随机落子 |
| Perfect AI 3x3 | 仅 3×3, m=3 | 完美 AI，不可战胜 |
| Perfect AI 4x4 | 仅 4×4, m=4 | 完美 AI |

---

## 底部按钮

| 按钮 | 说明 |
|------|------|
| **R** | 重置棋盘（重新开始当前对局）|
| **Play X** (PvAI 模式) | 玩家执 X（先手）|
| **Play O** (PvAI 模式) | 玩家执 O（后手），AI 先落子 |

PvP 模式无需额外按钮，点击模式切换后自动开始。

---

## 棋子视觉

### 颜色渐变
棋子颜色根据"新旧程度"渐变：
- **新棋子**：颜色鲜艳（X 为亮红，O 为亮蓝）
- **旧棋子**：颜色逐渐变淡

### 消失提示边框
- **红色虚线边框**：即将消失的棋子（最旧的棋子，下一回合会被移除）
- **黄色虚线边框**：下一个即将消失的棋子（仅当 max_move > 5 时显示）

这让玩家一眼就能判断哪些棋子快要消失。

---

## 状态栏

游戏进行中显示：`Round N | X' Turn (X) | vs Player`

- **Round N**: 当前回合数
- **X' Turn / O' Turn**: 当前轮到谁（PvP 模式）或 "Your Turn"/"AI's Turn"（PvAI 模式）
- **vs Player / vs [AI名]**: 对战模式

---

## 扩展：添加新策略

### 1. 创建策略模块

在 `strategies/` 下创建新目录，例如 `my_strategy/`：

```python
# strategies/my_strategy/my_strategy.py
class Strategy:
    def __init__(self, game):
        self.name = "My Strategy"
        self.game = game

    def make_move(self):
        """
        执行 AI 的一步
        返回 True 表示成功，False 表示失败（如 AI 不可用）
        """
        # 分析当前局面
        # 选择落子位置 (i, j)
        # self.game.play(i, j)
        return True
```

### 2. 创建包初始化文件

```python
# strategies/my_strategy/__init__.py
from .my_strategy import Strategy
__all__ = ['Strategy']
```

### 3. 在 display.py 中导入和使用

```python
import strategies.my_strategy.my_strategy as my_strategy_module

# 在 _filter_available_strategies() 中添加
my_instance = self._get_or_create_strategy(my_strategy_module)
self.available_strategies.append({
    "name": "My Strategy",
    "module": my_strategy_module,
    "description": "描述",
    "instance": my_instance,
    "supports_all": True  # 或 False（特定配置）
})
```
