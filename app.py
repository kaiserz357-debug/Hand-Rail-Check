import math
import streamlit as st
import plotly.graph_objects as go

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Hand Rail Check by Ardharn ver01 2026",
    page_icon="🏗️",
    layout="wide"
)

# --- DICTIONARY FOR I18N ---
I18N = {
    'th': {
        'title': "Hand Rail Check by Ardharn",
        'subtitle': "อ้างอิงมาตรฐาน: ASCE 7-05 & AISC ASD (Structural Steel Design)",
        'sec1_title': "1. ขนาดบันได (Stair Geometry)",
        'riser_h': "ลูกตั้ง Riser (m)",
        'tread_w': "ลูกนอน Tread (m)",
        'total_stairs': "จำนวนขั้น (Steps)",
        'h_post_m': "ความสูงเสา Post (m)",
        'sec2_title': "2. ระยะห่างเสา (Post Spacing)",
        'post_spacing_lbl': "การจัดวางเสาราวจับ",
        'opt_50mm': "ระยะคงที่ @ 50 MM.",
        'opt_100mm': "ระยะคงที่ @ 100 MM.",
        'opt_every1': "ทุกๆ 1 ขั้นบันได (Every 1 Step)",
        'opt_every2': "ทุกๆ 2 ขั้นบันได (Every 2 Steps)",
        'opt_every3': "ทุกๆ 3 ขั้นบันได (Every 3 Steps)",
        'opt_every4': "ทุกๆ 4 ขั้นบันได (Every 4 Steps)",
        'sec3_title': "3. หน้าตัดวัสดุ (Material Sections)",
        'rail_sel': "ราวมือจับ Top Rail",
        'post_sel': "เสาราวจับ Vertical Post",
        'sec4_title': "4. น้ำหนักบรรทุกออกแบบ (ASCE 7-05 Loads)",
        'load_conc': "Concentrated Load: 91 kg (200 lbs)",
        'load_line': "Uniform Line Load: 75 kg/m (50 lb/ft)",
        'pass_msg': "PASS: ราวจับผ่านเกณฑ์การทดสอบทั้งความแข็งแรง (Stress) และการแอ่นตัว (Deflection)",
        'fail_msg': "FAIL: ราวจับไม่ผ่านเกณฑ์ทดสอบ",
        'card_stress': "MAX STRESS UTILIZATION",
        'card_deflect': "MAX DEFLECTION",
        'card_limit': "DEFLECTION LIMIT",
        'sub_stress': "Allowable Stress ratio (Max 100%)",
        'sub_deflect': "Actual max lateral displacement",
        'sub_limit': "Allowable limit (Post Height / 90)",
        'chart_title': "ภาพจำลองรูปด้านโครงสร้าง (Side Elevation Preview)",
        'detail_title': "รายละเอียดการวิเคราะห์โครงสร้าง (Detailed Structural Analysis)",
        'fn_heading': "เกณฑ์อ้างอิงและพารามิเตอร์ที่ใช้คำนวณ:",
        'fn_modulus': "• E = 2,040,000 kg/cm² (Modulus of Elasticity ของเหล็กรูปพรรณ)",
        'fn_stress': "• Fb = 0.66 × Fy = 1,617 kg/cm² (หน่วยแรงดัดที่ยอมให้ AISC ASD, Fy=2450 kg/cm²)",
        'fn_stiff': "• ค่ากระจายแรงลงเสา (df) คำนวณตามอัตราส่วนความแข็งแรงสมบูรณ์ (Frame Stiffness Matrix Ratio)",
    },
    'en': {
        'title': "Hand Rail Check by Ardharn",
        'subtitle': "Reference Standard: ASCE 7-05 & AISC ASD (Structural Steel Design)",
        'sec1_title': "1. Stair Geometry",
        'riser_h': "Riser Height (m)",
        'tread_w': "Tread Width (m)",
        'total_stairs': "Total Steps",
        'h_post_m': "Post Height (m)",
        'sec2_title': "2. Post Spacing",
        'post_spacing_lbl': "Post Arrangement",
        'opt_50mm': "Fixed Spacing @ 50 MM.",
        'opt_100mm': "Fixed Spacing @ 100 MM.",
        'opt_every1': "Every 1 Step",
        'opt_every2': "Every 2 Steps",
        'opt_every3': "Every 3 Steps",
        'opt_every4': "Every 4 Steps",
        'sec3_title': "3. Material Sections",
        'rail_sel': "Top Rail Profile",
        'post_sel': "Vertical Post Profile",
        'sec4_title': "4. Design Loads (ASCE 7-05)",
        'load_conc': "Concentrated Load: 91 kg (200 lbs)",
        'load_line': "Uniform Line Load: 75 kg/m (50 lb/ft)",
        'pass_msg': "PASS: Handrail structural members pass both Stress and Deflection limits",
        'fail_msg': "FAIL: Handrail structure failed structural check",
        'card_stress': "MAX STRESS UTILIZATION",
        'card_deflect': "MAX DEFLECTION",
        'card_limit': "DEFLECTION LIMIT",
        'sub_stress': "Allowable Stress ratio (Max 100%)",
        'sub_deflect': "Actual max lateral displacement",
        'sub_limit': "Allowable limit (Post Height / 90)",
        'chart_title': "Side Elevation Preview",
        'detail_title': "Detailed Structural Analysis",
        'fn_heading': "Design Standards & Reference Parameters:",
        'fn_modulus': "• E = 2,040,000 kg/cm² (Modulus of Elasticity of Structural Steel)",
        'fn_stress': "• Fb = 0.66 × Fy = 1,617 kg/cm² (Allowable Bending Stress AISC ASD, Fy=2450 kg/cm²)",
        'fn_stiff': "• Load Distribution Factor (df) calculated using Frame Stiffness Matrix Ratio",
    }
}

