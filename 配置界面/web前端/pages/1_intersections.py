import streamlit as st
from dao_db import DB

st.title("📍 路口管理")

db = DB()

st.subheader("➕ 添加路口")
with st.form("add_intersection"):
    iid = st.text_input("路口ID")
    name = st.text_input("名称")
    loc = st.text_input("位置")
    desc = st.text_area("描述")

    if st.form_submit_button("添加"):
        db.execute("""
            INSERT INTO intersections (intersection_id, name, location, description)
            VALUES (%s,%s,%s,%s)
        """, (iid, name, loc, desc))
        st.success("添加成功")
        st.rerun()

st.subheader("📋 路口列表")
df = db.query("SELECT * FROM intersections")
st.dataframe(df)
