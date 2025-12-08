# import streamlit as st
# from dao_db import DB
#
# st.title("🎥 摄像头管理")
#
# db = DB()
#
# # 选择节点
# nodes_df = db.query("SELECT node_id, name FROM nodes")
# if nodes_df.empty:
#     st.warning("请先添加节点")
#     node_id = None
# else:
#     node_id = st.selectbox(
#         "选择节点",
#         nodes_df["node_id"],
#         format_func=lambda x: nodes_df.loc[nodes_df["node_id"] == x, "name"].values[0]
#     )
#
# # 初始化刷新状态
# if "camera_refresh" not in st.session_state:
#     st.session_state.camera_refresh = False
#
# # 添加摄像头表单
# st.subheader("➕ 添加摄像头")
# with st.form("add_camera"):
#     cam_id = st.text_input("摄像头ID")
#     name = st.text_input("摄像头名称")
#     rtsp_url = st.text_input("RTSP URL")
#     encoding = st.text_input("编码格式", value="H.264")
#     resolution = st.text_input("分辨率", value="1920x1080")
#     quality = st.number_input("视频质量(1-100)", min_value=1, max_value=100, value=80)
#     status = st.selectbox("状态", ["online", "offline"])
#
#     if st.form_submit_button("添加"):
#         if not node_id:
#             st.error("请先选择节点")
#         else:
#             db.execute("""
#                 INSERT INTO cameras
#                 (camera_id, name, node_id, rtsp_url, encoding, resolution, video_quality, status)
#                 VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
#             """, (cam_id, name, node_id, rtsp_url, encoding, resolution, quality, status))
#             st.success("摄像头添加成功")
#             st.session_state.camera_refresh = True
#
# # 展示摄像头列表
# st.subheader("📋 当前摄像头列表")
# if node_id:
#     cameras_df = db.query(f"SELECT * FROM cameras WHERE node_id='{node_id}'")
#     st.dataframe(cameras_df)
#
# # 自动刷新逻辑
# if st.session_state.camera_refresh:
#     st.session_state.camera_refresh = False
#     st.experimental_rerun = None  # 移除旧方法
#     st.experimental_rerun = True
import streamlit as st
from dao_db import DB

st.title("📷 摄像头管理")

db = DB()

# 初始化刷新状态
if "camera_refresh" not in st.session_state:
    st.session_state.camera_refresh = False

# 获取节点列表
nodes_df = db.query("SELECT node_id, name FROM nodes")
node_options = [""] + nodes_df["node_id"].tolist()

# 获取路口列表
intersections_df = db.query("SELECT intersection_id, name FROM intersections")
intersection_options = [""] + intersections_df["intersection_id"].tolist()

# 添加摄像头表单
st.subheader("➕ 添加摄像头")
with st.form("add_camera"):
    camera_id = st.text_input("摄像头ID")
    name = st.text_input("摄像头名称")
    node_id = st.selectbox(
        "挂载节点",
        options=node_options,
        format_func=lambda x: nodes_df.loc[nodes_df["node_id"] == x, "name"].values[0] if x else ""
    )
    intersection_id = st.selectbox(
        "所属路口",
        options=intersection_options,
        format_func=lambda x: intersections_df.loc[intersections_df["intersection_id"] == x, "name"].values[
            0] if x else ""
    )
    rtsp_url = st.text_input("RTSP URL")
    encoding = st.text_input("编码方式")
    resolution = st.text_input("分辨率")
    video_quality = st.number_input("画质（1~100）", min_value=1, max_value=100, value=80)
    status = st.selectbox("状态", ["online", "offline", "maintenance"])
    description = st.text_area("描述")

    if st.form_submit_button("添加"):
        if not camera_id or not node_id or not intersection_id:
            st.error("摄像头ID、挂载节点、所属路口不能为空")
        else:
            # 插入摄像头
            db.execute("""
                INSERT INTO cameras
                (camera_id, name, node_id, rtsp_url, encoding, resolution, video_quality, status, description)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (camera_id, name, node_id, rtsp_url, encoding, resolution, video_quality, status, description))

            # 在路口-摄像头映射表里建立关系
            db.execute("""
                INSERT INTO intersection_cameras (intersection_id, camera_id)
                VALUES (%s,%s)
            """, (intersection_id, camera_id))

            st.success("摄像头添加成功并映射到路口")
            st.session_state.camera_refresh = True

# 展示摄像头列表
st.subheader("📋 当前摄像头列表")
cameras_df = db.query("""
    SELECT c.*, n.name AS node_name,
           GROUP_CONCAT(ic.intersection_id) AS intersections
    FROM cameras c
    LEFT JOIN nodes n ON c.node_id = n.node_id
    LEFT JOIN intersection_cameras ic ON c.camera_id = ic.camera_id
    GROUP BY c.camera_id
""")
st.dataframe(cameras_df)

# 自动刷新逻辑
if st.session_state.camera_refresh:
    st.session_state.camera_refresh = False
    st.rerun()


