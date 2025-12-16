#include <iostream>
#include <filesystem>
#include <vector>
#include <string>
#include <cmath>

#define STB_IMAGE_IMPLEMENTATION
#include "stb_image.h"
#define STB_IMAGE_WRITE_IMPLEMENTATION
#include "stb_image_write.h"

namespace fs = std::filesystem;
using namespace std;

/* ---------------- 图像数据结构 ---------------- */
struct Image {
    int width;
    int height;
    int channels;
    vector<unsigned char> data; // 灰度图像
};

/* ---------------- 加载灰度图 ---------------- */
bool loadImageGray(const string& path, Image& img) {
    int w, h, c;
    unsigned char* raw = stbi_load(path.c_str(), &w, &h, &c, 0);
    if (!raw) return false;

    img.width = w;
    img.height = h;
    img.channels = 1;
    img.data.resize(w * h);

    for (int i = 0; i < w * h; ++i) {
        if (c >= 3) {
            int r = raw[i * c + 0];
            int g = raw[i * c + 1];
            int b = raw[i * c + 2];
            img.data[i] = static_cast<unsigned char>(0.299*r + 0.587*g + 0.114*b);
        } else {
            img.data[i] = raw[i];
        }
    }

    stbi_image_free(raw);
    return true;
}

/* ---------------- 连通区域标记 ---------------- */
void floodFill(const Image& img, int x, int y, int threshold, vector<int>& labels, int current_label) {
    int w = img.width;
    int h = img.height;
    vector<pair<int,int>> stack;
    stack.push_back({x,y});

    while (!stack.empty()) {
        auto [cx, cy] = stack.back(); stack.pop_back();
        int idx = cy * w + cx;
        if (labels[idx] != 0) continue;
        if (img.data[idx] > threshold) continue;
        labels[idx] = current_label;

        if (cx > 0) stack.push_back({cx-1, cy});
        if (cx < w-1) stack.push_back({cx+1, cy});
        if (cy > 0) stack.push_back({cx, cy-1});
        if (cy < h-1) stack.push_back({cx, cy+1});
    }
}

/* ---------------- 黑色遮挡检测 ---------------- */
pair<bool,double> detect_black_occlusion(const Image& img,
                                        int black_thresh = 40,
                                        double area_ratio_thresh = 0.15,
                                        double std_thresh = 15.0) {
    int w = img.width;
    int h = img.height;
    vector<int> labels(w*h,0);
    int current_label = 1;

    // 连通区域标记
    for (int y=0; y<h; ++y) {
        for (int x=0; x<w; ++x) {
            int idx = y*w + x;
            if (img.data[idx] <= black_thresh && labels[idx]==0) {
                floodFill(img, x, y, black_thresh, labels, current_label);
                current_label++;
            }
        }
    }

    if (current_label == 1) return {false, 0.0};

    // 统计各个连通域面积
    vector<int> areas(current_label,0);
    for (auto l : labels) if (l>0) areas[l]++;

    // 选择最大面积
    int max_area = 0;
    int max_label = 0;
    for (int i=1;i<current_label;i++) {
        if (areas[i] > max_area) {
            max_area = areas[i];
            max_label = i;
        }
    }

    double area_ratio = static_cast<double>(max_area) / (w*h);
    if (area_ratio < area_ratio_thresh) return {false, area_ratio};

    // 纹理标准差
    vector<unsigned char> block_pixels;
    for (int i=0;i<w*h;i++)
        if (labels[i]==max_label)
            block_pixels.push_back(img.data[i]);
    if (block_pixels.empty()) return {false, area_ratio};

    double mean = 0.0;
    for (auto v : block_pixels) mean += v;
    mean /= block_pixels.size();

    double var = 0.0;
    for (auto v : block_pixels) var += (v-mean)*(v-mean);
    var /= block_pixels.size();
    double stddev = sqrt(var);

    if (stddev > std_thresh) return {false, area_ratio};

    return {true, area_ratio};
}

/* ---------------- 保存灰度图片 ---------------- */
bool saveImage(const string& path, const Image& img) {
    return stbi_write_png(path.c_str(), img.width, img.height, 1, img.data.data(), img.width) != 0;
}

/* ---------------- 移除遮挡图片 ---------------- */
void remove_occluded_images(const string& input_dir, const string& output_dir) {
    if (!fs::exists(output_dir)) fs::create_directories(output_dir);

    int total_images=0, total_G=0, occluded_non_G=0, occluded_G=0;

    for (auto& entry : fs::directory_iterator(input_dir)) {
        if (!entry.is_regular_file()) continue;

        fs::path file_path = entry.path();
        string filename = file_path.filename().string();
        string stem = file_path.stem().string();

        Image img;
        if (!loadImageGray(file_path.string(), img)) continue;

        total_images++;
        bool is_G_image = stem.size()>=2 && stem.substr(stem.size()-2)=="_G";
        if (is_G_image) total_G++;

        auto [is_occ, area_ratio] = detect_black_occlusion(img);

        if (is_occ) {
            cout << "图片" << filename << "存在遮挡，遮挡面积为" << area_ratio*100 << "%" << endl;
            if (is_G_image) occluded_G++; else occluded_non_G++;
        } else {
            cout << "图片" << filename << "未被遮挡" << endl;
            saveImage((fs::path(output_dir)/filename).string(), img);
        }
    }

    cout << "\n处理完成:" << endl;
    cout << "  - 输入图片总数: " << total_images << endl;
    cout << "  - 保留图片数: " << total_images - occluded_non_G - occluded_G << endl;
}

/* ---------------- 主函数 ---------------- */
int main() {
    string input_dir = R"(E:\archive)";
    string output_dir = R"(E:\archive\R1)";

    cout << "开始处理图片..." << endl;
    remove_occluded_images(input_dir, output_dir);
    cout << "处理完成。" << endl;

    return 0;
}
