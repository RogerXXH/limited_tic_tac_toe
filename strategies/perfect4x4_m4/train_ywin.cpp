// train_ywin.cpp
// 4×4 max_move=4 Y-win 状态的无边 BFS 训练器
//
// 与 train_xwin.cpp 完全对称：
//   Phase 1: 枚举所有标准型，找终局 Y-win 状态
//   Phase 2: 为每个非终局状态计算 x 后继数量 (need[])
//   Phase 3: 无边 BFS 传播 Y-win 的 Type A' 和 Type B'
//   Phase 4: 保存结果
//
// Type A' (dp[1]=-1): Y 有制胜手（能走到某个 Type B'）
// Type B' (dp[0]=-1): X 的所有走法均通向 Type A'
// 终局 Y-win 状态 = Type B'（Y 刚赢，只讨论 lose 侧）
//
// 内存估算：
//   codes[]    583 MB  (72.8M × uint64)
//   need[]      73 MB  (72.8M × uint8)
//   dp_flags[]  73 MB  (72.8M × uint8)
//   depth_0[]  146 MB  (72.8M × uint16)
//   depth_1[]  146 MB  (72.8M × uint16)
//   合计约 1 GB，远低于 9.7 GB 上限
//
// 编译: g++ -O2 -std=c++17 -o train_ywin train_ywin.cpp

#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <ctime>
#include <queue>
#include <unordered_set>
#include <vector>

// ─────────────────────────────────────────────────────────
// 常量
// ─────────────────────────────────────────────────────────
static const int      CELLS    = 16;
static const int      MAX_MOVE = 4;
static const int      BASE     = 17;
static const uint64_t SEP      = 83521ULL; // 17^4

// ─────────────────────────────────────────────────────────
// 对称变换（与 train_xwin.cpp 完全一致）
// ─────────────────────────────────────────────────────────
static const int TR[8][16] = {
    { 0, 1, 2, 3, 4, 5, 6, 7, 8, 9,10,11,12,13,14,15},
    { 3, 7,11,15, 2, 6,10,14, 1, 5, 9,13, 0, 4, 8,12},
    {15,14,13,12,11,10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0},
    {12, 8, 4, 0,13, 9, 5, 1,14,10, 6, 2,15,11, 7, 3},
    { 3, 2, 1, 0, 7, 6, 5, 4,11,10, 9, 8,15,14,13,12},
    {12,13,14,15, 8, 9,10,11, 4, 5, 6, 7, 0, 1, 2, 3},
    { 0, 4, 8,12, 1, 5, 9,13, 2, 6,10,14, 3, 7,11,15},
    {15,11, 7, 3,14,10, 6, 2,13, 9, 5, 1,12, 8, 4, 0},
};

// ─────────────────────────────────────────────────────────
// 编码 / 解码 / 标准化
// ─────────────────────────────────────────────────────────
static uint64_t encode(const int* pos, int n) {
    uint64_t code = 0, base = 1;
    for (int i = 0; i < n; i++) { code += (uint64_t)(pos[i]+1)*base; base *= BASE; }
    return code;
}

static uint64_t encode_state(const int* x, int lx, const int* y, int ly) {
    return encode(x, lx) * SEP + encode(y, ly);
}

// 解码到固定数组；返回元素个数
static int decode_list(uint64_t code, int* out) {
    int n = 0;
    while (code) { out[n++] = (int)(code % BASE) - 1; code /= BASE; }
    return n;
}

static void decode_state(uint64_t state_code, int* x, int& lx, int* y, int& ly) {
    lx = decode_list(state_code / SEP, x);
    ly = decode_list(state_code % SEP, y);
}

// 返回最小 state_code（标准型）
static uint64_t canonicalize(const int* x, int lx, const int* y, int ly) {
    uint64_t best = UINT64_MAX;
    int xt[4], yt[4];
    for (int t = 0; t < 8; t++) {
        for (int i = 0; i < lx; i++) xt[i] = TR[t][x[i]];
        for (int i = 0; i < ly; i++) yt[i] = TR[t][y[i]];
        uint64_t c = encode_state(xt, lx, yt, ly);
        if (c < best) best = c;
    }
    return best;
}

