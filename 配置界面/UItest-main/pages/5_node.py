import streamlit as st
from dao_db import DB

st.set_page_config(layout="wide")
st.title("🖥 节点管理")

db = DB()

# ===============================
# 添加节点
# ===============================
st.subheader("➕ 添加节点")

nodes_df = db.query("SELECT node_id FROM nodes")
node_ids = nodes_df["node_id"].tolist()

with st.form("add_node"):
    col1, col2 = st.columns(2)

    with col1:
        node_id = st.text_input("节点ID")
        name = st.text_input("节点名称")
        ip_address = st.text_input("入网推流地址")

    with col2:
        is_master = st.checkbox("是否主节点", value=True)
        master_node = st.selectbox(
            "主节点（从节点才需要）",
            options=[""] + node_ids
        )
        description = st.text_area("描述")

    if st.form_submit_button("添加"):
        if not node_id or not ip_address:
            st.error("节点ID 和 IP 地址不能为空")
        else:
            db.execute("""
                INSERT INTO nodes
                (node_id, name, ip_address, is_master, master_node_id, description)
                VALUES (%s,%s,%s,%s,%s,%s)
            """, (
                node_id,
                name,
                ip_address,
                is_master,
                None if is_master else master_node,
                description
            ))
            st.success("节点添加成功")
            st.rerun()

# ===============================
# 当前节点列表
# ===============================
st.subheader("📋 当前节点列表")

nodes_df = db.query("SELECT * FROM nodes")

for _, row in nodes_df.iterrows():
    with st.container(border=True):
        col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 3])

        col1.markdown(f"**ID**：{row.node_id}")
        col2.markdown(f"**名称**：{row.name}")
        col3.markdown(f"**IP**：{row.ip_address}")
        col4.markdown(
            "🟢 主节点" if row.is_master else f"🔗 从属：{row.master_node_id}"
        )

        with col5:
            c1, c2 = st.columns(2)

            if c1.button("✏️ 编辑", key=f"edit_{row.node_id}"):
                st.session_state.edit_node = row.node_id

            if c2.button("🗑 删除", key=f"del_{row.node_id}"):
                st.session_state.delete_node = row.node_id

# ===============================
# 编辑节点
# ===============================
if "edit_node" in st.session_state:
    nid = st.session_state.edit_node
    node = nodes_df[nodes_df["node_id"] == nid].iloc[0]

    st.divider()
    st.subheader(f"✏️ 编辑节点：{nid}")

    with st.form("edit_node_form"):
        name = st.text_input("节点名称", node.name)
        ip_address = st.text_input("入网推流地址", node.ip_address)
        is_master = st.checkbox("是否主节点", value=bool(node.is_master))
        master_node = st.selectbox(
            "主节点",
            options=[""] + node_ids,
            index=0 if not node.master_node_id else node_ids.index(node.master_node_id) + 1
        )
        description = st.text_area("描述", node.description)

        col_a, col_b = st.columns(2)

        if col_a.form_submit_button("保存"):
            db.execute("""
                UPDATE nodes
                SET name=%s,
                    ip_address=%s,
                    is_master=%s,
                    master_node_id=%s,
                    description=%s
                WHERE node_id=%s
            """, (
                name,
                ip_address,
                is_master,
                None if is_master else master_node,
                description,
                nid
            ))
            del st.session_state.edit_node
            st.success("节点更新成功")
            st.rerun()

        if col_b.form_submit_button("取消"):
            del st.session_state.edit_node
            st.rerun()

# ===============================
# 删除节点（统一处理）
# ===============================
if "delete_node" in st.session_state:
    nid = st.session_state.delete_node

    db.execute(
        "DELETE FROM nodes WHERE node_id=%s",
        (nid,)
    )

    del st.session_state.delete_node
    st.warning(f"节点 {nid} 已删除")
    st.rerun()