# --- MATERIAL DATABASE & PROPERTIES ---
MATERIALS = {
    "Flat 50x6": {"type": "flat", "b": 0.6, "h": 5.0},
    "Flat 50x9": {"type": "flat", "b": 0.9, "h": 5.0},
    "Flat 50x12": {"type": "flat", "b": 1.2, "h": 5.0},
    "Flat 50x16": {"type": "flat", "b": 1.6, "h": 5.0},
    "Square Tube 32x2.3": {"type": "box", "D": 3.2, "t": 0.23},
    "Square Tube 38x2.3": {"type": "box", "D": 3.8, "t": 0.23},
    "Square Tube 50x2.3": {"type": "box", "D": 5.0, "t": 0.23},
    "Square Tube 50x3.2": {"type": "box", "D": 5.0, "t": 0.32},
    "Pipe 27.2x2.3": {"type": "pipe", "OD": 2.72, "t": 0.23},
    "Pipe 34.0x2.3": {"type": "pipe", "OD": 3.40, "t": 0.23},
    "Pipe 42.7x2.3": {"type": "pipe", "OD": 4.27, "t": 0.23},
    "Pipe 42.7x3.2": {"type": "pipe", "OD": 4.27, "t": 0.32},
    "Pipe 48.6x2.3": {"type": "pipe", "OD": 4.86, "t": 0.23},
    "Pipe 48.6x3.2": {"type": "pipe", "OD": 4.86, "t": 0.32}
}

def get_props(name):
    m = MATERIALS.get(name)
    if not m:
        return {"s_s": 1, "s_w": 1, "i_s": 1, "i_w": 1}
    
    m_type = m["type"]
    if m_type == "flat":
        s_s = (m["b"] * (m["h"] ** 2)) / 6
        s_w = (m["h"] * (m["b"] ** 2)) / 6
        i_s = (m["b"] * (m["h"] ** 3)) / 12
        i_w = (m["h"] * (m["b"] ** 3)) / 12
        return {"s_s": s_s, "s_w": s_w, "i_s": i_s, "i_w": i_w}
    elif m_type == "box":
        inner_d = max(0.0, m["D"] - 2 * m["t"])
        i = (math.pow(m["D"], 4) - math.pow(inner_d, 4)) / 12
        s = i / (m["D"] / 2)
        return {"s_s": s, "s_w": s, "i_s": i, "i_w": i}
    elif m_type == "pipe":
        inner_d = max(0.0, m["OD"] - 2 * m["t"])
        i = (math.pi * (math.pow(m["OD"], 4) - math.pow(inner_d, 4))) / 64
        s = i / (m["OD"] / 2)
        return {"s_s": s, "s_w": s, "i_s": i, "i_w": i}

# --- SIDEBAR & INPUTS ---
st.sidebar.title("⚙️ Configs")
lang = st.sidebar.radio("🌐 Language / ภาษา", ["TH", "EN"], index=0)
lang_key = lang.lower()
txt = I18N[lang_key]

