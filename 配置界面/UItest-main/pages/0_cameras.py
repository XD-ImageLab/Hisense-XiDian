import streamlit as st
from dao_db import DB
import time
from streamlit_autorefresh import st_autorefresh
st.set_page_config(page_title="摄像头管理", layout="wide")
st.title("📷 摄像头管理")

db = DB()

# ===============================
# 心跳自动刷新（每 5 秒）
# ===============================
# st_autorefresh = st.empty()
# if "last_refresh" not in st.session_state:
#     st.session_state.last_refresh = time.time()

st_autorefresh(
    interval=5000,   # 5 秒
    limit=None,
    key="camera_heartbeat"
)


# ===============================
# 基础数据
# ===============================
nodes_df = db.query("SELECT node_id, name FROM nodes")
intersections_df = db.query("SELECT intersection_id, name FROM intersections")

node_map = dict(zip(nodes_df["node_id"], nodes_df["name"]))
intersection_map = dict(zip(intersections_df["intersection_id"], intersections_df["name"]))

# ===============================
# 新增摄像头
# ===============================
st.subheader("➕ 添加摄像头")

with st.form("add_camera"):
    col1, col2, col3 = st.columns(3)

    with col1:
        camera_id = st.text_input("摄像头ID")
        name = st.text_input("摄像头名称")
        node_id = st.selectbox("挂载节点", [""] + list(node_map.keys()),
                               format_func=lambda x: node_map.get(x, ""))

    with col2:
        intersection_id = st.selectbox("所属路口", [""] + list(intersection_map.keys()),
                                       format_func=lambda x: intersection_map.get(x, ""))
        rtsp_url = st.text_input("RTSP URL")
        encoding = st.text_input("编码方式")

    with col3:
        resolution = st.text_input("分辨率")
        video_quality = st.number_input("画质(1-100)", 1, 100, 80)
        status = st.selectbox("状态", ["online", "offline", "maintenance"])

    description = st.text_area("描述")

    if st.form_submit_button("添加摄像头"):
        if not camera_id or not node_id or not intersection_id:
            st.error("摄像头ID / 节点 / 路口不能为空")
        else:
            db.execute("""
                INSERT INTO cameras
                (camera_id, name, node_id, rtsp_url, encoding,
                 resolution, video_quality, status, description)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (camera_id, name, node_id, rtsp_url, encoding,
                  resolution, video_quality, status, description))

            db.execute("""
                INSERT INTO intersection_cameras (intersection_id, camera_id)
                VALUES (%s,%s)
            """, (intersection_id, camera_id))

            st.success("摄像头添加成功")
            st.rerun()

# ===============================
# 路口筛选（带确认按钮）
# ===============================
st.subheader("🔍 摄像头列表")

# 初始化确认状态
if "confirmed_intersection" not in st.session_state:
    st.session_state.confirmed_intersection = "全部"

col_a, col_b = st.columns([3, 1])

with col_a:
    filter_intersection = st.selectbox(
        "按路口筛选",
        ["全部"] + list(intersection_map.keys()),
        format_func=lambda x: "全部" if x == "全部" else intersection_map[x]
    )

with col_b:
    if st.button("🔍 确认查询"):
        st.session_state.confirmed_intersection = filter_intersection
selected_intersection = st.session_state.confirmed_intersection

if selected_intersection == "全部":
    cameras = db.query("""
        SELECT c.*, n.name AS node_name,
               GROUP_CONCAT(ic.intersection_id) AS intersections
        FROM cameras c
        LEFT JOIN nodes n ON c.node_id = n.node_id
        LEFT JOIN intersection_cameras ic ON c.camera_id = ic.camera_id
        GROUP BY c.camera_id
    """)
else:
    cameras = db.query("""
        SELECT c.*, n.name AS node_name,
               GROUP_CONCAT(ic.intersection_id) AS intersections
        FROM cameras c
        LEFT JOIN nodes n ON c.node_id = n.node_id
        LEFT JOIN intersection_cameras ic ON c.camera_id = ic.camera_id
        WHERE ic.intersection_id = %s
        GROUP BY c.camera_id
    """, (selected_intersection,))

# ===============================
# 表格 + 行内按钮
# ===============================
for _, row in cameras.iterrows():
    with st.container(border=True):
        col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 3])

        col1.markdown(f"**ID**：{row.camera_id}")
        col2.markdown(f"**名称**：{row.name}")
        col3.markdown(f"**节点**：{row.node_name}")
        col4.markdown(f"**状态**：`{row.status}`")

        # ===== 行内操作 =====
        with col5:
            c1, c2, c3 = st.columns(3)

            # 快速状态切换
            # if c1.button("🔄 切换状态", key=f"status_{row.camera_id}"):
            #     new_status = "offline" if row.status == "online" else "online"
            #     db.execute(
            #         "UPDATE cameras SET status=%s WHERE camera_id=%s",
            #         (new_status, row.camera_id)
            #     )
            #     st.rerun()
            if c1.button("🔄 切换状态", key=f"status_{row.camera_id}"):
                st.session_state.pending_status = row.camera_id

            # 编辑
            if c2.button("✏️ 编辑", key=f"edit_{row.camera_id}"):
                st.session_state.edit_camera = row.camera_id

            # 删除
            # if c3.button("🗑 删除", key=f"del_{row.camera_id}"):
            #     db.execute(
            #         "DELETE FROM cameras WHERE camera_id=%s",
            #         (row.camera_id,)
            #     )
            #     st.warning(f"{row.camera_id} 已删除")
            #     st.rerun()
            if c3.button("🗑 删除", key=f"del_{row.camera_id}"):
                st.session_state.pending_delete = row.camera_id
# ===============================
# 统一处理按钮事件（稳定）
# ===============================
if "pending_status" in st.session_state:
    cam_id = st.session_state.pending_status

    db.execute("""
        UPDATE cameras
        SET status = CASE
            WHEN status='online' THEN 'offline'
            ELSE 'online'
        END
        WHERE camera_id=%s
    """, (cam_id,))

    del st.session_state.pending_status
    st.rerun()

if "pending_delete" in st.session_state:
    cam_id = st.session_state.pending_delete

    db.execute(
        "DELETE FROM cameras WHERE camera_id=%s",
        (cam_id,)
    )

    del st.session_state.pending_delete
    st.success(f"{cam_id} 已删除")
    st.rerun()

# ===============================
# 编辑弹窗区
# ===============================
if "edit_camera" in st.session_state:
    cam_id = st.session_state.edit_camera
    cam = cameras[cameras["camera_id"] == cam_id].iloc[0]

    st.divider()
    st.subheader(f"✏️ 编辑摄像头：{cam_id}")

    with st.form("edit_form"):
        name = st.text_input("名称", cam.name)
        rtsp_url = st.text_input("RTSP", cam.rtsp_url)
        encoding = st.text_input("编码", cam.encoding)
        resolution = st.text_input("分辨率", cam.resolution)
        video_quality = st.number_input("画质", 1, 100, int(cam.video_quality))
        description = st.text_area("描述", cam.description)

        col_a, col_b = st.columns(2)
        if col_a.form_submit_button("保存"):
            db.execute("""
                UPDATE cameras
                SET name=%s, rtsp_url=%s, encoding=%s,
                    resolution=%s, video_quality=%s, description=%s
                WHERE camera_id=%s
            """, (name, rtsp_url, encoding,
                  resolution, video_quality, description, cam_id))
            del st.session_state.edit_camera
            st.success("更新成功")
            st.rerun()

        if col_b.form_submit_button("取消"):
            del st.session_state.edit_camera
            st.rerun()
