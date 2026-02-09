from collections import deque
import os
import struct
import inspect

class SymmetryHelper:
    """处理3×3棋盘的对称性"""

    def __init__(self):
        # 8种对称变换的位置映射
        self.transforms = [
            [0, 1, 2, 3, 4, 5, 6, 7, 8],  # 0: 恒等
            [6, 3, 0, 7, 4, 1, 8, 5, 2],  # 1: 逆时针90°
            [8, 7, 6, 5, 4, 3, 2, 1, 0],  # 2: 180°
            [2, 5, 8, 1, 4, 7, 0, 3, 6],  # 3: 顺时针90°
            [2, 1, 0, 5, 4, 3, 8, 7, 6],  # 4: 水平翻转
            [6, 7, 8, 3, 4, 5, 0, 1, 2],  # 5: 垂直翻转
            [0, 3, 6, 1, 4, 7, 2, 5, 8],  # 6: 主对角线翻转
            [8, 5, 2, 7, 4, 1, 6, 3, 0],  # 7: 副对角线翻转
        ]

        # 预计算逆变换
        self.inv_transforms = []
        for trans in self.transforms:
            inv = [0] * 9
            for i in range(9):
                inv[trans[i]] = i
            self.inv_transforms.append(inv)

    def apply_transform(self, positions, trans_id):
        """应用变换，保持时间顺序"""
        trans = self.transforms[trans_id]
        return [trans[p] for p in positions]

    def encode(self, x_list, y_list):
        """编码状态（基数9）"""
        x_code = sum(pos * (9 ** i) for i, pos in enumerate(x_list))
        y_code = sum(pos * (9 ** i) for i, pos in enumerate(y_list))
        return x_code * 729 + y_code

    def canonicalize(self, x_list, y_list):
        """
        返回标准型
        Returns: (x_canon, y_canon, trans_id, canon_code)
        """
        min_code = None
        best_trans = 0
        best_x = None
        best_y = None

        for trans_id in range(8):
            x_trans = self.apply_transform(x_list, trans_id)
            y_trans = self.apply_transform(y_list, trans_id)
            code = self.encode(x_trans, y_trans)

            if min_code is None or code < min_code:
                min_code = code
                best_trans = trans_id
                best_x = x_trans
                best_y = y_trans

        return best_x, best_y, best_trans, min_code

    def inverse_transform(self, position, trans_id):
        """逆变换单个位置"""
        return self.inv_transforms[trans_id][position]


