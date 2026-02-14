class GameUI {
    constructor(canvasId, options = {}) {
        // Canvas 和上下文
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) {
            throw new Error(`Canvas element with id '${canvasId}' not found`);
        }
        this.ctx = this.canvas.getContext('2d');

        // 游戏实例
        this.game = null;
        this.ai = null;
        this.gameMode = 'pvp'; // 'pvp' 或 'pvai'
        this.aiPlayer = 2; // AI 玩家（2: O）

        // 配置选项
        this.options = {
            boardSize: options.boardSize || 4,
            maxMove: options.maxMove || 3,
            winCount: options.winCount || 3,
            ...options
        };

        // 颜色配置
        this.colors = {
            board: '#333',
            grid: '#999',
            x: '#FF5252',     // 红色 X
            o: '#2196F3',     // 蓝色 O
            bg: '#FFFFFF',
            text: '#333',
            status: '#666'
        };

        // 游戏状态
        this.isGameOver = false;
        this.isAITurn = false;

        // 初始化
        this.init();
    }

    // 初始化游戏
    init() {
        // 创建游戏实例
        this.game = new GameBase(
            this.options.boardSize,
            this.options.maxMove,
            this.options.winCount
        );

        // 创建AI实例
        this.ai = new RandomStrategy(this.game);

        // 重置游戏
        this.game.reset();

        // 设置画布大小
        this.resizeCanvas();

        // 绑定事件
        this.bindEvents();

        // 初始渲染
        this.render();

        // 更新状态显示
        this.updateStatus();
    }

    // 调整画布大小（响应式）
    resizeCanvas() {
        const container = this.canvas.parentElement;
        if (!container) return;

        const size = Math.min(container.clientWidth, container.clientHeight) * 0.9;
        this.canvas.width = size;
        this.canvas.height = size;

        // 重新渲染
        if (this.game) {
            this.render();
        }
    }

    // 绑定事件
    bindEvents() {
        // 窗口大小变化
        window.addEventListener('resize', () => {
            this.resizeCanvas();
        });

        // 画布点击事件
        this.canvas.addEventListener('click', (e) => {
            this.handleCanvasClick(e);
        });

        // 阻止画布上的上下文菜单
        this.canvas.addEventListener('contextmenu', (e) => {
            e.preventDefault();
            return false;
        });
    }

    // 处理画布点击
    handleCanvasClick(e) {
        if (this.isGameOver || this.isAITurn) {
            return;
        }

        const rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        const cellSize = this.canvas.width / this.game.n;
        const j = Math.floor(x / cellSize);
        const i = Math.floor(y / cellSize);

        if (i >= 0 && i < this.game.n && j >= 0 && j < this.game.n) {
            this.handleMove(i, j);
        }
    }

    // 处理落子
    handleMove(i, j) {
        // 尝试落子
        const success = this.game.play(i, j);

        if (success) {
            // 渲染更新
            this.render();
            this.updateStatus();

            // 检查游戏是否结束
            if (this.game.result !== 0) {
                this.isGameOver = true;
                return;
            }

            // 如果是人机对战且轮到AI
            if (this.gameMode === 'pvai' && this.game.getCurrentPlayer() === this.aiPlayer) {
                this.makeAIMove();
            }
        }
    }

    // AI落子
    makeAIMove() {
        if (this.isGameOver) return;

        this.isAITurn = true;
        this.updateStatus();

        // 添加短暂延迟，让玩家能看到AI思考
        setTimeout(() => {
            const success = this.ai.makeMove();

            if (success) {
                this.render();
                this.updateStatus();

                // 检查游戏是否结束
                if (this.game.result !== 0) {
                    this.isGameOver = true;
                }
            }

            this.isAITurn = false;

            // 如果游戏未结束且又是AI的回合（理论上不会发生，除非AI连续下棋）
            if (!this.isGameOver && this.gameMode === 'pvai' && this.game.getCurrentPlayer() === this.aiPlayer) {
                this.makeAIMove();
            }
        }, 500); // 500ms延迟
    }

    // 渲染游戏
    render() {
        const ctx = this.ctx;
        const game = this.game;
        const cellSize = this.canvas.width / game.n;

        // 清空画布
        ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        // 绘制背景
        ctx.fillStyle = this.colors.bg;
        ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

        // 绘制棋盘网格
        ctx.strokeStyle = this.colors.grid;
        ctx.lineWidth = 2;

        for (let i = 0; i <= game.n; i++) {
            // 竖线
            ctx.beginPath();
            ctx.moveTo(i * cellSize, 0);
            ctx.lineTo(i * cellSize, this.canvas.height);
            ctx.stroke();

            // 横线
            ctx.beginPath();
            ctx.moveTo(0, i * cellSize);
            ctx.lineTo(this.canvas.width, i * cellSize);
            ctx.stroke();
        }

        // 绘制棋子
        for (let i = 0; i < game.n; i++) {
            for (let j = 0; j < game.n; j++) {
                const player = game.board[i][j];
                if (player !== 0) {
                    this.drawPiece(i, j, player, cellSize);
                }
            }
        }

        // 如果有获胜序列，高亮显示
        if (game.result === 1 || game.result === 2) {
            this.highlightWinningLine();
        }
    }

    // 绘制棋子
    drawPiece(i, j, player, cellSize) {
        const ctx = this.ctx;
        const x = j * cellSize + cellSize / 2;
        const y = i * cellSize + cellSize / 2;
        const radius = cellSize * 0.35;
        const lineWidth = Math.max(2, cellSize * 0.08);

        // 确定棋子所在的队列
        const queue = player === 1 ? this.game.x : this.game.y;

        // 计算年龄（在队列中的位置）
        const age = queue.findIndex(p => p[0] === i && p[1] === j);

        // 计算透明度：越旧的棋子越透明
        let alpha = 1.0;
        if (queue.length > 0) {
            // 年龄为0表示最新，age/queue.length 越大表示越旧
            alpha = 0.2 + 0.8 * (1 - age / queue.length);
        }

        ctx.save();
        ctx.globalAlpha = alpha;
        ctx.lineWidth = lineWidth;

        if (player === 1) {
            // 绘制 X
            ctx.strokeStyle = this.colors.x;
            ctx.beginPath();
            ctx.moveTo(x - radius, y - radius);
            ctx.lineTo(x + radius, y + radius);
            ctx.moveTo(x + radius, y - radius);
            ctx.lineTo(x - radius, y + radius);
            ctx.stroke();
        } else {
            // 绘制 O
            ctx.strokeStyle = this.colors.o;
            ctx.beginPath();
            ctx.arc(x, y, radius, 0, Math.PI * 2);
            ctx.stroke();
        }

        ctx.restore();
    }

    // 高亮获胜连线（可选功能）
    highlightWinningLine() {
        // 这里可以添加高亮获胜连线的逻辑
        // 由于时间有限，暂时不实现
    }

    // 更新状态显示
    updateStatus() {
        const statusElement = document.getElementById('status');
        if (!statusElement) return;

        let statusText = '';

        if (this.isGameOver) {
            switch (this.game.result) {
                case 1:
                    statusText = '游戏结束：X 获胜！';
                    break;
                case 2:
                    statusText = '游戏结束：O 获胜！';
                    break;
                case 3:
                    statusText = '游戏结束：平局！';
                    break;
                default:
                    statusText = '游戏结束';
            }
        } else if (this.isAITurn) {
            statusText = 'AI 思考中...';
        } else {
            const currentPlayer = this.game.getCurrentPlayer();
            if (currentPlayer === 1) {
                statusText = '轮到：X';
            } else if (currentPlayer === 2) {
                if (this.gameMode === 'pvai' && this.aiPlayer === 2) {
                    statusText = '轮到：AI (O)';
                } else {
                    statusText = '轮到：O';
                }
            }
        }

        statusElement.textContent = statusText;
    }

    // 切换游戏模式
    setGameMode(mode) {
        this.gameMode = mode;
        this.resetGame();
    }

    // 更新配置
    updateConfig(boardSize, maxMove, winCount) {
        this.options.boardSize = boardSize;
        this.options.maxMove = maxMove;
        this.options.winCount = winCount;
        this.resetGame();
    }

    // 重置游戏
    resetGame() {
        this.isGameOver = false;
        this.isAITurn = false;
        this.init();
    }

    // 获取当前配置
    getConfig() {
        return { ...this.options };
    }
}

// 导出类供其他模块使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = GameUI;
}