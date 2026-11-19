import os
import json
import csv
import datetime
import streamlit as st
from search_engine import HybridSearcher
from stick_parser import parse_control_string, generate_animated_svg

st.set_page_config(
    page_title="FC 27 Companion",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Auto-detect CSV filename so minor naming differences don't crash the app
CSV_PATH = (
    "EAFC_27_Complete_Controls_2.csv"
    if os.path.exists("EAFC_27_Complete_Controls_2.csv")
    else "EAFC_27_Complete_Controls.csv"
)

# Split Defending rows into Basic vs Advanced for the chart tabs
BASIC_DEFENDING_ACTIONS = {
    "Change Player",
    "Tackle / Push or Pull (when chasing)",
    "Sliding Tackle",
    "Clearance",
    "Contain (Technical and Legacy Defending)",
    "Jockey",
    "Sprint Jockey",
    "Quick Get Up (after slide tackle)",
}


@st.cache_resource
def load_engine() -> HybridSearcher:
    return HybridSearcher(CSV_PATH)


def log_feedback(query_text: str, result_id: str) -> None:
    """Anonymous local logging to grow search aliases."""
    with open("feedback.csv", "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([datetime.datetime.now().isoformat(), query_text, result_id])


def render_result_card(row, query_text: str = "") -> None:
    """Renders an interactive 3-column control card with badges and stick SVG."""
    st.markdown(f"### {row['Action_Name']}")

    badges = [
        f"<span style='background:#374151; color:#F9FAFB; padding:2px 8px; border-radius:4px; font-size:12px;'>{row['Category']}</span>"
    ]
    if row["star_int"] > 0:
        badges.append(
            f"<span style='background:#2563EB; color:white; padding:2px 8px; border-radius:4px; font-size:12px;'>★ {row['star_int']}-Star</span>"
        )

    ver_text = str(row["Verification"])
    if "Conflicting" in ver_text or "Single source" in ver_text:
        badges.append(
            "<span style='background:#D97706; color:white; padding:2px 8px; border-radius:4px; font-size:12px;'>Unverified</span>"
        )
    elif ver_text:
        badges.append(
            "<span style='background:#059669; color:white; padding:2px 8px; border-radius:4px; font-size:12px;'>Verified</span>"
        )

    st.markdown(" ".join(badges), unsafe_allow_html=True)

    parsed = parse_control_string(str(row["PlayStation"]))
    svg_html = generate_animated_svg(parsed)
    if svg_html:
        st.markdown(svg_html, unsafe_allow_html=True)

    ps_col, xb_col, pc_col = st.columns(3)
    ps_col.info(f"**PlayStation**\n\n{row['PlayStation']}")
    xb_col.success(f"**Xbox**\n\n{row['Xbox']}")
    pc_col.warning(
        f"**PC**\n\nWASD: {row['PC_WASD_Layout']}\n\nArrows: {row['PC_Arrow_Layout']}"
    )

    with st.expander("Description & Notes"):
        st.write(row["Description"])
        if str(row["Context"]).strip():
            st.caption(f"Context: {row['Context']}")
        if str(row["Notes"]).strip():
            st.caption(f"Note: {row['Notes']}")

    if st.button("Not what I meant?", key=f"flag_{row['ID']}_{query_text}"):
        log_feedback(query_text, row["ID"])
        st.toast("Logged anonymously. Thanks!")


def render_chart(df_slice) -> None:
    """Renders a clean, scannable table of controls."""
    display_cols = [
        "Action_Name",
        "Category",
        "PlayStation",
        "Xbox",
        "PC_WASD_Layout",
        "PC_Arrow_Layout",
        "Description",
    ]
    st.dataframe(
        df_slice[display_cols].rename(
            columns={
                "Action_Name": "Move / Control",
                "PC_WASD_Layout": "PC (WASD)",
                "PC_Arrow_Layout": "PC (Arrows)",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )


# --- App Initialization ---
engine = load_engine()
df = engine.df

situations = {}
if os.path.exists("situations.json"):
    with open("situations.json", "r", encoding="utf-8") as f:
        situations = json.load(f)

# --- Header & Search Controls ---
st.title("FC 27 Companion")
st.caption("Instant mid-match lookup & complete controls chart — PlayStation | Xbox | PC")

query = st.text_input(
    "Search any move, trick, or situation",
    placeholder="e.g., 'finesse shot', 'pinched pass', 'spin', 'beat a defender 1v1'",
)

col_sit, col_filter = st.columns([0.65, 0.35])
with col_sit:
    selected_sit = st.pills(
        "Situational Playbook",
        options=["None"] + list(situations.keys()),
        default="None",
    )

with col_filter:
    use_star_filter = st.toggle("Filter by Skill Star Rating", value=False)
    max_stars = (
        st.slider("Player's Skill Move Stars (max)", 1, 5, 4)
        if use_star_filter
        else None
    )

st.divider()

# --- Mode 1: Active Search Results ---
if query.strip():
    results = engine.search(query, top_k=3, max_stars=max_stars)
    if results.empty:
        st.warning("No matching controls found. Try turning off the star filter or rephrasing.")
    else:
        st.subheader(f"Top matches for '{query}'")
        for _, row in results.iterrows():
            render_result_card(row, query_text=query)
            st.divider()

# --- Mode 2: Situational Playbook Results ---
elif selected_sit and selected_sit != "None":
    st.subheader(f"{selected_sit}")
    st.caption(f"Why: {situations[selected_sit]['description']}")
    target_ids = situations[selected_sit]["actions"]
    results = df[df["ID"].isin(target_ids)]
    for _, row in results.iterrows():
        render_result_card(row, query_text=selected_sit)
        st.divider()

# --- Mode 3: Default Home View — Full Categorized Controls Chart ---
else:
    st.subheader("Complete Controls Chart")
    st.caption("Browse by category below, or use the search bar above for instant 3-column cards & stick animations.")

    tab_basic, tab_adv, tab_skills, tab_playstyles, tab_more = st.tabs(
        [
            "Basic",
            "Advanced",
            "Skill Moves",
            "PlayStyles & Flair",
            "Set Pieces, GK & Tactics",
        ]
    )

    with tab_basic:
        basic_df = df[
            df["Category"].isin(["Movement", "Attacking - Simple"])
            | (
                (df["Category"] == "Defending")
                & (df["Action_Name"].isin(BASIC_DEFENDING_ACTIONS))
            )
        ]
        st.caption(f"{len(basic_df)} controls — Movement, Basic Passing/Shooting, and Core Defending (Jockey, Tackles, Switching).")
        render_chart(basic_df)

    with tab_adv:
        adv_df = df[
            (df["Category"] == "Attacking - Advanced")
            | (
                (df["Category"] == "Defending")
                & (~df["Action_Name"].isin(BASIC_DEFENDING_ACTIONS))
            )
        ]
        st.caption(f"{len(adv_df)} controls — Finesse, Driven/Pinched Pass, Low Cross, Power Shot, Player Lock & Advanced Defending/GK Rush.")
        render_chart(adv_df)

    with tab_skills:
        star_choice = st.pills(
            "Filter by Star Rating",
            options=["All", "1-Star", "2-Star", "3-Star", "4-Star", "5-Star", "Juggling"],
            default="All",
        )
        skill_df = df[df["Category"].str.contains("Skill Move|Juggling", case=False)]
        if star_choice == "Juggling":
            skill_df = df[df["Category"] == "Juggling Trick"]
        elif star_choice and star_choice != "All":
            skill_df = skill_df[skill_df["Category"].str.startswith(star_choice)]
        st.caption(f"{len(skill_df)} skill moves")
        render_chart(skill_df)

    with tab_playstyles:
        ps_mask = df.apply(
            lambda r: any(
                kw in " ".join(r.astype(str)).lower()
                for kw in ["playstyle", "trickster", "flair", "outside the foot", "trivela"]
            ),
            axis=1,
        )
        ps_df = df[ps_mask]
        st.caption(f"{len(ps_df)} PlayStyle & Flair-triggered controls.")
        render_chart(ps_df)

    with tab_more:
        other_cats = [
            "Set Pieces",
            "Goalkeeper",
            "Tactics",
            "Be A Pro",
            "The Grounds (Open World)",
            "Match and Menu",
        ]
        selected_other = st.selectbox("Select category", ["All"] + other_cats)
        more_df = (
            df[df["Category"].isin(other_cats)]
            if selected_other == "All"
            else df[df["Category"] == selected_other]
        )
        st.caption(f"{len(more_df)} controls")
        render_chart(more_df)
