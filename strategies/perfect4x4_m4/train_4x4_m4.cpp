// train_4x4_m4.cpp
// 将 perfect4x4_m4/perfect_strategy.py 的训练器逻辑完整改写为 C++
//
// 规则：4×4棋盘，max_move=4，胜利条件=4连子
//
// 输出格式（与 perfect_strategy.py 的 load_training_data_mmap 兼容）：
//   [8字节: 记录数 uint64_t]
//   每条记录 14字节：
//     [8字节: state_code uint64_t]
//     [1字节: dp0        int8_t  ]
//     [1字节: dp1        int8_t  ]
//     [2字节: depth0     uint16_t]
//     [2字节: depth1     uint16_t]
//   记录按 state_code 升序排列
//
// 编译：g++ -O2 -std=c++17 -o train_4x4_m4 train_4x4_m4.cpp
// 运行：./train_4x4_m4 [输出文件名]

#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdio>
#include <ctime>
#include <queue>
#include <unordered_map>
#include <unordered_set>
#include <vector>

// ─────────────────────────────────────────────
// 常量
// ─────────────────────────────────────────────
static const int N         = 4;
static const int CELLS     = N * N;      // 16
static const int MAX_MOVE  = 4;          // 每方最多保留棋子数，也是胜利所需连子数
static const int BASE      = 17;         // pos+1 最大16，需要基数≥17
static const uint64_t SEPARATOR = 83521; // BASE^MAX_MOVE = 17^4

// ─────────────────────────────────────────────
// SymmetryHelper：8种对称变换（与 Python 完全一致）
// 位置编号：
//  0  1  2  3
//  4  5  6  7
//  8  9 10 11
// 12 13 14 15
// ─────────────────────────────────────────────
static const int TRANSFORMS[8][CELLS] = {
    // 0: 恒等
    { 0, 1, 2, 3, 4, 5, 6, 7, 8, 9,10,11,12,13,14,15},
    // 1: 逆时针90°
    { 3, 7,11,15, 2, 6,10,14, 1, 5, 9,13, 0, 4, 8,12},
    // 2: 180°
    {15,14,13,12,11,10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0},
    // 3: 顺时针90°
    {12, 8, 4, 0,13, 9, 5, 1,14,10, 6, 2,15,11, 7, 3},
    // 4: 水平翻转
    { 3, 2, 1, 0, 7, 6, 5, 4,11,10, 9, 8,15,14,13,12},
    // 5: 垂直翻转
    {12,13,14,15, 8, 9,10,11, 4, 5, 6, 7, 0, 1, 2, 3},
    // 6: 主对角线翻转
    { 0, 4, 8,12, 1, 5, 9,13, 2, 6,10,14, 3, 7,11,15},
    // 7: 副对角线翻转
    {15,11, 7, 3,14,10, 6, 2,13, 9, 5, 1,12, 8, 4, 0},
};

// ─────────────────────────────────────────────
// 编码 / 解码（与 Python encode/decode 完全一致）
// ─────────────────────────────────────────────
static uint64_t encode_list(const std::vector<int>& pos) {
    uint64_t code = 0, base = 1;
    for (int p : pos) {
        code += (uint64_t)(p + 1) * base;
        base *= BASE;
    }
    return code;
}

static uint64_t encode_state(const std::vector<int>& x, const std::vector<int>& y) {
    return encode_list(x) * SEPARATOR + encode_list(y);
}

// 返回 false 表示非法（含中间零、重复位置）
static bool decode_list(uint64_t code, std::vector<int>& positions) {
    positions.clear();
    while (code > 0) {
        int digit = (int)(code % BASE);
        if (digit == 0) return false;
        positions.push_back(digit - 1);
        code /= BASE;
    }
    std::unordered_set<int> seen(positions.begin(), positions.end());
    if (seen.size() != positions.size()) return false;
    return true;
}

// ─────────────────────────────────────────────
// 标准化（canonicalize）
// ─────────────────────────────────────────────
struct CanonResult {
    std::vector<int> x, y;
    int trans_id;
    uint64_t code;
};

static CanonResult canonicalize(const std::vector<int>& x, const std::vector<int>& y) {
    CanonResult best;
    best.code = UINT64_MAX;
    best.trans_id = 0;
    for (int t = 0; t < 8; t++) {
        std::vector<int> xt, yt;
        for (int p : x) xt.push_back(TRANSFORMS[t][p]);
        for (int p : y) yt.push_back(TRANSFORMS[t][p]);
        uint64_t c = encode_state(xt, yt);
        if (c < best.code) {
            best.code = c;
            best.trans_id = t;
            best.x = xt;
            best.y = yt;
        }
    }
    return best;
}

