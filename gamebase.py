from collections import deque


class Game:
    def __init__(self):
        self.moves = 3
        self.x_deq = deque()
        self.y_deq = deque()
        self.history = []
        self.x_msk = 0
        self.y_msk = 0
        self.msk = 0
        self.dig = DiG(1000000)

    def reset(self):
        self.history = []
        self.x_msk, self.y_msk, self.msk = 0, 0, 0
        self.x_deq = deque()
        self.y_deq = deque()

    def play(self, player, p):
        if player == 1:
            if p in self.x_deq or p in self.y_deq:
                return False
            self.x_deq.append(p)
            if len(self.x_deq) > 3:
                self.x_deq.popleft()
        else:
            if p in self.y_deq or p in self.x_deq:
                return False
            self.y_deq.append(p)
            if len(self.y_deq) > 3:
                self.y_deq.popleft()
        self.x_msk = self.code(self.x_deq)
        self.y_msk = self.code(self.y_deq)

        self.history.append(p)
        self.code_msk()
        return True

    def judge(self, x_deq, y_deq):
        for i in [-1, 1]:
            if i == 1:
                l = sorted(list(x_deq))
            else:
                l = sorted(list(y_deq))
            if len(l) < 3:
                continue
            if l[0] % 3 == 0 and l[2] - l[0] == 2:
                return i
            elif len(set(l[j] % 3 for j in range(3))) == 1:
                return i
            elif l[1] == 4 and l[0] + l[2] == 8:
                return i
        return 0

    def get_result(self):
        r = self.judge(self.x_deq, self.y_deq)
        return r

    def code(self, l):
        r = 0
        for i in range(len(l)):
            r += 10 ** i * (l[i] + 1)
        return r
    
    def code_msk(self):
        self.x_msk = self.code(self.x_deq)
        self.y_msk = self.code(self.y_deq)
        self.msk = self.x_msk * 1000 + self.y_msk

        
    def train(self):
        edge0 = [[] for _ in range(self.dig.n)]
        edge1 = [[] for _ in range(self.dig.n)]
        win = set()
        lose = set()
        for msk in range(self.dig.n):
            x_msk, y_msk = msk // 1000, msk % 1000
            x, y = [], []
            while x_msk:
                x.append(x_msk % 10 - 1)
                x_msk //= 10
            while y_msk:
                y.append(y_msk % 10 - 1)
                y_msk //= 10
            result = self.judge(x, y)
            if result == 1:
                win.add(msk)
                continue
            elif result == -1:
                lose.add(msk)
                continue
            for j in range(9):
                if j in x or j in y:
                    continue
                x_ = x.copy()
                y_ = y.copy()
                x_.append(j)
                y_.append(j)
                if len(x_) > 3:
                    x_ = x_[1:]
                if len(y_) > 3:
                    y_ = y_[1:]
                t0 = self.code(x_) * 1000 + msk % 1000
                t1 = msk // 1000 * 1000 + self.code(y_)
                edge0[msk].append(t0)
                edge1[msk].append(t1)

        self.dig.set_edges(edge0, edge1)
        self.dig.set_win(win)
        self.dig.set_lose(lose)
        self.dig.solve()
        self.dig.save_training_data()

    def load_train(self, filename='DiG.train'):
        self.dig.load_training_data(filename)

    def show(self):
        board = [[' '] * 3 for _ in range(3)]
        for x in self.x_deq:
            i, j = x // 3, x % 3
            board[i][j] = 'X'
        for y in self.y_deq:
            i, j = y // 3, y % 3
            board[i][j] = 'O'
        print('|'.join(board[0]))
        print('|'.join(board[1]))
        print('|'.join(board[2]))

    def ai_make_move(self, force=-1, help=False):
        p = 0
        if len(self.history) & 1 == 0:
            p = 1
        moves = []
        for j in range(9):
            if j in self.x_deq or j in self.y_deq:
                continue
            if p == 1:
                x = list(self.x_deq)
                x.append(j)
                if len(x) > 3:
                    x = x[1:]
                msk_ = self.code(x) * 1000 + self.y_msk
                moves.append([j, self.dig.dp[msk_][1], self.dig.depth[msk_][1]])
            else:
                y = list(self.y_deq)
                y.append(j)
                if len(y) > 3:
                    y = y[1:]
                msk_ = self.x_msk * 1000 + self.code(y)
                moves.append([j, -self.dig.dp[msk_][0], self.dig.depth[msk_][0]])
        moves.sort(key=lambda x: (x[1], -x[2]))
        q = moves[-1][0]
        if moves[-1][1] == -1:
            moves.sort(key=lambda x: (x[1], x[2]))
            q = moves[-1][0]
        if help:
            print('hint', q % 3, q // 3)
            return
        if force >= 0:
            self.play(p, force)
        else:
            print(moves[-1][1], moves[-1][2])
            self.play(p, moves[-1][0])
        return


    def play_with_ai(self):
        self.reset()
        while 1:
            self.ai_make_move()
            self.show()
            print(self.msk, self.dig.dp[self.msk])
            if self.judge(self.x_deq, self.y_deq) == 1:
                print('AI wins')
                break
            i, j = map(int, input().split())
            flag = False
            while not flag:
                flag = self.play(0, i * 3 + j)
                if not flag:
                    print('invalid move, try again')
                    i, j = map(int, input().split())
            self.show()
            print(self.msk, self.dig.dp[self.msk])
            if self.judge(self.x_deq, self.y_deq) == -1:
                print('You win!')
                break

class DiG:
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

    def save_training_data(self, filename='DiG.train'):
        with open(filename, 'w') as file:
            dp0 = [self.dp[i][0] for i in range(self.n)]
            dp1 = [self.dp[i][1] for i in range(self.n)]
            file.write(' '.join(map(str, dp0)) + '\n')
            file.write(' '.join(map(str, dp1)) + '\n')
            depth0 = [self.depth[i][0] for i in range(self.n)]
            depth1 = [self.depth[i][1] for i in range(self.n)]
            file.write(' '.join(map(str, depth0)) + '\n')
            file.write(' '.join(map(str, depth1)) + '\n')

    def load_training_data(self, filename='DiG.load'):
        with open(filename, 'r') as file:
            s = file.read().strip()
            dp0, dp1, depth0, depth1 = s.split('\n')
            dp0 = list(map(int, dp0.split()))
            dp1 = list(map(int, dp1.split()))
            depth0 = list(map(int, depth0.split()))
            depth1 = list(map(int, depth1.split()))
            self.dp = [[x, y] for x, y in zip(dp0, dp1)]
            self.depth = [[x, y] for x, y in zip(depth0, depth1)]


if __name__ == "__main__":
    game = Game()
    # game.train()
    game.load_train()
    # print(game.dig.dp[589071])
    # print(game.dig.depth[589071])
    # print(game.dig.edge1[589071])
    # print(game.dig.dp[589471])
    # print(game.dig.depth[589471])
    game.play_with_ai()