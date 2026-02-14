// 主游戏控制器
class GameController {
    constructor() {
        this.gameUI = null;
        this.isInitialized = false;

        // 绑定事件
        this.bindEvents();

        // 初始化游戏
        this.initializeGame();
    }

    // 初始化游戏
    initializeGame() {
        try {
            // 获取配置值
            const boardSize = parseInt(document.getElementById('boardSize').value);
            const maxMove = parseInt(document.getElementById('maxMove').value);
            const winCount = parseInt(document.getElementById('winCount').value);

            // 创建游戏UI实例
            this.gameUI = new GameUI('gameCanvas', {
                boardSize,
                maxMove,
                winCount
            });

            this.isInitialized = true;

            // 更新信息显示
            this.updateInfoDisplay();
            this.updateHistoryDisplay();

            console.log('游戏初始化成功！');
        } catch (error) {
            console.error('游戏初始化失败:', error);
            this.showError('游戏初始化失败，请刷新页面重试。');
        }
    }

    // 绑定事件
    bindEvents() {
        // 配置变更事件
        document.getElementById('boardSize').addEventListener('change', () => this.onConfigChange());
        document.getElementById('maxMove').addEventListener('change', () => this.onConfigChange());
        document.getElementById('winCount').addEventListener('change', () => this.onConfigChange());

        // 游戏模式按钮
        document.getElementById('pvpBtn').addEventListener('click', () => this.setGameMode('pvp'));
        document.getElementById('pvaiBtn').addEventListener('click', () => this.setGameMode('pvai'));

        // 操作按钮
        document.getElementById('resetBtn').addEventListener('click', () => this.resetGame());
        document.getElementById('undoBtn').addEventListener('click', () => this.undoMove());
        document.getElementById('playAgainBtn').addEventListener('click', () => this.resetGame());

        // 游戏状态更新监听
        this.setupGameStateListener();
    }

    // 配置变更处理
    onConfigChange() {
        if (!this.isInitialized) return;

        const boardSize = parseInt(document.getElementById('boardSize').value);
        const maxMove = parseInt(document.getElementById('maxMove').value);
        const winCount = parseInt(document.getElementById('winCount').value);

        this.gameUI.updateConfig(boardSize, maxMove, winCount);
        this.updateInfoDisplay();
        this.updateHistoryDisplay();
    }

    // 设置游戏模式
    setGameMode(mode) {
        if (!this.isInitialized) return;

        this.gameUI.setGameMode(mode);

        // 更新按钮状态
        const pvpBtn = document.getElementById('pvpBtn');
        const pvaiBtn = document.getElementById('pvaiBtn');

        pvpBtn.classList.remove('active');
        pvaiBtn.classList.remove('active');

        if (mode === 'pvp') {
            pvpBtn.classList.add('active');
            pvpBtn.innerHTML = '<i class="fas fa-user-friends"></i> 玩家对战 (当前)';
            pvaiBtn.innerHTML = '<i class="fas fa-robot"></i> 人机对战';
        } else {
            pvaiBtn.classList.add('active');
            pvaiBtn.innerHTML = '<i class="fas fa-robot"></i> 人机对战 (当前)';
            pvpBtn.innerHTML = '<i class="fas fa-user-friends"></i> 玩家对战';
        }

        this.updateStatus();
    }

    // 重置游戏
    resetGame() {
        if (!this.isInitialized) return;

        this.gameUI.resetGame();
        this.updateHistoryDisplay();
        this.hideGameOverlay();
    }

    // 撤销一步
    undoMove() {
        if (!this.isInitialized) return;

        // 检查是否允许撤销
        if (this.gameUI.gameMode === 'pvai' && this.gameUI.isAITurn) {
            this.showMessage('AI思考时不能撤销');
            return;
        }

        // 调用游戏的undo方法
        if (this.gameUI.game.undo()) {
            this.gameUI.render();
            this.updateStatus();
            this.updateHistoryDisplay();
        } else {
            this.showMessage('没有可撤销的步数');
        }
    }

    // 设置游戏状态监听
    setupGameStateListener() {
        // 使用轮询方式检查游戏状态变化
        setInterval(() => {
            if (!this.isInitialized) return;

            this.updatePieceCounts();
            this.updateStatus();

            // 检查游戏是否结束
            if (this.gameUI.game.result !== 0 && !this.gameUI.isGameOver) {
                this.gameUI.isGameOver = true;
                this.showGameOver();
            }
        }, 100);
    }

