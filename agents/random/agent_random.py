import random

class agent:
    def __init__(self, game):
        self.name = 'random'
        self.game = game

    def make_move(self):
        candidate = []
        for i in range(self.game.n):
            for j in range(self.game.n):
                if self.game.board[i][j] == 0:
                    candidate.append([i, j])
        ci = random.randint(0, len(candidate) - 1)
        i, j = candidate[ci]
        self.game.play(i, j)
        return True