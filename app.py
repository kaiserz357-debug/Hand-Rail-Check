import streamlit as st
import matplotlib.pyplot as plt
import math

# ตั้งค่าหน้าจอให้เหมาะกับ Mobile
st.set_page_config(page_title="Stair Railing Check", layout="centered")

st.title("Stair Railing Structural Analysis")
st.write("ตรวจสอบความแข็งแรงตามมาตรฐาน **ASCE 7-05**")

# ==========================================
# 1. MATERIAL DATABASE
# ==========================================
materials = {
    "Flat 50x6": {"type": "flat", "b": 0.6, "h": 5.0},
    "Flat 50x9": {"type": "flat", "b": 0.9, "h": 5.0},
    "Square Tube 1.5\" (2.3mm)": {"type": "box", "D": 3.8, "t": 0.23},
    "Square Tube 2\" (3.2mm)": {"type": "box", "D": 5.0, "t": 0.32},
    "Pipe 1.5\" (3.2mm)": {"type": "pipe", "OD": 4.27, "t": 0.32}
}

def get_S_values(name):
    m = materials[name]
    if m["type"] == "flat":
        s_strong = (m["b"] * (m["h"]**2)) / 6
        s_weak = (m["h"] * (m["b"]**2)) / 6
        return s_strong, s_weak
    elif m["type"] == "box":
        s = (m["D"]**4 - (m["D"] - 2*m["t"])**4) / (6 * m["D"])
        return s, s
    elif m["type"] == "pipe":
        s = (math.pi * (m["OD"]**4 - (m["OD"] - 2*m["t"])**4)) / (32 * m["OD"])
        return s, s

# ==========================================
# 2. SIDEBAR INPUTS (สำหรับมือถือจะซ่อนอยู่ในเมนู)
# ==========================================
with st.sidebar:
    st.header("⚙️ Configuration")
    
    st.subheader("Stair Geometry")
    riser_h = st.number_input("Riser Height (m)", value=0.18, step=0.01)
    tread_w = st.number_input("Tread Width (m)", value=0.25, step=0.01)
    total_stairs = st.slider("Total Steps", 1, 20, 9)
    h_post_m = st.number_input("Post Height (m)", value=0.90, step=0.05)
    post_every_n = st.selectbox("Post every 'n' steps", [1, 2, 3, 4], index=1)

    st.subheader("Materials")
    rail_sel = st.selectbox("Select Railing Material", list(materials.keys()), index=0)
    post_sel = st.selectbox("Select Post Material", list(materials.keys()), index=2)

# ==========================================
# 3. CALCULATIONS
# ==========================================
S_rail_s, _ = get_S_values(rail_sel)
S_post_s, S_post_w = get_S_values(post_sel)

L_m = tread_w * post_every_n
L_cm = L_m * 100
P_point, w_dist = 91.0, 75.0
Fb = 2450.0 * 0.66

# Stress Checks
ratio_rail = ((P_point * L_cm / 4) / S_rail_s / Fb) * 100
ratio_post_s = (P_point * (h_post_m * 100) / S_post_s / Fb) * 100
ratio_post_w = (w_dist * L_m * (h_post_m * 100) / S_post_w / Fb) * 100

overall_pass = max(ratio_rail, ratio_post_s, ratio_post_w) < 100

# ==========================================
# 4. MAIN DISPLAY (เหมาะกับ Mobile)
# ==========================================
# แสดง Metric สำคัญ
col1, col2 = st.columns(2)
col1.metric("Max Utilization", f"{max(ratio_rail, ratio_post_s, ratio_post_w):.1f}%", 
            delta_color="inverse", delta=f"{max(ratio_rail, ratio_post_s, ratio_post_w)-100:.1f}%")
col2.metric("Overall Status", "SAFE" if overall_pass else "FAIL")

# วาดรูปบันได
fig, ax = plt.subplots(figsize=(10, 6))
for i in range(total_stairs):
    ax.plot([i*tread_w, (i+1)*tread_w], [i*riser_h, i*riser_h], color='black', lw=1.5)
    ax.plot([(i+1)*tread_w, (i+1)*tread_w], [i*riser_h, (i+1)*riser_h], color='black', lw=1.5)

post_idx = list(range(0, total_stairs, post_every_n))
if (total_stairs-1) not in post_idx: post_idx.append(total_stairs-1)

x_p, y_p = [], []
for s in post_idx:
    px, py = (s * tread_w) + (tread_w / 2), s * riser_h
    ax.plot([px, px], [py, py + h_post_m], color='seagreen' if overall_pass else 'crimson', lw=4)
    x_p.append(px); y_p.append(py + h_post_m)

ax.plot(x_p, y_p, color='royalblue', lw=3, marker='o')
ax.set_aspect('equal')
ax.grid(True, alpha=0.1)
st.pyplot(fig)

# แสดงรายละเอียด (Expander ช่วยประหยัดพื้นที่บนมือถือ)
with st.expander("🔍 See Detailed Stress Analysis"):
    st.write(f"**Rail:** {rail_sel} -> **{ratio_rail:.1f}%**")
    st.write(f"**Post (Strong):** {post_sel} -> **{ratio_post_s:.1f}%**")
    st.write(f"**Post (Weak):** {post_sel} -> **{ratio_post_w:.1f}%**")
    st.info(f"Post Spacing: {L_cm:.1f} cm")
