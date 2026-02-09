class agent:
    def __init__(self, game, input_func):
        self.name = 'manual'
        self.game = game
        self.input_func = input_func

    def make_move(self):
        i, j = self.input_func()
        if self.game.board[i][j] != 0:
            self.make_move()
            return
        self.game.play(i, j)
        return True