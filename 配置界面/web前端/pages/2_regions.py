import streamlit as st
from dao_db import DB

db = DB()
st.title("🟦 区域（斑马线）管理")

# 选择路口
intersections = db.query("SELECT intersection_id,name FROM intersections")
intersection = st.selectbox(
    "选择路口",
    intersections["intersection_id"],
    format_func=lambda x: intersections.loc[intersections["intersection_id"] == x, "name"].values[0]
)

# 添加区域
st.subheader("➕ 添加区域")
with st.form("add_region"):
    rid = st.text_input("区域ID")
    name = st.text_input("区域名称")
    desc = st.text_area("描述")

    if st.form_submit_button("提交"):
        db.execute("""
            INSERT INTO regions (region_id, intersection_id, region_name, description)
            VALUES (%s,%s,%s,%s)
        """, (rid, intersection, name, desc))
        st.success("区域添加成功")
        st.rerun()

# 展示区域
st.subheader("📋 当前路口区域")
regions_df = db.query(f"SELECT * FROM regions WHERE intersection_id='{intersection}'")
st.dataframe(regions_df)
