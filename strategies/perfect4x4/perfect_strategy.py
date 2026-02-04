from collections import deque
import os
import inspect

class GameTreeSolver:
    def __init__(self, n):
        self.n = n
        self.edge0 = [[] for _ in range(self.n)]
        self.edge1 = [[] for _ in range(self.n)]
        self.win = set()
        self.lose = set()

        self.dp = [[0, 0] for _ in range(self.n)]
        self.depth = [[0, 0] for _ in range(self.n)]

    def set_edges(self, edge0, edge1):
        self.edge0 = edge0
        self.edge1 = edge1

    def cal_edge_(self):
        self.edge0_ = [[] for _ in range(self.n)]
        self.edge1_ = [[] for _ in range(self.n)]
        for i in range(self.n):
            for j in self.edge0[i]:
                self.edge0_[j].append(i)
            for j in self.edge1[i]:
                self.edge1_[j].append(i)

    def set_win(self, win):
        self.win = set(win)

    def set_lose(self, lose):
        self.lose = set(lose)

    def solve(self):
        self.dp = [[0, 0] for _ in range(self.n)]
        self.depth = [[0, 0] for _ in range(self.n)]
        for x in self.win:
            self.dp[x] = [1, 1]
        for x in self.lose:
            self.dp[x] = [-1, -1]
        self.cal_edge_()
        self.need = [[len(self.edge0[i]), len(self.edge1[i])] for i in range(self.n)]

        deq = deque(self.win)
        while deq:
            x = deq.popleft()
            for y in self.edge0_[x]:
                if self.dp[y][0] == 1:
                    continue
                self.dp[y][0] = 1
                self.depth[y][0] = self.depth[x][1] + 1
                for z in self.edge1_[y]:
                    self.need[z][1] -= 1
                    if self.need[z][1] == 0:
                        deq.append(z)
                        self.dp[z][1] = 1
                        self.depth[z][1] = self.depth[y][0] + 1
        deq = deque(self.lose)
        while deq:
            x = deq.popleft()
            for y in self.edge1_[x]:
                if self.dp[y][1] == -1:
                    continue
                self.dp[y][1] = -1
                self.depth[y][1] = self.depth[x][0] + 1
                for z in self.edge0_[y]:
                    self.need[z][0] -= 1
                    if self.need[z][0] == 0:
                        deq.append(z)
                        self.dp[z][0] = -1
                        self.depth[z][0] = self.depth[y][1] + 1

    def save_training_data(self, filename='game_tree.data'):
        with open(filename, 'w') as file:
            dp0 = [self.dp[i][0] for i in range(self.n)]
            dp1 = [self.dp[i][1] for i in range(self.n)]
            file.write(' '.join(map(str, dp0)) + '\n')
            file.write(' '.join(map(str, dp1)) + '\n')
            depth0 = [self.depth[i][0] for i in range(self.n)]
            depth1 = [self.depth[i][1] for i in range(self.n)]
            file.write(' '.join(map(str, depth0)) + '\n')
            file.write(' '.join(map(str, depth1)) + '\n')

    def load_training_data(self, filename='game_tree.data'):
        with open(filename, 'r') as file:
            s = file.read().strip()
            dp0, dp1, depth0, depth1 = s.split('\n')
            dp0 = list(map(int, dp0.split()))
            dp1 = list(map(int, dp1.split()))
            depth0 = list(map(int, depth0.split()))
            depth1 = list(map(int, depth1.split()))
            self.dp = [[x, y] for x, y in zip(dp0, dp1)]
            self.depth = [[x, y] for x, y in zip(depth0, depth1)]


class Strategy:
    def __init__(self, game):
        self.name = 'Perfect Strategy (4x4)'
        self.game = game

        self.N = 1000000
        self.solver = GameTreeSolver(self.N)
        class_file = inspect.getfile(Strategy)
        class_dir = os.path.abspath(os.path.dirname(class_file))
        self.train_file = os.path.join(class_dir, 'game_tree.data')

        try:
            self.solver.load_training_data(self.train_file)
        except:
            self.train()

    def mask(self, l):
        r = 0
        for i in range(len(l)):
            r += 10 ** i * (l[i] + 1)
        return r

    def trans(self, deq):
        l = []
        for i, j in deq:
            l.append(i * 3 + j)
        return l

    def train(self):
        edge0 = [[] for _ in range(self.solver.n)]
        edge1 = [[] for _ in range(self.solver.n)]
        win = set()
        lose = set()
        for msk in range(self.solver.n):
            self.game.reset()
            x_msk, y_msk = msk // 1000, msk % 1000
            x, y = [], []
            while x_msk:
                x.append(x_msk % 10 - 1)
                x_msk //= 10
            while y_msk:
                y.append(y_msk % 10 - 1)
                y_msk //= 10
            for t in x:
                i, j = t // 3, t % 3
                self.game.board[i][j] = 1
            for t in y:
                i, j = t // 3, t % 3
                self.game.board[i][j] = -1

            result = 0
            if x:
                i, j = x[0] // 3, x[0] % 3
                self.game.history.append([i, j])
                result = self.game.get_result()
            if not result and y:
                i, j = y[0] // 3, y[0] % 3
                self.game.history.append([i, j])
                result = self.game.get_result()

            if result == 1:
                win.add(msk)
                continue
            elif result == -1:
                lose.add(msk)
                continue
            for i in range(3):
                for j in range(3):
                    if self.game.board[i][j] != 0:
                        continue
                    t = i * 3 + j
                    x_ = x.copy()
                    y_ = y.copy()
                    x_.append(t)
                    y_.append(t)
                    if len(x_) > 3:
                        x_ = x_[1:]
                    if len(y_) > 3:
                        y_ = y_[1:]
                    msk0 = self.mask(x_) * 1000 + msk % 1000
                    msk1 = msk // 1000 * 1000 + self.mask(y_)
                    edge0[msk].append(msk0)
                    edge1[msk].append(msk1)

        self.solver.set_edges(edge0, edge1)
        self.solver.set_win(win)
        self.solver.set_lose(lose)
        self.solver.solve()
        self.solver.save_training_data(self.train_file)

    def make_move(self):
        p = 0
        if len(self.game.history) & 1 == 0:
            p = 1
        moves = []
        for t in range(9):
            i, j = t // 3, t % 3
            if self.game.board[i][j] != 0:
                continue
            if p == 1:
                x = self.trans(self.game.x)
                x.append(t)
                if len(x) > 3:
                    x = x[1:]
                msk_ = self.mask(x) * 1000 + self.mask(self.trans(self.game.y))
                moves.append([t, self.solver.dp[msk_][1], self.solver.depth[msk_][1]])
            else:
                y = self.trans(self.game.y)
                y.append(t)
                if len(y) > 3:
                    y = y[1:]
                msk_ = self.mask(self.trans(self.game.x)) * 1000 + self.mask(y)
                moves.append([t, -self.solver.dp[msk_][0], self.solver.depth[msk_][0]])
        moves.sort(key=lambda x: (x[1], -x[2]))
        if moves[-1][1] == -1:
            moves.sort(key=lambda x: (x[1], x[2]))
        i, j = moves[-1][0] // 3, moves[-1][0] % 3
        self.game.play(i, j)
