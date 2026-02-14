class RandomStrategy {
    constructor(game) {
        this.name = 'Random AI';
        this.game = game;
    }

    makeMove() {
        // 获取所有空位
        const emptyCells = this.game.getEmptyCells();

        // 如果没有空位，返回false
        if (emptyCells.length === 0) {
            return false;
        }

        // 随机选择一个空位
        const randomIndex = Math.floor(Math.random() * emptyCells.length);
        const [i, j] = emptyCells[randomIndex];

        // 执行落子
        const success = this.game.play(i, j);

        if (!success) {
            console.warn('Random AI attempted invalid move at', i, j);
            return false;
        }

        return true;
    }

    // 获取AI名称
    getName() {
        return this.name;
    }

    // 设置游戏实例（如果需要切换游戏）
    setGame(game) {
        this.game = game;
    }
}

// 导出类供其他模块使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = RandomStrategy;
}