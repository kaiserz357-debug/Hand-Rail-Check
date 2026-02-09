import streamlit as st
import matplotlib.pyplot as plt
import math

# 1. บังคับให้หน้าจอ Refresh ทันทีที่มีการเปลี่ยนแปลง
st.set_page_config(page_title="Stair Structural Pro", layout="centered")

# ==========================================
# MATERIAL DATABASE
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

# ==========================================
# SIDEBAR INPUTS (วางไว้บนสุด)
# ==========================================
with st.sidebar:
    st.header("⚙️ Configuration")
    riser_h = st.number_input("Riser Height (m)", value=0.18, step=0.01)
    tread_w = st.number_input("Tread Width (m)", value=0.25, step=0.01)
    total_stairs = st.slider("Total Steps", 1, 20, 9)
    h_post_m = st.number_input("Post Height (m)", value=0.90, step=0.05)
    post_every_n = st.selectbox("Post Spacing (steps)", [1, 2, 3, 4], index=1)
    
    st.subheader("Materials")
    # ใช้ Key ของ materials มาทำ Dropdown
    rail_sel = st.selectbox("Select Rail", list(materials.keys()), index=0)
    post_sel = st.selectbox("Select Post", list(materials.keys()), index=2)
    is_end_post = st.checkbox("End Post (เสาริม)", value=False)

# ==========================================
# CALCULATIONS (ย้ายมาอยู่ใน Main เพื่อให้รันใหม่ทุกครั้ง)
# ==========================================
def get_props(name):
    m = materials[name]
    if m["type"] == "flat":
        return (m['b']*m['h']**2/6), (m['h']*m['b']**2/6), (m['b']*m['h']**3/12), m['h']
    elif m["type"] == "box":
        i = (m['D']**4 - (m['D']-2*m['t'])**4)/12
        return i/(m['D']/2), i/(m['D']/2), i, m['D']
    elif m["type"] == "pipe":
        i = (math.pi*(m['OD']**4 - (m['OD']-2*m['t'])**4))/64
        return i/(m['OD']/2), i/(m['OD']/2), i, m['OD']

# ดึงค่าล่าสุดจาก Dropdown มาคำนวณทันที
S_rail_s, _, I_rail, _ = get_props(rail_sel)
S_post_s, S_post_w, I_post, _ = get_props(post_sel)

# สรุปตัวเลข Stress
L_cm = (tread_w * post_every_n) * 100
H_cm = h_post_m * 100
Fb = 2450.0 * 0.66

# Stiffness & DF
k_post = (3 * I_post) / (H_cm**3)
k_rail = (48 * I_rail) / (L_cm**3)
df = max(min(k_post / (k_post + ((1 if is_end_post else 2) * k_rail)), 1.0), 0.6)

P_eff = 91.0 * df
ratio_rail = ((91.0 * L_cm / 4) / S_rail_s / Fb) * 100
ratio_post_s = (P_eff * H_cm / S_post_s / Fb) * 100
ratio_post_w = (75.0 * (L_cm/100) * H_cm / S_post_w / Fb) * 100

max_util = max(ratio_rail, ratio_post_s, ratio_post_w)

# ==========================================
# DISPLAY
# ==========================================
st.title("Stair Structural Pro")

# Metric Dashboard (จะเปลี่ยนตัวเลขทันที)
c1, c2 = st.columns(2)
c1.metric("Max Utilization", f"{max_util:.1f}%")
c2.metric("Load Factor (DF)", f"{df:.2f}")

if max_util > 100:
    st.error(f"⚠️ UNSAFE: Overloaded by {max_util-100:.1f}%")
else:
    st.success("✅ SAFE: Structure is within limits")

# DRAWING
fig, ax = plt.subplots(figsize=(10, 5))
# วาดขั้นบันได
for i in range(total_stairs):
    ax.plot([i*tread_w, (i+1)*tread_w], [i*riser_h, i*riser_h], color='gray', lw=1)
    ax.plot([(i+1)*tread_w, (i+1)*tread_w], [i*riser_h, (i+1)*riser_h], color='gray', lw=1)

# วาดเสาและราว
post_idx = list(range(0, total_stairs, post_every_n))
if (total_stairs-1) not in post_idx: post_idx.append(total_stairs-1)

x_tops, y_tops = [], []
for s in post_idx:
    px, py = (s * tread_w) + (tread_w/2), s * riser_h
    ax.plot([px, px], [py, py + h_post_m], color='red' if max_util > 100 else 'green', lw=3)
    x_tops.append(px); y_tops.append(py + h_post_m)

ax.plot(x_tops, y_tops, color='blue', lw=4, marker='o', label="Rail")
ax.set_aspect('equal')
st.pyplot(fig)
