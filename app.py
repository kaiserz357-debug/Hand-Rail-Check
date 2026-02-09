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
    "Square Tube 1.5\" (2.3mm)": {"type": "box", "D": 3.8, "t": 0.23},
    "Square Tube 2\" (3.2mm)": {"type": "box", "D": 5.0, "t": 0.32},
    "Pipe 1.5\" (3.2mm)": {"type": "pipe", "OD": 4.27, "t": 0.32}
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
    
    # --- ปรับปรุงจุดนี้: เพิ่มตัวเลือกเสาถี่ต่อลูกนอน ---
    spacing_options = {
        "5 posts per Tread": 1/5,
        "4 posts per Tread": 1/4,
        "3 posts per Tread": 1/3,
        "2 posts per Tread": 1/2,
        "1 post per Tread": 1,
        "1 post every 2 Treads": 2,
        "1 post every 3 Treads": 3,
        "1 post every 4 Treads": 4
    }
    spacing_sel = st.selectbox("Post Spacing", list(spacing_options.keys()), index=4)
    n_factor = spacing_options[spacing_sel]

    st.subheader("Materials")
    rail_sel = st.selectbox("Select Rail", list(materials.keys()), index=0)
    post_sel = st.selectbox("Select Post", list(materials.keys()), index=2)

# ==========================================
# 4. CALCULATIONS (Stress & Deflection)
# ==========================================
def get_props(name):
    m = materials[name]
    if m["type"] == "flat":
        return (m["b"]*m["h"]**2/6), (m["h"]*m["b"]**2/6), (m["b"]*m["h"]**3/12), (m["h"]*m["b"]**3/12)
    elif m["type"] == "box":
        i = (m["D"]**4 - (m["D"]-2*m["t"])**4)/12
        return i/(m["D"]/2), i/(m["D"]/2), i, i
    elif m["type"] == "pipe":
        i = (math.pi*(m["OD"]**4 - (m["OD"]-2*m["t"])**4))/64
        return i/(m["OD"]/2), i/(m["OD"]/2), i, i

S_rail_s, _, I_rail, _ = get_props(rail_sel)
S_post_s, S_post_w, I_post_s, I_post_w = get_props(post_sel)

# ระยะห่างระหว่างเสา (L) คำนวณจาก n_factor
L_cm = (tread_w * n_factor) * 100
H_cm = h_post_m * 100
E = 2.04e6
Fb = 2450.0 * 0.66
deflect_limit = H_cm / 90  # ปรับเป็น L/90 ตามที่คุยกัน

# Stiffness & Load Sharing (คิดแบบ Safe: End Post เสมอ)
k_post = (3 * E * I_post_s) / (H_cm**3)
k_rail = (48 * E * I_rail) / (L_cm**3)
df = max(min(k_post / (k_post + (1 * k_rail)), 1.0), 0.6)

# Stress & Deflection
P_eff = 91.0 * df
R_top = (75.0 / 100) * L_cm
ratio_rail = ((91.0 * L_cm / 4) / S_rail_s / Fb) * 100
ratio_post_s = (P_eff * H_cm / S_post_s / Fb) * 100
ratio_post_w = (R_top * H_cm / S_post_w / Fb) * 100

delta_s = (P_eff * (H_cm**3)) / (3 * E * I_post_s)
delta_w = (R_top * (H_cm**3)) / (3 * E * I_post_w)

max_util = max(ratio_rail, ratio_post_s, ratio_post_w)
deflect_pass = (max(delta_s, delta_w) <= deflect_limit)

# ==========================================
# 5. UI & PLOTTING
# ==========================================
st.title("Stair Structural Pro")

c1, c2, c3 = st.columns(3)
c1.metric("Max Stress", f"{max_util:.1f}%")
c2.metric("Max Deflect", f"{max(delta_s, delta_w):.2f} cm")
c3.metric("Limit (L/90)", f"{deflect_limit:.2f} cm")

# Drawing
fig, ax = plt.subplots(figsize=(10, 5))
for i in range(total_stairs):
    ax.plot([i*tread_w, (i+1)*tread_w], [i*riser_h, i*riser_h], color='black', lw=1)
    ax.plot([(i+1)*tread_w, (i+1)*tread_w], [i*riser_h, (i+1)*riser_h], color='black', lw=1)

# ปรับการวาดเสาให้ตรงตามจำนวนที่เลือก
x_tops, y_tops = [], []
total_length = total_stairs * tread_w
# วาดเสาตั้งแต่จุดเริ่มต้นจนสุดความยาวบันได ตามระยะ L_cm
current_x = 0
while current_x <= total_length + 0.01:
    # หาค่า y (ระดับความสูงบันได) ณ จุดที่เสาตั้งอยู่
    step_idx = math.floor(current_x / tread_w)
    step_idx = min(step_idx, total_stairs - 1)
    py = step_idx * riser_h
    
    color = 'green' if (max_util < 100 and deflect_pass) else 'red'
    ax.plot([current_x, current_x], [py, py + h_post_m], color=color, lw=3, zorder=3)
    x_tops.append(current_x); y_tops.append(py + h_post_m)
    current_x += (L_cm / 100)

ax.plot(x_tops, y_tops, color='royalblue', lw=4, marker='o', zorder=4)
ax.set_aspect('equal')
st.pyplot(fig)

with st.expander("🔍 See Detailed Analysis"):
    st.write(f"**Spacing Mode:** {spacing_sel}")
    st.write(f"**Actual Spacing (L):** {L_cm:.1f} cm")
    st.write(f"**Load Share (DF):** {df:.2f}")
    st.divider()
    st.write(f"Stress Rail: {ratio_rail:.1f}%")
    st.write(f"Stress Post: {max(ratio_post_s, ratio_post_w):.1f}%")
    st.write(f"Deflection Actual: {max(delta_s, delta_w):.2f} cm")