class DG:
    """使用字典存储的博弈图求解器"""

    def __init__(self):
        self.edge0 = {}  # state -> [next_states]
        self.edge1 = {}
        self.win = set()
        self.lose = set()
        self.dp = {}     # state -> [dp0, dp1]
        self.depth = {}  # state -> [depth0, depth1]

    def add_state(self, state):
        """添加状态"""
        if state not in self.edge0:
            self.edge0[state] = []
            self.edge1[state] = []
            self.dp[state] = [0, 0]
            self.depth[state] = [0, 0]

    def add_edge(self, from_state, to_state, player):
        """添加边"""
        self.add_state(from_state)
        self.add_state(to_state)
        if player == 0:
            self.edge0[from_state].append(to_state)
        else:
            self.edge1[from_state].append(to_state)

    def set_win(self, win):
        self.win = set(win)
        for s in win:
            self.add_state(s)
            self.dp[s] = [1, 1]

    def set_lose(self, lose):
        self.lose = set(lose)
        for s in lose:
            self.add_state(s)
            self.dp[s] = [-1, -1]

    def solve(self):
        """博弈树求解"""
        # 反向边
        edge0_ = {s: [] for s in self.edge0}
        edge1_ = {s: [] for s in self.edge1}
        for s in self.edge0:
            for t in self.edge0[s]:
                edge0_[t].append(s)
            for t in self.edge1[s]:
                edge1_[t].append(s)

        need = {s: [len(self.edge0[s]), len(self.edge1[s])] for s in self.edge0}

        # BFS求解必胜态
        deq = deque(self.win)
        while deq:
            x = deq.popleft()
            for y in edge0_[x]:
                if self.dp[y][0] == 1:
                    continue
                self.dp[y][0] = 1
                self.depth[y][0] = self.depth[x][1] + 1
                for z in edge1_[y]:
                    need[z][1] -= 1
                    if need[z][1] == 0:
                        deq.append(z)
                        self.dp[z][1] = 1
                        self.depth[z][1] = self.depth[y][0] + 1

        # BFS求解必败态
        deq = deque(self.lose)
        while deq:
            x = deq.popleft()
            for y in edge1_[x]:
                if self.dp[y][1] == -1:
                    continue
                self.dp[y][1] = -1
                self.depth[y][1] = self.depth[x][0] + 1
                for z in edge0_[y]:
                    need[z][0] -= 1
                    if need[z][0] == 0:
                        deq.append(z)
                        self.dp[z][0] = -1
                        self.depth[z][0] = self.depth[y][1] + 1

    def save_training_data(self, filename='DG.train'):
        """保存为紧凑二进制格式"""
        with open(filename, 'wb') as f:
            # 写入状态数量
            n = len(self.dp)
            f.write(struct.pack('I', n))

            # 写入每个状态: code(8字节) + dp0(1字节) + dp1(1字节) + depth0(2字节) + depth1(2字节)
            for state in sorted(self.dp.keys()):
                f.write(struct.pack('Q', state))  # 8 bytes: state code
                f.write(struct.pack('b', self.dp[state][0]))      # 1 byte: dp0
                f.write(struct.pack('b', self.dp[state][1]))      # 1 byte: dp1
                f.write(struct.pack('H', self.depth[state][0]))   # 2 bytes: depth0
                f.write(struct.pack('H', self.depth[state][1]))   # 2 bytes: depth1

    def load_training_data(self, filename='DG.train'):
        """加载二进制格式"""
        with open(filename, 'rb') as f:
            # 读取状态数量
            n = struct.unpack('I', f.read(4))[0]

            # 读取每个状态
            self.dp = {}
            self.depth = {}
            for _ in range(n):
                state = struct.unpack('Q', f.read(8))[0]
                dp0 = struct.unpack('b', f.read(1))[0]
                dp1 = struct.unpack('b', f.read(1))[0]
                depth0 = struct.unpack('H', f.read(2))[0]
                depth1 = struct.unpack('H', f.read(2))[0]
                self.dp[state] = [dp0, dp1]
                self.depth[state] = [depth0, depth1]


