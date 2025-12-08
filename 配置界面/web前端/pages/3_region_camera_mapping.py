# import streamlit as st
# import json
# from dao_db import DB
#
# db = DB()
# st.title("🎯 区域 - 摄像头绑定")
#
# # 选择路口
# intersections = db.query("SELECT intersection_id, name FROM intersections")
# intersection_id = st.selectbox(
#     "选择路口",
#     intersections["intersection_id"],
#     format_func=lambda x: intersections.loc[intersections["intersection_id"] == x, "name"].values[0]
# )
#
# # 根据路口选择区域
# regions = db.query(f"SELECT region_id, region_name FROM regions WHERE intersection_id='{intersection_id}'")
# region_id = st.selectbox(
#     "选择区域",
#     regions["region_id"],
#     format_func=lambda x: regions.loc[regions["region_id"] == x, "region_name"].values[0]
# )
#
# # 选择摄像头
# # cameras = db.query("SELECT camera_id, name FROM cameras")
# # camera_id = st.selectbox(
# #     "选择摄像头",
# #     cameras["camera_id"],
# #     format_func=lambda x: cameras.loc[cameras["camera_id"] == x, "name"].values[0]
# # )
# # 根据区域所在路口筛选摄像头
# cameras = db.query(f"""
#     SELECT c.camera_id, c.name
#     FROM cameras c
#     JOIN intersection_cameras icm
#     ON c.camera_id = icm.camera_id
#     JOIN regions r ON r.intersection_id = icm.intersection_id
#     WHERE r.region_id = '{region_id}'
# """)
#
# camera_id = st.selectbox(
#     "选择摄像头",
#     cameras["camera_id"],
#     format_func=lambda x: cameras.loc[cameras["camera_id"] == x, "name"].values[0]
# )
#
# st.subheader("➕ 添加摄像头范围 calibration_range")
# with st.form("add_range"):
#     cr = st.text_area("输入 JSON，如 [100,50,300,200]")
#     desc = st.text_area("描述")
#
#     if st.form_submit_button("绑定"):
#         db.execute("""
#             INSERT INTO region_camera_ranges
#             (region_id, camera_id, calibration_range, description)
#             VALUES (%s,%s,%s,%s)
#         """, (region_id, camera_id, cr, desc))
#         st.success("绑定成功")
#         st.rerun()  # 最新 Streamlit 推荐用这个方法刷新
#
# st.subheader("📋 当前区域所有摄像头范围")
# df = db.query(f"""
#     SELECT rr.*, c.name AS camera_name
#     FROM region_camera_ranges rr
#     JOIN cameras c ON c.camera_id = rr.camera_id
#     WHERE rr.region_id='{region_id}'
# """)
# st.dataframe(df)
import streamlit as st
from dao_db import DB

db = DB()
st.title("🎯 区域 - 摄像头绑定")

# 选择路口
intersections = db.query("SELECT intersection_id, name FROM intersections")
intersection_id = st.selectbox(
    "选择路口",
    intersections["intersection_id"],
    format_func=lambda x: intersections.loc[intersections["intersection_id"] == x, "name"].values[0]
)

# 根据路口选择区域
regions = db.query(f"SELECT region_id, region_name FROM regions WHERE intersection_id='{intersection_id}'")
region_id = st.selectbox(
    "选择区域",
    regions["region_id"],
    format_func=lambda x: regions.loc[regions["region_id"] == x, "region_name"].values[0]
)

# 根据区域所在路口筛选摄像头
cameras = db.query(f"""
    SELECT c.camera_id, c.name
    FROM cameras c
    JOIN intersection_cameras icm
    ON c.camera_id = icm.camera_id
    JOIN regions r ON r.intersection_id = icm.intersection_id
    WHERE r.region_id = '{region_id}'
""")

camera_id = st.selectbox(
    "选择摄像头",
    cameras["camera_id"],
    format_func=lambda x: cameras.loc[cameras["camera_id"] == x, "name"].values[0]
)

st.subheader("➕ 添加摄像头范围 calibration_range")
with st.form("add_range"):
    cr = st.text_area("输入 JSON，如 [100,50,300,200]")
    # 新增区域属性选择
    region_attr = st.selectbox("区域属性", ["行人区", "等待区"])

    if st.form_submit_button("绑定"):
        db.execute("""
            INSERT INTO region_camera_ranges
            (region_id, camera_id, calibration_range, description)
            VALUES (%s,%s,%s,%s)
        """, (region_id, camera_id, cr, region_attr))
        st.success("绑定成功")
        st.rerun()  # 最新 Streamlit 推荐用这个方法刷新

st.subheader("📋 当前区域所有摄像头范围")
df = db.query(f"""
    SELECT rr.*, c.name AS camera_name
    FROM region_camera_ranges rr
    JOIN cameras c ON c.camera_id = rr.camera_id
    WHERE rr.region_id='{region_id}'
""")
st.dataframe(df)