// ─────────────────────────────────────────────────────────
// 胜负判断（与 train_xwin.cpp 完全一致）
// ─────────────────────────────────────────────────────────
static const int DR[4] = {-1, 0,-1,-1};
static const int DC[4] = { 0,-1,-1, 1};

static bool check_win_at(const int board[CELLS], int pos) {
    int val = board[pos];
    if (!val) return false;
    int r = pos/4, c = pos%4;
    for (int d = 0; d < 4; d++) {
        int left=0, right=0, r_=r, c_=c;
        for (int k=0;k<MAX_MOVE-1;k++) {
            r_+=DR[d]; c_+=DC[d];
            if (r_>=0&&r_<4&&c_>=0&&c_<4&&board[r_*4+c_]==val) left++; else break;
        }
        r_=r; c_=c;
        for (int k=0;k<MAX_MOVE-1;k++) {
            r_-=DR[d]; c_-=DC[d];
            if (r_>=0&&r_<4&&c_>=0&&c_<4&&board[r_*4+c_]==val) right++; else break;
        }
        if (left+right+1 >= MAX_MOVE) return true;
    }
    return false;
}

// 返回 1=X赢, -1=Y赢, 0=未结束
static int check_result(const int* x, int lx, const int* y, int ly) {
    int board[CELLS] = {};
    for (int i=0;i<lx;i++) board[x[i]] =  1;
    for (int i=0;i<ly;i++) board[y[i]] = -1;
    if (lx>=3 && check_win_at(board, x[0])) return  1;
    if (ly>=3 && check_win_at(board, y[0])) return -1;
    return 0;
}

// ─────────────────────────────────────────────────────────
// 预计算 x_valid / y_valid
// ─────────────────────────────────────────────────────────
static void precompute_valid(std::vector<uint64_t>& xv, std::vector<uint64_t>& yv) {
    for (uint64_t code = 0; code < SEP; code++) {
        int pos[4]; int n = 0;
        bool ok = true;
        uint64_t tmp = code;
        while (tmp) {
            int d = (int)(tmp % BASE);
            if (d == 0) { ok = false; break; }
            pos[n++] = d-1;
            tmp /= BASE;
        }
        if (!ok) continue;
        // 检查重复
        bool dup = false;
        for (int i=0;i<n&&!dup;i++)
            for (int j=i+1;j<n;j++) if (pos[i]==pos[j]) { dup=true; break; }
        if (dup) continue;

        yv.push_back(code);

        // x_valid：最高位（pos[n-1]+1）∈ {1,2,6}，或空
        if (n == 0 || pos[n-1]+1==1 || pos[n-1]+1==2 || pos[n-1]+1==6)
            xv.push_back(code);
    }
}

// ─────────────────────────────────────────────────────────
// 二分查找（返回下标，-1 表示不存在）
// ─────────────────────────────────────────────────────────
static int64_t find_idx(const std::vector<uint64_t>& codes, uint64_t code) {
    auto it = std::lower_bound(codes.begin(), codes.end(), code);
    if (it != codes.end() && *it == code) return (int64_t)(it - codes.begin());
    return -1;
}

// ─────────────────────────────────────────────────────────
// get_x_preds: X 走到 (x,y) 的所有前驱（去重后的标准型 code）
//   无溢出: x_prev = x[:-1]，要求 len(x) > len(y)
//   有溢出: x_prev = [fallen]+x[:-1]，要求 len(x)==MAX_MOVE
// ─────────────────────────────────────────────────────────
static int get_x_preds(const int* x, int lx, const int* y, int ly,
                        uint64_t* out) {
    int cnt = 0;
    if (lx == 0) return 0;

    uint32_t occ = 0;
    for (int i=0;i<lx;i++) occ |= 1u<<x[i];
    for (int i=0;i<ly;i++) occ |= 1u<<y[i];

    uint64_t seen[9]; int nseen = 0;
    auto add = [&](uint64_t c) {
        for (int i=0;i<nseen;i++) if (seen[i]==c) return;
        seen[nseen++] = c;
        out[cnt++] = c;
    };

    if (lx > ly) {
        add(canonicalize(x, lx-1, y, ly));
    }
    if (lx == MAX_MOVE) {
        int xprev[4];
        for (int i=0;i<lx-1;i++) xprev[i+1] = x[i];
        for (int f=0; f<CELLS; f++) {
            if (occ & (1u<<f)) continue;
            xprev[0] = f;
            add(canonicalize(xprev, lx, y, ly));
        }
    }
    return cnt;
}