st.sidebar.markdown(f"### {txt['sec1_title']}")
riser_h = st.sidebar.number_input(txt['riser_h'], value=0.18, step=0.01, min_value=0.05, max_value=0.5)
tread_w = st.sidebar.number_input(txt['tread_w'], value=0.25, step=0.01, min_value=0.1, max_value=1.0)
total_stairs = st.sidebar.number_input(txt['total_stairs'], value=9, step=1, min_value=1, max_value=30)
h_post_m = st.sidebar.number_input(txt['h_post_m'], value=0.90, step=0.05, min_value=0.5, max_value=1.5)

st.sidebar.markdown(f"### {txt['sec2_title']}")
spacing_options = {
    txt['opt_every1']: 1.0,
    txt['opt_every2']: 2.0,
    txt['opt_every3']: 3.0,
    txt['opt_every4']: 4.0,
    txt['opt_50mm']: 0.05,
    txt['opt_100mm']: 0.10,
}
selected_spacing_label = st.sidebar.selectbox(txt['post_spacing_lbl'], list(spacing_options.keys()), index=0)
raw_spacing = spacing_options[selected_spacing_label]

if raw_spacing < 1.0:
    post_every_n = raw_spacing / tread_w
else:
    post_every_n = raw_spacing

st.sidebar.markdown(f"### {txt['sec3_title']}")
material_names = list(MATERIALS.keys())
rail_name = st.sidebar.selectbox(txt['rail_sel'], material_names, index=material_names.index("Pipe 42.7x2.3"))
post_name = st.sidebar.selectbox(txt['post_sel'], material_names, index=material_names.index("Pipe 42.7x3.2"))

st.sidebar.markdown(f"### {txt['sec4_title']}")
st.sidebar.caption(txt['load_conc'])
st.sidebar.caption(txt['load_line'])

# --- CALCULATIONS ---
rail_props = get_props(rail_name)
post_props = get_props(post_name)

L_cm = (tread_w * post_every_n) * 100
H_cm = h_post_m * 100

E = 2.04e6  # kg/cm^2
Fb = 2450.0 * 0.66  # 1617 kg/cm^2
deflect_limit = H_cm / 90.0

df = 0.5
if post_every_n > 0:
    k_post = (3 * E * post_props['i_s']) / (H_cm ** 3)
    k_rail = (6 * E * rail_props['i_s']) / (L_cm ** 3)
    denom = (2 * k_post + k_rail)
    df = k_post / (k_post + (k_rail * 2 * k_post) / denom) if denom != 0 else 1.0
    if math.isnan(df) or df > 1.0:
        df = 1.0
    if df < 0.2:
        df = 0.2

P_eff = 91.0 * df
delta_s = (P_eff * (H_cm ** 3)) / (3 * E * post_props['i_s'])

W_line = 75.0 / 100.0
R_top = W_line * L_cm
delta_w = (R_top * (H_cm ** 3)) / (3 * E * post_props['i_w'])

M_rail = (91.0 * L_cm) / 4.0
ratio_rail = (M_rail / rail_props['s_s'] / Fb) * 100.0

M_post_s = P_eff * H_cm
ratio_post_s = (M_post_s / post_props['s_s'] / Fb) * 100.0

M_post_w = R_top * H_cm
ratio_post_w = (M_post_w / post_props['s_w'] / Fb) * 100.0

max_util = max(ratio_rail, ratio_post_s, ratio_post_w)
max_deflect = max(delta_s, delta_w)

deflect_pass = (delta_s <= deflect_limit) and (delta_w <= deflect_limit)
stress_pass = max_util <= 100.0
is_overall_pass = stress_pass and deflect_pass

# --- HEADER & DISPLAY ---
st.title(txt['title'])
st.caption(txt['subtitle'])

# Status Banner
if is_overall_pass:
    st.success(f"✅ {txt['pass_msg']}")
else:
    reasons = []
    if not stress_pass:
        reasons.append("Overstress > 100%")
    if not deflect_pass:
        reasons.append("Excessive Deflection > Limit")
    st.error(f"❌ {txt['fail_msg']} ({', '.join(reasons)})")

