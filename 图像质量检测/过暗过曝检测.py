import cv2
import os
import numpy as np


# 过暗检测
def is_underexposed(image, threshold=50, underexposed_ratio=0.3):
    """
    判断图像是否过暗。过暗的图像亮度普遍偏低。
    :param image: 输入的灰度图像
    :param threshold: 判断过暗的亮度阈值，默认为50
    :param underexposed_ratio: 低亮度像素比例的阈值，默认为30%
    :return: 如果图像过暗，返回True；否则返回False
    """
    # 计算图像的亮度分布
    underexposed_pixels = np.sum(image < threshold)
    total_pixels = image.size
    underexposed_percentage = underexposed_pixels / total_pixels

    return underexposed_percentage > underexposed_ratio


# 改进的过曝检测函数
def is_overexposed(image, threshold=240, overexposed_ratio=0.3):
    """
    判断图像是否过曝。过曝的图像有大量的亮度值接近255。
    :param image: 输入的灰度图像
    :param threshold: 判断过曝的亮度阈值，默认为240
    :param overexposed_ratio: 过曝像素比例的阈值，默认为30%
    :return: 如果图像过曝，返回True；否则返回False
    """
    # 统计亮度大于阈值的像素数量
    overexposed_pixels = np.sum(image > threshold)
    total_pixels = image.size
    overexposed_percentage = overexposed_pixels / total_pixels

    # 如果图像中大于threshold的像素比例超过阈值，认为过曝
    if overexposed_percentage > overexposed_ratio:
        return True

    return False


# 计算图像的亮度直方图并检测局部过曝区域
def detect_local_overexposure(image, threshold=240, min_area=100, window_size=100):
    """
    检测图像中是否存在局部过曝区域。通过滑动窗口分析图像的局部区域。
    :param image: 输入的灰度图像
    :param threshold: 判断过曝的亮度阈值，默认为240
    :param min_area: 最小的过曝区域面积（小的高亮区域不计入）
    :param window_size: 滑动窗口的大小（每次分析图像的一小块区域）
    :return: 返回过曝的区域（如果有的话）
    """
    overexposed_regions = []
    height, width = image.shape

    # 使用滑动窗口检测局部区域
    for y in range(0, height - window_size, window_size):
        for x in range(0, width - window_size, window_size):
            # 截取当前窗口区域
            window = image[y:y + window_size, x:x + window_size]

            # 统计窗口中高于阈值的像素
            overexposed_pixels = np.sum(window > threshold)
            total_pixels = window.size
            overexposed_percentage = overexposed_pixels / total_pixels

            # 如果该窗口的过曝像素比例超过阈值，认为该区域过曝
            if overexposed_percentage > 0.5:  # 可以调整比例
                # 如果该区域的面积超过最小面积阈值，认为是过曝区域
                if window.size > min_area:
                    overexposed_regions.append((x, y, window_size, window_size))

    return overexposed_regions


# 处理单张图像，分开判断过暗和过曝
def check_image_brightness(image_path, underexposed_threshold=30, overexposed_threshold=240, underexposed_ratio=0.3,
                           overexposed_ratio=0.3, window_size=100):
    """
    检查图像是否过暗或过曝
    :param image_path: 图片文件路径
    :param underexposed_threshold: 判断过暗的亮度阈值
    :param overexposed_threshold: 判断过曝的亮度阈值
    :param underexposed_ratio: 低亮度像素比例的阈值
    :param overexposed_ratio: 过曝像素比例的阈值
    :param window_size: 滑动窗口大小
    :return: 'underexposed', 'overexposed', 'normal'，分别表示过暗，过曝，和正常图片
    """
    image = cv2.imread(image_path)
    if image is None:
        print(f"无法读取图像: {image_path}")
        return 'invalid'

    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)  # 转为灰度图

    # 判断图像是否过暗
    if is_underexposed(gray_image, threshold=underexposed_threshold, underexposed_ratio=underexposed_ratio):
        return 'underexposed'

    # 先进行全图过曝检测
    if is_overexposed(gray_image, threshold=overexposed_threshold, overexposed_ratio=overexposed_ratio):
        return 'overexposed'

    # 然后进行局部区域过曝检测
    overexposed_regions = detect_local_overexposure(gray_image, overexposed_threshold, window_size=window_size)

    if overexposed_regions:
        return 'overexposed'

    return 'normal'