// ─────────────────────────────────────────────────────────
// get_y_preds: Y 走到 (x,y) 的所有前驱
//   无溢出: y_prev = y[:-1]，要求 len(y) >= 1
//   有溢出: y_prev = [fallen]+y[:-1]，要求 len(y)==MAX_MOVE
// ─────────────────────────────────────────────────────────
static int get_y_preds(const int* x, int lx, const int* y, int ly,
                        uint64_t* out) {
    int cnt = 0;
    if (ly == 0) return 0;

    uint32_t occ = 0;
    for (int i=0;i<lx;i++) occ |= 1u<<x[i];
    for (int i=0;i<ly;i++) occ |= 1u<<y[i];

    uint64_t seen[9]; int nseen = 0;
    auto add = [&](uint64_t c) {
        for (int i=0;i<nseen;i++) if (seen[i]==c) return;
        seen[nseen++] = c;
        out[cnt++] = c;
    };

    add(canonicalize(x, lx, y, ly-1));

    if (ly == MAX_MOVE) {
        int yprev[4];
        for (int i=0;i<ly-1;i++) yprev[i+1] = y[i];
        for (int f=0; f<CELLS; f++) {
            if (occ & (1u<<f)) continue;
            yprev[0] = f;
            add(canonicalize(x, lx, yprev, ly));
        }
    }
    return cnt;
}

// ─────────────────────────────────────────────────────────
// get_x_succs: (x,y) 的所有 x 后继（用于初始化 need[]）
//   X 在空位落子，合法条件：len(y) >= len(x_new) - 1
// ─────────────────────────────────────────────────────────
static int get_x_succs(const int* x, int lx, const int* y, int ly,
                        uint64_t* out) {
    int cnt = 0;
    uint32_t occ = 0;
    for (int i=0;i<lx;i++) occ |= 1u<<x[i];
    for (int i=0;i<ly;i++) occ |= 1u<<y[i];

    uint64_t seen[16]; int nseen = 0;
    auto add = [&](uint64_t c) {
        for (int i=0;i<nseen;i++) if (seen[i]==c) return;
        seen[nseen++] = c;
        out[cnt++] = c;
    };

    int xnew[4];
    for (int pos=0; pos<CELLS; pos++) {
        if (occ & (1u<<pos)) continue;
        int lnew;
        if (lx < MAX_MOVE) {
            for (int i=0;i<lx;i++) xnew[i]=x[i];
            xnew[lx] = pos;
            lnew = lx+1;
        } else {
            for (int i=0;i<lx-1;i++) xnew[i]=x[i+1];
            xnew[lx-1] = pos;
            lnew = lx;
        }
        if (ly < lnew - 1) continue;
        add(canonicalize(xnew, lnew, y, ly));
    }
    return cnt;
}

