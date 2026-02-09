"""
测试 4×4 (max_move=3) 策略的训练
先用小样本测试，确保代码正确后再进行完整训练
"""

from Game import GameBase
import strategies.perfect4x4_m3.perfect_strategy as perfect_strategy

# 创建游戏实例
game = GameBase(4, 3)

# 创建策略实例
strategy = perfect_strategy.Strategy(game)

print("=" * 60)
print("测试模式：训练前 1000 个标准型")
print("=" * 60)

# 小范围测试
strategy.train(max_states=1000)

print("\n" + "=" * 60)
print("测试结果:")
print("=" * 60)
print(f"总状态数: {len(strategy.solver.dp)}")
print(f"Win状态数: {len(strategy.solver.win)}")
print(f"Lose状态数: {len(strategy.solver.lose)}")

# 显示一些DP值统计
dp_win_0 = sum(1 for s in strategy.solver.dp if strategy.solver.dp[s][0] == 1)
dp_lose_0 = sum(1 for s in strategy.solver.dp if strategy.solver.dp[s][0] == -1)
dp_draw_0 = sum(1 for s in strategy.solver.dp if strategy.solver.dp[s][0] == 0)

print(f"\nPlayer 0 (先手) 视角:")
print(f"  必胜状态: {dp_win_0}")
print(f"  必败状态: {dp_lose_0}")
print(f"  平局/未定: {dp_draw_0}")

dp_win_1 = sum(1 for s in strategy.solver.dp if strategy.solver.dp[s][1] == 1)
dp_lose_1 = sum(1 for s in strategy.solver.dp if strategy.solver.dp[s][1] == -1)
dp_draw_1 = sum(1 for s in strategy.solver.dp if strategy.solver.dp[s][1] == 0)

print(f"\nPlayer 1 (后手) 视角:")
print(f"  必胜状态: {dp_win_1}")
print(f"  必败状态: {dp_lose_1}")
print(f"  平局/未定: {dp_draw_1}")

print("\n" + "=" * 60)
print("如果以上结果看起来合理，可以进行完整训练:")
print("  strategy.train()  # 无参数 = 完整训练")
print("=" * 60)
