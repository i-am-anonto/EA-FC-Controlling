import streamlit as st
import json
import csv
import datetime
from search_engine import HybridSearcher
from stick_parser import parse_control_string, generate_animated_svg

st.set_page_config(page_title="FC 27 Playbook", layout="wide", initial_sidebar_state="collapsed")


@st.cache_resource
def load_engine():
    return HybridSearcher('EAFC_27_Complete_Controls.csv')

def log_feedback(query, result_id):
    """Anonymous local logging to grow aliases."""
    with open('feedback.csv', 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([datetime.datetime.now().isoformat(), query, result_id])

engine = load_engine()
with open('situations.json', 'r') as f:
    situations = json.load(f)

# Top Bar
st.title("FC 27 Companion")

# Situation Mode (Pills)
selected_sit = st.pills("Situational Playbook", options=["None"] + list(situations.keys()), default="None")

query = st.text_input("Describe the move (e.g., 'finesse shot', 'beat a defender')")
min_stars = st.slider("Filter by minimum Skill Stars", 1, 5, 1)

def render_result(row):
    st.markdown(f"### {row['Action_Name']}")
    
    # Badges
    badges = []
    if str(row['Skill_Star_Rating']).strip(): 
        badges.append(f"<span style='background:#3B82F6; color:white; padding:2px 6px; border-radius:4px; font-size:12px;'>★ {row['Skill_Star_Rating']}</span>")
    ver_color = "#10B981" if "Verified" in str(row['Verification']) else "#EF4444"
    badges.append(f"<span style='background:{ver_color}; color:white; padding:2px 6px; border-radius:4px; font-size:12px;'>{row['Verification']}</span>")
    st.markdown(" ".join(badges), unsafe_allow_html=True)
    
    # SVG Animation
    parsed = parse_control_string(str(row['PlayStation']))
    svg_html = generate_animated_svg(parsed)
    if svg_html:
        st.markdown(svg_html, unsafe_allow_html=True)

    # 3-Column Display
    ps_col, xb_col, pc_col = st.columns(3)
    ps_col.info(f"**PlayStation**\n\n{row['PlayStation']}")
    xb_col.success(f"**Xbox**\n\n{row['Xbox']}")
    pc_col.warning(f"**PC**\n\nWASD: {row['PC_WASD_Layout']}\n\nArr: {row['PC_Arrow_Layout']}")
    
    with st.expander("Context & Notes"):
        st.write(row['Description'])
        if str(row['Notes']).strip():
            st.caption(f"Note: {row['Notes']}")
    
    if st.button(f"Not what I meant? (Flag {row['ID']})", key=f"btn_{row['ID']}"):
        log_feedback(query, row['ID'])
        st.toast("Feedback logged anonymously. Thanks!")

# Execution Route
if selected_sit != "None":
    st.subheader(f"Why: {situations[selected_sit]['description']}")
    target_ids = situations[selected_sit]['actions']
    results = engine.df[engine.df['ID'].isin(target_ids)]
    for _, row in results.iterrows():
        render_result(row)
        st.divider()

elif query:
    results = engine.search(query, top_k=3, min_stars=min_stars)
    for _, row in results.iterrows():
        render_result(row)
        st.divider()
