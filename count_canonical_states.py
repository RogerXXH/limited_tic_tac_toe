"""统计标准型数量"""

from itertools import combinations, permutations
import time

class SymmetryHelper3x3:
    """处理3×3棋盘的对称性（基数10编码）"""

    def __init__(self):
        # 3×3棋盘的8种对称变换
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

    def apply_transform(self, positions, trans_id):
        """应用变换，保持时间顺序"""
        trans = self.transforms[trans_id]
        return tuple(trans[p] for p in positions)

    def encode(self, x_list, y_list):
        """编码状态（基数10，与perfect_strategy.py相同）"""
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


class SymmetryHelper4x4:
    """处理4×4棋盘的对称性"""

    def __init__(self):
        # 4×4棋盘的8种对称变换
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

    def apply_transform(self, positions, trans_id):
        """应用变换，保持时间顺序"""
        trans = self.transforms[trans_id]
        return tuple(trans[p] for p in positions)

    def encode(self, x_list, y_list):
        """编码状态（使用整数，基数17适配4×4棋盘）"""
        # 4×4棋盘: pos ∈ [0,15], pos+1 ∈ [1,16], 需要基数>=17
        x_code = sum((pos + 1) * (17 ** i) for i, pos in enumerate(x_list))
        y_code = sum((pos + 1) * (17 ** i) for i, pos in enumerate(y_list))
        # max_move=4时，最大code = 16 + 16*17 + 16*17^2 + 16*17^3 = 83520
        # 使用 17^4 = 83521 作为分隔符（精确覆盖）
        return x_code * (17 ** 4) + y_code

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


def count_canonical_states(board_size, max_move, sym_helper, verbose=True):
    """统计标准型数量"""
    sym = sym_helper
    total_positions = board_size * board_size

    canons = set()
    total_checked = 0

    start_time = time.time()

    # 枚举所有合法的棋子数量组合
    for x_count in range(max_move + 1):
        for y_count in range(max_move + 1):
            # 只考虑合法的数量关系
            if x_count != y_count and x_count != y_count + 1:
                continue

            if verbose:
                print(f"\n处理 X={x_count}, Y={y_count}...")

            batch_start = time.time()
            batch_count = 0
            batch_canonical = 0

            # 枚举X的所有有序放置
            if x_count == 0:
                x_perms = [()]
            else:
                x_perms = permutations(range(total_positions), x_count)

            for x_perm in x_perms:
                # 枚举Y的所有有序放置（不能与X重叠）
                remaining = [p for p in range(total_positions) if p not in x_perm]

                if y_count == 0:
                    y_perms = [()]
                else:
                    y_perms = permutations(remaining, y_count)

                for y_perm in y_perms:
                    batch_count += 1
                    total_checked += 1

                    # 计算标准型
                    _, _, _, canon_code = sym.canonicalize(list(x_perm), list(y_perm))

                    if canon_code not in canons:
                        canons.add(canon_code)
                        batch_canonical += 1

                    # 进度显示
                    if verbose and batch_count % 100000 == 0:
                        elapsed = time.time() - batch_start
                        print(f"  已检查 {batch_count:,} 个状态, "
                              f"发现 {batch_canonical:,} 个新标准型, "
                              f"用时 {elapsed:.1f}s")

            batch_elapsed = time.time() - batch_start
            if verbose:
                print(f"  完成 X={x_count}, Y={y_count}: "
                      f"检查 {batch_count:,} 个状态, "
                      f"新增 {batch_canonical:,} 个标准型, "
                      f"用时 {batch_elapsed:.1f}s")
                print(f"  累计标准型数量: {len(canons):,}")

    total_elapsed = time.time() - start_time

    return len(canons), total_checked, total_elapsed


if __name__ == "__main__":
    print("=" * 70)
    print("统计标准型数量（仿照 perfect_strategy.py 的方法）")
    print("=" * 70)

    # 先验证 3×3 的结果
    print("\n【验证：3×3, max_move=3】")
    print("这应该与实际训练得到的标准型数量一致...")
    sym_3x3 = SymmetryHelper3x3()
    count_3x3, total_3x3, time_3x3 = count_canonical_states(3, 3, sym_3x3, verbose=True)
    print(f"\n总结：")
    print(f"  总共检查状态数: {total_3x3:,}")
    print(f"  标准型数量: {count_3x3:,}")
    print(f"  缩减比例: {total_3x3 / count_3x3:.2f}x")
    print(f"  总耗时: {time_3x3:.2f}s")

    # 4×4, max_move=3
    print("\n" + "=" * 70)
    print("【计算：4×4, max_move=3】")
    sym_4x4 = SymmetryHelper4x4()
    count_4x4_m3, total_4x4_m3, time_4x4_m3 = count_canonical_states(4, 3, sym_4x4, verbose=True)
    print(f"\n总结：")
    print(f"  总共检查状态数: {total_4x4_m3:,}")
    print(f"  标准型数量: {count_4x4_m3:,}")
    print(f"  缩减比例: {total_4x4_m3 / count_4x4_m3:.2f}x")
    print(f"  相对于3×3的倍数: {count_4x4_m3 / count_3x3:.2f}x")
    print(f"  总耗时: {time_4x4_m3:.2f}s")

    # 4×4, max_move=4 的估算
    print("\n" + "=" * 70)
    print("【估算：4×4, max_move=4】")
    print("警告：这个计算量非常大，可能需要很长时间...")
    print("是否继续？(可以按Ctrl+C中断)")

    try:
        import sys
        # 给用户5秒时间决定是否中断
        print("5秒后开始计算...")
        time.sleep(5)

        count_4x4_m4, total_4x4_m4, time_4x4_m4 = count_canonical_states(4, 4, sym_4x4, verbose=True)
        print(f"\n总结：")
        print(f"  总共检查状态数: {total_4x4_m4:,}")
        print(f"  标准型数量: {count_4x4_m4:,}")
        print(f"  缩减比例: {total_4x4_m4 / count_4x4_m4:.2f}x")
        print(f"  相对于3×3的倍数: {count_4x4_m4 / count_3x3:.2f}x")
        print(f"  总耗时: {time_4x4_m4:.2f}s")

    except KeyboardInterrupt:
        print("\n\n计算被中断")
        print(f"基于 max_move=3 的结果，估算 max_move=4:")
        print(f"  假设缩减比例相似 (~7-8x)")
        print(f"  估算标准型数量: {total_4x4_m3 / count_4x4_m3 * 582913217 / 8:.0f}")
