// 存储格式单元测试
// 生成 N 条已知值的测试记录，写成与 perfect_strategy.py 完全相同的二进制格式
// 然后用 verify_storage.py 验证 Python 侧能正确读取
//
// 文件格式：
//   [8字节: 记录数 uint64_t]
//   每条记录 14字节：
//     [8字节: state_code uint64_t]
//     [1字节: dp0       int8_t  ]
//     [1字节: dp1       int8_t  ]
//     [2字节: depth0    uint16_t]
//     [2字节: depth1    uint16_t]
//   记录按 state_code 升序排列
//
// 编译：g++ -O2 -o test_storage test_storage.cpp
// 运行：./test_storage [输出文件名]

#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <vector>

struct Record {
    uint64_t state_code;
    int8_t   dp0;
    int8_t   dp1;
    uint16_t depth0;
    uint16_t depth1;
};

// 生成第 i 条记录（i 从 0 开始）
// 规则与 verify_storage.py 完全相同，便于对比
Record make_record(int i) {
    Record r;
    r.state_code = (uint64_t)(i + 1) * 1000000007ULL;
    r.dp0        = (int8_t)((i % 3) - 1);          // 循环 -1, 0, 1
    r.dp1        = (int8_t)(((i + 1) % 3) - 1);    // 循环  0, 1, -1
    r.depth0     = (uint16_t)(i % 1000);
    r.depth1     = (uint16_t)((i * 3) % 1000);
    return r;
}

int main(int argc, char* argv[]) {
    const char* filename = (argc > 1) ? argv[1] : "test_storage.data";
    const int   N        = 1000;

    // 生成记录
    std::vector<Record> records;
    records.reserve(N);
    for (int i = 0; i < N; i++) {
        records.push_back(make_record(i));
    }

    // 按 state_code 排序（与训练器保存方式一致）
    std::sort(records.begin(), records.end(),
              [](const Record& a, const Record& b) {
                  return a.state_code < b.state_code;
              });

    // 写入文件
    FILE* f = fopen(filename, "wb");
    if (!f) {
        fprintf(stderr, "错误：无法打开文件 %s\n", filename);
        return 1;
    }

    // 头部：记录数（8字节 uint64_t）
    uint64_t n = (uint64_t)N;
    fwrite(&n, sizeof(uint64_t), 1, f);

    // 逐字段写入，避免 struct 对齐填充导致 sizeof(Record) != 14
    for (const Record& r : records) {
        fwrite(&r.state_code, sizeof(uint64_t), 1, f);
        fwrite(&r.dp0,        sizeof(int8_t),   1, f);
        fwrite(&r.dp1,        sizeof(int8_t),   1, f);
        fwrite(&r.depth0,     sizeof(uint16_t), 1, f);
        fwrite(&r.depth1,     sizeof(uint16_t), 1, f);
    }

    fclose(f);

    // 打印摘要，便于与 Python 输出对比
    printf("写入完成: %s\n", filename);
    printf("  记录数:   %d\n", N);
    printf("  文件大小: %lu 字节  (预期 %lu)\n",
           8 + (uint64_t)N * 14, 8 + (uint64_t)N * 14);

    printf("\n前5条记录（排序后，供 Python 对比）:\n");
    for (int i = 0; i < 5 && i < N; i++) {
        printf("  [%d] state_code=%-20lu  dp=[%2d,%2d]  depth=[%4u,%4u]\n",
               i,
               (unsigned long)records[i].state_code,
               (int)records[i].dp0,
               (int)records[i].dp1,
               (unsigned)records[i].depth0,
               (unsigned)records[i].depth1);
    }

    return 0;
}
