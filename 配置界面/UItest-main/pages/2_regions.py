import streamlit as st
from dao_db import DB

st.set_page_config(layout="wide")
st.title("🟦 区域（斑马线）管理")

db = DB()

# ===============================
# 选择路口
# ===============================
intersections = db.query("SELECT intersection_id, name FROM intersections")

intersection = st.selectbox(
    "选择路口",
    intersections["intersection_id"],
    format_func=lambda x: intersections.loc[
        intersections["intersection_id"] == x, "name"
    ].values[0]
)

# ===============================
# 添加区域
# ===============================
st.subheader("➕ 添加区域")

with st.form("add_region"):
    col1, col2 = st.columns(2)

    with col1:
        rid = st.text_input("区域ID")
        name = st.text_input("区域名称")

    with col2:
        desc = st.text_area("描述")

    if st.form_submit_button("提交"):
        if not rid or not name:
            st.error("区域ID 和 区域名称不能为空")
        else:
            db.execute("""
                INSERT INTO regions
                (region_id, intersection_id, region_name, description)
                VALUES (%s,%s,%s,%s)
            """, (rid, intersection, name, desc))
            st.success("区域添加成功")
            st.rerun()

# ===============================
# 当前路口区域列表
# ===============================
st.subheader("📋 当前路口区域")

regions_df = db.query(
    "SELECT * FROM regions WHERE intersection_id=%s",
    (intersection,)
)

# ===============================
# 区域行内操作
# ===============================
for _, row in regions_df.iterrows():
    with st.container(border=True):
        col1, col2, col3, col4 = st.columns([2, 3, 4, 3])

        col1.markdown(f"**ID**：{row.region_id}")
        col2.markdown(f"**名称**：{row.region_name}")
        col3.markdown(f"**描述**：{row.description}")

        with col4:
            c1, c2 = st.columns(2)

            # 编辑
            if c1.button("✏️ 编辑", key=f"edit_{row.region_id}"):
                st.session_state.edit_region = row.region_id

            # 删除
            if c2.button("🗑 删除", key=f"del_{row.region_id}"):
                st.session_state.delete_region = row.region_id

# ===============================
# 编辑区域
# ===============================
if "edit_region" in st.session_state:
    region_id = st.session_state.edit_region
    region = regions_df[
        regions_df["region_id"] == region_id
    ].iloc[0]

    st.divider()
    st.subheader(f"✏️ 编辑区域：{region_id}")

    with st.form("edit_region_form"):
        name = st.text_input("区域名称", region.region_name)
        desc = st.text_area("描述", region.description)

        col_a, col_b = st.columns(2)

        if col_a.form_submit_button("保存"):
            db.execute("""
                UPDATE regions
                SET region_name=%s, description=%s
                WHERE region_id=%s
            """, (name, desc, region_id))
            del st.session_state.edit_region
            st.success("区域已更新")
            st.rerun()

        if col_b.form_submit_button("取消"):
            del st.session_state.edit_region
            st.rerun()

# ===============================
# 删除区域（统一处理）
# ===============================
if "delete_region" in st.session_state:
    rid = st.session_state.delete_region

    db.execute(
        "DELETE FROM regions WHERE region_id=%s",
        (rid,)
    )

    del st.session_state.delete_region
    st.warning(f"区域 {rid} 已删除")
    st.rerun()
