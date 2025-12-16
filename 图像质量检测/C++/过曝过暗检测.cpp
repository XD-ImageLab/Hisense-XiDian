#include <iostream>
#include <filesystem>
#include <vector>
#include <algorithm>
#include <string>

#define STB_IMAGE_IMPLEMENTATION
#include "stb_image.h"

namespace fs = std::filesystem;
using namespace std;

/* ---------------- 图像数据结构 ---------------- */

struct Image {
    int width;
    int height;
    int channels;
    vector<unsigned char> data;
};

/* ---------------- 图像加载 ---------------- */

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

/* ---------------- 过暗检测 ---------------- */

bool isUnderexposed(const Image& img, int threshold, double ratio) {
    int count = 0;
    for (auto v : img.data)
        if (v < threshold) count++;
    return static_cast<double>(count) / img.data.size() > ratio;
}

/* ---------------- 过曝检测（全局） ---------------- */

bool isOverexposed(const Image& img, int threshold, double ratio) {
    int count = 0;
    for (auto v : img.data)
        if (v > threshold) count++;
    return static_cast<double>(count) / img.data.size() > ratio;
}

/* ---------------- 局部过曝检测 ---------------- */

bool detectLocalOverexposure(const Image& img,
                             int threshold,
                             int window_size,
                             int min_area) {
    for (int y = 0; y + window_size <= img.height; y += window_size) {
        for (int x = 0; x + window_size <= img.width; x += window_size) {
            int over = 0;
            for (int j = 0; j < window_size; ++j) {
                for (int i = 0; i < window_size; ++i) {
                    int idx = (y + j) * img.width + (x + i);
                    if (img.data[idx] > threshold)
                        over++;
                }
            }
            int total = window_size * window_size;
            if (total > min_area &&
                static_cast<double>(over) / total > 0.5)
                return true;
        }
    }
    return false;
}

/* ---------------- 单张图像检测 ---------------- */

string checkImageBrightness(const string& path,
                            int under_t,
                            int over_t,
                            double under_r,
                            double over_r,
                            int window_size) {
    Image img;
    if (!loadImageGray(path, img)) {
        cerr << "无法读取图像: " << path << endl;
        return "invalid";
    }

    if (isUnderexposed(img, under_t, under_r))
        return "underexposed";

    if (isOverexposed(img, over_t, over_r))
        return "overexposed";

    if (detectLocalOverexposure(img, over_t, window_size, 100))
        return "overexposed";

    return "normal";
}

/* ---------------- 文件夹处理 ---------------- */

void processSingleFolder(const string& dir) {
    vector<fs::path> images;

    for (auto& e : fs::directory_iterator(dir)) {
        if (!e.is_regular_file()) continue;
        string ext = e.path().extension().string();
        transform(ext.begin(), ext.end(), ext.begin(), ::tolower);
        if (ext == ".jpg" || ext == ".png" || ext == ".jpeg")
            images.push_back(e.path());
    }

    if (images.empty()) {
        cout << "目录 " << dir << " 中没有找到任何图片文件" << endl;
        return;
    }

    sort(images.begin(), images.end());

    int idx = 1;
    for (auto& img : images) {
        string r = checkImageBrightness(img.string(), 30, 240, 0.5, 0.3, 100);
        cout << "图片" << idx++ << "是"
             << (r == "normal" ? "正常" :
                 r == "underexposed" ? "过暗" :
                 r == "overexposed" ? "过曝" : "无法处理")
             << "图片" << endl;
    }
}

/* ---------------- 基础目录处理 ---------------- */

void processPic1Folders(const string& base_dir) {
    if (!fs::exists(base_dir) || !fs::is_directory(base_dir)) {
        cout << "基础目录不存在或不是目录" << endl;
        return;
    }

    bool has_subfolder = false;
    for (auto& e : fs::directory_iterator(base_dir)) {
        if (e.is_directory()) {
            has_subfolder = true;
            cout << "\n处理文件夹: " << e.path().filename().string() << endl;
            processSingleFolder(e.path().string());
        }
    }

    if (!has_subfolder) {
        cout << "未找到子目录，直接处理基础目录中的图片" << endl;
        processSingleFolder(base_dir);
    }
}

/* ---------------- 主程序 ---------------- */

int main() {
    string base_dir = "E:\\bright\\light-data";;  // 修改为你的图片路径
    cout << "开始处理图片..." << endl;
    processPic1Folders(base_dir);
    cout << "处理完成。" << endl;
    return 0;
}
