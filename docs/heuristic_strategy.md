# Heuristic AI Strategy

## Overview
The `heuristic_strategy.py` file implements a heuristic-based AI for the limited-move Tic-Tac-Toe game. It is designed to be smarter than the Random AI and adapt to different game configurations (board size N, max moves M, win count K).

## Core Design Philosophy
The AI uses a modular, parameter-adaptive approach that dynamically adjusts to game parameters:
- **Dynamic pattern detection** based on the win count (K)
- **Adaptive weight calculation** based on both K and M
- **Universal evaluation** that combines multiple strategic factors

## Key Components

### 1. DynamicPatternDetector
**Purpose**: Detects threats and potential winning patterns of varying lengths based on the current win count (K).

**Key Features**:
- Classifies threats into four levels:
  - `immediate_win`: One move away from victory (length = K-1)
  - `one_move_threat`: Two moves away from victory (length = K-2)
  - `building_threat`: Three moves away (length = K-3)
  - `potential_threat`: Longer-term threats
- Searches for patterns in all directions (horizontal, vertical, diagonal)
- Filters out lines blocked by opponent pieces

### 2. AdaptiveWeightCalculator
**Purpose**: Dynamically calculates weights for different threat lengths based on game parameters K and M.

**Key Features**:
- Higher weights for threats closer to victory
- Time factor adjustment: shorter M values prioritize immediate threats
- Three time horizons:
  - Short-term (M ≤ 3): Strong focus on new threats
  - Medium-term (M ≤ 8): Balanced approach
  - Long-term (M > 8): Minimal age-based decay

### 3. UniversalEvaluator
**Purpose**: Integrates all evaluation factors into a single score.

**Evaluation Factors**:
- **Threat assessment**: Scores both offensive threats and defensive blocks
- **Position control**: Values center positions and areas with high player density
- **Age-based adjustment**: Considers piece aging and imminent disappearance
1. **Threat-based scoring**: Immediate wins (10,000), one-move threats (5,000), building threats (1,000), potential threats (100)
2. **Position control**: Center positions are more valuable
3. **Time adjustment**: Considers piece aging and imminent disappearance

### 4. Strategy (Main AI Class)
**Purpose**: The main AI controller that makes moves based on heuristic evaluation.

**Decision Process**:
1. Evaluates all empty positions on the board
2. For each position, simulates placing a piece there
3. Scores the resulting position using multiple factors:
   - Threat creation in all directions
   - Position control (center vs edge)
   - Potential to complete lines of length K
4. Selects the position with the highest score

## How It Works

### Move Selection Algorithm
```
For each empty cell:
  1. Simulate placing AI's piece there
  2. Evaluate the resulting position:
     - Check for immediate wins (length >= K)
     - Check for one-move threats (length = K-1)
     - Check for building threats (length >= K-2)
     - Calculate position control value
  3. Score = threat_score + position_score
  4. Select cell with highest score
```

### Parameter Adaptation
- **K (win count)**: Determines what constitutes a threat (K-1, K-2, etc.)
- **M (max moves)**: Influences time horizon and age-based decay
- **N (board size)**: Affects position control calculations

## Integration Points
- Used as the default AI in `display.py` (index 2 in strategy dropdown)
- Replaces the Random AI for better gameplay
- Works with all board sizes (3-15) and configurations

## Limitations and Future Improvements
1. **No lookahead**: Currently evaluates only one move ahead
2. **Simplified age tracking**: Age information is not fully integrated
3. **No opponent modeling**: Doesn't explicitly model opponent's strategy
4. **Performance**: Could be optimized for larger boards

## Quick Start for AI Developers
To understand or modify this AI:
1. **Start with `Strategy.make_move()`** - Main decision entry point
2. **Check `_evaluate_position_score()`** - Core scoring logic
3. **Review `UniversalEvaluator`** - Integrated scoring system
4. **Examine `DynamicPatternDetector`** - Threat detection logic
5. **See `AdaptiveWeightCalculator`** - Parameter adaptation

The AI is designed to be easily extensible - new evaluation factors can be added to `UniversalEvaluator` without changing the overall architecture.