# 井字棋游戏 - 技术文档

**运行环境**: 使用 `/home/xiaohu/ls/envs/ttt/bin/python` 来测试代码。

---

## 项目结构

```
ttt/
├── Game.py              # 旧版游戏逻辑（3x3，m=3，保留兼容）
├── gamebase.py          # 通用游戏逻辑基类
├── display.py           # 主UI实现
├── strategies/          # AI策略模块
│   ├── pvp/           # 双人对弈（无AI）
│   ├── nocpu/          # AI不可用占位
│   ├── random/         # 随机AI
│   ├── perfect3x3/     # 3x3完美AI
│   ├── perfect4x4_m3/  # 4x4 m=3完美AI
│   └── perfect4x4_m4/  # 4x4 m=4完美AI
└── docs/              # 文档目录（本文件）
```

---

## gamebase.py - 核心游戏逻辑

### 类: GameBase

```python
class GameBase:
    def __init__(self, n, m, win_count=None)
```

**参数**:
- `n`: 棋盘大小 (3-15)
- `m`: max_move，每位玩家最多保留的棋子数 (1-15)
- `win_count`: 胜利所需的连珠数 (2-15)，默认等于 m

**核心属性**:
- `self.n`: 棋盘大小
- `self.m`: max_move
- `self.win_count`: 胜利连线数
- `self.board`: n×n 二维数组，0=空，1=X，-1=O
- `self.x`: X 方棋子列表 `[(i,j), ...]`，按落子顺序
- `self.y`: O 方棋子列表 `[(i,j), ...]`，按落子顺序
- `self.history`: 完整落子历史 `[(i,jari,player), ...]`

**关键方法**:

1. `play(i, j)`: 在位置 (i,j) 落子
   - 返回 True 表示成功，False 表示位置已被占用
   - 自动处理 max_move 逻辑：超过 m 个时移除最老的棋子（列表头部）

2. `get_result()`: 检查游戏状态
   - 返回 1 表示 X 胜
   - 返回 -1 表示 O 胜
   - 返回 0 表示继续游戏

3. `reset()`: 重置游戏状态

---

## display.py - UI实现

### 整体架构

```
display.py
├── get_chinese_font()           # 中文字体查找
├── Dropdown 类                  # 下拉菜单组件
├── Button 类                   # 按钮组件
├── FontCache 类                # 字体缓存
└── GameUI 类                  # 主界面类
```

### GameUI 类核心属性

**配置参数**:
```python
self.board_sizes = list(range(3, 16))      # 3-15
self.max_moves = list(range(1, 16))       # 1-15
self.win_counts = list(range(2, 16))      # 2-15
self.current_board_size = 3
self.current_max_move = 3
self.current_win_count = 3
```

**棋子样式**:
```python
self.piece_styles = [
    {"name": "X/O Style", "type": "xo"},
    {"name": "Go Black/White", "type": "go_classic"},
    {"name": "Go with Border", "type": "go_border"},
    {"name": "Gradient Style", "type": "gradient"}
]
```

**游戏状态**:
```python
self.play_mode = "pvp"     # "pvp" 或 "pvai"
self.game_on = False        # 游戏是否进行中
self.play = -1             # PvAI模式：0=玩家执X，1=玩家执O
self.result = 0             # 0=继续，1=X胜，-1=O胜
```

**布局计算**:
```python
self.sidebar_width = 220                     # 侧边栏宽度
self.cell_size = 动态计算                    # 格子大小
self.board_offset_x = 侧边栏右缘 + 偏移      # 棋盘左上角X
self.board_offset_y = 顶部栏高度 + 偏移      # 棋盘左上角Y
```

### 关键方法

#### 初始化流程
```
__init__()
├── 初始化配置参数
├── self._init_game()
│   ├── 创建 GameBase 实例
│   ├── self._filter_available_strategies()
│   └── self._update_ui_dimensions()
└── self._init_ui_components()
    └── 创建所有UI组件（下拉菜单、按钮等）
```

