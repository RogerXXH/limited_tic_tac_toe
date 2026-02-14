import math

class DynamicPatternDetector:
    """动态模式检测器，适应不同的win_count(K)"""

    def __init__(self, win_count):
        self.K = win_count  # 胜利所需连线长度

    def detect_threats(self, board, player):
        """检测所有威胁级别

        Args:
            board: 二维数组棋盘
            player: 当前玩家 (1=X, -1=O)

        Returns:
            包含各级别威胁的字典
        """
        threats = {
            'immediate_win': [],      # 下一步就能赢
            'one_move_threat': [],    # 再一步能赢
            'building_threat': [],    # 正在构建的威胁
            'potential_threat': []    # 潜在威胁
        }

        # 根据K值动态检测不同长度的模式
        for length in range(1, self.K):
            pattern_type = self._classify_pattern_length(length)

            # 查找所有可能形成length连线的位置序列
            lines = self._find_all_lines(board, length)

            for line in lines:
                if self._is_potential_threat(board, line, player):
                    pattern = {
                        'positions': line,
                        'length': length,
                        'type': pattern_type,
                        'age_info': self._get_age_info(board, line, player)
                    }
                    threats[pattern_type].append(pattern)

        return threats

    def _classify_pattern_length(self, length):
        """根据当前长度和K值分类威胁级别"""
        if length == self.K - 1:
            return 'immediate_win'      # 差一个就胜利
        elif length == self.K - 2:
            return 'one_move_threat'    # 差两个
        elif length >= self.K - 3:
            return 'building_threat'    # 正在构建
        else:
            return 'potential_threat'   # 潜在威胁

    def _find_all_lines(self, board, length):
        """查找所有可能形成length连线的位置序列"""
        lines = []
        n = len(board)

        # 横线
        for i in range(n):
            for j in range(n - length + 1):
                line = [(i, j+k) for k in range(length)]
                lines.append(line)

        # 竖线
        for i in range(n - length + 1):
            for j in range(n):
                line = [(i+k, j) for k in range(length)]
                lines.append(line)

        # 对角线（主对角线）
        for i in range(n - length + 1):
            for j in range(n - length + 1):
                line = [(i+k, j+k) for k in range(length)]
                lines.append(line)

        # 反对角线
        for i in range(n - length + 1):
            for j in range(length - 1, n):
                line = [(i+k, j-k) for k in range(length)]
                lines.append(line)

        return lines

    def _is_potential_threat(self, board, line, player):
        """判断一条线是否可能形成威胁"""
        player_count = 0
        opponent_count = 0
        empty_count = 0

        for (i, j) in line:
            if board[i][j] == player:
                player_count += 1
            elif board[i][j] == -player:
                opponent_count += 1
            else:
                empty_count += 1

        # 对手棋子不能存在
        if opponent_count > 0:
            return False

        # 至少有玩家棋子，并且有足够的空位可以完成连线
        if player_count > 0 and player_count + empty_count >= self.K:
            return True

        return False

    def _get_age_info(self, board, line, player):
        """获取棋子年龄信息"""
        ages = []
        for (i, j) in line:
            if board[i][j] == player:
                # 这里需要从游戏中获取棋子年龄信息
                # 暂时返回占位值
                ages.append(0)
            else:
                ages.append(-1)  # 空位
        return ages


