"""
小规模测试 4×4 (max_move=4) 训练流程
仅处理1000个标准型，验证代码正确性
"""

from Game import GameBase
import strategies.perfect4x4_m4.perfect_strategy as perfect_strategy
import time

# 创建游戏实例
game = GameBase(4, 4)

# 创建策略实例
strategy = perfect_strategy.Strategy(game)

print("=" * 70)
print("小规模测试 4×4 (max_move=4)")
print("=" * 70)
print(f"测试规模: 1,000 个标准型")
print(f"预计时间: < 1 分钟")
print(f"目的: 验证代码逻辑正确性")
print("=" * 70)

input("按 Enter 键开始测试，或 Ctrl+C 取消...")

start_time = time.time()

# 小规模训练
strategy.train(max_states=1000)

elapsed_time = time.time() - start_time

print("\n" + "=" * 70)
print("测试完成!")
print("=" * 70)
print(f"总耗时: {elapsed_time:.1f} 秒")
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

print("\n✓ 如果没有报错，说明代码逻辑正确")
print("下一步: 运行 test_4x4_m4_medium.py 进行中等规模测试")