class agent:
    def __init__(self, game):
        self.name = 'complete3_optimized'
        self.game = game
        self.sym = SymmetryHelper()
        self.dg = DG()

        class_file = inspect.getfile(agent)
        class_dir = os.path.abspath(os.path.dirname(class_file))
        self.train_file = os.path.join(class_dir, 'DG_optimized.train')

        try:
            self.dg.load_training_data(self.train_file)
            print(f"Loaded {len(self.dg.dp)} canonical states")
        except:
            print("Training data not found, training...")
            self.train()
            print(f"Training complete, {len(self.dg.dp)} canonical states")

    def trans(self, deq):
        """将棋子位置队列转为列表"""
        return [i * 3 + j for i, j in deq]

    def train(self):
        """训练：枚举所有状态并标准化"""
        print("Building game graph with symmetry reduction...")

        # 记录原始状态到标准型的映射
        state_to_canon = {}

        # 枚举所有可能的状态
        max_code = 729 * 729  # 9^3 * 9^3
        processed = 0

        for code in range(max_code):
            # 解码
            x_code, y_code = code // 729, code % 729
            x, y = [], []

            temp = x_code
            while temp:
                x.append(temp % 9)
                temp //= 9

            temp = y_code
            while temp:
                y.append(temp % 9)
                temp //= 9

            # 回合约束
            if len(x) != len(y) and len(x) != len(y) + 1:
                continue

            # 检查位置是否重叠
            if set(x) & set(y):
                continue

            # 标准化
            x_canon, y_canon, trans_id, canon_code = self.sym.canonicalize(x, y)
            state_to_canon[code] = canon_code

            # 只处理标准型
            if canon_code in self.dg.dp:
                continue

            # 在标准型空间构建游戏状态
            self.game.reset()
            for t in x_canon:
                i, j = t // 3, t % 3
                self.game.board[i][j] = 1
            for t in y_canon:
                i, j = t // 3, t % 3
                self.game.board[i][j] = -1

            # 检查胜负
            result = 0
            if x_canon:
                i, j = x_canon[0] // 3, x_canon[0] % 3
                self.game.history.append([i, j])
                result = self.game.get_result()
            if not result and y_canon:
                i, j = y_canon[0] // 3, y_canon[0] % 3
                self.game.history.append([i, j])
                result = self.game.get_result()

            if result == 1:
                self.dg.win.add(canon_code)
                self.dg.add_state(canon_code)
                self.dg.dp[canon_code] = [1, 1]
                continue
            elif result == -1:
                self.dg.lose.add(canon_code)
                self.dg.add_state(canon_code)
                self.dg.dp[canon_code] = [-1, -1]
                continue

            # 枚举后续状态
            for i in range(3):
                for j in range(3):
                    if self.game.board[i][j] != 0:
                        continue

                    t = i * 3 + j
                    x_new = x_canon + [t]
                    y_new = y_canon + [t]

                    if len(x_new) > 3:
                        x_new = x_new[1:]
                    if len(y_new) > 3:
                        y_new = y_new[1:]

                    # 标准化后续状态
                    _, _, _, next_canon_0 = self.sym.canonicalize(x_new, y_canon)
                    _, _, _, next_canon_1 = self.sym.canonicalize(x_canon, y_new)

                    self.dg.add_edge(canon_code, next_canon_0, 0)
                    self.dg.add_edge(canon_code, next_canon_1, 1)

            processed += 1
            if processed % 10000 == 0:
                print(f"Processed {processed} states, {len(self.dg.dp)} canonical states")

        print(f"Graph built: {len(self.dg.dp)} canonical states")
        print("Solving game tree...")
        self.dg.solve()
        print("Saving training data...")
        self.dg.save_training_data(self.train_file)
        print("Done!")

    def make_move(self):
        """选择最优走法"""
        # 当前玩家
        p = 0
        if len(self.game.history) & 1 == 0:
            p = 1

        # 获取当前状态
        x_pos = self.trans(self.game.x)
        y_pos = self.trans(self.game.y)

        # 标准化当前状态
        x_canon, y_canon, trans_id, _ = self.sym.canonicalize(x_pos, y_pos)

        # 在标准型空间评估所有走法
        moves = []
        for i in range(3):
            for j in range(3):
                if self.game.board[i][j] != 0:
                    continue

                t = i * 3 + j
                # 转换到标准型空间
                t_canon = self.sym.apply_transform([t], trans_id)[0]

                if p == 1:  # X玩家
                    x_new = x_canon + [t_canon]
                    if len(x_new) > 3:
                        x_new = x_new[1:]
                    _, _, _, next_code = self.sym.canonicalize(x_new, y_canon)

                    if next_code in self.dg.dp:
                        dp_val = self.dg.dp[next_code][1]
                        depth_val = self.dg.depth[next_code][1]
                    else:
                        dp_val = 0
                        depth_val = 0

                    moves.append([t, dp_val, depth_val])
                else:  # O玩家
                    y_new = y_canon + [t_canon]
                    if len(y_new) > 3:
                        y_new = y_new[1:]
                    _, _, _, next_code = self.sym.canonicalize(x_canon, y_new)

                    if next_code in self.dg.dp:
                        dp_val = -self.dg.dp[next_code][0]
                        depth_val = self.dg.depth[next_code][0]
                    else:
                        dp_val = 0
                        depth_val = 0

                    moves.append([t, dp_val, depth_val])

        # 选择最优走法
        moves.sort(key=lambda x: (x[1], -x[2]))
        if moves[-1][1] == -1:
            moves.sort(key=lambda x: (x[1], x[2]))

        t = moves[-1][0]
        i, j = t // 3, t % 3
        self.game.play(i, j)
