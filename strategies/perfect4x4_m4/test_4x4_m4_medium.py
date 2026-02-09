"""
中等规模测试 4×4 (max_move=4) 训练流程
处理10,000个标准型，验证终局判断和博弈树构建
"""

from Game import GameBase
import strategies.perfect4x4_m4.perfect_strategy as perfect_strategy
import time

# 创建游戏实例
game = GameBase(4, 4)

# 创建策略实例
strategy = perfect_strategy.Strategy(game)

print("=" * 70)
print("中等规模测试 4×4 (max_move=4)")
print("=" * 70)
print(f"测试规模: 10,000 个标准型")
print(f"预计时间: 1-3 分钟")
print(f"目的: 验证终局判断和博弈树求解正确性")
print("=" * 70)

input("按 Enter 键开始测试，或 Ctrl+C 取消...")

start_time = time.time()

# 中等规模训练
strategy.train(max_states=10000)

elapsed_time = time.time() - start_time

print("\n" + "=" * 70)
print("测试完成!")
print("=" * 70)
print(f"总耗时: {elapsed_time:.1f} 秒 ({elapsed_time/60:.1f} 分钟)")
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

print("\n✓ 如果博弈树求解成功，说明算法正确")
print("下一步: 运行 count_canonical_states_4x4_m4.py 计算精确的标准型数量")
print("       然后运行 train_4x4_m4_full.py 进行完整训练")
