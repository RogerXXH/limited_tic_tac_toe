class Strategy:
    def __init__(self, game, input_func=None):
        self.name = 'Manual Input'
        self.game = game
        self.input_func = input_func

    def make_move(self):
        if self.input_func is None:
            return False
        i, j = self.input_func()
        if self.game.board[i][j] != 0:
            self.make_move()
            return
        self.game.play(i, j)
        return True
