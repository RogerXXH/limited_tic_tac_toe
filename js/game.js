class GameBase {
    constructor(n, maxMove, winCount = null) {
        this.n = n;                    // 棋盘大小
        this.m = maxMove;              // 最大棋子数
        this.winCount = winCount || maxMove; // 胜利条件，默认为最大棋子数
        this.board = Array(n).fill().map(() => Array(n).fill(0));
        this.x = [];                   // X的棋子队列（替代deque）
        this.y = [];                   // O的棋子队列
        this.history = [];             // 历史记录
        this.result = 0;               // 0: 进行中, 1: X赢, 2: O赢, 3: 平局
    }

    // 重置游戏
    reset() {
        this.board = Array(this.n).fill().map(() => Array(this.n).fill(0));
        this.x = [];
        this.y = [];
        this.history = [];
        this.result = 0;
        return this;
    }

    // 落子逻辑
    play(i, j) {
        // 检查游戏是否已经结束
        if (this.result !== 0) {
            return false;
        }

        // 检查位置是否有效且为空
        if (i < 0 || i >= this.n || j < 0 || j >= this.n || this.board[i][j] !== 0) {
            return false;
        }

        // 确定当前玩家（根据历史记录长度）
        const player = this.history.length % 2 === 0 ? 1 : 2; // 1: X, 2: O
        this.board[i][j] = player;

        // 更新队列（FIFO逻辑）
        const queue = player === 1 ? this.x : this.y;
        queue.push([i, j]);

        // 如果队列超过最大棋子数，移除最旧的棋子
        if (queue.length > this.m) {
            const [oldI, oldJ] = queue.shift();
            this.board[oldI][oldJ] = 0;
        }

        // 添加历史记录
        this.history.push([i, j, player]);

        // 检查胜负
        this.result = this.getResult();
        return true;
    }

    // 获取胜负结果
    getResult() {
        // 如果历史记录为空，游戏进行中
        if (this.history.length === 0) {
            return 0;
        }

        // 获取最后一步
        const [lastI, lastJ, player] = this.history[this.history.length - 1];

        // 检查四个方向
        const directions = [
            [0, 1],   // 水平
            [1, 0],   // 垂直
            [1, 1],   // 主对角线
            [1, -1]   // 副对角线
        ];

        for (const [dx, dy] of directions) {
            let count = 1; // 包括当前位置

            // 正向检查
            for (let step = 1; step < this.winCount; step++) {
                const ni = lastI + dx * step;
                const nj = lastJ + dy * step;
                if (ni >= 0 && ni < this.n && nj >= 0 && nj < this.n && this.board[ni][nj] === player) {
                    count++;
                } else {
                    break;
                }
            }

            // 反向检查
            for (let step = 1; step < this.winCount; step++) {
                const ni = lastI - dx * step;
                const nj = lastJ - dy * step;
                if (ni >= 0 && ni < this.n && nj >= 0 && nj < this.n && this.board[ni][nj] === player) {
                    count++;
                } else {
                    break;
                }
            }

            // 如果达到胜利条件
            if (count >= this.winCount) {
                return player; // 1: X赢, 2: O赢
            }
        }

        // 检查是否平局（棋盘已满）
        if (this.history.length >= this.n * this.n) {
            return 3; // 平局
        }

        // 游戏进行中
        return 0;
    }

    // 获取当前玩家
    getCurrentPlayer() {
        if (this.result !== 0) {
            return 0; // 游戏已结束
        }
        return this.history.length % 2 === 0 ? 1 : 2; // 1: X, 2: O
    }

    // 获取空位列表
    getEmptyCells() {
        const emptyCells = [];
        for (let i = 0; i < this.n; i++) {
            for (let j = 0; j < this.n; j++) {
                if (this.board[i][j] === 0) {
                    emptyCells.push([i, j]);
                }
            }
        }
        return emptyCells;
    }

    // 撤销上一步（可选功能）
    undo() {
        if (this.history.length === 0) {
            return false;
        }

        const [i, j, player] = this.history.pop();
        this.board[i][j] = 0;

        // 从相应队列中移除
        const queue = player === 1 ? this.x : this.y;
        const index = queue.findIndex(p => p[0] === i && p[1] === j);
        if (index !== -1) {
            queue.splice(index, 1);
        }

        // 重新计算结果
        this.result = this.getResult();
        return true;
    }
}

// 导出类供其他模块使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = GameBase;
}