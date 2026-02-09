"""
中等规模测试：10000个标准型
"""

from Game import GameBase
import strategies.perfect4x4_m3.perfect_strategy as perfect_strategy

# 创建游戏实例
game = GameBase(4, 3)

# 创建策略实例
strategy = perfect_strategy.Strategy(game)

print("=" * 60)
print("中等测试：训练 10,000 个标准型")
print("=" * 60)

# 中等规模测试
strategy.train(max_states=10000)

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

# 如果有win状态，显示几个示例
if strategy.solver.win:
    print(f"\n示例Win状态（前5个）:")
    for i, state in enumerate(list(strategy.solver.win)[:5]):
        print(f"  状态码: {state}")
