import streamlit as st
import json
from PIL import Image
from streamlit_drawable_canvas import st_canvas
from dao_db import DB

# ===============================
# 页面 & DB
# ===============================
st.set_page_config(layout="wide")
db = DB()
st.title("🎯 区域 - 摄像头绑定（并排视图版）")


# ===============================
# Session State 初始化
# ===============================
def init_state():
    defaults = {
        "locked": False,
        "canvas_key": 0,
        "frame_image": None,
        "calibration_json": "",
        "polygon_category": "等待区",
        "region_id": None,
        "camera_id": None
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_state()

# ===============================
# ① 路口 / 区域 / 摄像头 选择
# ===============================
st.subheader("① 选择绑定对象")
c1, c2, c3, c4 = st.columns([3, 3, 3, 2])

with c1:
    intersections = db.query("SELECT intersection_id, name FROM intersections")
    intersection_id = st.selectbox(
        "路口",
        intersections["intersection_id"],
        format_func=lambda x: intersections.loc[intersections["intersection_id"] == x, "name"].values[0],
        disabled=st.session_state.locked
    )

with c2:
    regions = db.query(
        "SELECT region_id, region_name FROM regions WHERE intersection_id=%s",
        (intersection_id,)
    )
    region_id = st.selectbox(
        "区域",
        regions["region_id"],
        format_func=lambda x: regions.loc[regions["region_id"] == x, "region_name"].values[0],
        disabled=st.session_state.locked
    )
    st.session_state.region_id = region_id

with c3:
    cameras = db.query("""
        SELECT c.camera_id, c.name
        FROM cameras c
        JOIN intersection_cameras ic ON c.camera_id = ic.camera_id
        WHERE ic.intersection_id=%s
    """, (intersection_id,))
    camera_id = st.selectbox(
        "摄像头",
        cameras["camera_id"],
        format_func=lambda x: cameras.loc[cameras["camera_id"] == x, "name"].values[0],
        disabled=st.session_state.locked
    )
    st.session_state.camera_id = camera_id

with c4:
    if not st.session_state.locked:
        if st.button("✅ 确认"):
            st.session_state.locked = True
            st.session_state.canvas_key += 1
            st.rerun()
    else:
        if st.button("🔄 重选"):
            st.session_state.locked = False
            st.session_state.frame_image = None
            st.session_state.calibration_json = ""
            st.session_state.canvas_key += 1
            st.rerun()


# ===============================
# ② 帧来源（Frame Provider）
# ===============================
def get_frame():
    st.subheader("② 选择标注帧来源")
    source = st.radio(
        "帧来源",
        ["上传图片", "（预留）实时视频流"],
        horizontal=True
    )

    if source == "上传图片":
        file = st.file_uploader(
            "上传摄像头截图",
            type=["png", "jpg", "jpeg"]
        )
        if file:
            img = Image.open(file).convert("RGB")
            return img.resize((640, 640))
    else:
        st.info("此处后续可接 RTSP / WebRTC / 抓帧服务")
        return None


# ===============================
# ③ 核心工作区 (并排布局)
# ===============================
if st.session_state.locked:
    frame = get_frame()
    if frame:
        st.session_state.frame_image = frame

    if st.session_state.frame_image:
        st.divider()

        # --- 创建左右两列 ---
        col_draw, col_hist = st.columns(2)

        CANVAS_SIZE = 640

        # ---------------------------
        # 左侧：绘制区域
        # ---------------------------
        with col_draw:
            st.subheader("✏️ 绘制新区域")

            canvas = st_canvas(
                background_image=st.session_state.frame_image,
                drawing_mode="polygon",
                fill_color="rgba(255,165,0,0.3)",
                stroke_color="#ff0000",
                stroke_width=2,
                height=CANVAS_SIZE,
                width=CANVAS_SIZE,
                key=f"canvas_draw_{st.session_state.canvas_key}",
                display_toolbar=True
            )

            # 解析绘制逻辑
            if canvas.json_data and canvas.json_data["objects"]:
                obj = canvas.json_data["objects"][-1]

                # 兼容 path 和 points 两种格式
                pts = []
                if "path" in obj:
                    # SVG path: [['M', x, y], ['L', x, y], ...]
                    for p in obj["path"]:
                        if p[0] in ["M", "L"]:
                            # 归一化: x/W, y/H
                            pts.append([p[1] / CANVAS_SIZE, p[2] / CANVAS_SIZE])
                elif "points" in obj:
                    # Points: [{'x': 10, 'y': 10}, ...]
                    # 注意：st_canvas 有时返回相对坐标，需谨慎。通常 path 更准。
                    for p in obj["points"]:
                        pts.append([p['x'] / CANVAS_SIZE, p['y'] / CANVAS_SIZE])

                # 简单去重
                uniq = []
                for p in pts:
                    if p not in uniq:
                        uniq.append(p)

                if len(uniq) >= 3:
                    st.session_state.calibration_json = json.dumps(uniq)
                    st.success(f"✅ 已捕捉 {len(uniq)} 个顶点")

        # ---------------------------
        # 右侧：历史概览 (只读回显)
        # ---------------------------
        with col_hist:
            st.subheader("📌 历史区域概览")

            # 读取历史数据
            rows_hist = db.query("""
                SELECT calibration_range, description
                FROM region_camera_ranges
                WHERE region_id=%s AND camera_id=%s
            """, (region_id, camera_id))

            color_map = {
                "等待区": ("rgba(0,255,0,0.3)", "#00aa00"),
                "行人区": ("rgba(0,0,255,0.3)", "#0000aa"),
                "禁行区": ("rgba(255,0,0,0.3)", "#aa0000"),
            }

            history_objects = []
            if not rows_hist.empty:
                for _, r in rows_hist.iterrows():
                    try:
                        pts_norm = json.loads(r["calibration_range"])
                        # 反归一化
                        # 假设数据格式是 [[x,y], [x,y]]
                        # x对应Width, y对应Height
                        pts_abs = [{"x": p[0] * CANVAS_SIZE, "y": p[1] * CANVAS_SIZE} for p in pts_norm]

                        fill, stroke = color_map.get(r["description"], ("rgba(128,128,128,0.3)", "#666"))

                        history_objects.append({
                            "type": "polygon",
                            "points": pts_abs,
                            "fill": fill,
                            "stroke": stroke,
                            "strokeWidth": 2,
                            "selectable": False,  # 禁止选中
                            "evented": False  # 禁止交互
                        })
                    except Exception as e:
                        print(f"Error parsing history: {e}")

            # 渲染只读 Canvas
            st_canvas(
                background_image=st.session_state.frame_image,
                height=CANVAS_SIZE,
                width=CANVAS_SIZE,
                drawing_mode="transform",  # 使用 transform 模式但禁用交互，模拟只读
                initial_drawing={"objects": history_objects},
                key=f"canvas_hist_{st.session_state.canvas_key}",
                display_toolbar=False
            )

# ===============================
# ④ 绑定提交
# ===============================
if st.session_state.locked and st.session_state.frame_image:
    st.divider()
    st.subheader("④ 确认并绑定")

    with st.form("bind_form"):
        c_form1, c_form2 = st.columns([3, 1])
        with c_form1:
            cr = st.text_area(
                "Calibration Range (JSON - 归一化数据)",
                value=st.session_state.calibration_json,
                height=100
            )
        with c_form2:
            st.session_state.polygon_category = st.selectbox(
                "区域属性", ["行人区", "等待区", "禁行区"]
            )
            st.write("")  # Spacer
            st.write("")  # Spacer
            submit_btn = st.form_submit_button("🚀 确认保存", use_container_width=True)

        if submit_btn:
            if not cr:
                st.error("❌ 请先在左侧绘制区域")
            else:
                try:
                    # 验证 JSON 格式
                    json.loads(cr)
                    db.execute("""
                        INSERT INTO region_camera_ranges
                        (region_id, camera_id, calibration_range, description)
                        VALUES (%s,%s,%s,%s)
                    """, (region_id, camera_id, cr, st.session_state.polygon_category))

                    st.success("✅ 绑定成功")
                    st.session_state.canvas_key += 1  # 刷新两个 Canvas
                    st.session_state.calibration_json = ""
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ 数据格式错误: {e}")

# ===============================
# ⑤ 列表管理
# ===============================
if st.session_state.locked:
    st.divider()
    st.subheader("📋 绑定列表管理")

    rows = db.query("""
        SELECT rr.id, c.name AS camera, rr.description, rr.calibration_range
        FROM region_camera_ranges rr
        JOIN cameras c ON c.camera_id = rr.camera_id
        WHERE rr.region_id=%s
    """, (region_id,))

    if not rows.empty:
        # 使用 st.dataframe 展示，更整洁
        st.dataframe(rows[["id", "camera", "description", "calibration_range"]], use_container_width=True)

        # 删除操作区
        del_col1, del_col2 = st.columns([1, 4])
        with del_col1:
            del_id = st.text_input("输入要删除的ID")
        with del_col2:
            if st.button("❌ 删除指定ID"):
                if del_id:
                    db.execute("DELETE FROM region_camera_ranges WHERE id=%s", (del_id,))
                    st.success(f"ID {del_id} 已删除")
                    st.session_state.canvas_key += 1
                    st.rerun()
    else:
        st.info("暂无绑定数据")