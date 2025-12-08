# import pymysql
#
# # 数据库连接配置
# conn = pymysql.connect(
#     host="127.0.0.1",       # MySQL 主机
#     port=3306,              # MySQL 端口
#     user="root",            # 用户名
#     password="1234",     # 密码
#     database="test_db",     # 数据库名
#     charset="utf8mb4",
#     autocommit=True          # 自动提交
# )
#
# cursor = conn.cursor()
#
# # 1. 创建路口表
# cursor.execute("""
# CREATE TABLE IF NOT EXISTS intersections (
#     id INT AUTO_INCREMENT PRIMARY KEY,
#     intersection_id VARCHAR(50) UNIQUE NOT NULL,
#     name VARCHAR(100),
#     location VARCHAR(255),
#     description TEXT
# )
# """)
#
# # 2. 创建节点表
# cursor.execute("""
# CREATE TABLE IF NOT EXISTS nodes (
#     id INT AUTO_INCREMENT PRIMARY KEY,
#     node_id VARCHAR(50) UNIQUE NOT NULL,
#     name VARCHAR(100),
#     ip_address VARCHAR(50) NOT NULL,
#     is_master BOOLEAN DEFAULT FALSE,
#     master_node_id VARCHAR(50),
#     description TEXT
# )
# """)
#
# # 3. 创建摄像头表
# cursor.execute("""
# CREATE TABLE IF NOT EXISTS cameras (
#     id INT AUTO_INCREMENT PRIMARY KEY,
#     camera_id VARCHAR(50) UNIQUE NOT NULL,
#     name VARCHAR(100),
#     node_id VARCHAR(50),
#     calibration_range JSON,
#     rtsp_url VARCHAR(255),
#     encoding VARCHAR(20),
#     resolution VARCHAR(20),
#     video_quality INT,
#     status VARCHAR(20) DEFAULT 'online',
#     description TEXT,
#     FOREIGN KEY (node_id) REFERENCES nodes(node_id) ON DELETE SET NULL
# )
# """)
#
# # 4. 创建路口-摄像头关联表
# cursor.execute("""
# CREATE TABLE IF NOT EXISTS intersection_cameras (
#     intersection_id VARCHAR(50) NOT NULL,
#     camera_id VARCHAR(50) NOT NULL,
#     PRIMARY KEY (intersection_id, camera_id),
#     FOREIGN KEY (intersection_id) REFERENCES intersections(intersection_id) ON DELETE CASCADE,
#     FOREIGN KEY (camera_id) REFERENCES cameras(camera_id) ON DELETE CASCADE
# )
# """)
#
# print("四张表创建成功！")
#
# # 关闭连接
# cursor.close()
# conn.close()
import pymysql

connection = pymysql.connect(
    host="127.0.0.1",
    user="root",
    password="1234",
    database="test_db",
    charset="utf8mb4"
)
cursor = connection.cursor()

# 1. 路口表（intersections）
cursor.execute("""
CREATE TABLE IF NOT EXISTS intersection_camera_mapping (
    id INT AUTO_INCREMENT PRIMARY KEY,
    intersection_id VARCHAR(50) NOT NULL,
    camera_id VARCHAR(50) NOT NULL,
    UNIQUE KEY uq_inter_camera (intersection_id, camera_id),
    FOREIGN KEY (intersection_id) REFERENCES intersections(intersection_id) ON DELETE CASCADE,
    FOREIGN KEY (camera_id) REFERENCES cameras(camera_id) ON DELETE CASCADE
);
""")
# # 1. 路口表（intersections）
# cursor.execute("""
# CREATE TABLE IF NOT EXISTS intersections (
#     id INT AUTO_INCREMENT PRIMARY KEY,
#     intersection_id VARCHAR(50) UNIQUE NOT NULL,
#     name VARCHAR(100),
#     location VARCHAR(255),
#     description TEXT
# )
# """)
#
# # 2. 节点表（nodes）
# cursor.execute("""
# CREATE TABLE IF NOT EXISTS nodes (
#     id INT AUTO_INCREMENT PRIMARY KEY,
#     node_id VARCHAR(50) UNIQUE NOT NULL,
#     name VARCHAR(100),
#     ip_address VARCHAR(50),
#     is_master BOOLEAN DEFAULT FALSE,
#     master_node_id VARCHAR(50),
#     description TEXT
# )
# """)
#
# # 3. 摄像头表（cameras）
# cursor.execute("""
# CREATE TABLE IF NOT EXISTS cameras (
#     id INT AUTO_INCREMENT PRIMARY KEY,
#     camera_id VARCHAR(50) UNIQUE NOT NULL,
#     name VARCHAR(100),
#     node_id VARCHAR(50),
#     rtsp_url VARCHAR(255),
#     encoding VARCHAR(20),
#     resolution VARCHAR(20),
#     video_quality INT,
#     status VARCHAR(20) DEFAULT 'online',
#     description TEXT,
#     FOREIGN KEY (node_id) REFERENCES nodes(node_id) ON DELETE SET NULL
# )
# """)
#
# # 4. 路口-摄像头 多对多表
# cursor.execute("""
# CREATE TABLE IF NOT EXISTS intersection_cameras (
#     intersection_id VARCHAR(50) NOT NULL,
#     camera_id VARCHAR(50) NOT NULL,
#     PRIMARY KEY (intersection_id, camera_id),
#     FOREIGN KEY (intersection_id) REFERENCES intersections(intersection_id) ON DELETE CASCADE,
#     FOREIGN KEY (camera_id) REFERENCES cameras(camera_id) ON DELETE CASCADE
# )
# """)
#
# # 5. 区域表（regions）
# cursor.execute("""
# CREATE TABLE IF NOT EXISTS regions (
#     id INT AUTO_INCREMENT PRIMARY KEY,
#     region_id VARCHAR(50) UNIQUE NOT NULL,
#     intersection_id VARCHAR(50) NOT NULL,
#     region_name VARCHAR(100),
#     description TEXT,
#     FOREIGN KEY (intersection_id) REFERENCES intersections(intersection_id) ON DELETE CASCADE
# )
# """)
#
# # 6. 区域-摄像头范围（可多对多 + 多个框）
# cursor.execute("""
# CREATE TABLE IF NOT EXISTS region_camera_ranges (
#     id INT AUTO_INCREMENT PRIMARY KEY,
#     region_id VARCHAR(50) NOT NULL,
#     camera_id VARCHAR(50) NOT NULL,
#     calibration_range JSON,
#     description TEXT,
#     FOREIGN KEY (region_id) REFERENCES regions(region_id) ON DELETE CASCADE,
#     FOREIGN KEY (camera_id) REFERENCES cameras(camera_id) ON DELETE CASCADE
# )
# """)

connection.commit()
cursor.close()
connection.close()

print("✔ 所有表创建成功！")
