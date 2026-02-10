# Limited Move Tic-Tac-Toe

井字棋变体：每个玩家只能保留最近的 N 步棋子，早期棋子会自动消失。

## 游戏规则

1. 标准井字棋棋盘（默认 3×3）
2. 每个玩家最多保留 **N 步**棋子（默认 N=3）
3. 当你落第 N+1 步时，最早放置的棋子自动从棋盘消失
4. 胜利条件：连成 N 个相同棋子（横、竖、斜）

由于棋子会消失，"堵住对方"的传统策略会失效，需要预判对方即将消失的棋子并创造动态获胜机会。

## 运行

```bash
pip install pygame

# 图形界面
python display.py

# 命令行（与最优 AI 对战，仅 3×3）
python Game.py
```

详见 [docs/display.md](docs/display.md) 了解图形界面的操作说明。

## 文件结构

```
├── gamebase.py          # 通用游戏引擎（支持任意 n×n 棋盘和步数限制）
├── Game.py              # 3×3 完整博弈树求解 + 命令行对战
├── display.py           # pygame 图形界面
├── strategies/          # AI 策略
│   ├── perfect3x3/      # 3×3 Perfect AI
│   └── perfect4x4_m4/   # 4×4 (max_move=4) Perfect AI（开发中）
└── docs/                # 开发文档
```

## 依赖

- Python 3.x
- pygame