// ─────────────────────────────────────────────
// 胜负判断：与 GameBase.get_result() 完全一致
// 从 pos 出发，沿4个方向检查是否有 MAX_MOVE 个连续同色棋子
// ─────────────────────────────────────────────
static const int DIR_R[4] = {-1,  0, -1, -1};
static const int DIR_C[4] = { 0, -1, -1,  1};

static bool check_win_at(const int board[CELLS], int pos) {
    int val = board[pos];
    if (val == 0) return false;
    int r = pos / N, c = pos % N;
    for (int d = 0; d < 4; d++) {
        int left = 0, right = 0;
        int r_ = r, c_ = c;
        for (int k = 0; k < MAX_MOVE - 1; k++) {
            r_ += DIR_R[d]; c_ += DIR_C[d];
            if (r_>=0 && r_<N && c_>=0 && c_<N && board[r_*N+c_]==val) left++;
            else break;
        }
        r_ = r; c_ = c;
        for (int k = 0; k < MAX_MOVE - 1; k++) {
            r_ -= DIR_R[d]; c_ -= DIR_C[d];
            if (r_>=0 && r_<N && c_>=0 && c_<N && board[r_*N+c_]==val) right++;
            else break;
        }
        if (left + right + 1 >= MAX_MOVE) return true;
    }
    return false;
}

// 与 Python train() 中的胜负检查完全一致：
// 只在 len >= 3 时才检查；先检查 x_canon[0]，再检查 y_canon[0]
static int check_result(const std::vector<int>& x, const std::vector<int>& y) {
    int board[CELLS] = {};
    for (int p : x) board[p] =  1;
    for (int p : y) board[p] = -1;
    if ((int)x.size() >= 3 && check_win_at(board, x[0])) return  1;
    if ((int)y.size() >= 3 && check_win_at(board, y[0])) return -1;
    return 0;
}

// ─────────────────────────────────────────────
// 博弈图数据结构
// ─────────────────────────────────────────────
struct StateInfo {
    std::array<int8_t,  2> dp    = {0, 0};
    std::array<uint16_t,2> depth = {0, 0};
};

static std::unordered_map<uint64_t, StateInfo>             g_states;
static std::unordered_map<uint64_t, std::vector<uint64_t>> g_edge0, g_edge1;
static std::unordered_set<uint64_t>                        g_wins, g_loses;

static void add_state(uint64_t s) {
    if (!g_states.count(s)) {
        g_states[s];
        g_edge0[s];
        g_edge1[s];
    }
}

static void add_edge(uint64_t from_s, uint64_t to_s, int player) {
    uint64_t x_code = to_s / SEPARATOR;
    uint64_t y_code = to_s % SEPARATOR;
    std::vector<int> x, y;
    if (!decode_list(x_code, x)) return;
    if (!decode_list(y_code, y)) return;
    int lx = (int)x.size(), ly = (int)y.size();
    if (lx != ly && lx != ly + 1) return;
    std::unordered_set<int> sy(y.begin(), y.end());
    for (int p : x) if (sy.count(p)) return;

    add_state(from_s);
    add_state(to_s);
    if (player == 0) g_edge0[from_s].push_back(to_s);
    else             g_edge1[from_s].push_back(to_s);
}

// ─────────────────────────────────────────────
// 预计算 x_valid 和 y_valid（与 Python train() 中完全一致）
// x_valid：标准型 x_code，最高位（最后解码的digit）∈ {1,2,6}
// y_valid：所有合法 y_code
// ─────────────────────────────────────────────
static void precompute_valid(std::vector<uint64_t>& x_valid,
                              std::vector<uint64_t>& y_valid) {
    static const std::unordered_set<int> valid_first = {1, 2, 6};

    for (uint64_t code = 0; code < SEPARATOR; code++) {
        std::vector<int> positions;
        if (!decode_list(code, positions)) continue;

        // y_valid：所有合法 code
        y_valid.push_back(code);

        // x_valid：额外要求最高位（positions.back()+1）∈ {1,2,6}
        // 空列表（code=0）也算合法
        if (positions.empty() || valid_first.count(positions.back() + 1)) {
            x_valid.push_back(code);
        }
    }
}

