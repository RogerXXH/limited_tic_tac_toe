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
        """编码状态（基数10，pos+1避免0冲突）"""
        x_code = sum((pos + 1) * (10 ** i) for i, pos in enumerate(x_list))
        y_code = sum((pos + 1) * (10 ** i) for i, pos in enumerate(y_list))
        return x_code * 1000 + y_code

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


class GameTreeSolver:
    """使用字典存储的博弈图求解器"""

    def __init__(self):
        self.edge0 = {}
        self.edge1 = {}
        self.win = set()
        self.lose = set()
        self.dp = {}
        self.depth = {}

    def add_state(self, state):
        """添加状态"""
        if state not in self.edge0:
            self.edge0[state] = []
            self.edge1[state] = []
            self.dp[state] = [0, 0]
            self.depth[state] = [0, 0]

    def add_edge(self, from_state, to_state, player):
        """添加边"""
        # 解码to_state检查合法性
        x_code, y_code = to_state // 1000, to_state % 1000
        x, y = [], []

        # 检查是否有0（非法code）
        temp = x_code
        while temp:
            digit = temp % 10
            if digit == 0:
                return  # 非法code，不添加边
            x.append(digit - 1)
            temp //= 10

        temp = y_code
        while temp:
            digit = temp % 10
            if digit == 0:
                return  # 非法code，不添加边
            y.append(digit - 1)
            temp //= 10

        # 检查棋子数量关系
        if len(x) != len(y) and len(x) != len(y) + 1:
            return

        # 检查重叠
        if set(x) & set(y):
            return

        # 检查重复位置
        if len(x) != len(set(x)) or len(y) != len(set(y)):
            return

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

    def solve(self, debug=False):
        """博弈树求解"""
        edge0_ = {s: [] for s in self.edge0}
        edge1_ = {s: [] for s in self.edge1}
        for s in self.edge0:
            for t in self.edge0[s]:
                edge0_[t].append(s)
            for t in self.edge1[s]:
                edge1_[t].append(s)

        need = {s: [len(self.edge0[s]), len(self.edge1[s])] for s in self.edge0}

        if debug:
            print(f"  solve开始: win={len(self.win)}, lose={len(self.lose)}")
            print(f"  edge0_有反向边的状态数: {sum(1 for s in edge0_ if edge0_[s])}")
            print(f"  edge1_有反向边的状态数: {sum(1 for s in edge1_ if edge1_[s])}")

        deq = deque(self.win)
        win_propagate_count = 0
        first_batch_updates = []
        iteration = 0
        while deq:
            x = deq.popleft()

            # 调试：记录第一轮的详细信息
            if debug and iteration < 3:
                edge0_predecessors = edge0_.get(x, [])
                if edge0_predecessors:
                    print(f"    迭代{iteration}: win状态{x}, edge0_前驱={len(edge0_predecessors)}个")
                    for pred in edge0_predecessors[:2]:
                        print(f"      前驱{pred}: dp[{pred}][0]={self.dp[pred][0]}")
                iteration += 1

            for y in edge0_.get(x, []):
                if self.dp[y][0] == 1:
                    continue
                self.dp[y][0] = 1
                self.depth[y][0] = self.depth[x][1] + 1
                win_propagate_count += 1

                if debug and len(first_batch_updates) < 5:
                    first_batch_updates.append((y, len(edge1_[y])))

                for z in edge1_[y]:
                    need[z][1] -= 1
                    if need[z][1] == 0:
                        deq.append(z)
                        self.dp[z][1] = 1
                        self.depth[z][1] = self.depth[y][0] + 1
                        win_propagate_count += 1

        if debug:
            print(f"  win传播更新了 {win_propagate_count} 次")
            print(f"  第一批更新的状态:")
            for state, edge1_count in first_batch_updates:
                print(f"    {state}: edge1_后继数={edge1_count}")

        deq = deque(self.lose)
        lose_propagate_count = 0
        while deq:
            x = deq.popleft()
            for y in edge1_[x]:
                if self.dp[y][1] == -1:
                    continue
                self.dp[y][1] = -1
                self.depth[y][1] = self.depth[x][0] + 1
                lose_propagate_count += 1
                for z in edge0_[y]:
                    need[z][0] -= 1
                    if need[z][0] == 0:
                        deq.append(z)
                        self.dp[z][0] = -1
                        self.depth[z][0] = self.depth[y][1] + 1
                        lose_propagate_count += 1

        if debug:
            print(f"  lose传播更新了 {lose_propagate_count} 次")

    def save_training_data(self, filename='game_tree.data'):
        """保存为紧凑二进制格式"""
        with open(filename, 'wb') as f:
            n = len(self.dp)
            f.write(struct.pack('I', n))

            for state in sorted(self.dp.keys()):
                f.write(struct.pack('Q', state))
                f.write(struct.pack('b', self.dp[state][0]))
                f.write(struct.pack('b', self.dp[state][1]))
                f.write(struct.pack('H', self.depth[state][0]))
                f.write(struct.pack('H', self.depth[state][1]))

    def load_training_data(self, filename='game_tree.data'):
        """加载二进制格式"""
        with open(filename, 'rb') as f:
            n = struct.unpack('I', f.read(4))[0]

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

        # 从dp中重建win和lose集合
        self.win = set()
        self.lose = set()
        for state, dp_val in self.dp.items():
            if dp_val == [1, 1]:
                self.win.add(state)
            elif dp_val == [-1, -1]:
                self.lose.add(state)


