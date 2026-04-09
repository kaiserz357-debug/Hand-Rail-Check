import streamlit as st
import matplotlib.pyplot as plt
import math
# ==========================================
# 1. Setup
# ==========================================
st.set_page_config(page_title="Hand Rail Check by Ardharn ver01 2026", layout="centered")
# ==========================================
# 2. MATERIAL DATABASE (เพิ่มคอมม่าที่บรรทัด Square Tube 50x2.3)
# ==========================================
materials = {
    "Flat 50x6": {"type": "flat", "b": 0.6, "h": 5.0},
    "Flat 50x9": {"type": "flat", "b": 0.9, "h": 5.0},
    "Flat 50x12": {"type": "flat", "b": 1.2, "h": 5.0},
    "Flat 50x16": {"type": "flat", "b": 1.6, "h": 5.0},
    "Square Tube 32x2.3": {"type": "box", "D": 3.2, "t": 0.23},
    "Square Tube 38x2.3": {"type": "box", "D": 3.8, "t": 0.23},
    "Square Tube 50x2.3": {"type": "box", "D": 5.0, "t": 0.23}, # เติมคอมม่าตรงนี้
    "Square Tube 50x3.2": {"type": "box", "D": 5.0, "t": 0.32},
    "Pipe 27.2x2.3": {"type": "pipe", "OD": 2.70, "t": 0.23},
    "Pipe 34.0x2.3": {"type": "pipe", "OD": 3.40, "t": 0.23},
    "Pipe 42.7x2.3": {"type": "pipe", "OD": 4.27, "t": 0.23},
    "Pipe 42.7x3.2": {"type": "pipe", "OD": 4.27, "t": 0.32},
    "Pipe 48.6x2.3": {"type": "pipe", "OD": 4.86, "t": 0.23},
    "Pipe 48.6x3.2": {"type": "pipe", "OD": 4.86, "t": 0.32}
}
# ==========================================
# 3. SIDEBAR INPUTS (ย้ายส่วนคำนวณมาไว้หลังรับค่า Input)
# ==========================================
with st.sidebar:
    st.header("⚙️ Configuration")
    riser_h = st.number_input("Riser Height (m)", value=0.18, step=0.01)
    tread_w = st.number_input("Tread Width (m)", value=0.25, step=0.01)
    total_stairs = st.slider("Total Steps", 1, 20, 9)
    h_post_m = st.number_input("Post Height (m)", value=0.90, step=0.05)

    # ย้าย Post Spacing มาไว้ใน Sidebar หรือหลัง Tread Width
    post_pitch = {
        "@50 MM.": 0.05/tread_w,
        "@100 MM.": 0.10/tread_w,
        "Every 1 Step": 1,
        "Every 2 Steps": 2,
        "Every 3 Steps": 3,
        "Every 4 Steps": 4
    }
    post_pitch_label = st.selectbox("Post Spacing", list(post_pitch.keys()), index=2)
    post_every_n = post_pitch[post_pitch_label] # แก้ชื่อตัวแปรให้ตรงกัน

    st.subheader("Materials")
    rail_sel = st.selectbox("Select Rail", list(materials.keys()), index=11)
    post_sel = st.selectbox("Select Post", list(materials.keys()), index=9)

# --- ส่วนที่เหลือ (Calculations & Plot) ใช้ตามเดิมได้เลยครับ ---


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
df = k_post/(k_post + (k_rail*2*k_post)/ (2*k_post + k_rail))

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
st.title("Hand Rail Check by Ardharn 2026")

c1, c2, c3 = st.columns(3)
c1.metric("Max Stress", f"{max_util:.1f}%")
c2.metric("Max Deflection", f"{max(delta_s, delta_w):.2f} cm")
c3.metric("Limit (L/90)", f"{deflect_limit:.2f} cm")

if max_util > 100 or not deflect_pass:
    st.error("⚠️ Hand Rail Fail (Check Stress or Deflection)")
else:
    st.success("✅ Hand Rail Pass all Stress and Deflection")

# ==========================================
# 6. DRAWING (Integrated Version)
# ==========================================
import numpy as np

fig, ax = plt.subplots(figsize=(10, 5))

# 6.1 วาดโครงขั้นบันได
for i in range(total_stairs):
    ax.plot([i*tread_w, (i+1)*tread_w], [i*riser_h, i*riser_h], color='black', lw=1)
    ax.plot([(i+1)*tread_w, (i+1)*tread_w], [i*riser_h, (i+1)*riser_h], color='black', lw=1)

# 6.2 คำนวณตำแหน่งเสา (รองรับการปักหลายต้นใน 1 ขั้น)
post_locations = []
current_pos = 0.5  # เริ่มต้นที่กึ่งกลางลูกนอนของขั้นแรก
total_length_in_steps = float(total_stairs)

while current_pos < total_length_in_steps:
    post_locations.append(current_pos)
    current_pos += post_every_n