// ─────────────────────────────────────────────
// solve()：逆向 BFS，与 Python GameTreeSolver.solve() 完全一致
// ─────────────────────────────────────────────
static void solve() {
    std::unordered_map<uint64_t, std::vector<uint64_t>> e0r, e1r;
    for (auto& [s, _] : g_states) { e0r[s]; e1r[s]; }
    for (auto& [s, v] : g_edge0) for (uint64_t t : v) e0r[t].push_back(s);
    for (auto& [s, v] : g_edge1) for (uint64_t t : v) e1r[t].push_back(s);

    std::unordered_map<uint64_t, std::array<int,2>> need;
    for (auto& [s, _] : g_states)
        need[s] = {(int)g_edge0[s].size(), (int)g_edge1[s].size()};

    int win_cnt = 0, lose_cnt = 0;
    std::queue<uint64_t> q;

    for (uint64_t s : g_wins) q.push(s);
    while (!q.empty()) {
        uint64_t x = q.front(); q.pop();
        for (uint64_t y : e0r[x]) {
            if (g_states[y].dp[0] == 1) continue;
            g_states[y].dp[0] = 1;
            g_states[y].depth[0] = g_states[x].depth[1] + 1;
            win_cnt++;
            for (uint64_t z : e1r[y]) {
                if (--need[z][1] == 0) {
                    q.push(z);
                    g_states[z].dp[1] = 1;
                    g_states[z].depth[1] = g_states[y].depth[0] + 1;
                    win_cnt++;
                }
            }
        }
    }

    for (uint64_t s : g_loses) q.push(s);
    while (!q.empty()) {
        uint64_t x = q.front(); q.pop();
        for (uint64_t y : e1r[x]) {
            if (g_states[y].dp[1] == -1) continue;
            g_states[y].dp[1] = -1;
            g_states[y].depth[1] = g_states[x].depth[0] + 1;
            lose_cnt++;
            for (uint64_t z : e0r[y]) {
                if (--need[z][0] == 0) {
                    q.push(z);
                    g_states[z].dp[0] = -1;
                    g_states[z].depth[0] = g_states[y].depth[1] + 1;
                    lose_cnt++;
                }
            }
        }
    }

    printf("  win  传播更新: %d 次\n", win_cnt);
    printf("  lose 传播更新: %d 次\n", lose_cnt);
}

// ─────────────────────────────────────────────
// save()：8字节头，按 state_code 升序
// ─────────────────────────────────────────────
static void save(const char* filename) {
    std::vector<uint64_t> keys;
    keys.reserve(g_states.size());
    for (auto& [k, _] : g_states) keys.push_back(k);
    std::sort(keys.begin(), keys.end());

    FILE* f = fopen(filename, "wb");
    if (!f) { fprintf(stderr, "无法打开文件: %s\n", filename); return; }

    uint64_t n = keys.size();
    fwrite(&n, sizeof(uint64_t), 1, f);
    for (uint64_t k : keys) {
        auto& info = g_states[k];
        fwrite(&k,             sizeof(uint64_t), 1, f);
        fwrite(&info.dp[0],    sizeof(int8_t),   1, f);
        fwrite(&info.dp[1],    sizeof(int8_t),   1, f);
        fwrite(&info.depth[0], sizeof(uint16_t), 1, f);
        fwrite(&info.depth[1], sizeof(uint16_t), 1, f);
    }
    fclose(f);
}

