#include <iostream>
#include <vector>
#include <set>
#include <chrono>
#include <algorithm>
#include <climits>
#include <iomanip>

using namespace std;
using ll = long long;

const ll SEPARATOR = 83521LL; // 17^4

// 8种对称变换
const int transforms[8][16] = {
    {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15},
    {3, 7, 11, 15, 2, 6, 10, 14, 1, 5, 9, 13, 0, 4, 8, 12},
    {15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0},
    {12, 8, 4, 0, 13, 9, 5, 1, 14, 10, 6, 2, 15, 11, 7, 3},
    {3, 2, 1, 0, 7, 6, 5, 4, 11, 10, 9, 8, 15, 14, 13, 12},
    {12, 13, 14, 15, 8, 9, 10, 11, 4, 5, 6, 7, 0, 1, 2, 3},
    {0, 4, 8, 12, 1, 5, 9, 13, 2, 6, 10, 14, 3, 7, 11, 15},
    {15, 11, 7, 3, 14, 10, 6, 2, 13, 9, 5, 1, 12, 8, 4, 0},
};

// 解码并检查合法性
pair<vector<int>, bool> decode_and_check(ll code) {
    vector<int> positions;
    if (code == 0) {
        return {positions, true};
    }

    ll temp = code;
    while (temp) {
        int digit = temp % 17;
        if (digit == 0) {
            return {positions, false};
        }
        positions.push_back(digit - 1);
        temp /= 17;
    }

    // 检查重复
    set<int> pos_set(positions.begin(), positions.end());
    if (positions.size() != pos_set.size()) {
        return {positions, false};
    }

    // 检查范围
    for (int p : positions) {
        if (p >= 16) {
            return {positions, false};
        }
    }

    return {positions, true};
}

// 编码
ll encode(const vector<int>& x, const vector<int>& y) {
    ll x_code = 0, y_code = 0;
    ll power = 1;
    for (int pos : x) {
        x_code += (pos + 1) * power;
        power *= 17;
    }
    power = 1;
    for (int pos : y) {
        y_code += (pos + 1) * power;
        power *= 17;
    }
    return x_code * SEPARATOR + y_code;
}

// 计算标准型
ll canonicalize(const vector<int>& x, const vector<int>& y) {
    ll min_code = LLONG_MAX;

    for (int t = 0; t < 8; t++) {
        vector<int> x_trans, y_trans;
        for (int p : x) {
            x_trans.push_back(transforms[t][p]);
        }
        for (int p : y) {
            y_trans.push_back(transforms[t][p]);
        }

        ll code = encode(x_trans, y_trans);
        min_code = min(min_code, code);
    }

    return min_code;
}

int main() {
    cout << "======================================================================" << endl;
    cout << "计算 4×4 (max_move=4) 标准型数量 (C++ 版本)" << endl;
    cout << "======================================================================" << endl;
    cout << endl;

    auto start_time = chrono::high_resolution_clock::now();

    // 预计算 x_valid
    cout << "预计算 x_valid..." << flush;
    auto precompute_start = chrono::high_resolution_clock::now();

    vector<ll> x_valid;
    for (ll x_code = 0; x_code < SEPARATOR; x_code++) {
        auto [positions, is_valid] = decode_and_check(x_code);
        if (!is_valid) continue;

        // 检查有效首位
        if (positions.size() > 0) {
            int highest_digit = positions.back() + 1;
            if (highest_digit != 1 && highest_digit != 2 && highest_digit != 6) {
                continue;
            }
        }

        x_valid.push_back(x_code);
    }

    cout << " 完成！找到 " << x_valid.size() << " 个" << endl;

    // 预计算 y_valid
    cout << "预计算 y_valid..." << flush;

    vector<ll> y_valid;
    for (ll y_code = 0; y_code < SEPARATOR; y_code++) {
        auto [positions, is_valid] = decode_and_check(y_code);
        if (is_valid) {
            y_valid.push_back(y_code);
        }
    }

    auto precompute_end = chrono::high_resolution_clock::now();
    auto precompute_duration = chrono::duration_cast<chrono::milliseconds>(precompute_end - precompute_start).count();

    cout << " 完成！找到 " << y_valid.size() << " 个" << endl;
    cout << "预计算耗时: " << precompute_duration / 1000.0 << " 秒" << endl;
    cout << "总组合: " << x_valid.size() * y_valid.size() << endl;
    cout << endl;

    // 枚举并计算标准型
    cout << "开始枚举标准型..." << endl;

    set<ll> canons;
    ll total_combinations = (ll)x_valid.size() * y_valid.size();
    ll checked = 0;
    auto last_report_time = chrono::high_resolution_clock::now();

    for (ll x_code : x_valid) {
        auto [x, _1] = decode_and_check(x_code);

        for (ll y_code : y_valid) {
            checked++;

            // 进度显示
            auto current_time = chrono::high_resolution_clock::now();
            auto elapsed_since_report = chrono::duration_cast<chrono::seconds>(current_time - last_report_time).count();
            if (elapsed_since_report >= 2) {
                auto total_elapsed = chrono::duration_cast<chrono::seconds>(current_time - start_time).count();
                double progress = 100.0 * checked / total_combinations;
                double rate = (double)checked / total_elapsed;
                double eta_seconds = (total_combinations - checked) / rate;

                cout << "  进度: " << checked << "/" << total_combinations
                     << " (" << fixed << setprecision(1) << progress << "%) | "
                     << "找到: " << canons.size() << " | "
                     << "速度: " << (ll)rate << "/秒 | "
                     << "剩余: " << (ll)(eta_seconds / 60) << "分" << endl;

                last_report_time = current_time;
            }

            auto [y, _2] = decode_and_check(y_code);

            // 检查棋子数量关系
            if (x.size() != y.size() && x.size() != y.size() + 1) {
                continue;
            }

            // 检查重叠
            set<int> x_set(x.begin(), x.end());
            set<int> y_set(y.begin(), y.end());
            bool overlap = false;
            for (int p : x_set) {
                if (y_set.count(p)) {
                    overlap = true;
                    break;
                }
            }
            if (overlap) continue;

            // 计算标准型
            ll canon_code = canonicalize(x, y);
            canons.insert(canon_code);
        }
    }

    auto end_time = chrono::high_resolution_clock::now();
    auto total_duration = chrono::duration_cast<chrono::milliseconds>(end_time - start_time).count();

    cout << endl;
    cout << "======================================================================" << endl;
    cout << "计算完成！" << endl;
    cout << "======================================================================" << endl;
    cout << "总耗时: " << total_duration / 1000.0 << " 秒 ("
         << total_duration / 60000.0 << " 分钟)" << endl;
    cout << "检查组合数: " << checked << endl;
    cout << "标准型数量: " << canons.size() << endl;
    cout << endl;
    cout << "这个数量是 4×4 (max_move=4) 游戏的精确标准型数量！" << endl;
    cout << "======================================================================" << endl;

    return 0;
}
