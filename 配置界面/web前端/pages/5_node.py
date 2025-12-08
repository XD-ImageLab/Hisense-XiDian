import streamlit as st
from dao_db import DB

st.title("🖥 节点管理")

db = DB()

# 初始化刷新状态
if "node_refresh" not in st.session_state:
    st.session_state.node_refresh = False

# 添加节点表单
st.subheader("➕ 添加节点")
with st.form("add_node"):
    node_id = st.text_input("节点ID")
    name = st.text_input("节点名称")
    ip_address = st.text_input("入网推流地址")
    is_master = st.checkbox("是否主节点", value=True)
    master_node = st.selectbox(
        "主节点ID（如果是从节点）",
        options=[""] + db.query("SELECT node_id FROM nodes").get("node_id", []).tolist()
    )
    description = st.text_area("描述")

    if st.form_submit_button("添加"):
        if not node_id or not ip_address:
            st.error("节点ID和IP地址不能为空")
        else:
            db.execute("""
                INSERT INTO nodes 
                (node_id, name, ip_address, is_master, master_node_id, description)
                VALUES (%s,%s,%s,%s,%s,%s)
            """, (node_id, name, ip_address, is_master, master_node if master_node else None, description))
            st.success("节点添加成功")
            st.session_state.node_refresh = True

# 展示节点列表
st.subheader("📋 当前节点列表")
nodes_df = db.query("SELECT * FROM nodes")
st.dataframe(nodes_df)

# 自动刷新逻辑
if st.session_state.node_refresh:
    st.session_state.node_refresh = False
    st.experimental_rerun = None  # 移除旧方法
    st.experimental_rerun = True