# 处理单个文件夹中的图片并按要求格式输出
def process_single_folder(image_dir, underexposed_threshold=30, overexposed_threshold=240, underexposed_ratio=0.5,
                          overexposed_ratio=0.3, window_size=100):
    """
    处理单个文件夹中的图片，并按照指定格式输出结果
    :param image_dir: 图片文件夹路径
    :param underexposed_threshold: 判断过暗的亮度阈值
    :param overexposed_threshold: 判断过曝的亮度阈值
    :param underexposed_ratio: 低亮度像素比例的阈值
    :param overexposed_ratio: 过曝像素比例的阈值
    :param window_size: 滑动窗口大小
    """
    print(f"正在检查目录: {image_dir}")

    # 检查目录是否存在
    if not os.path.exists(image_dir):
        print(f"目录不存在: {image_dir}")
        return

    if not os.path.isdir(image_dir):
        print(f"路径不是目录: {image_dir}")
        return

    # 获取文件夹中的所有图片文件
    image_files = []
    try:
        all_files = os.listdir(image_dir)
        print(f"目录 {image_dir} 中的文件: {all_files}")
        for filename in all_files:
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                image_files.append(filename)
    except Exception as e:
        print(f"读取目录时出错: {e}")
        return

    print(f"找到 {len(image_files)} 个图片文件")

    # 按文件名排序以保证输出顺序一致
    image_files.sort()

    # 逐个处理图片并输出结果
    for idx, filename in enumerate(image_files, 1):
        image_path = os.path.join(image_dir, filename)
        result = check_image_brightness(
            image_path,
            underexposed_threshold,
            overexposed_threshold,
            underexposed_ratio,
            overexposed_ratio,
            window_size
        )

        # 按照指定格式输出
        if result == 'underexposed':
            print(f"图片{idx}是过暗图片")
        elif result == 'overexposed':
            print(f"图片{idx}是过曝图片")
        elif result == 'normal':
            print(f"图片{idx}是正常图片")
        else:
            print(f"图片{idx}无法处理")


# 处理pic1.py生成的文件夹结构
def process_pic1_folders(base_dir, underexposed_threshold=30, overexposed_threshold=240, underexposed_ratio=0.5,
                         overexposed_ratio=0.3, window_size=100):
    """
    处理pic1.py生成的文件夹结构，逐个判断图片的过暗、过曝情况
    :param base_dir: pic1.py生成的基准目录路径
    :param underexposed_threshold: 判断过暗的亮度阈值
    :param overexposed_threshold: 判断过曝的亮度阈值
    :param underexposed_ratio: 低亮度像素比例的阈值
    :param overexposed_ratio: 过曝像素比例的阈值
    :param window_size: 滑动窗口大小
    """
    print(f"检查基础目录: {base_dir}")

    # 检查基础目录是否存在
    if not os.path.exists(base_dir):
        print(f"基础目录不存在: {base_dir}")
        return

    if not os.path.isdir(base_dir):
        print(f"路径不是目录: {base_dir}")
        return

    # 获取基础目录内容
    try:
        base_contents = os.listdir(base_dir)
        print(f"基础目录内容: {base_contents}")
    except Exception as e:
        print(f"读取基础目录时出错: {e}")
        return

    # 遍历基准目录下的所有子目录
    folder_count = 0
    for folder_name in base_contents:
        folder_path = os.path.join(base_dir, folder_name)

        # 确保是目录
        if os.path.isdir(folder_path):
            folder_count += 1
            print(f"\n处理文件夹: {folder_name}")
            process_single_folder(
                folder_path,
                underexposed_threshold,
                overexposed_threshold,
                underexposed_ratio,
                overexposed_ratio,
                window_size
            )

    if folder_count == 0:
        print("未找到任何子目录，尝试直接处理基础目录中的图片")
        process_single_folder(
            base_dir,
            underexposed_threshold,
            overexposed_threshold,
            underexposed_ratio,
            overexposed_ratio,
            window_size
        )


# 主程序入口
if __name__ == "__main__":
    # 设置pic1.py生成的基准目录路径
    base_dir = r'E:\bright\test'  # 修改为实际路径

    print("开始处理图片...")
    # 处理所有文件夹中的图片
    process_pic1_folders(base_dir)
    print("处理完成。")