class AdaptiveWeightCalculator:
    """自适应权重计算器，根据K和M调整权重"""

    def __init__(self, win_count, max_move):
        self.K = win_count
        self.M = max_move

    def calculate_weights(self):
        """根据K和M计算动态权重

        Returns:
            按长度索引的权重字典
        """
        weights = {}

        for length in range(1, self.K):
            # 基础权重：越接近K，权重越高
            if length == self.K - 1:
                base_weight = 100.0  # 差一步胜利
            elif length == self.K - 2:
                base_weight = 30.0   # 差两步胜利
            elif length >= self.K - 3:
                base_weight = 10.0   # 构建中的威胁
            else:
                base_weight = 1.0    # 潜在威胁

            # 时间因子调整：M越小，短期威胁越重要
            time_factor = self._calculate_time_factor(length)

            weights[length] = base_weight * time_factor

        return weights

    def _calculate_time_factor(self, length):
        """根据max_move计算时间衰减因子"""
        # M越小，短期威胁越重要
        if self.M <= 3:
            # 短期导向：新威胁权重高，旧威胁权重低
            return max(0.1, 1.0 - (length / self.K) * 0.8)
        elif self.M <= 8:
            # 平衡：中等时间视野
            return 0.5 + 0.5 * (1.0 - length / self.K)
        else:
            # 长期导向：新旧威胁差异不大
            return 0.8 + 0.2 * (1.0 - length / self.K)