    // 更新状态显示
    updateStatus() {
        if (!this.isInitialized) return;
        this.gameUI.updateStatus();
    }

    // 更新棋子计数
    updatePieceCounts() {
        if (!this.gameUI || !this.gameUI.game) return;

        document.getElementById('xCount').textContent = this.gameUI.game.x.length;
        document.getElementById('oCount').textContent = this.gameUI.game.y.length;
    }

    // 更新信息显示
    updateInfoDisplay() {
        if (!this.gameUI) return;

        const config = this.gameUI.getConfig();
        document.getElementById('currentBoardSize').textContent = `${config.boardSize}x${config.boardSize}`;
        document.getElementById('currentMaxMove').textContent = config.maxMove;
        document.getElementById('currentWinCount').textContent = `${config.winCount}连`;
    }

    // 更新历史记录显示
    updateHistoryDisplay() {
        const historyList = document.getElementById('historyList');
        if (!historyList || !this.gameUI || !this.gameUI.game) return;

        const history = this.gameUI.game.history;

        if (history.length === 0) {
            historyList.innerHTML = '<div class="history-empty">暂无记录</div>';
            return;
        }

        let html = '';
        history.forEach((move, index) => {
            const [i, j, player] = move;
            const playerSymbol = player === 1 ? 'X' : 'O';
            const playerClass = player === 1 ? 'player-x' : 'player-o';
            const step = index + 1;

            html += `
                <div class="history-item">
                    <span class="history-step">第${step}步</span>
                    <span class="history-position">位置: (${i + 1}, ${j + 1})</span>
                    <span class="history-player ${playerClass}">${playerSymbol}</span>
                </div>
            `;
        });

        historyList.innerHTML = html;
        historyList.scrollTop = historyList.scrollHeight;
    }

    // 显示游戏结束界面
    showGameOver() {
        const overlay = document.getElementById('gameOverlay');
        const resultText = document.getElementById('gameResultText');

        if (!overlay || !resultText) return;

        let message = '';
        switch (this.gameUI.game.result) {
            case 1:
                message = '🎉 X 玩家获胜！ 🎉';
                break;
            case 2:
                message = this.gameUI.gameMode === 'pvai' && this.gameUI.aiPlayer === 2
                    ? '🤖 AI 获胜！ 🤖'
                    : '🎉 O 玩家获胜！ 🎉';
                break;
            case 3:
                message = '🤝 平局！ 🤝';
                break;
        }

        resultText.textContent = message;
        overlay.style.display = 'flex';
    }

    // 隐藏游戏结束界面
    hideGameOverlay() {
        const overlay = document.getElementById('gameOverlay');
        if (overlay) {
            overlay.style.display = 'none';
        }
    }

    // 显示错误消息
    showError(message) {
        const status = document.getElementById('status');
        if (status) {
            status.textContent = `❌ ${message}`;
            status.style.color = '#ff4444';
        }
    }

    // 显示普通消息
    showMessage(message) {
        const status = document.getElementById('status');
        if (status) {
            const originalText = status.textContent;
            status.textContent = `💡 ${message}`;
            status.style.color = '#ff9800';

            // 3秒后恢复原始状态
            setTimeout(() => {
                status.textContent = originalText;
                status.style.color = '';
            }, 3000);
        }
    }
}

// 页面加载完成后初始化游戏
document.addEventListener('DOMContentLoaded', () => {
    console.log('页面加载完成，开始初始化游戏...');

    // 添加CSS类用于按钮激活状态
    const style = document.createElement('style');
    style.textContent = `
        .btn-primary.active, .btn-secondary.active {
            transform: translateY(-3px);
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
            position: relative;
        }
        .btn-primary.active::after, .btn-secondary.active::after {
            content: '✓';
            position: absolute;
            right: 10px;
            font-weight: bold;
        }
        .history-player.player-x {
            color: #FF5252;
            font-weight: bold;
        }
        .history-player.player-o {
            color: #2196F3;
            font-weight: bold;
        }
    `;
    document.head.appendChild(style);

    // 初始化游戏控制器
    window.gameController = new GameController();

    console.log('游戏控制器初始化完成！');
});

// 窗口大小变化时重新调整画布
window.addEventListener('resize', () => {
    if (window.gameController && window.gameController.gameUI) {
        // 游戏UI会自动处理resize
    }
});

// 导出供调试使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = GameController;
}