class Strategy:
    def __init__(self, game):
        self.name = 'Player vs Player'
        self.game = game

    def make_move(self):
        """PvP 模式不需要 AI 做决策，返回 False"""
        return False
