"""
使用 x_valid 和 y_valid 精确计算 4×4 (max_move=4) 的标准型数量
"""
import time

SEPARATOR = 17 ** 4

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


def encode(x_list, y_list):
    """编码状态"""
    x_code = sum((pos + 1) * (17 ** i) for i, pos in enumerate(x_list))
    y_code = sum((pos + 1) * (17 ** i) for i, pos in enumerate(y_list))
    return x_code * SEPARATOR + y_code


def canonicalize(x_list, y_list):
    """返回标准型编码"""
    # 8种对称变换
    transforms = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
        [3, 7, 11, 15, 2, 6, 10, 14, 1, 5, 9, 13, 0, 4, 8, 12],
        [15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
        [12, 8, 4, 0, 13, 9, 5, 1, 14, 10, 6, 2, 15, 11, 7, 3],
        [3, 2, 1, 0, 7, 6, 5, 4, 11, 10, 9, 8, 15, 14, 13, 12],
        [12, 13, 14, 15, 8, 9, 10, 11, 4, 5, 6, 7, 0, 1, 2, 3],
        [0, 4, 8, 12, 1, 5, 9, 13, 2, 6, 10, 14, 3, 7, 11, 15],
        [15, 11, 7, 3, 14, 10, 6, 2, 13, 9, 5, 1, 12, 8, 4, 0],
    ]

    min_code = None
    for trans in transforms:
        x_trans = [trans[p] for p in x_list]
        y_trans = [trans[p] for p in y_list]
        code = encode(x_trans, y_trans)

        if min_code is None or code < min_code:
            min_code = code

    return min_code


print("=" * 70)
print("计算 4×4 (max_move=4) 标准型数量")
print("=" * 70)

# 预计算 x_valid 和 y_valid
print("\n预计算合法编码...")
precompute_start = time.time()

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

y_valid = []
for y_code in range(SEPARATOR):
    positions, is_valid = decode_and_check(y_code)
    if is_valid:
        y_valid.append(y_code)

precompute_time = time.time() - precompute_start

print(f"  预计算完成 (耗时: {precompute_time:.1f}秒)")
print(f"  x_valid: {len(x_valid):,} 个")
print(f"  y_valid: {len(y_valid):,} 个")
print(f"  总组合: {len(x_valid) * len(y_valid):,}")
print()

# 开始枚举并计算标准型
print("开始枚举标准型...")
start_time = time.time()
last_report_time = start_time

canons = set()
total_combinations = len(x_valid) * len(y_valid)
checked = 0

for i, x_code in enumerate(x_valid):
    # 解码
    x, _ = decode_and_check(x_code)

    for y_code in y_valid:
        checked += 1

        # 进度显示
        current_time = time.time()
        if current_time - last_report_time >= 2.0:
            progress = checked / total_combinations * 100
            elapsed = current_time - start_time
            rate = checked / elapsed if elapsed > 0 else 0
            eta_seconds = (total_combinations - checked) / rate if rate > 0 else 0
            eta_minutes = eta_seconds / 60

            print(f"  进度: {checked:,}/{total_combinations:,} ({progress:.1f}%) | "
                  f"找到: {len(canons):,} | 速度: {rate:.0f}/秒 | 剩余: {eta_minutes:.1f}分")
            last_report_time = current_time

        # 解码
        y, _ = decode_and_check(y_code)

        # 检查棋子数量关系
        if len(x) != len(y) and len(x) != len(y) + 1:
            continue

        # 检查重叠
        if set(x) & set(y):
            continue

        # 计算标准型
        canon_code = canonicalize(x, y)
        canons.add(canon_code)

enumeration_time = time.time() - start_time

print()
print("=" * 70)
print("计算完成！")
print("=" * 70)
print(f"总耗时: {enumeration_time:.1f} 秒 ({enumeration_time/60:.1f} 分钟)")
print(f"检查组合数: {checked:,}")
print(f"标准型数量: {len(canons):,}")
print()
print(f"这个数量是 4×4 (max_move=4) 游戏的精确标准型数量！")
print("=" * 70)
