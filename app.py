import subprocess
import sys

# ฟังก์ชันตรวจสอบและติดตั้งไลบรารีอัตโนมัติเผื่อกรณีลืมใส่ใน requirements.txt
def install_and_import(package):
    try:
        __import__(package)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

install_and_import("streamlit")
install_and_import("plotly")

import streamlit as st
import plotly.graph_objects as go
import numpy as np

# ตั้งค่าหน้าเว็บ Streamlit
st.set_page_config(
    page_title="Hand Rail Check by Ardharn ver01 2026",
    page_icon="📐",
    layout="wide"
)

# --- ส่วนของการทำงานแอปพลิเคชัน ---
st.title("🏗️ Hand Rail Check by Ardharn")
st.markdown("Reference Standard: **ASCE 7-05 & AISC ASD (Structural Steel Design)**")

# Sidebar สำหรับรับค่าตัวแปร
st.sidebar.header("🎛️ ตัวแปรบันไดและราวจับ")
riser_h = st.sidebar.number_input("ลูกตั้ง Riser (m)", value=0.18, step=0.01)
tread_w = st.sidebar.number_input("ลูกนอน Tread (m)", value=0.25, step=0.01)
total_stairs = st.sidebar.number_input("จำนวนขั้น (Steps)", value=9, min_value=1, step=1)
h_post_m = st.sidebar.number_input("ความสูงเสา Post (m)", value=0.90, step=0.05)

post_spacing_opt = st.sidebar.selectbox("การจัดวางเสาราวจับ", [
    "ทุกๆ 1 ขั้นบันได (Every 1 Step)",
    "ทุกๆ 2 ขั้นบันได (Every 2 Steps)",
    "ทุกๆ 3 ขั้นบันได (Every 3 Steps)",
    "ทุกๆ 4 ขั้นบันได (Every 4 Steps)"
])

post_every_n = 1
if "2" in post_spacing_opt: post_every_n = 2
elif "3" in post_spacing_opt: post_every_n = 3
elif "4" in post_spacing_opt: post_every_n = 4

# Material Database
materials = {
    "Flat 50x6": {"type": "flat", "b": 0.6, "h": 5.0},
    "Flat 50x9": {"type": "flat", "b": 0.9, "h": 5.0},
    "Flat 50x12": {"type": "flat", "b": 1.2, "h": 5.0},
    "Square Tube 50x2.3": {"type": "box", "D": 5.0, "t": 0.23},
    "Pipe 42.7x2.3": {"type": "pipe", "OD": 4.27, "t": 0.23},
    "Pipe 42.7x3.2": {"type": "pipe", "OD": 4.27, "t": 0.32}
}

rail_sel = st.sidebar.selectbox("ราวมือจับ Top Rail", list(materials.keys()), index=4)
post_sel = st.sidebar.selectbox("เสาราวจับ Vertical Post", list(materials.keys()), index=5)

def get_props(name):
    m = materials[name]
    if m["type"] == "flat":
        s_s = (m["b"] * (m["h"] ** 2)) / 6
        s_w = (m["h"] * (m["b"] ** 2)) / 6
        i_s = (m["b"] * (m["h"] ** 3)) / 12
        i_w = (m["h"] * (m["b"] ** 3)) / 12
    elif m["type"] == "box":
        innerD = max(0, m["D"] - 2 * m["t"])
        i = (m["D"]**4 - innerD**4) / 12
        s_s = s_w = i / (m["D"] / 2)
        i_s = i_w = i
    else:
        innerD = max(0, m["OD"] - 2 * m["t"])
        i = (np.pi * (m["OD"]**4 - innerD**4)) / 64
        s_s = s_w = i / (m["OD"] / 2)
        i_s = i_w = i
    return {"s_s": s_s, "s_w": s_w, "i_s": i_s, "i_w": i_w}

railProps = get_props(rail_sel)
postProps = get_props(post_sel)

L_cm = (tread_w * post_every_n) * 100
H_cm = h_post_m * 100
E = 2.04e6
Fb = 2450.0 * 0.66
deflect_limit = H_cm / 90

k_post = (3 * E * postProps["i_s"]) / (H_cm**3)
k_rail = (6 * E * railProps["i_s"]) / (L_cm**3)
df = k_post / (k_post + (k_rail * 2 * k_post) / (2 * k_post + k_rail))
if np.isnan(df) or df > 1: df = 1

P_eff = 91.0 * df
delta_s = (P_eff * (H_cm**3)) / (3 * E * postProps["i_s"])

W_line = 75.0 / 100
R_top = W_line * L_cm
delta_w = (R_top * (H_cm**3)) / (3 * E * postProps["i_w"])

M_rail = (91.0 * L_cm) / 4
ratio_rail = (M_rail / railProps["s_s"] / Fb) * 100
ratio_post_s = (P_eff * H_cm / postProps["s_s"] / Fb) * 100
ratio_post_w = (R_top * H_cm / postProps["s_w"] / Fb) * 100

max_util = max(ratio_rail, ratio_post_s, ratio_post_w)
max_deflect = max(delta_s, delta_w)
is_pass = (max_util <= 100) and (delta_s <= deflect_limit) and (delta_w <= deflect_limit)

# แสดงผลลัพธ์ UI หลัก
if is_pass:
    st.success("✅ PASS: ราวจับผ่านเกณฑ์การทดสอบทั้งความแข็งแรง (Stress) และการแอ่นตัว (Deflection)")
else:
    st.error("❌ FAIL: ราวจับไม่ผ่านเกณฑ์การทดสอบโครงสร้าง กรุณาเปลี่ยนหน้าตัดวัสดุหรือปรับระยะเสา")

col1, col2, col3 = st.columns(3)
col1.metric("Max Stress Utilization", f"{max_util:.1f}%", "Allowable Max 100%")
col2.metric("Max Deflection", f"{max_deflect:.2f} cm", f"Limit: {deflect_limit:.2f} cm")
col3.metric("Status", "SAFE" if is_pass else "UNSAFE")

# กราฟแสดงผล (Plotly)
st.subheader("📊 ภาพจำลองรูปด้านโครงสร้าง (Side Elevation Preview)")
fig = go.Figure()

# วาดขั้นบันได
stair_x = [i * tread_w for i in range(total_stairs + 1)]
stair_y = [i * riser_h for i in range(total_stairs + 1)]
fig.add_trace(go.Scatter(x=stair_x, y=stair_y, mode='lines', line=dict(color='#334155', width=3), name='Stairs', line_shape='hv'))

# วาดเสาและราว
post_locs = [i + 0.5 for i in range(0, total_stairs, post_every_n)]
for s in post_locs:
    if s < total_stairs:
        px = s * tread_w
        py = int(s) * riser_h
        fig.add_trace(go.Scatter(x=[px, px], y=[py, py + h_post_m], mode='lines', line=dict(color='#10b981' if is_pass else '#f43f5e', width=4), showlegend=False))

fig.update_layout(
    xaxis_title="Horizontal Span (m)",
    yaxis_title="Height (m)",
    margin=dict(l=20, r=20, t=20, b=20),
    height=350
)
st.plotly_chart(fig, use_container_width=True)
