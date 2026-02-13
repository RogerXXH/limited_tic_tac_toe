import pygame
import sys
import os
from Game import GameBase
import strategies.random.random_strategy as random_strategy
import strategies.pvp.pvp_strategy as pvp_strategy
import strategies.nocpu.nocpu_strategy as nocpu_strategy
import strategies.perfect3x3.perfect_strategy as perfect3x3_strategy
import strategies.perfect4x4_m4.perfect_strategy as perfect4x4_m4_strategy


# ==================== 字体管理 ====================

def get_chinese_font():
    """获取支持中文的字体，如果找不到则使用默认字体"""
    # 常见的中文字体文件名
    chinese_fonts = [
        'SimHei.ttf',        # 黑体
        'SimSun.ttf',       # 宋体
        'Microsoft YaHei',  # 微软雅黑
        'WenQuanYi Zen Hei', # 文泉驿正黑
        'Noto Sans CJK SC', # 思源黑体
        'PingFang SC',     # 萍方
        'STHeiti',         # 华文黑体
        'Arial Unicode MS', # Arial Unicode
    ]

    # 首先尝试通过 pygame.font.match_font 查找
    for font_name in chinese_fonts:
        font_path = pygame.font.match_font(font_name)
        if font_path:
            try:
                font = pygame.font.Font(font_path, 20)
                # 测试是否能渲染中文
                test = font.render("中", True, (0, 0, 0))
                return font_path
            except:
                continue

    # 尝试常见的系统字体路径
    system_paths = [
        '/System/Library/Fonts/PingFang.ttc',           # macOS
        '/Windows/Fonts/msyh.ttc',                     # Windows
        '/Windows/Fonts/simhei.ttf',                   # Windows
        '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc', # Linux
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', # Linux
    ]

    for font_path in system_paths:
        if os.path.exists(font_path):
            try:
                font = pygame.font.Font(font_path, 20)
                test = font.render("中", True, (0, 0, 0))
                return font_path
            except:
                continue

    # 找不到中文字体，返回 None
    return None


# ==================== UI 组件类 ====================

