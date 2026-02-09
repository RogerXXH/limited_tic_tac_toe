"""
完整训练 4×4 (max_move=4) Perfect AI
标准型数量未知，需要扫描完整编码空间
预计训练时间: 1-4小时（取决于CPU性能）
"""

from Game import GameBase
import strategies.perfect4x4_m4.perfect_strategy as perfect_strategy
import time

# 创建游戏实例
game = GameBase(4, 4)

# 创建策略实例
strategy = perfect_strategy.Strategy(game)

print("=" * 70)
print("完整训练 4×4 (max_move=4) Perfect AI")
print("=" * 70)
print(f"棋盘大小: 4×4")
print(f"每方最多保留棋子数: 4")
print(f"胜利条件: 连成3个")
print()
print("预计统计信息:")
print(f"  - 标准型数量: 估计 ~7000万（具体需要计算确认）")
print(f"  - 编码空间: 4.19亿（预计算优化）")
print(f"  - 优化策略: 预计算所有标准型x_code和合法y_code")
print(f"    · x_valid: ~8,869 个（标准型x_code）")
print(f"    · y_valid: ~47,297 个（合法y_code）")
print(f"    · 减少倍数: 16.6x（相比原始17^8）")
print(f"  - 预计训练时间: 15-70分钟（取决于CPU性能）")
print(f"  - 内存需求: ~1-2 GB")
print()
print("注意事项:")
print("  1. 训练过程中会每秒显示一次进度")
print("  2. 可以随时按 Ctrl+C 中断（已完成的部分会丢失）")
print("  3. 建议在后台运行或使用 tmux/screen")
print("  4. 训练数据保存在 strategies/perfect4x4_m4/game_tree_4x4_m4.data")
print()
print("进度显示说明:")
print("  - 已找到: 当前发现的标准型数量")
print("  - 扫描: 在编码空间中的扫描进度")
print("  - 速度: 每秒发现的标准型数量")
print("=" * 70)
print()

# 如果知道精确数量，可以在这里设置
# 例如：EXPECTED_COUNT = 73000000
# 可以先运行 count_canonical_states.py 来获取精确数量
EXPECTED_COUNT = None

# 询问用户是否知道精确数量
try:
    user_input = input("如果你知道精确的标准型数量，请输入（否则直接按Enter）: ").strip()
    if user_input.isdigit():
        EXPECTED_COUNT = int(user_input)
        print(f"将使用目标数量: {EXPECTED_COUNT:,}")
except:
    pass

print()
input("按 Enter 键开始完整训练，或 Ctrl+C 取消...")
print()

start_time = time.time()

try:
    # 完整训练
    strategy.train(expected_count=EXPECTED_COUNT)

    elapsed_time = time.time() - start_time

    print("\n" + "=" * 70)
    print("训练完成!")
    print("=" * 70)
    print(f"总耗时: {elapsed_time:.1f} 秒 ({elapsed_time/60:.1f} 分钟 / {elapsed_time/3600:.2f} 小时)")
    print(f"总状态数: {len(strategy.solver.dp):,}")
    print(f"Win状态数: {len(strategy.solver.win):,}")
    print(f"Lose状态数: {len(strategy.solver.lose):,}")

    # 显示DP值统计
    dp_win_0 = sum(1 for s in strategy.solver.dp if strategy.solver.dp[s][0] == 1)
    dp_lose_0 = sum(1 for s in strategy.solver.dp if strategy.solver.dp[s][0] == -1)
    dp_draw_0 = sum(1 for s in strategy.solver.dp if strategy.solver.dp[s][0] == 0)

    print(f"\nPlayer 0 (先手X) 视角:")
    print(f"  必胜状态: {dp_win_0:,}")
    print(f"  必败状态: {dp_lose_0:,}")
    print(f"  平局/未定: {dp_draw_0:,}")

    dp_win_1 = sum(1 for s in strategy.solver.dp if strategy.solver.dp[s][1] == 1)
    dp_lose_1 = sum(1 for s in strategy.solver.dp if strategy.solver.dp[s][1] == -1)
    dp_draw_1 = sum(1 for s in strategy.solver.dp if strategy.solver.dp[s][1] == 0)

    print(f"\nPlayer 1 (后手O) 视角:")
    print(f"  必胜状态: {dp_win_1:,}")
    print(f"  必败状态: {dp_lose_1:,}")
    print(f"  平局/未定: {dp_draw_1:,}")

    # 判断游戏性质
    init_state_code = strategy.sym.encode([], [])
    if init_state_code in strategy.solver.dp:
        dp_val = strategy.solver.dp[init_state_code]
        print(f"\n初始状态 dp 值: {dp_val}")
        if dp_val[0] == 1:
            print("🎉 结论: 先手(X)必胜!")
        elif dp_val[0] == -1:
            print("🎉 结论: 后手(O)必胜!")
        else:
            print("🎉 结论: 双方最优博弈下为平局或未定")
    else:
        print("\n⚠️ 警告: 未找到初始状态，训练可能不完整")

    print("\n" + "=" * 70)
    print("✓ 训练数据已保存，现在可以在UI中使用 Perfect AI 了！")
    print(f"✓ 数据文件: {strategy.train_file}")
    print("=" * 70)

except KeyboardInterrupt:
    print("\n\n训练被中断")
    elapsed_time = time.time() - start_time
    print(f"已运行: {elapsed_time:.1f} 秒 ({elapsed_time/60:.1f} 分钟)")
    if hasattr(strategy.solver, 'dp'):
        print(f"已找到状态数: {len(strategy.solver.dp):,}")
    print("\n注意: 中断的训练数据不会保存，需要重新开始")
    print("建议: 使用 tmux 或 screen 在后台运行完整训练")

except Exception as e:
    print(f"\n\n训练过程中出现错误: {e}")
    import traceback
    traceback.print_exc()
    print("\n请检查错误信息并修复后重试")