class UniversalEvaluator:
    """通用评估器，整合所有评估因素"""

    def __init__(self, game):
        self.game = game
        self.K = game.win_count
        self.M = game.m
        self.detector = DynamicPatternDetector(self.K)
        self.weights = AdaptiveWeightCalculator(self.K, self.M).calculate_weights()

        # 基础评分表
        self.base_scores = {
            'immediate_win': 10000,
            'one_move_threat': 5000,
            'building_threat': 1000,
            'potential_threat': 100
        }

    def evaluate_position(self, player):
        """评估当前局面得分

        Args:
            player: 要评估的玩家 (1=X, -1=O)

        Returns:
            局面评估分数
        """
        score = 0

        # 1. 威胁评估
        threats = self.detector.detect_threats(self.game.board, player)
        opponent_threats = self.detector.detect_threats(self.game.board, -player)

        # 进攻得分
        for threat_type, patterns in threats.items():
            for pattern in patterns:
                score += self._score_pattern(pattern, threat_type, is_attack=True)

        # 防守得分（阻止对手）
        for threat_type, patterns in opponent_threats.items():
            for pattern in patterns:
                score += self._score_pattern(pattern, threat_type, is_attack=False)

        # 2. 位置控制得分
        score += self._evaluate_position_control(player)

        # 3. 时间线调整（考虑棋子消失）
        score = self._adjust_for_fading_timeline(score)

        return score

    def _score_pattern(self, pattern, threat_type, is_attack):
        """评分单个模式"""
        base_score = self.base_scores.get(threat_type, 0)

        # 根据模式长度调整
        length = pattern['length']
        length_factor = self.weights.get(length, 1.0)

        # 进攻/防守调整
        attack_factor = 1.2 if is_attack else 1.0

        # 棋子年龄调整（考虑棋子消失）
        age_factor = self._calculate_age_factor(pattern['age_info'])

        return base_score * length_factor * attack_factor * age_factor

    def _evaluate_position_control(self, player):
        """评估位置控制得分"""
        score = 0
        n = self.game.n

        # 棋盘价值分布：中心价值高
        for i in range(n):
            for j in range(n):
                if self.game.board[i][j] == 0:
                    # 位置基础价值：距离中心越近，价值越高

                    center_dist = math.sqrt(((i - n/2) ** 2 + (j - n/2) ** 2))
                    position_value = 1.0 / (1.0 + center_dist)

                    # 周围威胁密度

                    threat_density = self._calculate_threat_density(i, j, player)

                    score += position_value * threat_density * 10

        return score

    def _calculate_threat_density(self, i, j, player):
        """计算位置周围的威胁密度"""
        density = 0
        radius = 2  # 搜索半径

        for di in range(-radius, radius+1):
            for dj in range(-radius, radius+1):
                ni, nj = i + di, j + dj
                if 0 <= ni < self.game.n and 0 <= nj < self.game.n:
                    if self.game.board[ni][nj] == player:
                        # 距离越近，权重越高

                        dist = math.sqrt(di*di + dj*dj)
                        density += 1.0 / (1.0 + dist)

        return density

    def _calculate_age_factor(self, age_info):
        """根据棋子年龄计算调整因子

        新棋子权重高，即将消失的棋子权重低

        """

        if not age_info or all(age == -1 for age in age_info):
            return 1.0  # 全是空位

        # 计算有效棋子的平均年龄

        valid_ages = [age for age in age_info if age != -1]

        if not valid_ages:

            return 1.0

        avg_age = sum(valid_ages) / len(valid_ages)


        # 年龄因子：年龄越小（越新），因子越大

        if self.M > 0:

            age_ratio = avg_age / self.M

            # 指数衰减：新棋子权重高，旧棋子权重低

            return math.exp(-2 * age_ratio)

        return 1.0

    def _adjust_for_fading_timeline(self, score):
        """根据棋子消失时间线调整分数

        考虑即将消失的棋子的战略价值变化

        """

        # 暂时简单实现

        # 获取即将消失的棋子信息（从游戏状态）

        # 这里需要从self.game中获取相关信息

        # 暂时返回原分数

        return score

    def _check_win_at_position(self, board, player, i, j):
        """检查在位置(i,j)落子后，玩家是否获胜

        Args:
            board: 棋盘状态
            player: 玩家 (1=X, -1=O)
            i, j: 落子位置

        Returns:
            True如果获胜，否则False
        """
        n = len(board)
        K = self.game.win_count

        # 临时创建模拟棋盘
        sim_board = [row[:] for row in board]
        sim_board[i][j] = player

        # 检查所有方向
        directions = [
            [(0, 1), (0, -1)],  # 水平
            [(1, 0), (-1, 0)],  # 垂直
            [(1, 1), (-1, -1)], # 主对角线
            [(1, -1), (-1, 1)]  # 反对角线
        ]

        for dir_pair in directions:
            total_length = 1  # 当前落子
            for (di, dj) in dir_pair:
                length_in_dir = 0
                ni, nj = i + di, j + dj
                while 0 <= ni < n and 0 <= nj < n and sim_board[ni][nj] == player:
                    length_in_dir += 1
                    ni += di
                    nj += dj
                total_length += length_in_dir

            if total_length >= K:
                return True

        return False

    def evaluate_move_score(self, board, player, move_i, move_j):
        """评估落子位置的综合得分（进攻+防守）

        Args:
            board: 当前棋盘状态（二维数组）
            player: 要评估的玩家 (1=X, -1=O)
            move_i, move_j: 落子位置

        Returns:
            综合得分
        """
        n = len(board)
        opponent = -player

        # 1. 紧急情况检查：如果自己能立即获胜，直接给最高分
        if self._check_win_at_position(board, player, move_i, move_j):
            return 100000  # 立即获胜，最高优先级

        # 2. 防守紧急情况：如果对手在此位置落子能立即获胜，给予极高防守分
        if self._check_win_at_position(board, opponent, move_i, move_j):
            # 防守立即获胜威胁，优先级仅次于自己立即获胜
            defensive_score = 50000
        else:
            # 3. 常规防守得分：评估对手在此位置落子后的威胁潜力
            sim_board_opp = [row[:] for row in board]  # 深拷贝
            sim_board_opp[move_i][move_j] = opponent
            defensive_threat = self._evaluate_board_score(sim_board_opp, opponent)

            # 动态防守权重：根据威胁级别调整
            if defensive_threat > 5000:
                defensive_weight = 1.5  # 紧急防守
            elif defensive_threat > 1000:
                defensive_weight = 1.2  # 重要防守
            else:
                defensive_weight = 0.8  # 常规防守

            defensive_score = defensive_threat * defensive_weight

        # 4. 常规进攻得分
        sim_board_ai = [row[:] for row in board]  # 深拷贝
        sim_board_ai[move_i][move_j] = player
        offensive_score = self._evaluate_board_score(sim_board_ai, player)

        # 5. 位置控制得分（中心价值）
        center_dist = math.sqrt(((move_i - n/2) ** 2 + (move_j - n/2) ** 2))
        position_value = 10.0 / (1.0 + center_dist)
        position_score = position_value * 100

        # 6. 综合得分：进攻 + 防守 + 位置
        total_score = offensive_score + defensive_score + position_score


        return total_score

    def _evaluate_board_score(self, board, player):
        """评估指定棋盘状态对指定玩家的得分

        Args:
            board: 棋盘状态（二维数组）
            player: 要评估的玩家 (1=X, -1=O)

        Returns:
            评估得分
        """
        score = 0

        # 使用detector检测威胁
        threats = self.detector.detect_threats(board, player)
        opponent_threats = self.detector.detect_threats(board, -player)

        # 进攻得分（己方威胁）
        for threat_type, patterns in threats.items():
            for pattern in patterns:
                score += self._score_pattern(pattern, threat_type, is_attack=True)

        # 防守得分（对手威胁）
        for threat_type, patterns in opponent_threats.items():
            for pattern in patterns:
                score += self._score_pattern(pattern, threat_type, is_attack=False)

        # 位置控制得分（简化版本）
        n = len(board)
        position_score = 0
        for i in range(n):
            for j in range(n):
                if board[i][j] == player:
                    # 中心价值
                    center_dist = math.sqrt(((i - n/2) ** 2 + (j - n/2) ** 2))
                    position_value = 1.0 / (1.0 + center_dist)
                    position_score += position_value * 10

        score += position_score

        return score


