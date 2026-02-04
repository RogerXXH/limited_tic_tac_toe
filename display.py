import pygame
import sys
from Game import GameBase
# import strategies.perfect3x3.perfect_strategy as strategy_ai
import strategies.random.random_strategy as strategy_ai
# import strategies.manual.manual_strategy as strategy_manual


class GameUI:
    def __init__(self):
        self.game = GameBase(3, 3)
        self.strategy = strategy_ai.Strategy(self.game)
        self.result = 0

        pygame.init()
        if self.game.n < 6:
            self.window_size = self.game.n * 110
        else:
            self.window_size = 600

        self.cell_size = self.window_size // (self.game.n * 1.1)
        self.grid = self.game.n
        self.screen = pygame.display.set_mode((self.window_size, self.window_size + 50))
        pygame.display.set_caption("tic-tac-toc")

        self.button_width = 120
        self.button_height = 40
        self.button_y = self.window_size

        # Modern color scheme
        self.bg_gradient_top = (245, 247, 250)
        self.bg_gradient_bottom = (230, 235, 243)
        self.button_primary = (59, 130, 246)
        self.button_primary_hover = (37, 99, 235)
        self.button_secondary = (168, 85, 247)
        self.button_secondary_hover = (147, 51, 234)
        self.text_color = (255, 255, 255)

        # Modern piece colors
        self.xx_color = (239, 68, 68)
        self.xx_color_trc = (252, 165, 165)
        self.o_color = (59, 130, 246)
        self.o_color_trc = (147, 197, 253)

        # Grid and cell colors
        self.grid_line_color = (203, 213, 225)
        self.cell_background = (255, 255, 255)
        self.cell_hover = (248, 250, 252)

        self.piece_gap = self.cell_size // 5

        # Effect settings
        self.button_radius = 10
        self.cell_radius = 6
        self.shadow_offset = (4, 4)

        # Hover state tracking
        self.hovered_button = None
        self.hovered_cell = None

        self.current_player = 1
        self.game_on = None
        self.play = -1

        self.button1_text = "Play with X"
        self.button2_text = "Play with O"

        self.button1_rect = pygame.Rect(20, self.button_y, self.button_width, self.button_height)
        self.button2_rect = pygame.Rect(self.window_size - self.button_width - 20, self.button_y, self.button_width,
                                        self.button_height)
        self.button3_rect = pygame.Rect(self.window_size // 2 - 10, self.button_y, self.button_height, self.button_height)

    def draw_gradient_background(self):
        """Draw vertical gradient background"""
        height = self.window_size + 50
        for y in range(height):
            # Linear interpolation between top and bottom colors
            ratio = y / height
            color = tuple(
                int(self.bg_gradient_top[i] * (1 - ratio) + self.bg_gradient_bottom[i] * ratio)
                for i in range(3)
            )
            pygame.draw.line(self.screen, color, (0, y), (self.window_size, y))

    def draw_rounded_rect_with_shadow(self, color, rect, radius, shadow=True, hover=False):
        """Draw rounded rectangle with optional shadow"""
        if shadow:
            # Draw shadow
            shadow_color = (0, 0, 0, 25)
            offset_x, offset_y = self.shadow_offset
            if hover:
                offset_x, offset_y = 6, 8
            shadow_rect = rect.copy()
            shadow_rect.x += offset_x
            shadow_rect.y += offset_y

            # Create shadow surface with alpha
            shadow_surface = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(shadow_surface, shadow_color, shadow_surface.get_rect(), border_radius=radius)

            # Blur effect (simple approximation)
            blur_radius = 10 if not hover else 15
            for i in range(blur_radius // 2):
                offset = i * 0.5
                temp_rect = shadow_rect.copy()
                temp_rect.x += offset
                temp_rect.y += offset
                self.screen.blit(shadow_surface, temp_rect, special_flags=pygame.BLEND_ALPHA_SDL2)

        # Draw main rounded rectangle
        pygame.draw.rect(self.screen, color, rect, border_radius=radius)

    def draw_board_with_modern_effects(self):
        """Draw board with modern effects including shadows, rounded corners, and hover states"""
        board_x = (self.window_size - self.grid * self.cell_size) // 2
        board_y = (self.window_size - self.grid * self.cell_size) // 2

        # Draw board shadow
        board_rect = pygame.Rect(board_x - 5, board_y - 5,
                                 self.grid * self.cell_size + 10,
                                 self.grid * self.cell_size + 10)
        shadow_surface = pygame.Surface((board_rect.width, board_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surface, (0, 0, 0, 13), shadow_surface.get_rect(), border_radius=8)
        shadow_rect = board_rect.copy()
        shadow_rect.y += 4
        self.screen.blit(shadow_surface, shadow_rect, special_flags=pygame.BLEND_ALPHA_SDL2)

        # Draw cells with rounded corners
        for i in range(self.grid):
            for j in range(self.grid):
                cell_x = board_x + i * self.cell_size
                cell_y = board_y + j * self.cell_size
                cell_rect = pygame.Rect(cell_x + 1, cell_y + 1,
                                       self.cell_size - 2, self.cell_size - 2)

                # Check if this cell is hovered
                is_hovered = (self.hovered_cell == (i, j))
                cell_color = self.cell_hover if is_hovered else self.cell_background

                pygame.draw.rect(self.screen, cell_color, cell_rect, border_radius=self.cell_radius)
                pygame.draw.rect(self.screen, self.grid_line_color, cell_rect,
                               width=2, border_radius=self.cell_radius)

    def draw_pieces(self):
        """Draw X and O pieces on the board"""
        board_x = (self.window_size - self.grid * self.cell_size) // 2
        board_y = (self.window_size - self.grid * self.cell_size) // 2

        for ti, (i, j) in enumerate(self.game.x):
            cell_x = board_x + i * self.cell_size
            cell_y = board_y + j * self.cell_size
            t = 1 - (len(self.game.x) - ti) / self.game.m / 1.5
            if len(self.game.x) == self.game.m and ti == 0:
                self.draw_x(cell_x, cell_y, 0)
            else:
                self.draw_x(cell_x, cell_y, t)

        for ti, (i, j) in enumerate(self.game.y):
            cell_x = board_x + i * self.cell_size
            cell_y = board_y + j * self.cell_size
            t = 1 - (len(self.game.y) - ti) / self.game.m / 1.5
            if len(self.game.y) == self.game.m and ti == 0:
                self.draw_o(cell_x, cell_y, 0)
            else:
                self.draw_o(cell_x, cell_y, t)

    def draw(self):
        # Draw gradient background
        self.draw_gradient_background()

        # Draw modern board
        self.draw_board_with_modern_effects()

        # Draw pieces
        self.draw_pieces()

        # Draw modern buttons with shadows
        button1_color = self.button_primary_hover if self.hovered_button == 1 else self.button_primary
        button2_color = self.button_primary_hover if self.hovered_button == 2 else self.button_primary
        button3_color = self.button_secondary_hover if self.hovered_button == 3 else self.button_secondary

        self.draw_rounded_rect_with_shadow(button1_color, self.button1_rect, self.button_radius,
                                          shadow=True, hover=(self.hovered_button == 1))
        self.draw_rounded_rect_with_shadow(button2_color, self.button2_rect, self.button_radius,
                                          shadow=True, hover=(self.hovered_button == 2))
        self.draw_rounded_rect_with_shadow(button3_color, self.button3_rect, self.button_height // 2,
                                          shadow=True, hover=(self.hovered_button == 3))

        # Draw button text
        font = pygame.font.Font(None, 25)
        text1 = font.render(self.button1_text, True, self.text_color)
        text2 = font.render(self.button2_text, True, self.text_color)

        # Center text in buttons
        text1_x = self.button1_rect.x + (self.button1_rect.width - text1.get_width()) // 2
        text1_y = self.button1_rect.y + (self.button1_rect.height - text1.get_height()) // 2
        text2_x = self.button2_rect.x + (self.button2_rect.width - text2.get_width()) // 2
        text2_y = self.button2_rect.y + (self.button2_rect.height - text2.get_height()) // 2

        self.screen.blit(text1, (text1_x, text1_y))
        self.screen.blit(text2, (text2_x, text2_y))

        # Draw reset symbol (↻) for button3
        reset_font = pygame.font.Font(None, 30)
        reset_text = reset_font.render("↻", True, self.text_color)
        reset_x = self.button3_rect.x + (self.button3_rect.width - reset_text.get_width()) // 2
        reset_y = self.button3_rect.y + (self.button3_rect.height - reset_text.get_height()) // 2
        self.screen.blit(reset_text, (reset_x, reset_y))

        # Show result
        if self.result != 0:
            font = pygame.font.Font(None, 50)
            if self.result == 1:
                text = "X Wins!"
                text_surface = font.render(text, True, self.xx_color)
            elif self.result == -1:
                text = "O Wins!"
                text_surface = font.render(text, True, self.o_color)

            # Draw text with shadow
            text_x = (self.window_size - text_surface.get_width()) // 2
            text_y = 20

            # Shadow
            shadow_surface = font.render(text, True, (0, 0, 0, 50))
            self.screen.blit(shadow_surface, (text_x + 2, text_y + 2))
            # Main text
            self.screen.blit(text_surface, (text_x, text_y))

        if self.game_on:
            self.result = self.game.get_result()
            if self.result != 0:
                self.game_on = False

    def draw_x(self, x, y, t):
        r, g, b = self.xx_color
        r_, g_, b_ = self.xx_color_trc
        xx_color = (r * t + r_ * (1 - t), g * t + g_ * (1 - t), b * t + b_ * (1 - t))

        # Draw shadow
        shadow_offset = 2
        shadow_color = (0, 0, 0, 30)
        pygame.draw.line(self.screen, shadow_color,
                        (x + self.piece_gap + shadow_offset, y + self.cell_size - self.piece_gap + shadow_offset),
                        (x + self.cell_size - self.piece_gap + shadow_offset, y + self.piece_gap + shadow_offset), 4)
        pygame.draw.line(self.screen, shadow_color,
                        (x + self.piece_gap + shadow_offset, y + self.piece_gap + shadow_offset),
                        (x + self.cell_size - self.piece_gap + shadow_offset, y + self.cell_size - self.piece_gap + shadow_offset), 4)

        # Draw main X
        pygame.draw.line(self.screen, xx_color, (x + self.piece_gap, y + self.cell_size - self.piece_gap),
                         (x + self.cell_size - self.piece_gap, y + self.piece_gap), 5)
        pygame.draw.line(self.screen, xx_color, (x + self.piece_gap, y + self.piece_gap),
                         (x + self.cell_size - self.piece_gap, y + self.cell_size - self.piece_gap), 5)

    def draw_o(self, x, y, t):
        r, g, b = self.o_color
        r_, g_, b_ = self.o_color_trc
        o_color = (r * t + r_ * (1 - t), g * t + g_ * (1 - t), b * t + b_ * (1 - t))
        center = (x + self.cell_size // 2, y + self.cell_size // 2)

        # Draw shadow
        shadow_offset = 2
        shadow_color = (0, 0, 0, 30)
        shadow_center = (center[0] + shadow_offset, center[1] + shadow_offset)
        pygame.draw.circle(self.screen, shadow_color, shadow_center, self.cell_size // 2 - self.piece_gap, 5)

        # Draw main O
        pygame.draw.circle(self.screen, o_color, center, self.cell_size // 2 - self.piece_gap, 5)


    def handle_events(self, event):
        if event.type == pygame.QUIT:
            sys.exit()

        # Handle mouse motion for hover effects
        if event.type == pygame.MOUSEMOTION:
            mouse_pos = pygame.mouse.get_pos()

            # Check button hover
            self.hovered_button = None
            if self.button1_rect.collidepoint(mouse_pos):
                self.hovered_button = 1
            elif self.button2_rect.collidepoint(mouse_pos):
                self.hovered_button = 2
            elif self.button3_rect.collidepoint(mouse_pos):
                self.hovered_button = 3

            # Check cell hover
            if self.game_on:
                board_x = (self.window_size - self.grid * self.cell_size) // 2
                board_y = (self.window_size - self.grid * self.cell_size) // 2
                cell_x = mouse_pos[0] - board_x
                cell_y = mouse_pos[1] - board_y

                if 0 <= cell_x < self.grid * self.cell_size and 0 <= cell_y < self.grid * self.cell_size:
                    i = int(cell_x // self.cell_size)
                    j = int(cell_y // self.cell_size)
                    if self.game.board[i][j] == 0:
                        self.hovered_cell = (i, j)
                    else:
                        self.hovered_cell = None
                else:
                    self.hovered_cell = None
            else:
                self.hovered_cell = None

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            if self.button1_rect.collidepoint(mouse_pos):
                self.start_game(0)
            elif self.button2_rect.collidepoint(mouse_pos):
                self.start_game(1)
            elif self.button3_rect.collidepoint(mouse_pos):
                self.start_game(-1)

        if self.game_on and event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            board_x = (self.window_size - self.grid * self.cell_size) // 2
            board_y = (self.window_size - self.grid * self.cell_size) // 2

            cell_x = mouse_pos[0] - board_x
            cell_y = mouse_pos[1] - board_y

            if 0 <= cell_x < self.grid * self.cell_size and 0 <= cell_y < self.grid * self.cell_size:
                i = int(cell_x // self.cell_size)
                j = int(cell_y // self.cell_size)

                if self.game.board[i][j] == 0:
                    self.game.play(i, j)
                    self.draw()
                    if self.game_on and self.play != -1:
                        self.strategy.make_move()
                        self.draw()

    def start_game(self, player):
        self.result = 0
        self.game.reset()
        self.play = player
        self.game_on = True
        self.draw()
        if player == 1:
            self.strategy.make_move()
            self.draw()

    def run(self):
        while True:
            for event in pygame.event.get():
                self.handle_events(event)
            self.draw()
            pygame.display.flip()


# 初始化并运行游戏
if __name__ == "__main__":
    game_ui = GameUI()
    game_ui.run()
