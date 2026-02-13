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
    """使用 mmap + 二分查找 的训练数据加载器"""

    def __init__(self):
        # mmap相关（用于快速查询）
        self.mmap_file = None
        self.mmap_obj = None
        self.record_size = 14  # state(8) + dp0(1) + dp1(1) + depth0(2) + depth1(2)
        self.num_records = 0

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
        except FileNotFoundError:
            print("未找到训练数据，请先运行训练程序")
            raise

    def trans(self, deq):
        """将棋子位置队列转为列表"""
        return [i * 4 + j for i, j in deq]

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
        return True