# Metrics Summary Cards
col1, col2, col3 = st.columns(3)
col1.metric(
    label=txt['card_stress'],
    value=f"{max_util:.1f}%",
    delta="PASS" if stress_pass else "FAIL",
    delta_color="normal" if stress_pass else "inverse",
    help=txt['sub_stress']
)
col2.metric(
    label=txt['card_deflect'],
    value=f"{max_deflect:.2f} cm",
    delta="PASS" if deflect_pass else "FAIL",
    delta_color="normal" if deflect_pass else "inverse",
    help=txt['sub_deflect']
)
col3.metric(
    label=txt['card_limit'],
    value=f"{deflect_limit:.2f} cm",
    help=txt['sub_limit']
)

# --- PLOTLY ELEVATION CHART ---
st.markdown(f"### {txt['chart_title']}")

fig = go.Figure()

# 1. Stairs Line
stair_x = []
stair_y = []
for i in range(total_stairs + 1):
    stair_x.append(i * tread_w)
    stair_y.append(i * riser_h)

fig.add_trace(go.Scatter(
    x=stair_x, y=stair_y,
    mode='lines',
    line=dict(color='#334155', width=3, shape='vh'),
    name='Stair Profile'
))

# 2. Calculate Posts Locations
post_locations = []
if post_every_n < 1:
    current_x = 0.1
    total_length = total_stairs * tread_w
    step_x = post_every_n * tread_w
    while current_x <= total_length:
        post_locations.append(current_x / tread_w)
        current_x += step_x
else:
    current_pos = 0.5
    while current_pos < total_stairs:
        post_locations.append(current_pos)
        current_pos += post_every_n

last_step_pos = total_stairs - 0.5
if len(post_locations) == 0 or post_locations[-1] < last_step_pos:
    post_locations.append(last_step_pos)

post_color = '#10b981' if is_overall_pass else '#f43f5e'

# Draw Vertical Posts
for idx, s in enumerate(post_locations):
    px = s * tread_w
    py = math.floor(s) * riser_h
    fig.add_trace(go.Scatter(
        x=[px, px],
        y=[py, py + h_post_m],
        mode='lines',
        line=dict(color=post_color, width=4),
        showlegend=(idx == 0),
        name='Posts'
    ))

# 3. Top Rail Line
first_x = post_locations[0] * tread_w
first_y = math.floor(post_locations[0]) * riser_h + h_post_m
last_x = post_locations[-1] * tread_w
last_y = math.floor(post_locations[-1]) * riser_h + h_post_m

fig.add_trace(go.Scatter(
    x=[first_x, last_x],
    y=[first_y, last_y],
    mode='lines',
    line=dict(color='#2563eb', width=6),
    name='Top Rail'
))

fig.update_layout(
    xaxis_title="Horizontal Span (m)",
    yaxis_title="Height (m)",
    height=380,
    margin=dict(l=20, r=20, t=30, b=20),
    showlegend=False
)

st.plotly_chart(fig, use_container_width=True)

# --- ANALYSIS DETAILS TABLE ---
st.markdown(f"### {txt['detail_title']}")

analysis_data = [
    {
        "Member": "Top Rail",
        "Axis": "Strong Axis Bending",
        "Ratio (%)": f"{ratio_rail:.1f}%",
        "Status": "PASS" if ratio_rail <= 100 else "FAIL"
    },
    {
        "Member": "Vertical Post",
        "Axis": "Strong Axis Bending",
        "Ratio (%)": f"{ratio_post_s:.1f}%",
        "Status": "PASS" if ratio_post_s <= 100 else "FAIL"
    },
    {
        "Member": "Vertical Post",
        "Axis": "Weak Axis Bending",
        "Ratio (%)": f"{ratio_post_w:.1f}%",
        "Status": "PASS" if ratio_post_w <= 100 else "FAIL"
    },
]

st.table(analysis_data)

col_d1, col_d2 = st.columns(2)
col_d1.info(f"**Strong Axis Deflection (δs):** {delta_s:.2f} cm ({'PASS' if delta_s <= deflect_limit else 'FAIL'})")
col_d2.info(f"**Weak Axis Deflection (δw):** {delta_w:.2f} cm ({'PASS' if delta_w <= deflect_limit else 'FAIL'})")

# Footnote
st.caption(f"**{txt['fn_heading']}**")
st.caption(txt['fn_modulus'])
st.caption(txt['fn_stress'])
st.caption(txt['fn_stiff'])
