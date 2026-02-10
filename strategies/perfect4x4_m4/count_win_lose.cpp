// count_win_lose.cpp
// 在枚举所有标准型的同时，统计 win/lose 终局状态的数量
//
// 编译：g++ -O2 -std=c++17 -o count_win_lose count_win_lose.cpp
// 运行：./count_win_lose

#include <algorithm>
#include <chrono>
#include <climits>
#include <iomanip>
#include <iostream>
#include <set>
#include <unordered_set>
#include <vector>

using namespace std;
using ll = long long;

static const int N        = 4;
static const int CELLS    = 16;
static const int MAX_MOVE = 4;
static const ll  SEPARATOR = 83521LL; // 17^4

static const int TRANSFORMS[8][16] = {
    { 0, 1, 2, 3, 4, 5, 6, 7, 8, 9,10,11,12,13,14,15},
    { 3, 7,11,15, 2, 6,10,14, 1, 5, 9,13, 0, 4, 8,12},
    {15,14,13,12,11,10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0},
    {12, 8, 4, 0,13, 9, 5, 1,14,10, 6, 2,15,11, 7, 3},
    { 3, 2, 1, 0, 7, 6, 5, 4,11,10, 9, 8,15,14,13,12},
    {12,13,14,15, 8, 9,10,11, 4, 5, 6, 7, 0, 1, 2, 3},
    { 0, 4, 8,12, 1, 5, 9,13, 2, 6,10,14, 3, 7,11,15},
    {15,11, 7, 3,14,10, 6, 2,13, 9, 5, 1,12, 8, 4, 0},
};

// ── 解码 ──────────────────────────────────────────────
static bool decode(ll code, vector<int>& pos) {
    pos.clear();
    while (code > 0) {
        int d = (int)(code % 17);
        if (d == 0) return false;
        pos.push_back(d - 1);
        code /= 17;
    }
    set<int> s(pos.begin(), pos.end());
    if (s.size() != pos.size()) return false;
    for (int p : pos) if (p >= 16) return false;
    return true;
}

// ── 编码 ──────────────────────────────────────────────
static ll encode(const vector<int>& x, const vector<int>& y) {
    ll xc = 0, yc = 0, pw = 1;
    for (int p : x) { xc += (p+1)*pw; pw *= 17; }
    pw = 1;
    for (int p : y) { yc += (p+1)*pw; pw *= 17; }
    return xc * SEPARATOR + yc;
}

// ── 标准化（返回 code + 变换后的 x, y）────────────────
struct Canon { ll code; vector<int> x, y; };

static Canon canonicalize(const vector<int>& x, const vector<int>& y) {
    Canon best; best.code = LLONG_MAX;
    for (int t = 0; t < 8; t++) {
        vector<int> xt, yt;
        for (int p : x) xt.push_back(TRANSFORMS[t][p]);
        for (int p : y) yt.push_back(TRANSFORMS[t][p]);
        ll c = encode(xt, yt);
        if (c < best.code) { best.code = c; best.x = xt; best.y = yt; }
    }
    return best;
}

// ── 胜负判断（与 train_4x4_m4.cpp 完全一致）──────────
static const int DIR_R[4] = {-1,  0, -1, -1};
static const int DIR_C[4] = { 0, -1, -1,  1};

static bool check_win_at(const int board[CELLS], int pos) {
    int val = board[pos];
    if (val == 0) return false;
    int r = pos / N, c = pos % N;
    for (int d = 0; d < 4; d++) {
        int left = 0, right = 0;
        int r_ = r, c_ = c;
        for (int k = 0; k < MAX_MOVE-1; k++) {
            r_ += DIR_R[d]; c_ += DIR_C[d];
            if (r_>=0&&r_<N&&c_>=0&&c_<N&&board[r_*N+c_]==val) left++; else break;
        }
        r_ = r; c_ = c;
        for (int k = 0; k < MAX_MOVE-1; k++) {
            r_ -= DIR_R[d]; c_ -= DIR_C[d];
            if (r_>=0&&r_<N&&c_>=0&&c_<N&&board[r_*N+c_]==val) right++; else break;
        }
        if (left + right + 1 >= MAX_MOVE) return true;
    }
    return false;
}

