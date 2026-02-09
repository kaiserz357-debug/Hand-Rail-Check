import streamlit as st
import matplotlib.pyplot as plt
import math

# ตั้งค่าหน้าจอ
st.set_page_config(page_title="Stair Structural Pro", layout="centered")

st.title("Stair Railing: Stiffness Analysis")
st.info("💡 ปรับเปลี่ยนวัสดุที่ Sidebar เพื่อดูการกระจายแรงแบบ Real-time")

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

def get_properties(name):
    m = materials[name]
    if m["type"] == "flat":
        s_s = (m["b"] * (m["h"]**2)) / 6
        s_w = (m["h"] * (m["b"]**2)) / 6
        i_s = (m["b"] * (m["h"]**3)) / 12
        return s_s, s_w, i_s, m["h"]
    elif m["type"] == "box":
        i_s = (m["D"]**4 - (m["D"] - 2*m["t"])**4) / 12
        s_s = i_s / (m["D"]/2)
        return s_s, s_s, i_s, m["D"]
    elif m["type"] == "pipe":
        i_s = (math.pi * (m["OD"]**4 - (m["OD"] - 2*m["t"])**4)) / 64
        s_s = i_s / (m["OD"]/2)
        return s_s, s_s, i_s, m["OD"]

# ==========================================
# 2. SIDEBAR INPUTS
# ==========================================
with st.sidebar:
    st.header("⚙️ Configuration")
    riser_h = st.number_input("Riser Height (m)", value=0.18, step=0.01)
    tread_w = st.number_input("Tread Width (m)", value=0.25, step=0.01)
    total_stairs = st.slider("Total Steps", 1, 20, 9)
    h_post_m = st.number_input("Post Height (m)", value=0.90, step=0.05)
    post_every_n = st.selectbox("Post Spacing (steps)", [1, 2, 3, 4], index=1)
    
    st.subheader("Materials Selection")
    rail_sel = st.selectbox("Select Railing Material", list(materials.keys()), index=0)
    post_sel = st.selectbox("Select Post Material", list(materials.keys()), index=2)
    
    is_end_post = st.checkbox("เช็คที่เสาต้นริม (End Post)", value=False)

# ==========================================
# 3. CALCULATIONS
# ==========================================
S_rail_s, _, I_rail, h_rail = get_properties(rail_sel)
S_post_s, S_post_w, I_post, h_post = get_properties(post_sel)

L_cm = (tread_w * post_every_n) * 100
H_cm = h_post_m * 100
P_point, w_dist = 91.0, 75.0
Fb = 2450.0 * 0.66

# Stiffness-Based Distribution Factor (DF)
k_post = (3 * I_post) / (H_cm**3)
k_rail = (48 * I_rail) / (L_cm**3)
neighbor_count = 1 if is_end_post else 2
df = k_post / (k_post + (neighbor_count * k_rail))
df = max(min(df, 1.0), 0.6) # มาตรฐานความปลอดภัยไม่ควรต่ำกว่า 0.6

# Final Stress
P_eff = P_point * df
ratio_rail = ((P_point * L_cm / 4) / S_rail_s / Fb) * 100
ratio_post_s = (P_eff * H_cm / S_post_s / Fb) * 100
ratio_post_w = (w_dist * (L_cm/100) * H_cm / S_post_w / Fb) * 100

max_util = max(ratio_rail, ratio_post_s, ratio_post_w)

# ==========================================
# 4. VISUALIZATION
# ==========================================
col1, col2 = st.columns(2)
col1.metric("Max Utilization", f"{max_util:.1f}%", delta=f"{df*100:.0f}% Load Share", delta_color="inverse")
col2.metric("Overall Status", "SAFE" if max_util < 100 else "FAIL")

fig, ax = plt.subplots(figsize=(10, 6))

# 4.1 วาดบันได (Tread & Riser)
for i in range(total_stairs):
    ax.plot([i*tread_w, (i+1)*tread_w], [i*riser_h, i*riser_h], color='black', lw=1.2) # Tread
    ax.plot([(i+1)*tread_w, (i+1)*tread_w], [i*riser_h, (i+1)*riser_h], color='black', lw=1.2) # Riser

# 4.2 วาดเสาและเก็บตำแหน่งยอดเสาเพื่อวาดราว
post_idx = list(range(0, total_stairs, post_every_n))
if (total_stairs-1) not in post_idx: post_idx.append(total_stairs-1)

x_tops, y_tops = [], []
for s in post_idx:
    px = (s * tread_w) + (tread_w / 2)
    py = s * riser_h
    # วาดเสา
    ax.plot([px, px], [py, py + h_post_m], color='seagreen' if max_util < 100 else 'crimson', lw=4, zorder=3)
    # เก็บค่าไว้ลากเส้นราว
    x_tops.append(px)
    y_tops.append(py + h_post_m)

# 4.3 วาดราว (Rail) เชื่อมต่อยอดเสา
ax.plot(x_tops, y_tops, color='royalblue', lw=5, marker='o', markersize=8, label='Handrail', zorder=4)

ax.set_aspect('equal')
ax.grid(True, alpha=0.1)
st.pyplot(fig)

with st.expander("📊 Detailed Structural Analysis"):
    st.write(f"**Load Share (DF):** {df:.2f} (เสารับแรงจริง {P_eff:.1f} kg)")
    st.divider()
    st.write(f"- Rail Stress Ratio: {ratio_rail:.1f}%")
    st.write(f"- Post Strong Axis (Push): {ratio_post_s:.1f}%")
    st.write(f"- Post Weak Axis (Uniform): {ratio_post_w:.1f}%")
    st.info(f"Post Spacing: {L_cm:.1f} cm")
