"""
完整训练 4×4 (max_move=3) Perfect AI
预计约 79.2万 个标准型，训练时间可能需要几分钟到十几分钟
"""

from Game import GameBase
import strategies.perfect4x4_m3.perfect_strategy as perfect_strategy
import time

# 创建游戏实例
game = GameBase(4, 3)

# 创建策略实例
strategy = perfect_strategy.Strategy(game)

print("=" * 70)
print("完整训练 4×4 (max_move=3) Perfect AI")
print("=" * 70)
print(f"标准型数量: 792,169 (已精确计算)")
print(f"预计总状态数: ~800,000 - 900,000")
print(f"预计训练时间: 10-30分钟（取决于CPU性能）")
print()
print("进度显示说明:")
print("  - 每秒更新一次进度")
print("  - 显示: 当前数量 / 792,169 (百分比)")
print("  - 估算剩余时间")
print("=" * 70)

input("按 Enter 键开始完整训练，或 Ctrl+C 取消...")

start_time = time.time()

# 完整训练
strategy.train()

elapsed_time = time.time() - start_time

print("\n" + "=" * 70)
print("训练完成!")
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

# 判断游戏性质
init_state_code = strategy.sym.encode([], [])
if init_state_code in strategy.solver.dp:
    dp_val = strategy.solver.dp[init_state_code]
    print(f"\n初始状态 dp 值: {dp_val}")
    if dp_val[0] == 1:
        print("结论: 先手(X)必胜!")
    elif dp_val[0] == -1:
        print("结论: 后手(O)必胜!")
    else:
        print("结论: 双方最优博弈下为平局或未定")

print("\n训练数据已保存，现在可以在UI中使用 Perfect AI 了！")