// 返回 1=X赢, -1=O赢, 0=未终局
static int check_result(const vector<int>& x, const vector<int>& y) {
    int board[CELLS] = {};
    for (int p : x) board[p] =  1;
    for (int p : y) board[p] = -1;
    if ((int)x.size() >= 3 && !x.empty() && check_win_at(board, x[0])) return  1;
    if ((int)y.size() >= 3 && !y.empty() && check_win_at(board, y[0])) return -1;
    return 0;
}

// ── main ──────────────────────────────────────────────
int main() {
    cout << "=== 统计 4×4 (max_move=4) win/lose 标准型数量 ===" << endl << endl;

    auto t0 = chrono::high_resolution_clock::now();

    // 预计算 x_valid / y_valid
    vector<ll> x_valid, y_valid;
    for (ll code = 0; code < SEPARATOR; code++) {
        vector<int> pos;
        if (!decode(code, pos)) continue;
        y_valid.push_back(code);
        if (pos.empty() || (pos.back()+1==1||pos.back()+1==2||pos.back()+1==6))
            x_valid.push_back(code);
    }
    cout << "x_valid: " << x_valid.size() << "  y_valid: " << y_valid.size()
         << "  总枚举量: " << (ll)x_valid.size()*y_valid.size() << endl << endl;

    // 枚举标准型并统计 win/lose
    unordered_set<ll> canons;
    canons.reserve(80000000); // 预分配，减少 rehash
    ll win_cnt = 0, lose_cnt = 0;

    ll total = (ll)x_valid.size() * y_valid.size();
    ll scanned = 0;
    auto last_report = t0;

    for (ll xc : x_valid) {
        vector<int> x;
        { ll tmp=xc; while(tmp){x.push_back((int)(tmp%17)-1);tmp/=17;} }

        for (ll yc : y_valid) {
            scanned++;

            // 进度（每2秒一次）
            auto now = chrono::high_resolution_clock::now();
            if (chrono::duration_cast<chrono::seconds>(now - last_report).count() >= 2) {
                double pct = 100.0 * scanned / total;
                double elapsed = chrono::duration_cast<chrono::milliseconds>(now-t0).count()/1000.0;
                double rate = scanned / elapsed;
                double eta = (total - scanned) / rate / 60.0;
                cout << fixed << setprecision(1)
                     << "  扫描: " << pct << "%  标准型: " << canons.size()
                     << "  win: " << win_cnt << "  lose: " << lose_cnt
                     << "  速度: " << (ll)rate << "/秒  剩余: " << eta << "分" << endl;
                last_report = now;
            }

            vector<int> y;
            { ll tmp=yc; while(tmp){y.push_back((int)(tmp%17)-1);tmp/=17;} }

            int lx = (int)x.size(), ly = (int)y.size();
            if (lx != ly && lx != ly+1) continue;

            // 重叠检查
            bool overlap = false;
            set<int> ys(y.begin(), y.end());
            for (int p : x) if (ys.count(p)) { overlap=true; break; }
            if (overlap) continue;

            auto cr = canonicalize(x, y);
            if (canons.count(cr.code)) continue;
            canons.insert(cr.code);

            int result = check_result(cr.x, cr.y);
            if      (result ==  1) win_cnt++;
            else if (result == -1) lose_cnt++;
        }
    }

    double elapsed = chrono::duration_cast<chrono::milliseconds>(
        chrono::high_resolution_clock::now() - t0).count() / 1000.0;

    cout << endl;
    cout << "======================================" << endl;
    cout << "总标准型数:  " << canons.size() << endl;
    cout << "  win  状态: " << win_cnt  << endl;
    cout << "  lose 状态: " << lose_cnt << endl;
    cout << "  非终局:    " << (ll)canons.size() - win_cnt - lose_cnt << endl;
    cout << "win+lose 合计内存估算: "
         << (win_cnt + lose_cnt) * 8 / 1024 / 1024 << " MB (仅key)" << endl;
    cout << "耗时: " << elapsed << " 秒" << endl;
    cout << "======================================" << endl;
    return 0;
}
