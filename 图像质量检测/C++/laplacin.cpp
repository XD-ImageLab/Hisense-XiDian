#include <iostream>
#include <filesystem>
#include <vector>
#include <string>
#include <cmath>
#include <algorithm>

#define STB_IMAGE_IMPLEMENTATION
#include "stb_image.h"

namespace fs = std::filesystem;
using namespace std;

/* ---------------- 图像结构 ---------------- */
struct Image {
    int width;
    int height;
    vector<unsigned char> data; // 灰度图
};

/* ---------------- 加载灰度图 ---------------- */
bool loadImageGray(const string& path, Image& img) {
    int w, h, c;
    unsigned char* raw = stbi_load(path.c_str(), &w, &h, &c, 0);
    if (!raw) return false;

    img.width = w;
    img.height = h;
    img.data.resize(w * h);

    for (int i=0; i<w*h; i++) {
        if (c>=3) {
            int r = raw[i*c+0];
            int g = raw[i*c+1];
            int b = raw[i*c+2];
            img.data[i] = static_cast<unsigned char>(0.299*r + 0.587*g + 0.114*b);
        } else {
            img.data[i] = raw[i];
        }
    }
    stbi_image_free(raw);
    return true;
}

/* ---------------- Laplacian 卷积 ---------------- */
double variance_of_laplacian(const Image& img) {
    int w = img.width;
    int h = img.height;
    vector<double> lap(w*h, 0.0);

    int kernel[3][3] = {{0,1,0},{1,-4,1},{0,1,0}};

    for (int y=1; y<h-1; y++) {
        for (int x=1; x<w-1; x++) {
            double val = 0;
            for (int ky=-1; ky<=1; ky++) {
                for (int kx=-1; kx<=1; kx++) {
                    int px = x+kx;
                    int py = y+ky;
                    val += kernel[ky+1][kx+1] * img.data[py*w + px];
                }
            }
            lap[y*w + x] = val;
        }
    }

    // 计算方差
    double mean = 0;
    int count = (w-2)*(h-2);
    for (int i=0; i<w*h; i++) mean += lap[i];
    mean /= count;

    double var = 0;
    for (int i=0; i<w*h; i++) var += (lap[i]-mean)*(lap[i]-mean);
    var /= count;

    return var;
}

/* ---------------- 模糊检测 ---------------- */
struct EvalResult {
    int TP=0, TN=0, FP=0, FN=0;
    int total_images=0;
    double total_time=0;
};

void evaluate(const string& root, double threshold=100.0) {
    EvalResult res;
    vector<string> blurry_folders = {"blur","blur_gamma"};

    for (auto& entry : fs::recursive_directory_iterator(root)) {
        if (!entry.is_regular_file()) continue;

        fs::path file_path = entry.path();
        string folder = file_path.parent_path().filename().string();
        string filename = file_path.filename().string();

        Image img;
        if (!loadImageGray(file_path.string(), img)) {
            cout << "无法读取图片: " << filename << endl;
            continue;
        }

        res.total_images++;

        clock_t start = clock();
        double fm = variance_of_laplacian(img);
        double elapsed = double(clock()-start)/CLOCKS_PER_SEC;
        res.total_time += elapsed;

        int pred = (fm < threshold) ? 1 : 0;  // 1=Blurry
        int gt = (find(blurry_folders.begin(), blurry_folders.end(), folder) != blurry_folders.end()) ? 1 : 0;

        if (gt==1 && pred==1) res.TP++;
        else if (gt==0 && pred==0) res.TN++;
        else if (gt==0 && pred==1) res.FP++;
        else if (gt==1 && pred==0) res.FN++;

        cout << file_path.string() << "  GT=" << gt << "  Pred=" << pred << "  Score=" << fm << endl;
    }

    // 指标计算
    double accuracy = double(res.TP+res.TN)/res.total_images;
    double recall = double(res.TP)/(res.TP+res.FN+1e-6);
    double precision = double(res.TP)/(res.TP+res.FP+1e-6);
    double f1 = 2*precision*recall/(precision+recall+1e-6);
    double avg_time = res.total_time / res.total_images;

    cout << "\n======= Evaluation Result =======" << endl;
    cout << "Total images     : " << res.total_images << endl;
    cout << "Accuracy         : " << accuracy << endl;
    cout << "Recall           : " << recall << endl;
    cout << "Precision        : " << precision << endl;
    cout << "F1-score         : " << f1 << endl;
    cout << "Avg time/image   : " << avg_time*1000 << " ms" << endl;
    cout << "=================================" << endl;
}

/* ---------------- 主函数 ---------------- */
int main() {
    string root = R"(E:\1\2)";
    double threshold = 100.0;

    cout << "开始模糊检测..." << endl;
    evaluate(root, threshold);
    cout << "处理完成。" << endl;

    return 0;
}