// ─────────────────────────────────────────────
// train()：与 Python Strategy.train() 完全一致
// 使用预计算的 x_valid / y_valid 优化枚举空间
// ─────────────────────────────────────────────
static void train(const std::vector<uint64_t>& x_valid,
                  const std::vector<uint64_t>& y_valid) {
    std::unordered_set<uint64_t> canons;
    long long scanned = 0;
    int report_interval = 5000000; // 每500万次打印一次进度

    clock_t t_start = clock();

    for (uint64_t x_code : x_valid) {
        for (uint64_t y_code : y_valid) {
            scanned++;

            if (scanned % report_interval == 0) {
                double elapsed = (double)(clock() - t_start) / CLOCKS_PER_SEC;
                double total = (double)x_valid.size() * y_valid.size();
                double pct = scanned / total * 100.0;
                double rate = scanned / elapsed;
                double eta = (total - scanned) / rate / 60.0;
                printf("  扫描: %.1f%%  标准型: %zu  速度: %.0f/秒  剩余: %.1f分\n",
                       pct, canons.size(), rate, eta);
                fflush(stdout);
            }

            uint64_t code = x_code * SEPARATOR + y_code;

            std::vector<int> x, y;
            // x_valid/y_valid 已保证合法，直接解码
            {
                uint64_t tmp = x_code;
                while (tmp) { x.push_back((int)(tmp % BASE) - 1); tmp /= BASE; }
            }
            {
                uint64_t tmp = y_code;
                while (tmp) { y.push_back((int)(tmp % BASE) - 1); tmp /= BASE; }
            }

            int lx = (int)x.size(), ly = (int)y.size();
            if (lx != ly && lx != ly + 1) continue;

            // 重叠检查
            std::unordered_set<int> sy(y.begin(), y.end());
            bool overlap = false;
            for (int p : x) { if (sy.count(p)) { overlap = true; break; } }
            if (overlap) continue;

            auto cr = canonicalize(x, y);
            if (canons.count(cr.code)) continue;
            canons.insert(cr.code);

            int result = check_result(cr.x, cr.y);
            if (result == 1) {
                g_wins.insert(cr.code);
                add_state(cr.code);
                g_states[cr.code].dp = {1, 1};
                continue;
            } else if (result == -1) {
                g_loses.insert(cr.code);
                add_state(cr.code);
                g_states[cr.code].dp = {-1, -1};
                continue;
            }

            // 非终局：枚举空位，建边
            int board[CELLS] = {};
            for (int p : cr.x) board[p] =  1;
            for (int p : cr.y) board[p] = -1;

            for (int t = 0; t < CELLS; t++) {
                if (board[t] != 0) continue;

                std::vector<int> x_new = cr.x, y_new = cr.y;
                x_new.push_back(t);
                y_new.push_back(t);
                if ((int)x_new.size() > MAX_MOVE) x_new.erase(x_new.begin());
                if ((int)y_new.size() > MAX_MOVE) y_new.erase(y_new.begin());

                auto c0 = canonicalize(x_new, cr.y);
                auto c1 = canonicalize(cr.x, y_new);
                add_edge(cr.code, c0.code, 0);
                add_edge(cr.code, c1.code, 1);
            }
        }
    }

    printf("  枚举完成:\n");
    printf("    扫描总量:   %lld\n", scanned);
    printf("    标准型总数: %zu\n", canons.size());
    printf("    win  状态:  %zu\n", g_wins.size());
    printf("    lose 状态:  %zu\n", g_loses.size());
    printf("    总状态数:   %zu\n", g_states.size());
}

// ─────────────────────────────────────────────
// main
// ─────────────────────────────────────────────
int main(int argc, char* argv[]) {
    const char* filename = (argc > 1) ? argv[1] : "game_tree_4x4_m4.data";

    printf("=== 4×4 训练器 (max_move=4, 胜利=4连子) ===\n\n");

    // 预计算
    clock_t t0 = clock();
    printf("[0/3] 预计算合法编码...\n");
    std::vector<uint64_t> x_valid, y_valid;
    precompute_valid(x_valid, y_valid);
    printf("  x_valid: %zu 个\n", x_valid.size());
    printf("  y_valid: %zu 个\n", y_valid.size());
    printf("  总枚举量: %zu × %zu = %llu\n",
           x_valid.size(), y_valid.size(),
           (unsigned long long)x_valid.size() * y_valid.size());
    printf("  耗时: %.3f 秒\n\n", (double)(clock()-t0)/CLOCKS_PER_SEC);

    // 枚举 + 建图
    t0 = clock();
    printf("[1/3] 枚举状态，构建博弈图...\n");
    train(x_valid, y_valid);
    printf("  耗时: %.1f 秒\n\n", (double)(clock()-t0)/CLOCKS_PER_SEC);

    // 求解
    t0 = clock();
    printf("[2/3] 求解博弈树...\n");
    solve();
    printf("  耗时: %.1f 秒\n\n", (double)(clock()-t0)/CLOCKS_PER_SEC);

    // 打印初始空棋盘状态
    uint64_t empty_code = canonicalize({}, {}).code;  // = 0
    printf("初始状态 (code=%lu):\n", (unsigned long)empty_code);
    if (g_states.count(empty_code)) {
        auto& info = g_states[empty_code];
        printf("  dp=[%d,%d]  depth=[%u,%u]\n",
               (int)info.dp[0], (int)info.dp[1],
               (unsigned)info.depth[0], (unsigned)info.depth[1]);
        const char* conclusion =
            (info.dp[0] == 1)  ? "先手(X)必胜" :
            (info.dp[0] == -1) ? "先手(X)必败，后手(O)必胜" : "平局/未定";
        printf("  结论: %s\n", conclusion);
    }
    printf("\n");

    // 保存
    t0 = clock();
    printf("[3/3] 排序并保存到 %s ...\n", filename);
    save(filename);
    printf("  记录数:   %zu\n", g_states.size());
    printf("  文件大小: %.1f MB\n", (8.0 + g_states.size() * 14.0) / 1024 / 1024);
    printf("  耗时: %.1f 秒\n", (double)(clock()-t0)/CLOCKS_PER_SEC);

    return 0;
}
