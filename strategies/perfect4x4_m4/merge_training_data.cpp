/**
 * 合并 xwin 和 ywin 训练数据，生成完整的博弈树数据
 *
 * 数据文件格式：
 * - 头部：8字节（记录数）
 * - 每条记录：14字节 [state_code(8B) | dp0(1B) | dp1(1B) | depth0(2B) | depth1(2B)]
 *
 * 合并规则：
 * - 按 state_code 排序合并（两个文件都已排序）
 * - 使用双指针法，一次只加载少量数据到内存
 * - 如果同一个 state 在两个文件中，优先保留非零的 dp 值
 */

#include <iostream>
#include <fstream>
#include <vector>
#include <cstdint>
#include <cstring>

struct Record {
    uint64_t state_code;
    int8_t dp0;
    int8_t dp1;
    uint16_t depth0;
    uint16_t depth1;

    // 合并逻辑：优先保留非零的 dp 值
    void merge(const Record& other) {
        if (dp0 == 0) dp0 = other.dp0;
        if (dp1 == 0) dp1 = other.dp1;
        if (depth0 == 0) depth0 = other.depth0;
        if (depth1 == 0) depth1 = other.depth1;
    }

    bool is_valid() const {
        return dp0 != 0 || dp1 != 0 || depth0 != 0 || depth1 != 0;
    }
};

class DataReader {
public:
    DataReader(const std::string& filename) : filename_(filename), pos_(0) {}

    bool open() {
        file_.open(filename_, std::ios::binary);
        if (!file_.is_open()) {
            std::cerr << "无法打开文件: " << filename_ << std::endl;
            return false;
        }

        // 读取记录数
        file_.read(reinterpret_cast<char*>(&num_records_), sizeof(uint64_t));
        pos_ = 0;
        return true;
    }

    uint64_t get_count() const { return num_records_; }

    // 读取一批记录到缓冲区
    bool read_batch(std::vector<Record>& buffer, size_t batch_size = 1000000) {
        buffer.clear();
        size_t to_read = std::min(batch_size, num_records_ - pos_);

        if (to_read == 0) return false;

        buffer.resize(to_read);
        char record_bytes[14];

        for (size_t i = 0; i < to_read; i++) {
            file_.read(record_bytes, 14);

            // 解析记录
            uint64_t state_code;
            memcpy(&state_code, record_bytes, 8);

            int8_t dp0 = static_cast<int8_t>(record_bytes[8]);
            int8_t dp1 = static_cast<int8_t>(record_bytes[9]);

            uint16_t depth0, depth1;
            memcpy(&depth0, record_bytes + 10, 2);
            memcpy(&depth1, record_bytes + 12, 2);

            buffer[i] = {state_code, dp0, dp1, depth0, depth1};
        }

        pos_ += to_read;
        return true;
    }

    bool eof() const { return pos_ >= num_records_; }

private:
    std::string filename_;
    std::ifstream file_;
    uint64_t num_records_;
    uint64_t pos_;
};

int main() {
    const char* xwin_file = "xwin_4x4_m4.data";
    const char* ywin_file = "ywin_4x4_m4.data";
    const char* output_file = "game_tree_4x4_m4.data";
    const uint64_t EXPECTED_COUNT = 72864169;

    std::cout << "========================================" << std::endl;
    std::cout << "合并训练数据: xwin + ywin" << std::endl;
    std::cout << "========================================" << std::endl;

    // 打开输入文件
    DataReader xwin(xwin_file);
    DataReader ywin(ywin_file);

    if (!xwin.open() || !ywin.open()) {
        return 1;
    }

    std::cout << "xwin 记录数: " << xwin.get_count() << std::endl;
    std::cout << "ywin 记录数: " << ywin.get_count() << std::endl;

    // 打开输出文件
    std::ofstream out(output_file, std::ios::binary);
    if (!out.is_open()) {
        std::cerr << "无法创建输出文件: " << output_file << std::endl;
        return 1;
    }

    // 写入记录数（稍后修正为实际值）
    out.write(reinterpret_cast<const char*>(&EXPECTED_COUNT), sizeof(uint64_t));

    // 双指针合并
    std::vector<Record> xwin_batch, ywin_batch;
    size_t xwin_idx = 0, ywin_idx = 0;
    uint64_t written = 0;
    uint64_t xonly = 0, yonly = 0, both = 0;
    uint64_t last_progress = 0;

    // 批量读取大小（约 14MB / 批）
    const size_t BATCH_SIZE = 1000000;

    xwin.read_batch(xwin_batch, BATCH_SIZE);
    ywin.read_batch(ywin_batch, BATCH_SIZE);

    while (!xwin.eof() || !ywin.eof()) {
        Record current;

        // 判断下一个写哪个
        bool take_xwin;
        if (xwin_idx >= xwin_batch.size()) {
            take_xwin = false;  // xwin 耗尽，取 ywin
        } else if (ywin_idx >= ywin_batch.size()) {
            take_xwin = true;   // ywin 耗尽，取 xwin
        } else {
            take_xwin = (xwin_batch[xwin_idx].state_code <= ywin_batch[ywin_idx].state_code);
        }

        if (take_xwin) {
            current = xwin_batch[xwin_idx];
            xwin_idx++;

            // 检查是否有相同 state_code 的 ywin 记录
            if (ywin_idx < ywin_batch.size() &&
                ywin_batch[ywin_idx].state_code == current.state_code) {
                current.merge(ywin_batch[ywin_idx]);
                ywin_idx++;
                both++;
            } else {
                xonly++;
            }
        } else {
            current = ywin_batch[ywin_idx];
            ywin_idx++;
            yonly++;
        }

        // 写入当前记录
        char record_bytes[14];
        memcpy(record_bytes, &current.state_code, 8);
        record_bytes[8] = static_cast<char>(current.dp0);
        record_bytes[9] = static_cast<char>(current.dp1);
        memcpy(record_bytes + 10, &current.depth0, 2);
        memcpy(record_bytes + 12, &current.depth1, 2);
        out.write(record_bytes, 14);

        written++;

        // 进度显示
        if (written - last_progress >= 1000000) {
            double progress = static_cast<double>(written) / EXPECTED_COUNT * 100;
            std::cout << "已写入: " << written << "/" << EXPECTED_COUNT
                      << " (" << progress << "%)" << std::endl;
            last_progress = written;
        }

        // 需要重新加载 xwin 批次
        if (xwin_idx >= xwin_batch.size() && !xwin.eof()) {
            xwin.read_batch(xwin_batch, BATCH_SIZE);
            xwin_idx = 0;
        }

        // 需要重新加载 ywin 批次
        if (ywin_idx >= ywin_batch.size() && !ywin.eof()) {
            ywin.read_batch(ywin_batch, BATCH_SIZE);
            ywin_idx = 0;
        }
    }

    // 修正文件头的记录数
    out.seekp(0, std::ios::beg);
    out.write(reinterpret_cast<const char*>(&written), sizeof(uint64_t));

    out.close();

    std::cout << "\n========================================" << std::endl;
    std::cout << "合并完成！" << std::endl;
    std::cout << "仅在 xwin: " << xonly << std::endl;
    std::cout << "仅在 ywin: " << yonly << std::endl;
    std::cout << "两个都有: " << both << std::endl;
    std::cout << "合计: " << written << std::endl;
    std::cout << "输出文件: " << output_file << std::endl;
    std::cout << "========================================" << std::endl;

    return 0;
}
