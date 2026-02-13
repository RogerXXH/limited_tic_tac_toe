class Strategy:
    def __init__(self, game):
        self.name = 'AI Not Available'
        self.game = game

    def make_move(self):
        """AI 不可用占位策略，返回 False"""
        return False