# บังคับให้มีเสาต้นสุดท้ายที่กึ่งกลางลูกนอนของขั้นสุดท้าย
last_step_center = total_stairs - 0.5
if len(post_locations) > 0 and post_locations[-1] < last_step_center:
    post_locations.append(last_step_center)

# ==========================================
# 6.3 วาดเสา
# ==========================================
x_tops, y_tops = [], []
for s in post_locations:
    px = s * tread_w
    py = math.floor(s) * riser_h 
    color = 'green' if (max_util < 100 and deflect_pass) else 'red'
    
    # วาดเสาตามปกติ
    ax.plot([px, px], [py, py + h_post_m], color=color, lw=4, zorder=3)
    
    x_tops.append(px)
    y_tops.append(py + h_post_m)

# ==========================================
# 6.3.1 เขียนชื่อ Post (ต้นเดียว, ตรงกลาง, เอียงขนานแนว Rail)
# ==========================================
if len(x_tops) > 0:
    # 1. หาเสาต้นกลาง
    mid_idx = len(x_tops) // 2
    px_mid = x_tops[mid_idx]
    
    # 2. หาความสูงกึ่งกลางเสา (Y-axis)
    py_mid_base = math.floor(post_locations[mid_idx]) * riser_h
    label_y = py_mid_base + (h_post_m / 2)
    
    # 3. คำนวณมุมเอียงจากราวจับ (เพื่อให้เอียงขนานกัน)
    if len(x_tops) >= 2:
        dx = x_tops[-1] - x_tops[0]
        dy = y_tops[-1] - y_tops[0]
        angle_deg = np.degrees(np.arctan2(dy, dx))
    else:
        angle_deg = 0 # กรณีมีเสาต้นเดียว ไม่ต้องเอียง
    
    # 4. วางข้อความ
    ax.text(px_mid, label_y, f"Post: {post_sel}", 
            color='black', fontsize=8, fontweight='bold',
            rotation=angle_deg,   # เอียงขนานตามแนว Rail
            ha='center', va='center',
            bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=1))
# ==========================================
# 6.4 วาดราวจับและเขียนชื่อวัสดุเหนือราว
# ==========================================
if len(x_tops) >= 2:
    ax.plot([x_tops[0], x_tops[-1]], [y_tops[0], y_tops[-1]], 
            color='royalblue', lw=5, zorder=4)
    
    # มุมเอียงราวจับ
    dx = x_tops[-1] - x_tops[0]
    dy = y_tops[-1] - y_tops[0]
    angle_deg = np.degrees(np.arctan2(dy, dx))
    
    # เขียนชื่อ Rail เหนือราว (กึ่งกลางเส้น)
    mid_x_rail = (x_tops[0] + x_tops[-1]) / 2
    mid_y_rail = (y_tops[0] + y_tops[-1]) / 2
    ax.text(mid_x_rail, mid_y_rail + 0.00, f"Rail: {rail_sel}", 
            color='royalblue', fontsize=9, fontweight='bold',
            rotation=angle_deg, ha='center', va='bottom')

ax.set_aspect('equal')
ax.set_title("Handrail Structural Analysis View")
st.pyplot(fig)


# ==========================================
# 7. DETAILED ANALYSIS
# ==========================================
with st.expander("🔍 See Detailed Stress & Deflection Analysis"):
    # 7.1 รายงานค่าความเค้น (Stress)
    st.subheader("📊 Stress Analysis")
    col_s1, col_s2, col_s3 = st.columns(3)
    col_s1.write(f"**Rail (Strong)**\n\n{ratio_rail:.1f}%")
    col_s2.write(f"**Post (Strong)**\n\n{ratio_post_s:.1f}%")
    col_s3.write(f"**Post (Weak)**\n\n{ratio_post_w:.1f}%")
    
    st.divider()

    # 7.2 รายงานค่าการโก่งตัว (Deflection)
    st.subheader("📏 Deflection Analysis (L/90)")
    st.write(f"**Limit:** {deflect_limit:.2f} cm")
    
    c_def1, c_def2 = st.columns(2)
    with c_def1:
        status_s = "✅ Pass" if delta_s <= deflect_limit else "❌ Fail"
        st.write(f"**Actual Strong Axis**")
        st.write(f"{delta_s:.2f} cm ({status_s})")
    with c_def2:
        status_w = "✅ Pass" if delta_w <= deflect_limit else "❌ Fail"
        st.write(f"**Actual Weak Axis**")
        st.write(f"{delta_w:.2f} cm ({status_w})")
    
    st.divider()

    # 7.3 พารามิเตอร์ทางวิศวกรรม (Stiffness & Factors)
    st.subheader("🧬 Engineering Parameters")
    c_p1, c_p2, c_p3 = st.columns(3)
    c_p1.write(f"**DF:** {df:.2f}")
    c_p2.write(f"**K-Post:** {k_post:.2e}") # ใช้ .2e สำหรับค่าที่อาจจะเยอะมาก
    c_p3.write(f"**K-Rail:** {k_rail:.2e}")
    
    st.info(f"📍 **Post Spacing (L):** {L_cm:.1f} cm")