class Strategy:
    """启发式AI策略"""

    def __init__(self, game):
        self.name = "Heuristic AI"
        self.game = game
        self.evaluator = UniversalEvaluator(game)

    def make_move(self):
        """执行AI落子"""
        # 确定当前该谁下棋
        # 0 = X的回合，1 = O的回合
        current_turn = len(self.game.history) % 2
        ai_player = 1 if current_turn == 0 else -1  # X=1, O=-1

        best_score = -float('inf')
        best_move = None

        # 获取当前棋盘状态
        n = self.game.n
        current_board = self.game.board  # 直接引用，evaluate_move_score会深拷贝

        # 评估所有空位
        for i in range(n):
            for j in range(n):
                if current_board[i][j] == 0:
                    # 使用UniversalEvaluator评估落子位置的综合得分
                    score = self.evaluator.evaluate_move_score(
                        current_board, ai_player, i, j
                    )

                    if score > best_score:
                        best_score = score
                        best_move = (i, j)

        # 执行最佳落子
        if best_move:
            i, j = best_move
            self.game.play(i, j)
            return True

        return False

    def _evaluate_position_score(self, board, player, move_i, move_j):
        """评估落子位置得分"""

        score = 0

        # 1. 威胁检测得分

        n = len(board)

        K = self.game.win_count  # 胜利所需连线数

        # 检查所有方向（横、竖、斜）的连线潜力

        directions = [

            [(0, 1), (0, -1)],  # 水平

            [(1, 0), (-1, 0)],  # 垂直

            [(1, 1), (-1, -1)], # 主对角线

            [(1, -1), (-1,1)]  # 反对角线

        ]



        for dir_pair in directions:

            # 计算在这个方向上的连线长度

            total_length = 1  # 当前落子

            for (di, dj) in dir_pair:

                length_in_dir = 0

                ni, nj = move_i + di, move_j + dj

                while 0 <= ni < n and 0 <= nj < n and board[ni][nj] == player:

                    length_in_dir += 1

                    ni += di

                    nj += dj



                total_length += length_in_dir



            # 根据总长度评分

            if total_length >= K:

                # 立即获胜

                score += 10000

            elif total_length == K - 1:

                # 差一步胜利

                score += 5000

            elif total_length >= K - 2:

                # 构建中的威胁

                score += 1000

            else:

                # 潜在威胁

                score += 100 * total_length



        # 2. 位置控制得分（中心价值）

        center_dist = math.sqrt(((move_i - n/2) ** 2 + (move_j - n/2) ** 2))

        position_value = 10.0 / (1.0 + center_dist)

        score += position_value * 100



        # 3. 棋子年龄考虑（如果知道棋子年龄）

        # 这里需要从游戏状态获取棋子年龄信息

        # 暂时简化处理

        score *= 1.0  # 暂时不调整



        return score