from collections import deque
import os
import struct
import inspect

class SymmetryHelper:
    """处理4×4棋盘的对称性"""

    def __init__(self):
        # 8种对称变换的位置映射 (4×4 = 16个位置)
        # 位置编号: 0  1  2  3
        #          4  5  6  7
        #          8  9 10 11
        #         12 13 14 15
        self.transforms = [
            # 0: 恒等
            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
            # 1: 逆时针90°
            [3, 7, 11, 15, 2, 6, 10, 14, 1, 5, 9, 13, 0, 4, 8, 12],
            # 2: 180°
            [15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
            # 3: 顺时针90°
            [12, 8, 4, 0, 13, 9, 5, 1, 14, 10, 6, 2, 15, 11, 7, 3],
            # 4: 水平翻转
            [3, 2, 1, 0, 7, 6, 5, 4, 11, 10, 9, 8, 15, 14, 13, 12],
            # 5: 垂直翻转
            [12, 13, 14, 15, 8, 9, 10, 11, 4, 5, 6, 7, 0, 1, 2, 3],
            # 6: 主对角线翻转
            [0, 4, 8, 12, 1, 5, 9, 13, 2, 6, 10, 14, 3, 7, 11, 15],
            # 7: 副对角线翻转
            [15, 11, 7, 3, 14, 10, 6, 2, 13, 9, 5, 1, 12, 8, 4, 0],
        ]

        # 预计算逆变换
        self.inv_transforms = []
        for trans in self.transforms:
            inv = [0] * 16
            for i in range(16):
                inv[trans[i]] = i
            self.inv_transforms.append(inv)

    def apply_transform(self, positions, trans_id):
        """应用变换，保持时间顺序"""
        trans = self.transforms[trans_id]
        return [trans[p] for p in positions]

    def encode(self, x_list, y_list):
        """编码状态（基数17，pos+1避免0冲突）"""
        # 4×4: pos ∈ [0,15], pos+1 ∈ [1,16], 需要基数>=17
        # max_move=4 时，单个code最大 = 16 + 16*17 + 16*17^2 + 16*17^3 = 83520
        # 使用 17^4 = 83521 作为分隔符（精确覆盖所有可能值）
        SEPARATOR = 17 ** 4  # = 83521
        x_code = sum((pos + 1) * (17 ** i) for i, pos in enumerate(x_list))
        y_code = sum((pos + 1) * (17 ** i) for i, pos in enumerate(y_list))
        return x_code * SEPARATOR + y_code

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

        # mmap相关（用于快速查询）
        self.mmap_file = None
        self.mmap_obj = None
        self.record_size = 14  # state(8) + dp0(1) + dp1(1) + depth0(2) + depth1(2)
        self.num_records = 0

    def add_state(self, state):
        """添加状态"""
        if state not in self.edge0:
            self.edge0[state] = []
            self.edge1[state] = []
            self.dp[state] = [0, 0]
            self.depth[state] = [0, 0]

    def add_edge(self, from_state, to_state, player):
        """添加边"""
        # 解码to_state检查合法性（基数17）
        SEPARATOR = 17 ** 4  # = 83521
        x_code, y_code = to_state // SEPARATOR, to_state % SEPARATOR
        x, y = [], []

        # 检查是否有0（非法code）
        temp = x_code
        while temp:
            digit = temp % 17
            if digit == 0:
                return  # 非法code，不添加边
            x.append(digit - 1)
            temp //= 17

        temp = y_code
        while temp:
            digit = temp % 17
            if digit == 0:
                return  # 非法code，不添加边
            y.append(digit - 1)
            temp //= 17

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
            print(f"  总状态数: {len(self.edge0)}")

        deq = deque(self.win)
        win_propagate_count = 0
        while deq:
            x = deq.popleft()

            for y in edge0_.get(x, []):
                if self.dp[y][0] == 1:
                    continue
                self.dp[y][0] = 1
                self.depth[y][0] = self.depth[x][1] + 1
                win_propagate_count += 1

                for z in edge1_.get(y, []):
                    need[z][1] -= 1
                    if need[z][1] == 0:
                        deq.append(z)
                        self.dp[z][1] = 1
                        self.depth[z][1] = self.depth[y][0] + 1
                        win_propagate_count += 1

        if debug:
            print(f"  win传播更新了 {win_propagate_count} 次")

        deq = deque(self.lose)
        lose_propagate_count = 0
        while deq:
            x = deq.popleft()
            for y in edge1_.get(x, []):
                if self.dp[y][1] == -1:
                    continue
                self.dp[y][1] = -1
                self.depth[y][1] = self.depth[x][0] + 1
                lose_propagate_count += 1
                for z in edge0_.get(y, []):
                    need[z][0] -= 1
                    if need[z][0] == 0:
                        deq.append(z)
                        self.dp[z][0] = -1
                        self.depth[z][0] = self.depth[y][1] + 1
                        lose_propagate_count += 1

        if debug:
            print(f"  lose传播更新了 {lose_propagate_count} 次")

    def save_training_data(self, filename='game_tree.data'):
        """保存为紧凑二进制格式（排序后，支持mmap二分查找）"""
        import time

        n = len(self.dp)
        print(f"\n准备保存 {n:,} 个状态...")

        # 排序（按state_code）
        print(f"正在排序...")
        print(f"  状态数量: {n:,}")
        print(f"  预计用时: {n / 1000000:.1f}-{n / 500000:.1f} 分钟（取决于内存和CPU）")

        sort_start = time.time()
        sorted_states = sorted(self.dp.keys())
        sort_time = time.time() - sort_start

        print(f"  排序完成，耗时: {sort_time:.1f} 秒 ({sort_time/60:.1f} 分钟)")

        # 写入文件
        print(f"正在写入文件...")
        write_start = time.time()

        with open(filename, 'wb') as f:
            # 写入记录数（用于验证）
            f.write(struct.pack('Q', n))

            # 写入所有记录（已排序）
            for i, state in enumerate(sorted_states):
                f.write(struct.pack('Q', state))
                f.write(struct.pack('b', self.dp[state][0]))
                f.write(struct.pack('b', self.dp[state][1]))
                f.write(struct.pack('H', self.depth[state][0]))
                f.write(struct.pack('H', self.depth[state][1]))

                # 进度显示
                if (i + 1) % 1000000 == 0:
                    progress = (i + 1) / n * 100
                    print(f"  已写入: {i+1:,}/{n:,} ({progress:.1f}%)")

        write_time = time.time() - write_start
        total_time = sort_time + write_time

        print(f"  写入完成，耗时: {write_time:.1f} 秒")
        print(f"\n保存完成！总耗时: {total_time:.1f} 秒 ({total_time/60:.1f} 分钟)")

    def load_training_data(self, filename='game_tree.data'):
        """使用mmap加载（瞬间完成，不占内存）"""
        import mmap
        import time

        load_start = time.time()
        print(f"加载训练数据（使用mmap，不占内存）...")

        # 打开文件并创建mmap
        self.mmap_file = open(filename, 'rb')
        self.mmap_obj = mmap.mmap(self.mmap_file.fileno(), 0, access=mmap.ACCESS_READ)

        # 读取记录数
        self.num_records = struct.unpack('Q', self.mmap_obj[0:8])[0]

        load_time = time.time() - load_start
        print(f"  加载完成！耗时: {load_time:.3f} 秒")
        print(f"  记录数: {self.num_records:,}")
        print(f"  文件大小: {len(self.mmap_obj) / 1024 / 1024:.1f} MB")
        print(f"  查询方式: 二分查找（O(log n) ≈ {self.num_records.bit_length()} 次比较）")

    def query_state(self, state_code):
        """二分查找指定状态的dp和depth值

        Returns: (dp, depth) 或 None（如果不存在）
        """
        if self.mmap_obj is None:
            return None

        # 二分查找
        left, right = 0, self.num_records - 1

        while left <= right:
            mid = (left + right) // 2
            # 跳过文件头的8字节（记录数），每条记录14字节
            offset = 8 + mid * self.record_size

            # 读取state_code
            current_code = struct.unpack('Q', self.mmap_obj[offset:offset+8])[0]

            if current_code < state_code:
                left = mid + 1
            elif current_code > state_code:
                right = mid - 1
            else:
                # 找到了，读取dp和depth
                dp0 = struct.unpack('b', self.mmap_obj[offset+8:offset+9])[0]
                dp1 = struct.unpack('b', self.mmap_obj[offset+9:offset+10])[0]
                depth0 = struct.unpack('H', self.mmap_obj[offset+10:offset+12])[0]
                depth1 = struct.unpack('H', self.mmap_obj[offset+12:offset+14])[0]
                return [dp0, dp1], [depth0, depth1]

        return None

    def __del__(self):
        """清理mmap资源"""
        if self.mmap_obj is not None:
            self.mmap_obj.close()
        if self.mmap_file is not None:
            self.mmap_file.close()


class Strategy:
    def __init__(self, game):
        self.name = 'Perfect AI 4x4 (m4)'
        self.game = game
        self.sym = SymmetryHelper()
        self.solver = GameTreeSolver()

        class_file = inspect.getfile(Strategy)
        class_dir = os.path.abspath(os.path.dirname(class_file))
        self.train_file = os.path.join(class_dir, 'game_tree_4x4_m4.data')

        try:
            self.solver.load_training_data(self.train_file)
            print(f"已加载训练数据: {len(self.solver.dp)} 个状态")
        except:
            print("未找到训练数据，需要进行训练")
            # 不自动训练，等待用户手动调用

    def trans(self, deq):
        """将棋子位置队列转为列表"""
        return [i * 4 + j for i, j in deq]

    def train(self, max_states=None, expected_count=None):
        """训练：枚举所有状态并标准化

        Args:
            max_states: 限制处理的最大状态数，用于测试。None表示处理所有状态
            expected_count: 预期的标准型数量，如果已知的话
        """
        # 编码上限计算：
        # max_move=4, 4×4棋盘，基数17编码
        # code = x_code * SEPARATOR + y_code，SEPARATOR = 17^4 = 83,521
        #
        # 优化策略：预计算所有合法的 x_code 和 y_code
        # - x_valid: 标准型 x_code（无中间零、无重复、有效首位∈{1,2,6}）
        # - y_valid: 合法 y_code（无中间零、无重复）
        SEPARATOR = 17 ** 4  # = 83521
        processed = 0
        canons = set()

        print(f"开始训练 4×4 (max_move=4)...")
        if expected_count:
            print(f"目标标准型数量: {expected_count:,}")
        else:
            print(f"标准型数量未知，将扫描优化后的编码空间")
        if max_states:
            print(f"测试模式: 最多处理 {max_states:,} 个标准型")
        print()

        import time
        start_time = time.time()
        last_report_time = start_time

        # 预计算 x_valid 和 y_valid
        print("预计算合法编码...")
        precompute_start = time.time()

        def decode_and_check(code):
            """解码并检查合法性，返回 (positions, is_valid)"""
            if code == 0:
                return [], True

            positions = []
            temp = code
            while temp:
                digit = temp % 17
                if digit == 0:  # 中间零
                    return None, False
                positions.append(digit - 1)
                temp //= 17

            # 检查重复
            if len(positions) != len(set(positions)):
                return None, False

            # 检查范围
            if any(p >= 16 for p in positions):
                return None, False

            return positions, True

        # 预计算 x_valid（标准型 x_code）
        x_valid = []
        for x_code in range(SEPARATOR):
            positions, is_valid = decode_and_check(x_code)
            if not is_valid:
                continue

            # 检查有效首位（最高位）
            if len(positions) > 0:
                highest_digit = positions[-1] + 1
                if highest_digit not in {1, 2, 6}:
                    continue

            x_valid.append(x_code)

        # 预计算 y_valid（合法 y_code）
        y_valid = []
        for y_code in range(SEPARATOR):
            positions, is_valid = decode_and_check(y_code)
            if is_valid:
                y_valid.append(y_code)

        precompute_time = time.time() - precompute_start

        print(f"  预计算完成 (耗时: {precompute_time:.1f}秒)")
        print(f"  x_valid: {len(x_valid):,} 个标准型 x_code")
        print(f"  y_valid: {len(y_valid):,} 个合法 y_code")
        print(f"  总枚举量: {len(x_valid):,} × {len(y_valid):,} = {len(x_valid) * len(y_valid):,}")
        print(f"  优化倍数: {17**8 / (len(x_valid) * len(y_valid)):.1f}x")
        print()

        total_codes_to_scan = len(x_valid) * len(y_valid)
        codes_scanned = 0

        for x_code in x_valid:
            # 如果达到早停条件或测试限制，跳出外层循环
            if expected_count and len(canons) >= expected_count:
                print(f"\n✓ 已找到所有 {expected_count:,} 个标准型，停止枚举")
                break
            if max_states and len(canons) > max_states:
                print(f"\n达到测试限制: {max_states} 个状态")
                break

            for y_code in y_valid:
                code = x_code * SEPARATOR + y_code
                codes_scanned += 1

                # 早停：如果知道预期数量，找到所有就停止
                if expected_count and len(canons) >= expected_count:
                    break

                # 测试模式：限制状态数
                if max_states and len(canons) > max_states:
                    break

                # 进度显示 - 每秒最多更新一次
                current_time = time.time()
                if current_time - last_report_time >= 1.0 and len(canons) > 0:
                    code_progress = codes_scanned / total_codes_to_scan * 100
                    elapsed = current_time - start_time
                    rate = len(canons) / elapsed if elapsed > 0 else 0

                    if expected_count and len(canons) > 100:  # 有足够样本才估算
                        progress = len(canons) / expected_count * 100
                        eta_seconds = elapsed / len(canons) * (expected_count - len(canons))
                        eta_minutes = eta_seconds / 60
                        print(f"  进度: {len(canons):,}/{expected_count:,} ({progress:.1f}%) | "
                              f"扫描: {code_progress:.1f}% | 速度: {rate:.0f}状态/秒 | 剩余: {eta_minutes:.1f}分")
                    else:
                        print(f"  已找到: {len(canons):,} | 扫描: {code_progress:.2f}% | 速度: {rate:.0f}状态/秒")
                    last_report_time = current_time

                # 解码（已知合法，直接解码）
                x, y = [], []

                temp = x_code
                while temp:
                    digit = temp % 17
                    x.append(digit - 1)
                    temp //= 17

                temp = y_code
                while temp:
                    digit = temp % 17
                    y.append(digit - 1)
                    temp //= 17

                # 检查棋子数量关系（x和y的数量必须相等或相差1）
                if len(x) != len(y) and len(x) != len(y) + 1:
                    continue

                # 检查重叠
                if set(x) & set(y):
                    continue

                x_canon, y_canon, trans_id, canon_code = self.sym.canonicalize(x, y)

                # 如果这个标准型已经处理过，跳过
                if canon_code in canons:
                    continue

                canons.add(canon_code)

                # 设置棋盘状态
                self.game.reset()
                for t in x_canon:
                    i, j = t // 4, t % 4
                    self.game.board[i][j] = 1
                for t in y_canon:
                    i, j = t // 4, t % 4
                    self.game.board[i][j] = -1

                # 判断是否终局（只在可能胜负时才判断，优化性能）
                # max_move=4时，需要连成3个才能获胜，所以至少需要3个棋子
                result = 0
                if len(x_canon) >= 3 and x_canon:
                    i, j = x_canon[0] // 4, x_canon[0] % 4
                    self.game.history.append([i, j])
                    result = self.game.get_result()
                if not result and len(y_canon) >= 3 and y_canon:
                    i, j = y_canon[0] // 4, y_canon[0] % 4
                    self.game.history.append([i, j])
                    result = self.game.get_result()

                if result == 1:
                    self.solver.win.add(canon_code)
                    self.solver.add_state(canon_code)
                    self.solver.dp[canon_code] = [1, 1]
                    continue
                elif result == -1:
                    self.solver.lose.add(canon_code)
                    self.solver.add_state(canon_code)
                    self.solver.dp[canon_code] = [-1, -1]
                    continue

                # 非终局状态：添加边
                for i in range(4):
                    for j in range(4):
                        if self.game.board[i][j] != 0:
                            continue

                        t = i * 4 + j
                        x_new = x_canon + [t]
                        y_new = y_canon + [t]

                        if len(x_new) > 4:
                            x_new = x_new[1:]
                        if len(y_new) > 4:
                            y_new = y_new[1:]

                        _, _, _, next_canon_0 = self.sym.canonicalize(x_new, y_canon)
                        _, _, _, next_canon_1 = self.sym.canonicalize(x_canon, y_new)

                        self.solver.add_edge(canon_code, next_canon_0, 0)
                        self.solver.add_edge(canon_code, next_canon_1, 1)

                processed += 1

        enumeration_time = time.time() - start_time
        print(f"\n枚举完成 (耗时: {enumeration_time:.1f}秒):")
        print(f"  找到标准型: {len(canons):,}")
        if expected_count:
            if len(canons) == expected_count:
                print(f"  ✓ 数量正确 (预期 {expected_count:,})")
            else:
                print(f"  ⚠ 数量不符 (预期 {expected_count:,})")
        print(f"  Win状态: {len(self.solver.win):,}")
        print(f"  Lose状态: {len(self.solver.lose):,}")
        print(f"\n开始博弈树求解...")

        self.solver.solve(debug=True)

        print(f"\n求解完成，保存训练数据...")
        self.solver.save_training_data(self.train_file)
        print(f"训练数据已保存到: {self.train_file}")

    def make_move(self):
        """选择最优走法"""
        p = 0
        if len(self.game.history) & 1 == 0:
            p = 1

        x_pos = self.trans(self.game.x)
        y_pos = self.trans(self.game.y)

        x_canon, y_canon, trans_id, _ = self.sym.canonicalize(x_pos, y_pos)

        moves = []
        for i in range(4):
            for j in range(4):
                if self.game.board[i][j] != 0:
                    continue

                t = i * 4 + j
                t_canon = self.sym.apply_transform([t], trans_id)[0]

                if p == 1:
                    x_new = x_canon + [t_canon]
                    if len(x_new) > 4:
                        x_new = x_new[1:]
                    _, _, _, next_code = self.sym.canonicalize(x_new, y_canon)

                    # 使用query_state查询（mmap + 二分查找）
                    result = self.solver.query_state(next_code)
                    if result:
                        dp, depth = result
                        dp_val = dp[1]
                        depth_val = depth[1]
                    else:
                        dp_val = 0
                        depth_val = 0

                    moves.append([t, dp_val, depth_val])
                else:
                    y_new = y_canon + [t_canon]
                    if len(y_new) > 4:
                        y_new = y_new[1:]
                    _, _, _, next_code = self.sym.canonicalize(x_canon, y_new)

                    # 使用query_state查询（mmap + 二分查找）
                    result = self.solver.query_state(next_code)
                    if result:
                        dp, depth = result
                        dp_val = -dp[0]
                        depth_val = depth[0]
                    else:
                        dp_val = 0
                        depth_val = 0

                    moves.append([t, dp_val, depth_val])

        moves.sort(key=lambda x: (x[1], -x[2]))
        if moves[-1][1] == -1:
            moves.sort(key=lambda x: (x[1], x[2]))

        t = moves[-1][0]
        i, j = t // 4, t % 4
        self.game.play(i, j)