// ─────────────────────────────────────────────────────────
// 主函数
// ─────────────────────────────────────────────────────────
int main(int argc, char* argv[]) {
    const char* outfile = (argc > 1) ? argv[1] : "ywin_4x4_m4.data";
    clock_t t0;

    printf("=== 4×4 Y-win 训练器 (无边 BFS) ===\n\n");

    // ── 预计算 x_valid / y_valid ──────────────────────────
    t0 = clock();
    printf("[0] 预计算合法编码...\n");
    std::vector<uint64_t> xv, yv;
    precompute_valid(xv, yv);
    printf("    x_valid=%zu  y_valid=%zu  总枚举量=%llu\n",
           xv.size(), yv.size(),
           (unsigned long long)xv.size()*yv.size());
    printf("    耗时 %.3f 秒\n\n", (double)(clock()-t0)/CLOCKS_PER_SEC);

    // ── Phase 1：枚举所有标准型 ───────────────────────────
    t0 = clock();
    printf("[1] 枚举标准型...\n");

    std::unordered_set<uint64_t> canon_set;
    canon_set.reserve(80000000);
    std::vector<uint64_t> terminal_wins;

    long long scanned = 0;
    long long total_combos = (long long)xv.size() * yv.size();

    for (uint64_t xcode : xv) {
        int x[4], lx = decode_list(xcode, x);

        for (uint64_t ycode : yv) {
            scanned++;

            if (scanned % 5000000 == 0) {
                double now = (double)(clock()-t0)/CLOCKS_PER_SEC;
                double pct = 100.0*scanned/total_combos;
                printf("    %.1f%%  标准型:%zu  速度:%.0f/s  剩余:%.1f分\n",
                       pct, canon_set.size(),
                       scanned/now, (total_combos-scanned)/scanned*(now/60.0));
                fflush(stdout);
            }

            int y[4], ly = decode_list(ycode, y);

            if (lx != ly && lx != ly+1) continue;
            uint32_t yset = 0;
            for (int i=0;i<ly;i++) yset |= 1u<<y[i];
            bool overlap = false;
            for (int i=0;i<lx;i++) if (yset & (1u<<x[i])) { overlap=true; break; }
            if (overlap) continue;

            uint64_t canon = canonicalize(x, lx, y, ly);
            if (canon_set.count(canon)) continue;
            canon_set.insert(canon);

            int res = check_result(x, lx, y, ly);
            if (res == -1) terminal_wins.push_back(canon);
        }
    }

    printf("    枚举完成：标准型=%zu  Y-win终局=%zu\n",
           canon_set.size(), terminal_wins.size());
    printf("    耗时 %.1f 秒\n\n", (double)(clock()-t0)/CLOCKS_PER_SEC);

    printf("    排序中...\n"); fflush(stdout);
    std::vector<uint64_t> codes(canon_set.begin(), canon_set.end());
    std::sort(codes.begin(), codes.end());
    uint32_t N = (uint32_t)codes.size();
    printf("    排序完成，N=%u\n\n", N);

    // ── 分配数组 ─────────────────────────────────────────
    printf("[1.5] 分配数组 (约 %.0f MB)...\n",
           (double)N * (1+1+2+2) / 1024.0 / 1024.0);
    std::vector<uint8_t>  need(N, 0);
    std::vector<uint8_t>  dp_flags(N, 0);
    std::vector<uint16_t> depth_0(N, 0);
    std::vector<uint16_t> depth_1(N, 0);

    for (uint64_t code : terminal_wins) {
        int64_t idx = find_idx(codes, code);
        if (idx >= 0) {
            dp_flags[idx] = 3;
            depth_0[idx] = 0;
            depth_1[idx] = 0;
        }
    }
    printf("    终局 Y-win 已标记\n\n");

    // ── Phase 2：计算 need[]（x 后继数量）─────────────────────
    t0 = clock();
    printf("[2] 计算 need[]（各状态的 x 后继数量）...\n");

    uint64_t succ_buf[16];
    for (uint32_t i = 0; i < N; i++) {
        if (dp_flags[i]) continue;

        int x[4], y[4], lx, ly;
        decode_state(codes[i], x, lx, y, ly);

        int ns = get_x_succs(x, lx, y, ly, succ_buf);
        need[i] = (uint8_t)ns;
    }

    printf("    需要传播的非终局状态：%u\n", N);
    printf("    耗时 %.1f 秒\n\n", (double)(clock()-t0)/CLOCKS_PER_SEC);

    { std::unordered_set<uint64_t> tmp; tmp.swap(canon_set); }
    printf("    canon_set 已释放\n\n");

    // ── Phase 3：无边 BFS（对称）──────────────────────────────
    t0 = clock();
    printf("[3] BFS 传播 Y-win...\n");

    std::queue<uint32_t> bfs;
    for (uint64_t code : terminal_wins) {
        int64_t idx = find_idx(codes, code);
        if (idx >= 0) bfs.push((uint32_t)idx);
    }

    uint64_t cnt_A = 0, cnt_B = terminal_wins.size();
    uint64_t iters = 0;

    uint64_t xpred_buf[9], ypred_buf[9];

    while (!bfs.empty()) {
        uint32_t i = bfs.front(); bfs.pop();
        iters++;

        if (iters % 1000000 == 0) {
            printf("    BFS: 已处理=%lu  TypeA=%lu  TypeB=%lu  队列=%zu\n",
                   iters, cnt_A, cnt_B, bfs.size());
            fflush(stdout);
        }

        int xi[4], yi[4], lxi, lyi;
        decode_state(codes[i], xi, lxi, yi, lyi);

        int np = get_y_preds(xi, lxi, yi, lyi, ypred_buf);
        for (int p = 0; p < np; p++) {
            int64_t j = find_idx(codes, ypred_buf[p]);
            if (j < 0) continue;
            if (dp_flags[j] & 2) continue;

            dp_flags[j] |= 2;
            depth_1[j] = depth_0[i] + 1;
            cnt_A++;

            int xj[4], yj[4], lxj, lyj;
            decode_state(codes[j], xj, lxj, yj, lyj);

            int nq = get_x_preds(xj, lxj, yj, lyj, xpred_buf);
            for (int q = 0; q < nq; q++) {
                int64_t k = find_idx(codes, xpred_buf[q]);
                if (k < 0) continue;
                if (dp_flags[k] & 1) continue;

                if (need[k] > 0) {
                    need[k]--;
                    if (need[k] == 0) {
                        dp_flags[k] |= 1;
                        depth_0[k] = depth_1[j] + 1;
                        cnt_B++;
                        bfs.push((uint32_t)k);
                    }
                }
            }
        }
    }

    printf("    BFS 完成：TypeA=%lu  TypeB=%lu\n", cnt_A, cnt_B);
    printf("    耗时 %.1f 秒\n\n", (double)(clock()-t0)/CLOCKS_PER_SEC);

    // ── Phase 4：保存（dp值取-1）─────────────────────────────
    t0 = clock();
    printf("[4] 保存到 %s ...\n", outfile);

    std::vector<uint32_t> win_indices;
    win_indices.reserve((uint32_t)(cnt_A + cnt_B));
    for (uint32_t i = 0; i < N; i++) {
        if (dp_flags[i]) win_indices.push_back(i);
    }

    FILE* f = fopen(outfile, "wb");
    if (!f) { fprintf(stderr, "无法打开文件: %s\n", outfile); return 1; }

    uint64_t nrec = win_indices.size();
    fwrite(&nrec, sizeof(uint64_t), 1, f);

    for (uint32_t i : win_indices) {
        int8_t  dp0 = (dp_flags[i] & 1) ? -1 : 0;
        int8_t  dp1 = (dp_flags[i] & 2) ? -1 : 0;
        uint16_t d0 = depth_0[i];
        uint16_t d1 = depth_1[i];
        fwrite(&codes[i], sizeof(uint64_t), 1, f);
        fwrite(&dp0,      sizeof(int8_t),   1, f);
        fwrite(&dp1,      sizeof(int8_t),   1, f);
        fwrite(&d0,       sizeof(uint16_t), 1, f);
        fwrite(&d1,       sizeof(uint16_t), 1, f);
    }
    fclose(f);

    printf("    记录数：%lu\n", nrec);
    printf("    文件大小：%.1f MB\n", (8.0 + nrec*14.0)/1024/1024);
    printf("    耗时 %.1f 秒\n\n", (double)(clock()-t0)/CLOCKS_PER_SEC);

    // ── 打印初始状态结果 ──────────────────────────────────
    uint64_t empty_code = 0;
    int64_t idx = find_idx(codes, empty_code);
    if (idx >= 0) {
        printf("初始状态 (空棋盘)：\n");
        printf("  dp[0]=%d  dp[1]=%d\n",
               (dp_flags[idx]&1)?-1:0, (dp_flags[idx]&2)?-1:0);
        printf("  depth[0]=%u  depth[1]=%u\n", depth_0[idx], depth_1[idx]);
        if (dp_flags[idx] & 2)
            printf("  结论：后手(Y) 必胜\n");
        else
            printf("  结论：后手(Y) 不能保证必胜（平局或先手必胜）\n");
    }

    printf("\n=== 完成 ===\n");
    return 0;
}