class Strategy:
    def __init__(self, game):
        self.name = 'Perfect AI Test'
        self.game = game
        self.sym = SymmetryHelper()
        self.solver = GameTreeSolver()

        class_file = inspect.getfile(Strategy)
        class_dir = os.path.abspath(os.path.dirname(class_file))
        self.train_file = os.path.join(class_dir, 'game_tree_optimized.data')

        try:
            self.solver.load_training_data(self.train_file)
        except:
            self.train()

    def trans(self, deq):
        """将棋子位置队列转为列表"""
        return [i * 3 + j for i, j in deq]

    def train(self):
        """训练：枚举所有状态并标准化"""
        max_code = 1000 * 1000
        processed = 0
        edge_added = 0
        cnt = 0
        canons = set()
        canons_draw = set()
        for code in range(max_code):
            x_code, y_code = code // 1000, code % 1000
            x, y = [], []

            # 解码时检查是否有0（非法code）
            temp = x_code
            has_zero_x = False
            while temp:
                digit = temp % 10
                if digit == 0:
                    has_zero_x = True
                    break
                x.append(digit - 1)
                temp //= 10

            temp = y_code
            has_zero_y = False
            while temp:
                digit = temp % 10
                if digit == 0:
                    has_zero_y = True
                    break
                y.append(digit - 1)
                temp //= 10

            # 跳过包含0的code（非法）
            if has_zero_x or has_zero_y:
                continue

            # 长度检查
            if len(x) != len(y) and len(x) != len(y) + 1:
                continue

            # 重叠检查
            if set(x) & set(y):
                continue

            # 重复检查
            if len(x) != len(set(x)) or len(y) != len(set(y)):
                continue

            x_canon, y_canon, trans_id, canon_code = self.sym.canonicalize(x, y)
            
            # 如果这个标准型已经完整处理过（有出边），跳过
            if canon_code in canons:
                continue

            canons.add(canon_code)

            self.game.reset()
            for t in x_canon:
                i, j = t // 3, t % 3
                self.game.board[i][j] = 1
            for t in y_canon:
                i, j = t // 3, t % 3
                self.game.board[i][j] = -1

            result = 0
            if x_canon:
                i, j = x_canon[0] // 3, x_canon[0] % 3
                self.game.history.append([i, j])
                result = self.game.get_result()
            if not result and y_canon:
                i, j = y_canon[0] // 3, y_canon[0] % 3
                self.game.history.append([i, j])
                result = self.game.get_result()

            edge_added += 1
            if result == 1:
                cnt += 1
                self.solver.win.add(canon_code)
                self.solver.add_state(canon_code)
                self.solver.dp[canon_code] = [1, 1]
                continue
            elif result == -1:
                cnt += 1
                self.solver.lose.add(canon_code)
                self.solver.add_state(canon_code)
                self.solver.dp[canon_code] = [-1, -1]
                continue
            
            canons_draw.add(canon_code)
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

                    _, _, _, next_canon_0 = self.sym.canonicalize(x_new, y_canon)
                    _, _, _, next_canon_1 = self.sym.canonicalize(x_canon, y_new)

                    self.solver.add_edge(canon_code, next_canon_0, 0)
                    self.solver.add_edge(canon_code, next_canon_1, 1)

            processed += 1

        self.solver.solve(debug=True)
        self.solver.save_training_data(self.train_file)

    def make_move(self):
        """选择最优走法"""
        p = 0
        if len(self.game.history) & 1 == 0:
            p = 1

        x_pos = self.trans(self.game.x)
        y_pos = self.trans(self.game.y)

        x_canon, y_canon, trans_id, _ = self.sym.canonicalize(x_pos, y_pos)

        moves = []
        for i in range(3):
            for j in range(3):
                if self.game.board[i][j] != 0:
                    continue

                t = i * 3 + j
                t_canon = self.sym.apply_transform([t], trans_id)[0]

                if p == 1:
                    x_new = x_canon + [t_canon]
                    if len(x_new) > 3:
                        x_new = x_new[1:]
                    _, _, _, next_code = self.sym.canonicalize(x_new, y_canon)

                    if next_code in self.solver.dp:
                        dp_val = self.solver.dp[next_code][1]
                        depth_val = self.solver.depth[next_code][1]
                    else:
                        dp_val = 0
                        depth_val = 0

                    moves.append([t, dp_val, depth_val])
                else:
                    y_new = y_canon + [t_canon]
                    if len(y_new) > 3:
                        y_new = y_new[1:]
                    _, _, _, next_code = self.sym.canonicalize(x_canon, y_new)

                    if next_code in self.solver.dp:
                        dp_val = -self.solver.dp[next_code][0]
                        depth_val = self.solver.depth[next_code][0]
                    else:
                        dp_val = 0
                        depth_val = 0

                    moves.append([t, dp_val, depth_val])

        moves.sort(key=lambda x: (x[1], -x[2]))
        if moves[-1][1] == -1:
            moves.sort(key=lambda x: (x[1], x[2]))

        t = moves[-1][0]
        i, j = t // 3, t % 3
        self.game.play(i, j)
