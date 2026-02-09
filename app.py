import streamlit as st
import matplotlib.pyplot as plt
import math

# ตั้งค่าหน้าจอ
st.set_page_config(page_title="Stair Structural Pro", layout="centered")

st.title("Stair Railing: Stiffness Analysis")
st.write("คำนวณการกระจายแรง (Load Distribution) ตามความแข็งแรงของวัสดุ")

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
    riser_h = st.number_input("Riser Height (m)", value=0.18)
    tread_w = st.number_input("Tread Width (m)", value=0.25)
    total_stairs = st.slider("Steps", 1, 20, 9)
    h_post_m = st.number_input("Post Height (m)", value=0.90)
    post_every_n = st.selectbox("Post Spacing (steps)", [1, 2, 3, 4], index=1)
    
    st.subheader("Materials")
    rail_sel = st.selectbox("Rail Material", list(materials.keys()), index=0)
    post_sel = st.selectbox("Post Material", list(materials.keys()), index=2)
    
    is_end_post = st.checkbox("เป็นเสาต้นแรก/สุดท้าย (End Post)", value=False)

# ==========================================
# 3. ADVANCED CALCULATIONS
# ==========================================
# 3.1 Get Structural Properties
S_rail_s, _, I_rail, h_rail = get_properties(rail_sel)
S_post_s, S_post_w, I_post, h_post = get_properties(post_sel)

L_cm = (tread_w * post_every_n) * 100
H_cm = h_post_m * 100
P_point, w_dist = 91.0, 75.0
Fb = 2450.0 * 0.66

# 3.2 Stiffness & Distribution Logic
# k = Load / Deflection
k_post = (3 * I_post) / (H_cm**3)
k_rail = (48 * I_rail) / (L_cm**3)

# Distribution Factor (DF)
# กรณีเสากลาง แรงจะกระจายไป 2 ข้าง (2*k_rail)
# กรณีเสาริม แรงกระจายได้ข้างเดียว (1*k_rail)
neighbor_count = 1 if is_end_post else 2
df = k_post / (k_post + (neighbor_count * k_rail))
df = max(min(df, 1.0), 0.6) # Limit ต่ำสุดที่ 0.6 ตามมาตรฐานความปลอดภัย

# 3.3 Final Stress Calculations
P_eff = P_point * df
M_rail = (P_point * L_cm) / 4
M_post_s = P_eff * H_cm
M_post_w = (w_dist * (L_cm/100) * H_cm) # Weak axis จาก Uniform load

ratio_rail = (M_rail / S_rail_s / Fb) * 100
ratio_post_s = (M_post_s / S_post_s / Fb) * 100
ratio_post_w = (M_post_w / S_post_w / Fb) * 100

max_util = max(ratio_rail, ratio_post_s, ratio_post_w)

# ==========================================
# 4. MOBILE-FIRST UI
# ==========================================
col1, col2 = st.columns(2)
col1.metric("Max Utilization", f"{max_util:.1f}%", delta=f"{df*100:.0f}% Load Share", delta_color="normal")
col2.metric("Post Status", "SAFE" if max_util < 100 else "FAIL")

# Drawing
fig, ax = plt.subplots(figsize=(10, 5))
for i in range(total_stairs):
    ax.plot([i*tread_w, (i+1)*tread_w], [i*riser_h, i*riser_h], color='black', lw=1)
    ax.plot([(i+1)*tread_w, (i+1)*tread_w], [i*riser_h, (i+1)*riser_h], color='black', lw=1)

post_idx = list(range(0, total_stairs, post_every_n))
if (total_stairs-1) not in post_idx: post_idx.append(total_stairs-1)

for s in post_idx:
    px, py = (s * tread_w) + (tread_w / 2), s * riser_h
    ax.plot([px, px], [py, py + h_post_m], color='seagreen' if max_util < 100 else 'crimson', lw=4)

ax.set_aspect('equal')
st.pyplot(fig)

with st.expander("📊 Detailed Analysis"):
    st.write(f"**Distribution Factor:** {df:.2f} (เสารับแรงจริง {P_eff:.1f} kg)")
    st.write(f"**Rail Stiffness (k_rail):** {k_rail:.4f}")
    st.write(f"**Post Stiffness (k_post):** {k_post:.4f}")
    st.divider()
    st.write(f"Ratio Rail: {ratio_rail:.1f}%")
    st.write(f"Ratio Post (Strong): {ratio_post_s:.1f}%")
    st.write(f"Ratio Post (Weak): {ratio_post_w:.1f}%")
