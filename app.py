import streamlit as st
import matplotlib.pyplot as plt
import math

# 1. Setup
st.set_page_config(page_title="Stair Structural Pro", layout="centered")

# ==========================================
# 2. MATERIAL DATABASE
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
# 3. SIDEBAR INPUTS
# ==========================================
with st.sidebar:
    st.header("⚙️ Configuration")
    riser_h = st.number_input("Riser Height (m)", value=0.18, step=0.01)
    tread_w = st.number_input("Tread Width (m)", value=0.25, step=0.01)
    total_stairs = st.slider("Total Steps", 1, 20, 9)
    h_post_m = st.number_input("Post Height (m)", value=0.90, step=0.05)
    post_every_n = st.selectbox("Post Spacing (steps)", [1, 2, 3, 4], index=1)
    
    st.subheader("Materials")
    rail_sel = st.selectbox("Select Rail", list(materials.keys()), index=0)
    post_sel = st.selectbox("Select Post", list(materials.keys()), index=2)


# ==========================================
# 4. CALCULATIONS (Stress & Deflection)
# ==========================================
def get_props(name):
    m = materials[name]
    if m["type"] == "flat":
        s_s = (m["b"] * (m["h"]**2)) / 6
        s_w = (m["h"] * (m["b"]**2)) / 6
        i_s = (m["b"] * (m["h"]**3)) / 12
        i_w = (m["h"] * (m["b"]**3)) / 12
        return s_s, s_w, i_s, i_w
    elif m["type"] == "box":
        i = (m["D"]**4 - (m["D"] - 2*m["t"])**4) / 12
        return i/(m["D"]/2), i/(m["D"]/2), i, i
    elif m["type"] == "pipe":
        i = (math.pi * (m["OD"]**4 - (m["OD"] - 2*m["t"])**4)) / 64
        return i/(m["OD"]/2), i/(m["OD"]/2), i, i

S_rail_s, _, I_rail, _ = get_props(rail_sel)
S_post_s, S_post_w, I_post_s, I_post_w = get_props(post_sel)

L_cm = (tread_w * post_every_n) * 100
H_cm = h_post_m * 100
E = 2.04e6  # Modulus of Elasticity for Steel (kg/cm^2)
Fb = 2450.0 * 0.66
# แก้จาก 120 เป็น 90
deflect_limit = H_cm / 90  # L/90 Limit ตามเกณฑ์ที่ต้องการ

# 4.1 Stiffness & Load Sharing
k_post = (3 * E * I_post_s) / (H_cm**3)
k_rail = (6 * E * I_rail) / (L_cm**3)
df = k_post / (k_post + k_rail)

# 4.2 Post Deflection Calculation (Cantilever Case)
P_eff = 91.0 * df
# delta = (P * L^3) / (3 * E * I)
delta_s = (P_eff * (H_cm**3)) / (3 * E * I_post_s)

# Weak Axis Deflection (จาก Uniform Load 75 kg/m)
W_line = 75.0 / 100 # kg/cm
R_top = W_line * L_cm
delta_w = (R_top * (H_cm**3)) / (3 * E * I_post_w)

# 4.3 Stress Check (เดิม)
ratio_rail = ((91.0 * L_cm / 4) / S_rail_s / Fb) * 100
ratio_post_s = (P_eff * H_cm / S_post_s / Fb) * 100
ratio_post_w = (R_top * H_cm / S_post_w / Fb) * 100

max_util = max(ratio_rail, ratio_post_s, ratio_post_w)
deflect_pass = (delta_s <= deflect_limit) and (delta_w <= deflect_limit)

# ==========================================
# 5. MAIN UI
# ==========================================
st.title("Stair Structural Pro + Deflection Check")

c1, c2, c3 = st.columns(3)
c1.metric("Max Stress", f"{max_util:.1f}%")
c2.metric("Max Deflection", f"{max(delta_s, delta_w):.2f} cm")
c3.metric("Limit (L/90)", f"{deflect_limit:.2f} cm")

if max_util > 100 or not deflect_pass:
    st.error("⚠️ โครงสร้างไม่ผ่านเกณฑ์ (Check Stress หรือ Deflection)")
else:
    st.success("✅ โครงสร้างผ่านเกณฑ์ทั้งความแข็งแรงและการโก่งตัว")

# --- Drawing (Same as before) ---
fig, ax = plt.subplots(figsize=(10, 5))
for i in range(total_stairs):
    ax.plot([i*tread_w, (i+1)*tread_w], [i*riser_h, i*riser_h], color='black', lw=1)
    ax.plot([(i+1)*tread_w, (i+1)*tread_w], [i*riser_h, (i+1)*riser_h], color='black', lw=1)

post_idx = list(range(0, total_stairs, post_every_n))
if (total_stairs-1) not in post_idx: post_idx.append(total_stairs-1)

x_tops, y_tops = [], []
for s in post_idx:
    px, py = (s * tread_w) + (tread_w/2), s * riser_h
    # สีเสาเปลี่ยนตามเงื่อนไข Stress & Deflection
    color = 'green' if (max_util < 100 and deflect_pass) else 'red'
    ax.plot([px, px], [py, py + h_post_m], color=color, lw=4, zorder=3)
    x_tops.append(px); y_tops.append(py + h_post_m)

ax.plot(x_tops, y_tops, color='royalblue', lw=5, marker='o', zorder=4)
ax.set_aspect('equal')
st.pyplot(fig)

# Detailed Analysis
with st.expander("🔍 See Detailed Stress & Deflection Analysis"):
    st.subheader("Stress Analysis")
    st.write(f"- Rail (Strong): {ratio_rail:.1f}%")
    st.write(f"- Post (Strong): {ratio_post_s:.1f}%")
    st.write(f"- Post (Weak): {ratio_post_w:.1f}%")
    
    st.subheader("Deflection Analysis (L/90)")
    st.write(f"- Limit: {deflect_limit:.2f} cm")
    st.write(f"- Actual Strong Axis: {delta_s:.2f} cm {'✅' if delta_s <= deflect_limit else '❌'}")
    st.write(f"- Actual Weak Axis: {delta_w:.2f} cm {'✅' if delta_w <= deflect_limit else '❌'}")
    
    st.divider()
    st.write(f"**Distribution Factor (DF):** {df:.2f}")
    st.write(f"**Kpost:** {k_post:.2f}")
    st.write(f"**Krail:** {k_rail:.2f}")
    st.info(f"Post Spacing: {L_cm:.1f} cm")
