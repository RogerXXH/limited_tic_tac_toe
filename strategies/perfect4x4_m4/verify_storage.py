"""
存储格式验证脚本
与 test_storage.cpp 配合使用：
  1. 编译并运行 C++ 程序生成测试文件
  2. 运行本脚本验证 Python 能正确读取

用法：
  python verify_storage.py [文件名]
  python verify_storage.py test_storage.data
"""

import mmap
import struct
import sys

RECORD_SIZE = 14  # state(8) + dp0(1) + dp1(1) + depth0(2) + depth1(2)


def query_state(mm, num_records, state_code):
    """mmap + 二分查找，与 perfect_strategy.py 中的 query_state 完全相同"""
    left, right = 0, num_records - 1
    while left <= right:
        mid = (left + right) // 2
        offset = 8 + mid * RECORD_SIZE
        current_code = struct.unpack('Q', mm[offset:offset + 8])[0]
        if current_code < state_code:
            left = mid + 1
        elif current_code > state_code:
            right = mid - 1
        else:
            dp0    = struct.unpack('b', mm[offset + 8 :offset + 9 ])[0]
            dp1    = struct.unpack('b', mm[offset + 9 :offset + 10])[0]
            depth0 = struct.unpack('H', mm[offset + 10:offset + 12])[0]
            depth1 = struct.unpack('H', mm[offset + 12:offset + 14])[0]
            return [dp0, dp1], [depth0, depth1]
    return None


# 与 test_storage.cpp 中 make_record(i) 完全相同的期望值计算
def expected_values(i):
    state_code = (i + 1) * 1000000007
    dp0        = (i % 3) - 1
    dp1        = ((i + 1) % 3) - 1
    depth0     = i % 1000
    depth1     = (i * 3) % 1000
    return state_code, dp0, dp1, depth0, depth1


def verify(filename):
    print(f"验证文件: {filename}")
    print("=" * 50)

    with open(filename, 'rb') as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)

        # --- 1. 头部校验 ---
        num_records = struct.unpack('Q', mm[0:8])[0]
        expected_size = 8 + num_records * RECORD_SIZE
        actual_size   = len(mm)

        print(f"记录数:   {num_records:,}")
        print(f"文件大小: {actual_size} 字节  (预期 {expected_size})")

        if actual_size != expected_size:
            print(f"✗ 文件大小不匹配！差 {actual_size - expected_size} 字节")
            return False
        print("✓ 文件大小正确")

        # --- 2. 排序校验（顺序扫描）---
        prev_code = 0
        sort_ok = True
        for i in range(num_records):
            offset = 8 + i * RECORD_SIZE
            code = struct.unpack('Q', mm[offset:offset + 8])[0]
            if code <= prev_code and i > 0:
                print(f"✗ 排序错误：记录 {i}  code={code} <= 前一条 {prev_code}")
                sort_ok = False
                break
            prev_code = code
        if sort_ok:
            print("✓ 排序验证通过（全部升序）")

        # --- 3. 逐条二分查找并校验值 ---
        print(f"\n校验全部 {num_records:,} 条记录的值...")
        errors = 0
        for i in range(int(num_records)):
            state_code, exp_dp0, exp_dp1, exp_d0, exp_d1 = expected_values(i)
            result = query_state(mm, num_records, state_code)

            if result is None:
                print(f"  ✗ 记录 {i} (state_code={state_code}) 未找到")
                errors += 1
                continue

            dp, depth = result
            if (dp[0] != exp_dp0 or dp[1] != exp_dp1 or
                    depth[0] != exp_d0 or depth[1] != exp_d1):
                print(f"  ✗ 记录 {i} 值不匹配:")
                print(f"      预期: dp=[{exp_dp0},{exp_dp1}]  depth=[{exp_d0},{exp_d1}]")
                print(f"      实际: dp={dp}  depth={depth}")
                errors += 1

        if errors == 0:
            print(f"✓ 全部 {num_records:,} 条记录值验证通过")
        else:
            print(f"✗ {errors} 条记录验证失败")

        # --- 4. 打印前5条记录，与 C++ 输出对比 ---
        print("\n前5条记录（供与 C++ 输出对比）:")
        for i in range(min(5, int(num_records))):
            offset = 8 + i * RECORD_SIZE
            code   = struct.unpack('Q', mm[offset:offset + 8])[0]
            dp0    = struct.unpack('b', mm[offset + 8 :offset + 9 ])[0]
            dp1    = struct.unpack('b', mm[offset + 9 :offset + 10])[0]
            d0     = struct.unpack('H', mm[offset + 10:offset + 12])[0]
            d1     = struct.unpack('H', mm[offset + 12:offset + 14])[0]
            print(f"  [{i}] state_code={code:<20}  dp=[{dp0:2d},{dp1:2d}]  depth=[{d0:4d},{d1:4d}]")

        mm.close()

    print("\n" + "=" * 50)
    if errors == 0 and sort_ok and actual_size == expected_size:
        print("✓ 存储格式验证全部通过！")
        return True
    else:
        print("✗ 存在错误，请检查上方输出")
        return False


if __name__ == '__main__':
    filename = sys.argv[1] if len(sys.argv) > 1 else 'test_storage.data'
    ok = verify(filename)
    sys.exit(0 if ok else 1)