#### 绘制流程
```
draw()
├── draw_gradient_background()      # 渐变背景
├── draw_sidebar()               # 侧边栏
│   ├── 绘制所有按钮和下拉菜单
│   └── self.xxx_dropdown.draw()  # 绘制下拉菜单按钮
├── draw_board()                 # 绘制棋盘格子
├── draw_pieces()                # 绘制棋子
│   ├── 计算即将消失的棋子（红框）
│   ├── 计算下一个即将消失的棋子（黄框，仅max_move>5）
│   └── 根据样式绘制棋子
├── draw_status_bar()            # 状态栏（当前回合）
├── draw_control_buttons()       # 控制按钮
├── draw_result()                # 胜利提示
└── xxx_dropdown.draw_dropdown()  # 绘制打开的下拉选项（最上层）
```

#### 事件处理
```
handle_events(event)
├── 处理下拉菜单点击
├── 处理模式切换（PvP/PvAI）
├── 处理 Play X / Play O 按钮（PvAI模式）
├── 处理棋盘点击
│   └── 如果 self.game_on 且格子为空
│       ├── self.game.play(i, j)
│       └── PvAI模式且AI回合时：self.strategy.make_move()
└── 处理重置按钮
```

### 棋子消失提示逻辑

```python
show_yellow_border = self.game.m > 5

is_fading = len(self.game.x) >= self.game.m and ti == 0
# 红色虚线边框：最老的棋子（下一回合将被移除）

is_next_fading = show_yellow_border and len(self.game.x) >= self.game.m - 1 and ti == 1
# 黄色虚线边框：倒数第二个棋子（仅当 max_move > 5 时显示）
```

### 窗口大小动态调整

```python
def _update_ui_dimensions(self):
    max_window_size = 700
    min_cell_size = 35
    max_cell_size = 60

    ideal_cell_size = max_window_size // self.current_board_size
    self.cell_size = max(min_cell_size, min(max_cell_size, ideal_cell_size))

    board_size = self.grid * self.cell_size
    self.window_width = max(self.sidebar_width + 280, self.sidebar_width + board_size + 40)
    self.window_height = max(550, board_size + self.top_bar_height + self.bottom_bar_height)
```

---

## strategies/ - AI策略接口

### 策略接口标准

每个策略模块必须包含:

```python
class Strategy:
    def __init__(self, game):
        self.name = "策略显示名称"
        self.game = game

    def make_move(self):
        """
        执行AI的一步
        返回 True 表示成功，False 表示失败（如AI不可用）
        """
        # 1. 分析当前局面
        # 2. 选择落子位置 (i, j)
        # 3. self.game.play(i, j)
        return True
```

### 可用策略

| 策略 | 支持配置 | 描述 |
|-------|---------|------|
| pvp | 全部 | 双人对弈，无AI |
| random | 全部 | 随机落子 |
| perfect3x3 | 仅 3×3, m=3 | 完美AI，基于博弈树 |
| perfect4x4_m3 | 仅 4×4, m=3 | 完美AI |
| perfect4x4_m4 | 仅 4×4, m=4 | 完美AI |

### 策略选择逻辑

```python
def _filter_available_strategies(self):
    current_config = (self.current_board_size, self.current_max_move)

    # PvP 和 Random 总是可用
    # Perfect AI 根据配置过滤
    if current_config == (3, 3):
        # 添加 Perfect AI 3x3
    elif current_config == (4, 4):
        # 添加 Perfect AI 4x4
```

---

## 开发建议

### 修改棋子样式
在 `draw_piece()` 中添加新的样式分支，实现对应的 `_draw_xxx_style()` 方法。

### 添加新AI策略
1. 在 `strategies/` 下创建新目录和 `xxx_strategy.py`
2. 实现标准 `Strategy` 类接口
3. 在 `display.py` 中导入新策略
4. 在 `_filter_available_strategies()` 中添加配置判断

### 调试
```bash
/home/xiaohu/ls/envs/ttt/bin/python display.py
```
