import streamlit as st
import matplotlib.pyplot as plt
import math
import numpy as np

# ==========================================
# 1. Setup & Page Configuration
# ==========================================
st.set_page_config(page_title="Hand Rail Check by Ardharn ver01 2026", layout="centered")

# CSS สำหรับซ่อนส่วนควบคุมเมื่อกดพิมพ์รายงาน (Print Styling)
st.markdown("""
    <style>
    @media print {
        .no-print {
            display: none !important;
        }
        body {
            background-color: white;
        }
    }
    </style>
""", unsafe_allow_html=True)

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

    post_pitch = {
        "@50 MM.": 0.05/tread_w,
        "@100 MM.": 0.10/tread_w,
        "Every 1 Step": 1,
        "Every 2 Steps": 2,
        "Every 3 Steps": 3,
        "Every 4 Steps": 4
    }
    post_pitch_label = st.selectbox("Post Spacing", list(post_pitch.keys()), index=2)
    post_every_n = post_pitch[post_pitch_label]

    st.subheader("Materials")
    rail_sel = st.selectbox("Select Rail", list(materials.keys()), index=10)
    post_sel = st.selectbox("Select Post", list(materials.keys()), index=10)

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
deflect_limit = H_cm / 90  # L/90 Limit

if post_every_n < 1:
    df = 0.2
else:
    k_post = (3 * E * I_post_s) / (H_cm**3)
    k_rail = (6 * E * I_rail) / (L_cm**3)
    df = k_post / (k_post + (k_rail * 2 * k_post) / (2 * k_post + k_rail))

P_eff = 91.0 * df
delta_s = (P_eff * (H_cm**3)) / (3 * E * I_post_s)

W_line = 75.0 / 100 # kg/cm
R_top = W_line * L_cm
delta_w = (R_top * (H_cm**3)) / (3 * E * I_post_w)

ratio_rail = ((91.0 * L_cm / 4) / S_rail_s / Fb) * 100
ratio_post_s = (P_eff * H_cm / S_post_s / Fb) * 100
ratio_post_w = (R_top * H_cm / S_post_w / Fb) * 100

max_util = max(ratio_rail, ratio_post_s, ratio_post_w)
deflect_pass = (delta_s <= deflect_limit) and (delta_w <= deflect_limit)
is_overall_pass = (max_util <= 100) and deflect_pass

# ==========================================
# 5. MAIN UI
# ==========================================
st.title("Hand Rail Check by Ardharn 2026")
st.subheader("Reference Code ASCE7-05, AISC ASD")

c1, c2, c3 = st.columns(3)
c1.metric("Max Stress", f"{max_util:.1f}%")
c2.metric("Max Deflection", f"{max(delta_s, delta_w):.2f} cm")
c3.metric("Limit (L/90)", f"{deflect_limit:.2f} cm")

if not is_overall_pass:
    st.error("⚠️ Hand Rail Fail (Check Stress or Deflection)")
else:
    st.success("✅ Hand Rail Pass all Stress and Deflection")

# ==========================================
# 6. DRAWING (Integrated Version)
# ==========================================
fig, ax = plt.subplots(figsize=(10, 5))

for i in range(total_stairs):
    ax.plot([i*tread_w, (i+1)*tread_w], [i*riser_h, i*riser_h], color='black', lw=1)
    ax.plot([(i+1)*tread_w, (i+1)*tread_w], [i*riser_h, (i+1)*riser_h], color='black', lw=1)

post_locations = []
current_pos = 0.5  
total_length_in_steps = float(total_stairs)

while current_pos < total_length_in_steps:
    post_locations.append(current_pos)
    current_pos += post_every_n

last_step_center = total_stairs - 0.5
if len(post_locations) > 0 and post_locations[-1] < last_step_center:
    post_locations.append(last_step_center)

x_tops, y_tops = [], []
for s in post_locations:
    px = s * tread_w
    py = math.floor(s) * riser_h 
    color = 'green' if is_overall_pass else 'red'
    
    ax.plot([px, px], [py, py + h_post_m], color=color, lw=4, zorder=3)
    x_tops.append(px)
    y_tops.append(py + h_post_m)

if len(x_tops) > 0:
    mid_idx = len(x_tops) // 2
    px_mid = x_tops[mid_idx]
    py_mid_base = math.floor(post_locations[mid_idx]) * riser_h
    label_y = py_mid_base + (h_post_m / 2)
    
    if len(x_tops) >= 2:
        dx = x_tops[-1] - x_tops[0]
        dy = y_tops[-1] - y_tops[0]
        angle_deg = np.degrees(np.arctan2(dy, dx))
    else:
        angle_deg = 0 
    
    ax.text(px_mid, label_y, f"Post: {post_sel}", 
            color='black', fontsize=8, fontweight='bold',
            rotation=angle_deg, 
            ha='center', va='center',
            bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=1))

if len(x_tops) >= 2:
    ax.plot([x_tops[0], x_tops[-1]], [y_tops[0], y_tops[-1]], 
            color='royalblue', lw=5, zorder=4)
    
    dx = x_tops[-1] - x_tops[0]
    dy = y_tops[-1] - y_tops[0]
    angle_deg = np.degrees(np.arctan2(dy, dx))
    
    mid_x_rail = (x_tops[0] + x_tops[-1]) / 2
    mid_y_rail = (y_tops[0] + y_tops[-1]) * 0.45
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
    st.subheader("📊 Stress Analysis")
    col_s1, col_s2, col_s3 = st.columns(3)
    col_s1.write(f"**Rail (Strong)**\n\n{ratio_rail:.1f}%")
    col_s2.write(f"**Post (Strong)**\n\n{ratio_post_s:.1f}%")
    col_s3.write(f"**Post (Weak)**\n\n{ratio_post_w:.1f}%")
    
    st.divider()

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

    st.subheader("🧬 Engineering Parameters")
    c_p1, c_p2, c_p3 = st.columns(3)
    c_p1.write(f"**DF:** {df:.2f}")

    if post_every_n < 1:
        c_p2.write("**K-Post:** N/A")
        c_p3.write("**K-Rail:** N/A")
    else:
        c_p2.write(f"**K-Post:** {k_post:.2e}")
        c_p3.write(f"**K-Rail:** {k_rail:.2e}")

# ==========================================
# 8. PRINT REPORT SECTION (HTML Button)
# ==========================================
st.markdown("---")
st.markdown("### 🖨️ พิมพ์หรือบันทึกรายงานคำนวณ (Print Report)")

# สร้างปุ่มสั่งพิมพ์ด้วย HTML/JS ที่ทำงานบนเบราว์เซอร์ของผู้ใช้โดยตรง
print_html = """
<!DOCTYPE html>
<html>
<head>
<style>
.print-btn {
    background-color: #2563eb;
    color: white;
    padding: 10px 20px;
    text-align: center;
    text-decoration: none;
    display: inline-block;
    font-size: 16px;
    font-weight: 600;
    margin: 4px 2px;
    cursor: pointer;
    border-radius: 8px;
    border: none;
    width: 100%;
    font-family: 'Source Sans Pro', sans-serif;
}
.print-btn:hover {
    background-color: #1d4ed8;
}
</style>
</head>
<body>
<button class="print-btn" onclick="window.print()">📄 คลิกเพื่อพิมพ์รายงาน / Save as PDF</button>
</body>
</html>
"""

# แสดงปุ่มผ่าน streamlit components
import streamlit.components.v1 as components
components.html(print_html, height=60)
