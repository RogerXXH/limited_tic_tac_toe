from collections import deque
import random


class GameBase:
    def __init__(self, n, max_move):
        self.n = n
        self.m = max_move
        self.board = [[0] * self.n for _ in range(self.n)]
        self.x = deque()
        self.y = deque()
        self.history = []

    def make_move(self):
        empty_cell = []

        for i in range(self.n):
            for j in range(self.n):
                if self.board[i][j] == 0:
                    empty_cell.append([i, j])

        ci = random.randint(0, len(empty_cell) - 1)
        i, j = empty_cell[ci]
        return i, j

    def reset(self):
        self.__init__(self.n, self.m)

    def get_result(self):
        if not self.history:
            return 0
        i, j = self.history[-1]
        directions = [[-1, 0], [0, -1], [-1, -1], [-1, 1]]
        for di, dj in directions:
            left, right = 0, 0
            i_, j_ = i, j
            for _ in range(self.m - 1):
                i_, j_ = i_ + di, j_ + dj
                if 0 <= i_ < self.n and 0 <= j_ < self.n and self.board[i_][j_] == self.board[i][j]:
                    left += 1
                else:
                    break
            i_, j_ = i, j
            for _ in range(self.m - 1):
                i_, j_ = i_ - di, j_ - dj
                if 0 <= i_ < self.n and 0 <= j_ < self.n and self.board[i_][j_] == self.board[i][j]:
                    right += 1
                else:
                    break
            if left + right + 1 >= self.m:
                return self.board[i][j]
        return 0

    def play(self, i, j):
        if self.board[i][j] != 0:
            return False
        if len(self.history) & 1 == 0:
            self.x.append([i, j])
            self.board[i][j] = 1
            if len(self.x) > self.m:
                i_, j_ = self.x.popleft()
                self.board[i_][j_] = 0
        else:
            self.y.append([i, j])
            self.board[i][j] = -1
            if len(self.y) > self.m:
                i_, j_ = self.y.popleft()
                self.board[i_][j_] = 0
        self.history.append([i, j])
        return True

    def run(self, strategy0, strategy1, round_limit=1000, render=None):
        self.reset()
        strategy0.game, strategy1.game = self, self
        for round in range(round_limit):
            if round & 1 == 0:
                strategy0.make_move()
            else:
                strategy1.make_move()
            result = self.get_result()
            if result != 0:
                return result
            if render:
                render()
        return 0
    
