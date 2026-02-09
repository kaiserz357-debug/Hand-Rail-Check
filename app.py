import streamlit as st
import matplotlib.pyplot as plt
import math

# ตั้งค่าหน้าจอให้เหมาะกับ Mobile
st.set_page_config(page_title="Stair Railing Check", layout="centered")

st.title("Stair Railing Structural Analysis")
st.info("💡 แตะปุ่มลูกศรมุมซ้ายบน เพื่อปรับเปลี่ยนขนาดเหล็กและระยะบันได")

# ==========================================
# 1. MATERIAL DATABASE & LOGIC
# ==========================================
materials = {
    "Flat 50x6": {"type": "flat", "b": 0.6, "h": 5.0},
    "Flat 50x9": {"type": "flat", "b": 0.9, "h": 5.0},
    "Flat 50x12": {"type": "flat", "b": 1.2, "h": 5.0},
    "Flat 50x16": {"type": "flat", "b": 1.6, "h": 5.0},
    "Square Tube 32x2.3": {"type": "box", "D": 3.2, "t": 0.23},
    "Square Tube 38x2.3": {"type": "box", "D": 3.8, "t": 0.23},
    "Square Tube 50x2.3": {"type": "box", "D": 5.0, "t": 0.23},
    "Square Tube 50x3.2": {"type": "box", "D": 5.0, "t": 0.32},
    "Pipe 27.2x2.3": {"type": "pipe", "OD": 2.70, "t": 0.23},
    "Pipe 34.0x2.3": {"type": "pipe", "OD": 3.40, "t": 0.23},
    "Pipe 42.7x2.3": {"type": "pipe", "OD": 4.27, "t": 0.23},
    "Pipe 42.7x3.2": {"type": "pipe", "OD": 4.27, "t": 0.32},
    "Pipe 48.6x2.3": {"type": "pipe", "OD": 4.86, "t": 0.23},
    "Pipe 48.6x3.2": {"type": "pipe", "OD": 4.86, "t": 0.32}
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
# 2. SIDEBAR INPUTS (รับค่าก่อนคำนวณ)
# ==========================================
with st.sidebar:
    st.header("⚙️ Configuration")
    
    st.subheader("Stair Geometry")
    riser_h = st.number_input("Riser Height (m)", value=0.18, step=0.01)
    tread_w = st.number_input("Tread Width (m)", value=0.25, step=0.01)
    total_stairs = st.slider("Total Steps", 1, 20, 9)
    h_post_m = st.number_input("Post Height (m)", value=0.90, step=0.05)
    post_every_n = st.selectbox("Post every 'n' steps", [1, 2, 3, 4], index=1)

    st.subheader("Materials Selection")
    rail_sel = st.selectbox("Select Railing Material", list(materials.keys()), index=0)
    post_sel = st.selectbox("Select Post Material", list(materials.keys()), index=2)

# ==========================================
# 3. CALCULATIONS (ย้ายมาไว้หลัง Input เพื่อให้ Dynamic)
# ==========================================
S_rail_s, _ = get_S_values(rail_sel)
S_post_s, S_post_w = get_S_values(post_sel)

L_m = tread_w * post_every_n
L_cm = L_m * 100
P_point = 91.0   # kg (Concentrated load)
w_dist = 75.0    # kg/m (Uniform load)
Fb = 2450.0 * 0.66 # Allowable Stress

# 3.1 Rail Stress (Strong Axis)
M_rail = (P_point * L_cm) / 4
ratio_rail = (M_rail / S_rail_s / Fb) * 100

# 3.2 Post Stress (Strong Axis - Point Load)
M_post_s = P_point * (h_post_m * 100)
ratio_post_s = (M_post_s / S_post_s / Fb) * 100

# 3.3 Post Stress (Weak Axis - Reaction from Uniform Load)
R_top = w_dist * L_m
M_post_w = R_top * (h_post_m * 100)
ratio_post_w = (M_post_w / S_post_w / Fb) * 100

max_util = max(ratio_rail, ratio_post_s, ratio_post_w)
overall_pass = max_util < 100

# ==========================================
# 4. MAIN DISPLAY
# ==========================================
# Metric Dashboard
col1, col2 = st.columns(2)
col1.metric("Max Utilization", f"{max_util:.1f}%", 
            delta=f"{max_util-100:.1f}%", delta_color="inverse")
col2.metric("Overall Status", "SAFE" if overall_pass else "FAIL")

if not overall_pass:
    st.error(f"❌ โครงสร้างไม่ปลอดภัย: {max_util:.1f}% (เกิน 100%)")
else:
    st.success("✅ โครงสร้างผ่านเกณฑ์ความปลอดภัย")

# Plotting
fig, ax = plt.subplots(figsize=(10, 6))

# วาดลูกนอนและลูกตั้ง (Tread & Riser)
for i in range(total_stairs):
    ax.plot([i*tread_w, (i+1)*tread_w], [i*riser_h, i*riser_h], color='black', lw=1.5)
    ax.plot([(i+1)*tread_w, (i+1)*tread_w], [i*riser_h, (i+1)*riser_h], color='black', lw=1.5)

# วาดเสา
post_idx = list(range(0, total_stairs, post_every_n))
if (total_stairs-1) not in post_idx: 
    post_idx.append(total_stairs-1)

x_p, y_p = [], []
for s in post_idx:
    px, py = (s * tread_w) + (tread_w / 2), s * riser_h
    # สีเสาเปลี่ยนตามความปลอดภัยรายต้น (เช็คเฉพาะเสา)
    post_safe = max(ratio_post_s, ratio_post_w) < 100
    ax.plot([px, px], [py, py + h_post_m], color='seagreen' if post_safe else 'crimson', lw=4)
    x_p.append(px); y_p.append(py + h_post_m)

# วาดราว
ax.plot(x_p, y_p, color='royalblue', lw=3, marker='o', label='Handrail')

ax.set_aspect('equal')
ax.grid(True, alpha=0.1)
st.pyplot(fig)

# Detailed Analysis
with st.expander("🔍 See Detailed Stress Analysis"):
    st.write(f"**Rail Material:** {rail_sel}")
    st.write(f"**Post Material:** {post_sel}")
    st.divider()
    st.write(f"1. Rail (Strong Axis): {ratio_rail:.1f}%")
    st.write(f"2. Post (Strong Axis): {ratio_post_s:.1f}%")
    st.write(f"3. Post (Weak Axis): {ratio_post_w:.1f}%")
    st.info(f"Actual Post Spacing: {L_cm:.1f} cm")