class Dropdown:
    """下拉菜单组件"""
    def __init__(self, rect, options, default_index=0, font_path=None):
        self.rect = rect
        self.options = options  # list of: {"label": str, "value": any}
        self.selected_index = default_index
        self.is_open = False
        self.item_height = 30
        self.border_radius = 6
        self.font_path = font_path

    def get_selected_value(self):
        return self.options[self.selected_index]["value"] if self.options else None

    def get_selected_label(self):
        return self.options[self.selected_index]["label"] if self.options else ""

    def set_selected_index(self, index):
        if 0 <= index < len(self.options):
            self.selected_index = index

    def set_selected_value(self, value):
        for i, opt in enumerate(self.options):
            if opt["value"] == value:
                self.selected_index = i
                break

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()

            # 检查是否点击了主按钮
            if self.rect.collidepoint(mouse_pos):
                self.is_open = not self.is_open
                return True

            # 如果下拉菜单打开，检查是否点击了选项或外部
            if self.is_open:
                dropdown_rect = self.get_dropdown_rect()
                if dropdown_rect.collidepoint(mouse_pos):
                    # 点击了下拉选项区域
                    relative_y = mouse_pos[1] - dropdown_rect.y
                    clicked_index = int(relative_y // self.item_height)
                    if 0 <= clicked_index < len(self.options):
                        self.selected_index = clicked_index
                        self.is_open = False
                        return True
                # 如果下拉菜单打开，且点击不在按钮和下拉区域内，返回True表示已处理
                # 这样就不会触发其他下拉菜单
                return True

        return False

    def get_dropdown_rect(self):
        """获取下拉菜单的矩形区域"""
        return pygame.Rect(
            self.rect.x,
            self.rect.y + self.rect.height,
            self.rect.width,
            len(self.options) * self.item_height
        )

    def draw(self, screen, font_cache, bg_color, hover_color, text_color):
        # 获取字体
        font = font_cache.get_font(18, self.font_path)

        # 绘制按钮背景
        mouse_pos = pygame.mouse.get_pos()
        is_hovered = self.rect.collidepoint(mouse_pos)
        color = hover_color if is_hovered else bg_color

        pygame.draw.rect(screen, color, self.rect, border_radius=self.border_radius)
        pygame.draw.rect(screen, (148, 163, 184), self.rect, width=1, border_radius=self.border_radius)

        # 绘制选中的文本
        text = font.render(self.get_selected_label(), True, text_color)
        text_x = self.rect.x + 10
        text_y = self.rect.y + (self.rect.height - text.get_height()) // 2
        screen.blit(text, (text_x, text_y))

        # 绘制下拉箭头
        arrow_size = 6
        center_x = self.rect.right - 15
        center_y = self.rect.centery
        if self.is_open:
            # 向上箭头
            pygame.draw.polygon(screen, text_color, [
                (center_x - arrow_size, center_y + 3),
                (center_x + arrow_size, center_y + 3),
                (center_x, center_y - 3)
            ])
        else:
            # 向下箭头
            pygame.draw.polygon(screen, text_color, [
                (center_x - arrow_size, center_y - 3),
                (center_x + arrow_size, center_y - 3),
                (center_x, center_y + 3)
            ])

    def draw_dropdown(self, screen, font_cache, bg_color, hover_color, text_color):
        """只绘制下拉选项列表（在最上层调用）"""
        if not self.is_open:
            return

        dropdown_rect = self.get_dropdown_rect()
        font = font_cache.get_font(18, self.font_path)

        # 绘制背景
        pygame.draw.rect(screen, bg_color, dropdown_rect, border_radius=self.border_radius)
        pygame.draw.rect(screen, (148, 163, 184), dropdown_rect, width=1, border_radius=self.border_radius)

        # 绘制选项
        for i, option in enumerate(self.options):
            item_rect = pygame.Rect(
                dropdown_rect.x,
                dropdown_rect.y + i * self.item_height,
                dropdown_rect.width,
                self.item_height
            )

            # 高亮选中的项 - 使用深灰色
            if i == self.selected_index:
                pygame.draw.rect(screen, (203, 213, 225), item_rect)

            # 绘制文本
            option_text = font.render(option["label"], True, text_color)
            option_x = item_rect.x + 10
            option_y = item_rect.y + (item_rect.height - option_text.get_height()) // 2
            screen.blit(option_text, (option_x, option_y))

            # 绘制分隔线（除了最后一项）
            if i < len(self.options) - 1:
                pygame.draw.line(screen, (226, 232, 240),
                                (item_rect.x + 5, item_rect.bottom),
                                (item_rect.right - 5, item_rect.bottom))


class Button:
    """按钮组件"""
    def __init__(self, rect, text, primary=True, font_path=None):
        self.rect = rect
        self.text = text
        self.primary = primary
        self.border_radius = 8
        self.hovered = False
        self.font_path = font_path

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            mouse_pos = pygame.mouse.get_pos()
            self.hovered = self.rect.collidepoint(mouse_pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.hovered:
                return True
        return False

    def draw(self, screen, font_cache, primary_color, primary_hover, secondary_color, secondary_hover, text_color):
        font = font_cache.get_font(24, self.font_path)
        mouse_pos = pygame.mouse.get_pos()
        is_hovered = self.rect.collidepoint(mouse_pos)

        if self.primary:
            color = primary_hover if is_hovered else primary_color
        else:
            color = secondary_hover if is_hovered else secondary_color

        # 绘制按钮
        pygame.draw.rect(screen, color, self.rect, border_radius=self.border_radius)

        # 绘制文本
        text_surface = font.render(self.text, True, text_color)
        text_x = self.rect.x + (self.rect.width - text_surface.get_width()) // 2
        text_y = self.rect.y + (self.rect.height - text_surface.get_height()) // 2
        screen.blit(text_surface, (text_x, text_y))


class FontCache:
    """字体缓存类，用于管理中文字体"""
    def __init__(self):
        self.chinese_font_path = get_chinese_font()
        self.font_cache = {}

    def get_font(self, size, font_path=None):
        """获取字体，优先使用指定字体，其次使用中文字体，最后使用默认字体"""
        cache_key = (font_path or self.chinese_font_path, size)
        if cache_key not in self.font_cache:
            if font_path and os.path.exists(font_path):
                try:
                    self.font_cache[cache_key] = pygame.font.Font(font_path, size)
                except:
                    pass
            if cache_key not in self.font_cache and self.chinese_font_path:
                try:
                    self.font_cache[cache_key] = pygame.font.Font(self.chinese_font_path, size)
                except:
                    pass
            if cache_key not in self.font_cache:
                self.font_cache[cache_key] = pygame.font.Font(None, size)
        return self.font_cache[cache_key]

    def get_font_small(self):
        return self.get_font(18)

    def get_font_medium(self):
        return self.get_font(22)

    def get_font_large(self):
        return self.get_font(24)

    def get_font_button(self):
        return self.get_font(20)


# ==================== 主界面类 ====================

class GameUI:
    def __init__(self):
        pygame.init()

        # 字体缓存
        self.font_cache = FontCache()

        # ==================== 配置参数范围 ====================
        self.board_sizes = list(range(3, 16))  # 3-15
        self.max_moves = list(range(1, 16))   # 1-15
        self.win_counts = list(range(2, 16))  # 2-15

        # 当前配置配置
        self.current_board_size = 3
        self.current_max_move = 3
        self.current_win_count = 3

        # 棋子样式配置
        self.piece_styles = [
            {"name": "X/O Style", "type": "xo"},
            {"name": "Go Black/White", "type": "go_classic"},
            {"name": "Go with Border", "type": "go_border"},
            {"name": "Gradient Style", "type": "gradient"}
        ]
        self.current_piece_style = 0

        # ==================== 侧边菜单配置 ====================
        self.sidebar_width = 220
        self.sidebar_bg = (248, 250, 252)
        self.sidebar_text_color = (51, 65, 85)
        self.sidebar_section_bg = (241, 245, 249)
        self.sidebar_border_color = (203, 213, 225)

        # ==================== 现代配色方案 ====================
        self.bg_gradient_top = (245, 247, 250)
        self.bg_gradient_bottom = (230, 235, 243)
        self.button_primary = (59, 130, 246)
        self.button_primary_hover = (37, 99, 235)
        self.button_secondary = (168, 85, 247)
        self.button_secondary_hover = (147, 51, 234)
        self.button_success = (34, 197, 94)
        self.button_success_hover = (22, 163, 74)
        self.button_warning = (251, 146, 60)
        self.button_warning_hover = (245, 124, 0)
        self.text_color = (255, 255, 255)

        # 现代棋子颜色
        self.xx_color = (239, 68, 68)
        self.xx_color_trc = (252, 165, 165)
        self.o_color = (59, 130, 246)
        self.o_color_trc = (147, 197, 253)

        # 棋盘和格子颜色
        self.grid_line_color = (203, 213, 225)
        self.cell_background = (255, 255, 255)
        self.cell_hover = (248, 250, 252)

        # 效果设置
        self.button_radius = 10
        self.cell_radius = 6
        self.shadow_offset = (4, 4)

        # 悬停状态跟踪
        self.hovered_cell = None
        self.hovered_dropdown = None

        # ==================== 游戏状态 ====================
        self.current_player = 1
        self.game_on = False
        self.play = -1  # -1 = reset/not started, 0 = play with X, 1 = play with O
        self.result = 0

        # ==================== 对战模式 ====================
        self.play_mode = "pvp"  # "pvp" or "pvai"

        # ==================== 初始化游戏 ====================
        self._init_game()
        self._init_ui_components()

    def _init_game(self):
        """根据当前配置初始化游戏"""
        self.game = GameBase(
            self.current_board_size,
            self.current_max_move,
            self.current_win_count
        )

        # 过滤可用策略
        self._filter_available_strategies()

        # 更新 UI 尺寸
        self._update_ui_dimensions()

        # PvP 模式默认开始游戏
        if self.play_mode == "pvp":
            self.game_on = True
        else:
            self.game_on = False

    def _filter_available_strategies(self):
        """根据当前配置过滤可用策略"""
        current_config = (self.current_board_size, self.current_max_move)
        self.available_strategies = []

        # PvP 策略 - 总是可用
        pvp_instance = self._get_or_create_strategy(pvp_strategy)
        self.available_strategies.append({
            "name": "Player vs Player",
            "module": pvp_strategy,
            "description": "Two players",
            "instance": pvp_instance,
            "supports_all": True
        })

        # Random 策略 - 总是可用
        random_instance = self._get_or_create_strategy(random_strategy)
        self.available_strategies.append({
            "name": "Random AI",
            "module": random_strategy,
            "description": "Random moves",
            "instance": random_instance,
            "supports_all": True
        })

        # Perfect AI 3x3
        if current_config == (3, 3):
            perfect3x3_instance = self._get_or_create_strategy(perfect3x3_strategy)
            self.available_strategies.append({
                "name": "Perfect AI 3x3",
                "module": perfect3x3_strategy,
                "description": "Unbeatable 3x3",
                "instance": perfect3x3_instance,
                "supports_all": False
            })

        # Perfect AI 4x4
        if current_config == (4, 4):
            perfect4x4_instance = self._get_or_create_strategy(perfect4x4_m4_strategy)
            self.available_strategies.append({
                "name": "Perfect AI 4x4",
                "module": perfect4x4_m4_strategy,
                "description": "Unbeatable 4x4",
                "instance": perfect4x4_instance,
                "supports_all": False
            })

        # 设置当前策略
        if not hasattr(self, 'current_strategy_index') or self.current_strategy_index >= len(self.available_strategies):
            # 默认选择 Random AI（索引1）
            self.current_strategy_index = 1 if len(self.available_strategies) > 1 else 0

        self.strategy = self.available_strategies[self.current_strategy_index]["instance"]

    def _get_or_create_strategy(self, strategy_module):
        """获取或创建策略实例（带缓存）"""
        cache_key = (
            strategy_module.__name__,
            self.current_board_size,
            self.current_max_move,
            self.current_win_count
        )

        if not hasattr(self, 'strategy_cache'):
            self.strategy_cache = {}

        if cache_key in self.strategy_cache:
            instance = self.strategy_cache[cache_key]
            instance.game = self.game
        else:
            instance = strategy_module.Strategy(self.game)
            self.strategy_cache[cache_key] = instance

        return instance

    def _update_ui_dimensions(self):
        """根据棋盘大小动态计算窗口尺寸"""
        # 根据棋盘大小计算格子大小
        max_window_size = 700
        min_cell_size = 35
        max_cell_size = 60

        # 动态计算格子大小
        ideal_cell_size = max_window_size // self.current_board_size
        self.cell_size = max(min_cell_size, min(max_cell_size, ideal_cell_size))

        # 计算棋盘总大小
        self.grid = self.current_board_size
        board_size = self.grid * self.cell_size

        # 顶部和底部边栏高度
        self.top_bar_height = 30
        self.bottom_bar_height = 120  # 增加底部高度以容纳按钮

        # 窗口总大小 - 确保按钮不重叠
        self.window_width = max(self.sidebar_width + 280, self.sidebar_width + board_size + 40)
        # 增加侧边菜单高度以确保 AI Strategy 下拉菜单可见
        self.window_height = max(550, board_size + self.top_bar_height + self.bottom_bar_height)

        # 创建窗口
        self.screen = pygame.display.set_mode((self.window_width, self.window_height))
        pygame.display.set_caption("Tic-Tac-Toe Extended")

        # 棋盘偏移量（在侧边菜单右侧，水平居中）
        self.board_offset_x = self.sidebar_width + 20
        if self.window_width - self.sidebar_width > board_size + 40:
            # 在可用空间内居中
            available_width = self.window_width - self.sidebar_width
            self.board_offset_x = self.sidebar_width + (available_width - board_size) // 2

        self.board_offset_y = self.top_bar_height + 20

        # 棋子间隙
        self.piece_gap = self.cell_size // 5

        # 重新初始化 UI 组件
        self._init_ui_components()

    def _init_ui_components(self):
        """初始化 UI 组件"""
        font_small = self.font_cache.get_font_small()
        font_medium = self.font_cache.get_font_medium()

        # 侧边菜单组件起始位置
        menu_start_x = 15
        menu_start_y = 20
        item_height = 30
        label_height = 25
        dropdown_height = 30
        gap = 10
        section_gap = 20

        y = menu_start_y

        # ==================== 配置部分 ====================
        # 标题
        self.config_title_y = y
        y += label_height + gap

        # 棋盘大小下拉菜单
        board_size_options = [{"label": f"{size}x{size}", "value": size} for size in self.board_sizes]
        self.board_size_dropdown = Dropdown(
            pygame.Rect(menu_start_x, y, 180, dropdown_height),
            board_size_options,
            self.board_sizes.index(self.current_board_size),
            self.font_cache.chinese_font_path
        )
        self.board_size_label_y = y - 22
        y += dropdown_height + gap

        # Max Move 下拉菜单
        max_move_options = [{"label": str(m), "value": m} for m in self.max_moves]
        self.max_move_dropdown = Dropdown(
            pygame.Rect(menu_start_x, y, 180, dropdown_height),
            max_move_options,
            self.max_moves.index(self.current_max_move),
            self.font_cache.chinese_font_path
        )
        self.max_move_label_y = y - 22
        y += dropdown_height + gap

        # Win Count 下拉菜单
        win_count_options = [{"label": str(w), "value": w} for w in self.win_counts]
        self.win_count_dropdown = Dropdown(
            pygame.Rect(menu_start_x, y, 180, dropdown_height),
            win_count_options,
            self.win_counts.index(self.current_win_count),
            self.font_cache.chinese_font_path
        )
        self.win_count_label_y = y - 22
        y += dropdown_height + gap + section_gap

        # ==================== 棋子样式部分 ====================
        self.style_title_y = y
        y += label_height + gap

        # 棋子样式下拉菜单
        piece_style_options = [{"label": s["name"], "value": i} for i, s in enumerate(self.piece_styles)]
        self.piece_style_dropdown = Dropdown(
            pygame.Rect(menu_start_x, y, 180, dropdown_height),
            piece_style_options,
            self.current_piece_style,
            self.font_cache.chinese_font_path
        )
        self.piece_style_label_y = y - 22
        y += dropdown_height + gap + section_gap

        # ==================== 对战模式部分 ====================
        self.mode_title_y = y
        y += label_height + gap

        # PvP 按钮
        button_width = 80
        self.pvp_button = Button(
            pygame.Rect(menu_start_x, y, button_width, 35),
            "PvP",
            primary=True,
            font_path=self.font_cache.chinese_font_path
        )
        # PvAI 按钮
        self.pvai_button = Button(
            pygame.Rect(menu_start_x + button_width + 10, y, button_width, 35),
            "PvAI",
            primary=False,
            font_path=self.font_cache.chinese_font_path
        )
        y += 35 + gap + section_gap

        # ==================== AI 策略部分 ====================
        self.strategy_title = y
        y += label_height + gap

        # 策略下拉菜单
        self._update_strategy_dropdown(menu_start_x, y, dropdown_height)
        y += dropdown_height + gap + section_gap

        # ==================== 开始/重置按钮 ====================
        button_y = self.window_height - 60
        button_x_start = self.sidebar_width + 20

        # 在 PvP 模式下，不需要 Start 按钮，直接开始
        # 在 PvAI 模式下，显示 "Play X" 和 "Play O" 按钮
        if self.play_mode == "pvai":
            # PvAI 模式 - Play X 和 Play O 按钮
            board_size = self.grid * self.cell_size
            button_x = self.board_offset_x + board_size - 230

            self.play_x_button = Button(
                pygame.Rect(button_x, button_y, 100, 40),
                "Play X",
                primary=True,
                font_path=self.font_cache.chinese_font_path
            )

            self.play_o_button = Button(
                pygame.Rect(button_x + 110, button_y, 100, 40),
                "Play O",
                primary=True,
                font_path=self.font_cache.chinese_font_path
            )

        # Reset 按钮
        self.reset_button = Button(
            pygame.Rect(self.window_width - 50, button_y, 40, 40),
            "R",
            primary=False,
            font_path=self.font_cache.chinese_font_path
        )

    def _update_strategy_dropdown(self, x, y, height):
        """更新策略下拉菜单"""
        strategy_options = [{"label": s["name"], "value": i} for i, s in enumerate(self.available_strategies)]
        self.strategy_dropdown = Dropdown(
            pygame.Rect(x, y, 180, height),
            strategy_options,
            self.current_strategy_index if hasattr(self, 'current_strategy_index') else 0,
            self.font_cache.chinese_font_path
        )
        self.strategy_label_y = y - 22

    # ==================== 绘制方法 ====================

    def draw_gradient_background(self):
        """绘制垂直渐变背景"""
        for y in range(self.window_height):
            ratio = y / self.window_height
            color = tuple(
                int(self.bg_gradient_top[i] * (1 - ratio) + self.bg_gradient_bottom[i] * ratio)
                for i in range(3)
            )
            pygame.draw.line(self.screen, color, (0, y), (self.window_width, y))

    def draw_sidebar(self):
        """绘制侧边菜单"""
        font_small = self.font_cache.get_font_small()
        font_medium = self.font_cache.get_font_medium()

        # 绘制侧边栏背景
        sidebar_rect = pygame.Rect(0, 0, self.sidebar_width, self.window_height)
        pygame.draw.rect(self.screen, self.sidebar_bg, sidebar_rect)
        pygame.draw.line(self.screen, self.sidebar_border_color,
                       (self.sidebar_width, 0), (self.sidebar_width, self.window_height), 2)

        # ==================== 配置部分 ====================
        config_title = font_medium.render("Board Config", True, (30, 41, 59))
        self.screen.blit(config_title, (15, self.config_title_y))

        # Board Size 标签
        board_size_label = font_small.render("Board Size:", True, self.sidebar_text_color)
        self.screen.blit(board_size_label, (15, self.board_size_label_y))

        # Max Move 标签
        max_move_label = font_small.render("Max Move:", True, self.sidebar_text_color)
        self.screen.blit(max_move_label, (15, self.max_move_label_y))

        # Win Count 标签
        win_count_label = font_small.render("Win Count:", True, self.sidebar_text_color)
        self.screen.blit(win_count_label, (15, self.win_count_label_y))

        # ==================== 棋子样式部分 ====================
        style_title = font_medium.render("Piece Style", True, (30, 41, 59))
        self.screen.blit(style_title, (15, self.style_title_y))

        piece_style_label = font_small.render("Style:", True, self.sidebar_text_color)
        self.screen.blit(piece_style_label, (15, self.piece_style_label_y))

        # ==================== 对战模式部分 ====================
        mode_title = font_medium.render("Game Mode", True, (30, 41, 59))
        self.screen.blit(mode_title, (15, self.mode_title_y))

        # PvP/PvAI 按钮
        self.pvp_button.draw(self.screen, self.font_cache,
                            self.button_primary, self.button_primary_hover,
                            self.button_secondary, self.button_secondary_hover,
                            self.text_color)
        self.pvai_button.draw(self.screen, self.font_cache,
                             self.button_secondary, self.button_secondary_hover,
                             self.button_primary, self.button_primary_hover,
                             self.text_color)

        # ==================== AI 策略部分 ====================
        strategy_title = font_medium.render("AI Strategy", True, (30, 41, 59))
        self.screen.blit(strategy_title, (15, self.strategy_title))

        strategy_label = font_small.render("Strategy:", True, self.sidebar_text_color)
        self.screen.blit(strategy_label, (15, self.strategy_label_y))

        # ==================== 绘制下拉菜单按钮 ====================
        dropdown_bg = (255, 255, 255)
        dropdown_hover = (248, 250, 252)

        self.board_size_dropdown.draw(self.screen, self.font_cache, dropdown_bg, dropdown_hover, self.sidebar_text_color)
        self.max_move_dropdown.draw(self.screen, self.font_cache, dropdown_bg, dropdown_hover, self.sidebar_text_color)
        self.win_count_dropdown.draw(self.screen, self.font_cache, dropdown_bg, dropdown_hover, self.sidebar_text_color)
        self.piece_style_dropdown.draw(self.screen, self.font_cache, dropdown_bg, dropdown_hover, self.sidebar_text_color)
        self.strategy_dropdown.draw(self.screen, self.font_cache, dropdown_bg, dropdown_hover, self.sidebar_text_color)

    def draw_board(self):
        """绘制棋盘"""
        board_x = self.board_offset_x
        board_y = self.board_offset_y

        # 绘制棋盘阴影
        board_rect = pygame.Rect(board_x - 3, board_y - 3,
                                self.grid * self.cell_size + 6,
                                self.grid * self.cell_size + 6)
        shadow_surface = pygame.Surface((board_rect.width, board_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surface, (0, 0, 0, 20), shadow_surface.get_rect(), border_radius=8)
        shadow_rect = board_rect.copy()
        shadow_rect.y += 3
        self.screen.blit(shadow_surface, shadow_rect, special_flags=pygame.BLEND_ALPHA_SDL2)

        # 绘制格子
        for i in range(self.grid):
            for j in range(self.grid):
                cell_x = board_x + i * self.cell_size
                cell_y = board_y + j * self.cell_size
                cell_rect = pygame.Rect(cell_x + 1, cell_y + 1,
                                       self.cell_size - 2, self.cell_size - 2)

                # 检查是否悬停
                is_hovered = (self.hovered_cell == (i, j))
                cell_color = self.cell_hover if is_hovered else self.cell_background

                pygame.draw.rect(self.screen, cell_color, cell_rect, border_radius=self.cell_radius)
                pygame.draw.rect(self.screen, self.grid_line_color, cell_rect,
                               width=1, border_radius=self.cell_radius)

    def draw_pieces(self):
        """绘制棋子"""
        board_x = self.board_offset_x
        board_y = self.board_offset_y

        # 判断是否需要显示黄框（max_move > 5）
        show_yellow_border = self.game.m > 5

        # 绘制 X 的棋子
        for ti, (i, j) in enumerate(self.game.x):
            cell_x = board_x + i * self.cell_size
            cell_y = board_y + j * self.cell_size
            # 计算年龄因子：0 = 最淡（即将消失），1 = 最浓（刚下）
            age_factor = (ti + 1) / min(len(self.game.x), self.game.m)

            # 检查是否即将消失：如果棋子数量已达到 max_move，这是最老的棋子（索引0）
            is_fading = len(self.game.x) >= self.game.m and ti == 0
            # 下一个即将消失：这是倒数第二个棋子（仅当 max_move > 5 时显示）
            is_next_fading = show_yellow_border and len(self.game.x) >= self.game.m - 1 and ti == 1

            # 绘制消失提示边框
            if is_fading:
                self._draw_fading_border(cell_x, cell_y, (239, 68, 68))  # 红色边框
            elif is_next_fading:
                self._draw_fading_border(cell_x, cell_y, (251, 191, 19))  # 黄色边框

            self.draw_piece(cell_x, cell_y, 1, age_factor, ti)

        # 绘制 O 的棋子
        for ti, (i, j) in enumerate(self.game.y):
            cell_x = board_x + i * self.cell_size
            cell_y = board_y + j * self.cell_size
            age_factor = (ti + 1) / min(len(self.game.y), self.game.m)

            # 检查是否即将消失
            is_fading = len(self.game.y) >= self.game.m and ti == 0
            is_next_fading = show_yellow_border and len(self.game.y) >= self.game.m - 1 and ti == 1

            # 绘制消失提示边框
            if is_fading:
                self._draw_fading_border(cell_x, cell_y, (239, 68, 68))  # 红色边框
            elif is_next_fading:
                self._draw_fading_border(cell_x, cell_y, (251, 191, 19))  # 黄色边框

            self.draw_piece(cell_x, cell_y, -1, age_factor, ti)

    def _draw_fading_border(self, x, y, color):
        """绘制虚线边框提示棋子即将消失"""
        rect = pygame.Rect(x + 2, y + 2, self.cell_size - 4, self.cell_size - 4)
        border_width = 3
        dash_length = 8

        # 绘制虚线边框
        for i in range(0, rect.width, dash_length * 2):
            # 上边
            if i + dash_length <= rect.width:
                pygame.draw.line(self.screen, color, (rect.left + i, rect.top), (rect.left + i + dash_length, rect.top), border_width)
            else:
                pygame.draw.line(self.screen, color, (rect.left + i, rect.top), (rect.right, rect.top), border_width)
            # 下边
            if i + dash_length <= rect.width:
                pygame.draw.line(self.screen, color, (rect.left + i, rect.bottom), (rect.left + i + dash_length, rect.bottom), border_width)
            else:
                pygame.draw.line(self.screen, color, (rect.left + i, rect.bottom), (rect.right, rect.bottom), border_width)

        for i in range(0, rect.height, dash_length * 2):
            # 左边
            if i + dash_length <= rect.height:
                pygame.draw.line(self.screen, color, (rect.left, rect.top + i), (rect.left, rect.top + i + dash_length), border_width)
            else:
                pygame.draw.line(self.screen, color, (rect.left, rect.top + i), (rect.left, rect.bottom), border_width)
            # 右边
            if i + dash_length <= rect.height:
                pygame.draw.line(self.screen, color, (rect.right, rect.top + i), (rect.right, rect.top + i + dash_length), border_width)
            else:
                pygame.draw.line(self.screen, color, (rect.right, rect.top + i), (rect.right, rect.bottom), border_width)

    def draw_piece(self, x, y, player, age_factor, ti):
        """根据当前样式绘制棋子"""
        style = self.piece_styles[self.current_piece_style]["type"]

        if style == "xo":
            self._draw_xo_style(x, y, player, age_factor)
        elif style == "go_classic":
            self._draw_go_classic(x, y, player, age_factor)
        elif style == "go_border":
            self._draw_go_border(x, y, player, age_factor)
        elif style == "gradient":
            self._draw_gradient_style(x, y, player, age_factor)
        else:
            self._draw_xo_style(x, y, player, age_factor)

    def _draw_xo_style(self, x, y, player, age_factor):
        """X/O 样式 - 添加透明度效果"""
        if player == 1:  # X
            r, g, b = self.xx_color
            r_, g_, b_ = self.xx_color_trc
            # 使用 age_factor 调整颜色强度
            base_intensity = 0.5 + 0.5 * age_factor
            piece_color = (int(r * base_intensity), int(g * base_intensity), int(b * base_intensity))

            # 根据年龄调整线宽
            line_width = max(2, int(5 * age_factor))

            pygame.draw.line(self.screen, piece_color,
                            (x + self.piece_gap, y + self.cell_size - self.piece_gap),
                            (x + self.cell_size - self.piece_gap, y + self.piece_gap), line_width)
            pygame.draw.line(self.screen, piece_color,
                            (x + self.piece_gap, y + self.piece_gap),
                            (x + self.cell_size - self.piece_gap, y + self.cell_size - self.piece_gap), line_width)
        else:  # O
            r, g, b = self.o_color
            r_, g_, b_ = self.o_color_trc
            base_intensity = 0.5 + 0.5 * age_factor
            piece_color = (int(r * base_intensity), int(g * base_intensity), int(b * base_intensity))
            center = (x + self.cell_size // 2, y + self.cell_size // 2)
            line_width = max(2, int(5 * age_factor))
            pygame.draw.circle(self.screen, piece_color, center, self.cell_size // 2 - self.piece_gap, line_width)

    def _draw_go_classic(self, x, y, player, age_factor):
        """围棋黑白棋样式 - 添加透明度效果 (100% -> 20% 平滑过渡)"""
        center = (x + self.cell_size // 2, y + self.cell_size // 2)
        radius = (self.cell_size // 2) - 4

        # 创建带 alpha 通道的表面
        piece_surface = pygame.Surface((self.cell_size, self.cell_size), pygame.SRCALPHA)
        local_center = (self.cell_size // 2, self.cell_size // 2)

        # 根据年龄计算透明度：100% -> 20% 平滑过渡
        # 新棋子 alpha=255，最老棋子 alpha=51 (20%)
        alpha = int(51 + 204 * age_factor)

        if player == 1:  # X - 黑棋
            # 主体
            pygame.draw.circle(piece_surface, (20, 20, 20, alpha), local_center, radius)
            # 高光
            if alpha > 50:
                highlight_alpha = min(255, alpha + 30)
                pygame.draw.circle(piece_surface, (80, 80, 80, highlight_alpha),
                                (local_center[0] - radius // 4, local_center[1] - radius // 4), radius // 3)
        else:  # O - 白棋
            # 主体
            pygame.draw.circle(piece_surface, (245, 245, 245, alpha), local_center, radius)
            # 阴影效果
            if alpha > 50:
                shadow_alpha = min(255, int(alpha * 0.8))
                pygame.draw.circle(piece_surface, (200, 200, 200, shadow_alpha), local_center, radius, 2)

        self.screen.blit(piece_surface, (x, y))

    def _draw_go_border(self, x, y, player, age_factor):
        """带边框的围棋样式 - 添加透明度效果 (100% -> 20% 平滑过渡)"""
        center = (x + self.cell_size // 2, y + self.cell_size // 2)
        radius = (self.cell_size // 2) - 5

        # 创建带 alpha 通道的表面
        piece_surface = pygame.Surface((self.cell_size, self.cell_size), pygame.SRCALPHA)
        local_center = (self.cell_size // 2, self.cell_size // 2)

        # 根据年龄计算透明度：100% -> 20%
        alpha = int(51 + 204 * age_factor)

        if player == 1:  # X - 黑棋
            # 主体
            pygame.draw.circle(piece_surface, (25, 25, 25, alpha), local_center, radius)
            # 边框
            if alpha > 30:
                pygame.draw.circle(piece_surface, (0, 0, 0, alpha), local_center, radius, 2)
                # 高光
                pygame.draw.circle(piece_surface, (60, 60, 60, min(255, alpha + 20)),
                                (local_center[0] - radius // 3, local_center[1] - radius // 3), radius // 4)
        else:  # O - 白棋
            # 主体
            pygame.draw.circle(piece_surface, (250, 250, 250, alpha), local_center, radius)
            # 边框
            if alpha > 30:
                pygame.draw.circle(piece_surface, (180, 180, 180, alpha), local_center, radius, 2)
                # 阴影
                pygame.draw.circle(piece_surface, (200, 200, 200, min(255, int(alpha * 0.7))),
                                (local_center[0] + radius // 4, local_center[1] + radius // 4), radius // 4)

        self.screen.blit(piece_surface, (x, y))

    def _draw_gradient_style(self, x, y, player, age_factor):
        """渐变样式 - 添加透明度效果 (100% -> 20% 平滑过渡)"""
        center = (x + self.cell_size // 2, y + self.cell_size // 2)
        radius = (self.cell_size // 2) - 4

        # 创建带 alpha 通道的表面
        piece_surface = pygame.Surface((self.cell_size, self.cell_size), pygame.SRCALPHA)
        local_center = (self.cell_size // 2, self.cell_size // 2)

        # 根据年龄计算透明度：100% -> 20%
        alpha = int(51 + 204 * age_factor)

        if player == 1:  # X
            # 渐变红色
            base_color = (220, 50, 50, alpha)
            gradient_color = (255, 100, 100, min(255, int(alpha * 0.8)))
        else:  # O
            # 渐变蓝色
            base_color = (40, 100, 200, alpha)
            gradient_color = (100, 160, 255, min(255, int(alpha * 0.8)))

        # 绘制渐变圆
        pygame.draw.circle(piece_surface, base_color, local_center, radius)
        pygame.draw.circle(piece_surface, gradient_color,
                          (local_center[0] - radius // 3, local_center[1] - radius // 3), radius // 2)

        self.screen.blit(piece_surface, (x, y))

    def draw_status_bar(self):
        """绘制状态栏"""
        if not self.game_on:
            return

        font = self.font_cache.get_font_large()

        # 计算当前轮次和回合
        round_num = len(self.game.history) // 2 + 1
        current_turn = len(self.game.history) % 2  # 0 = X, 1 = O

        # 确定回合文本
        if self.play_mode == "pvp":
            # PvP 模式
            if current_turn == 0:
                turn_text = "X' Turn"
                turn_color = self.xx_color
            else:
                turn_text = "O' Turn"
                turn_color = self.o_color
            vs_text = "vs Player"
        else:
            # PvAI 模式
            if current_turn == self.play:
                turn_text = "AI's Turn"
                turn_color = self.o_color if self.play == 1 else self.xx_color
            else:
                turn_text = "Your Turn"
                turn_color = (34, 197, 94)
            vs_text = f"vs {self.strategy.name}"

        symbol = "X" if current_turn == 0 else "O"
        status_text = f"Round {round_num} | {turn_text} ({symbol}) | {vs_text}"

        # 绘制状态栏
        text_surface = font.render(status_text, True, (51, 65, 85))
        text_width = text_surface.get_width()
        text_height = text_surface.get_height()

        # 背景矩形
        bg_padding = 15
        board_center_x = self.board_offset_x + (self.grid * self.cell_size) // 2
        bg_x = board_center_x - (text_width + bg_padding * 2) // 2
        # 状态栏放在棋盘下方 + 10px 的间距
        board_bottom = self.board_offset_y + self.grid * self.cell_size
        bg_y = board_bottom + 10
        bg_rect = pygame.Rect(bg_x, bg_y, text_width + bg_padding * 2, text_height + 10)

        # 半透明背景
        bg_surface = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(bg_surface, (255, 255, 255, 200), bg_surface.get_rect(), border_radius=8)
        self.screen.blit(bg_surface, bg_rect, special_flags=pygame.BLEND_ALPHA_SDL2)

        # 边框
        pygame.draw.rect(self.screen, turn_color, bg_rect, width=2, border_radius=8)

        # 文本
        text_x = board_center_x - text_width // 2
        text_y = bg_y + 5
        self.screen.blit(text_surface, (text_x, text_y))

    def draw_result(self):
        """绘制游戏结果"""
        if self.result == 0:
            return

        font_large = pygame.font.Font(None, 60)
        if self.result == 1:
            text = "X win"
            text_color = self.xx_color
        else:
            text = "O win"
            text_color = self.o_color

        # 位置在棋盘中央
        board_center_x = self.board_offset_x + (self.grid * self.cell_size) // 2
        board_center_y = self.board_offset_y + (self.grid * self.cell_size) // 2

        # 绘制结果文本
        text_surface = font_large.render(text, True, text_color)
        text_x = board_center_x - text_surface.get_width() // 2
        text_y = board_center_y - text_surface.get_height() // 2

        # 背景
        bg_padding = 30
        bg_rect = pygame.Rect(text_x - bg_padding, text_y - bg_padding // 2,
                             text_surface.get_width() + bg_padding * 2,
                             text_surface.get_height() + bg_padding)
        bg_surface = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(bg_surface, (255, 255, 255, 230), bg_surface.get_rect(), border_radius=15)
        self.screen.blit(bg_surface, bg_rect)

        # 阴影
        shadow_surface = font_large.render(text, True, (0, 0, 0, 60))
        self.screen.blit(shadow_surface, (text_x + 3, text_y + 3))

        # 主文本
        self.screen.blit(text_surface, (text_x, text_y))

    def draw_control_buttons(self):
        """绘制控制按钮"""
        font = self.font_cache.get_font_button()

        # PvAI 模式 - Play X 和 Play O 按钮
        if self.play_mode == "pvai":
            if hasattr(self, 'play_x_button'):
                self.play_x_button.draw(self.screen, self.font_cache,
                                      self.button_primary, self.button_primary_hover,
                                      self.button_secondary, self.button_secondary_hover,
                                      self.text_color)
            if hasattr(self, 'play_o_button'):
                self.play_o_button.draw(self.screen, self.font_cache,
                                      self.button_primary, self.button_primary_hover,
                                      self.button_secondary, self.button_secondary_hover,
                                      self.text_color)

        # Reset 按钮
        self.reset_button.draw(self.screen, self.font_cache,
                             self.button_warning, self.button_warning_hover,
                              self.button_secondary, self.button_secondary_hover,
                              self.text_color)

    def draw(self):
        """主绘制方法"""
        self.draw_gradient_background()
        self.draw_sidebar()
        self.draw_board()
        self.draw_pieces()
        self.draw_status_bar()
        self.draw_control_buttons()
        self.draw_result()

        # 绘制打开的下拉菜单选项（在最上层）
        dropdown_bg = (255, 255, 255)
        dropdown_hover = (248, 250, 252)

        self.board_size_dropdown.draw_dropdown(self.screen, self.font_cache, dropdown_bg, dropdown_hover, self.sidebar_text_color)
        self.max_move_dropdown.draw_dropdown(self.screen, self.font_cache, dropdown_bg, dropdown_hover, self.sidebar_text_color)
        self.win_count_dropdown.draw_dropdown(self.screen, self.font_cache, dropdown_bg, dropdown_hover, self.sidebar_text_color)
        self.piece_style_dropdown.draw_dropdown(self.screen, self.font_cache, dropdown_bg, dropdown_hover, self.sidebar_text_color)
        self.strategy_dropdown.draw_dropdown(self.screen, self.font_cache, dropdown_bg, dropdown_hover, self.sidebar_text_color)

        # 检查游戏是否结束
        if self.game_on:
            self.result = self.game.get_result()
            if self.result != 0:
                self.game_on = False

    # ==================== 事件处理 ====================

    def handle_events(self, event):
        if event.type == pygame.QUIT:
            sys.exit()

        # 处理鼠标移动
        if event.type == pygame.MOUSEMOTION:
            self._handle_mouse_motion(event)

        # 处理鼠标点击
        if event.type == pygame.MOUSEBUTTONDOWN:
            self._handle_mouse_click(event)

    def _handle_mouse_motion(self, event):
        mouse_pos = pygame.mouse.get_pos()

        # 更新按钮悬停状态
        self.pvp_button.handle_event(event)
        self.pvai_button.handle_event(event)
        self.reset_button.handle_event(event)

        if self.play_mode == "pvai":
            if hasattr(self, 'play_x_button'):
                self.play_x_button.handle_event(event)
            if hasattr(self, 'play_o_button'):
                self.play_o_button.handle_event(event)

        # 检查格子悬停
        if self.game_on:
            board_x = self.board_offset_x
            board_y = self.board_offset_y
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

    def _close_other_dropdowns(self, except_name):
        """关闭除指定外的所有下拉菜单"""
        dropdowns = {
            'board_size': self.board_size_dropdown,
            'max_move': self.max_move_dropdown,
            'win_count': self.win_count_dropdown,
            'piece_style': self.piece_style_dropdown,
            'strategy': self.strategy_dropdown
        }
        for name, dd in dropdowns.items():
            if name != except_name:
                dd.is_open = False

    def _handle_mouse_click(self, event):
        mouse_pos = pygame.mouse.get_pos()

        # 保存之前每个下拉菜单的打开状态
        was_open = {
            'board_size': self.board_size_dropdown.is_open,
            'max_move': self.max_move_dropdown.is_open,
            'win_count': self.win_count_dropdown.is_open,
            'piece_style': self.piece_style_dropdown.is_open,
            'strategy': self.strategy_dropdown.is_open
        }

        # 处理下拉菜单
        dropdown_handled = False
        if self.board_size_dropdown.handle_event(event):
            dropdown_handled = True
            new_size = self.board_size_dropdown.get_selected_value()
            if new_size != self.current_board_size:
                self.current_board_size = new_size
                self._init_game()
                self._init_ui_components()
            else:
                self._close_other_dropdowns('board_size')

        elif self.max_move_dropdown.handle_event(event):
            dropdown_handled = True
            new_max = self.max_move_dropdown.get_selected_value()
            if new_max != self.current_max_move:
                self.current_max_move = new_max
                self._init_game()
            else:
                self._close_other_dropdowns('max_move')

        elif self.win_count_dropdown.handle_event(event):
            dropdown_handled = True
            new_win = self.win_count_dropdown.get_selected_value()
            if new_win != self.current_win_count:
                self.current_win_count = new_win
                self._init_game()
            else:
                self._close_other_dropdowns('win_count')

        elif self.piece_style_dropdown.handle_event(event):
            dropdown_handled = True
            self.current_piece_style = self.piece_style_dropdown.get_selected_value()
            self._close_other_dropdowns('piece_style')

        elif self.strategy_dropdown.handle_event(event):
            dropdown_handled = True
            self.current_strategy_index = self.strategy_dropdown.get_selected_value()
            self.strategy = self.available_strategies[self.current_strategy_index]["instance"]
            self._close_other_dropdowns('strategy')

        else:
            # 没有点击任何下拉菜单，关闭所有
            if any(was_open.values()):
                self.board_size_dropdown.is_open = False
                self.max_move_dropdown.is_open = False
                self.win_count_dropdown.is_open = False
                self.piece_style_dropdown.is_open = False
                self.strategy_dropdown.is_open = False

        # 处理对战模式按钮
        if self.pvp_button.handle_event(event):
            self.play_mode = "pvp"
            self._init_ui_components()
            # PvP 模式自动开始
            self.result = 0
            self.game.reset()
            self.play = -1  # PvP 不需要 play 变量
            self.game_on = True  # 直接开始游戏
            self.draw()

        if self.pvai_button.handle_event(event):
            self.play_mode = "pvai"
            self._init_ui_components()
            # PvAI 模式需要玩家选择执 X 或 O
            self.game_on = False
            self.play = -1
            self.result = 0
            self.game.reset()
            self.draw()

        # 处理开始/重置按钮
        if self.reset_button.handle_event(event):
            self.start_game(-1)

        if self.play_mode == "pvai":
            if hasattr(self, 'play_x_button') and self.play_x_button.handle_event(event):
                self.start_game(0)
            if hasattr(self, 'play_o_button') and self.play_o_button.handle_event(event):
                self.start_game(1)

        # 处理棋盘点击
        if self.game_on and event.button == 1:  # 左键
            board_x = self.board_offset_x
            board_y = self.board_offset_y
            cell_x = mouse_pos[0] - board_x
            cell_y = mouse_pos[1] - board_y

            if 0 <= cell_x < self.grid * self.cell_size and 0 <= cell_y < self.grid * self.cell_size:
                i = int(cell_x // self.cell_size)
                j = int(cell_y // self.cell_size)

                if self.game.board[i][j] == 0:
                    # 在落子前判断是否是玩家回合
                    if self.play_mode == "pvai" and self._is_ai_turn():
                        # AI回合，玩家不能落子
                        return

                    self.game.play(i, j)
                    self.draw()

                    # 检查游戏是否结束
                    self.result = self.game.get_result()
                    if self.result != 0:
                        self.game_on = False
                        self.draw()
                        return

                    # PvAI 模式，让AI走棋
                    if self.play_mode == "pvai":
                        # AI回合
                        if self.strategy.make_move():
                            self.draw()
                            # 检查 AI 是否获胜
                            self.result = self.game.get_result()
                            if self.result != 0:
                                self.game_on = False
                                self.draw()

    def _is_ai_turn(self):
        """判断当前是否是 AI 回合"""
        if self.play_mode != "pvai" or self.play == -1:
            return False

        # 当前该谁走（0=X，1=O）
        current_player = len(self.game.history) % 2

        # AI执另一方棋子
        # 如果玩家执X(0)，AI执O(1)，AI在O回合走(current_player == 1)
        # 如果玩家执O(1)，AI执X(0)，AI在X回合走(current_player == 0)
        ai_player = 1 - self.play

        return current_player == ai_player

    def start_game(self, player):
        """开始或重置游戏"""
        self.result = 0
        self.game.reset()
        self.play = player

        if player == -1:
            # 重置按钮
            if self.play_mode == "pvp":
                # PvP模式重置后应该仍然可以继续游戏
                self.game_on = True
            else:
                # PvAI模式重置后需要重新选择执棋方
                self.game_on = False
        elif self.play_mode == "pvp":
            # PvP 模式 - 直接开始
            self.game_on = True
        else:
            # PvAI 模式开始
            self.game_on = True

            # AI先手的情况：玩家执O（player == 1）时，AI执X先手
            if self.play_mode == "pvai" and player == 1:
                # AI 先手（X）
                if not self.strategy.make_move():
                    # AI 不可用，切换到 PvP 模式
                    self.play_mode = "pvp"
                    self._init_ui_components()
                    print("AI not available for this configuration, switching to PvP mode")

        self.draw()

    def run(self):
        """运行主循环"""
        while True:
            for event in pygame.event.get():
                self.handle_events(event)
            self.draw()
            pygame.display.flip()


# ==================== 主程序入口 ====================

if __name__ == "__main__":
    game_ui = GameUI()
    game_ui.run()
