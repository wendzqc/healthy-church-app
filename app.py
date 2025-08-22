
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 30 16:56:21 2025

@author: wqcampano
"""
# -*- coding: utf-8 -*-
#"""
#H.E.A.L.T.H.Y. Church Checklist
#- Excel upload path (Q1..Q7), OR
#- Live survey path gated by Church Code (writes to Google Sheets)
#"""

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import re
import pandas as pd

import gspread
#from google.oauth2.service_account import Credentials
from datetime import datetime
from zoneinfo import ZoneInfo

from google.oauth2.service_account import Credentials

# =========================
# GOOGLE SHEETS SETUP
# =========================
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Load service account from Streamlit secrets
creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
client = gspread.authorize(creds)

# Open the sheet from secrets
sheet = client.open_by_url(st.secrets["app"]["sheet_url"]).sheet1

# =========================
# VISUALS
# =========================
colors = [
    "#ff0000", "#ff4500", "#ff8c00", "#ffaa00", "#ffff00", "#ffff00", "#ffff00",
    "#aaff00", "#55ff00", "#00ff00", "#008800"
]
cmap = LinearSegmentedColormap.from_list("health_scale", colors, N=256)

def draw_custom_radar(scores, categories):
    scores = list(scores)  # copy so we can append
    avg_score = float(np.mean(scores))
    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    angles += angles[:1]
    scores += scores[:1]

    fig = plt.figure(figsize=(10, 11))
    gs = fig.add_gridspec(2, 1, height_ratios=[0.9, 0.1])

    ax_radar = fig.add_subplot(gs[0], polar=True)
    ax_radar.set_theta_offset(np.pi / 2)
    ax_radar.set_theta_direction(-1)
    ax_radar.set_rlabel_position(0)
    plt.xticks(angles[:-1], categories, fontsize=11)
    plt.yticks([1, 3, 5, 7, 9], ["1", "3", "5", "7", "9"], color="grey", size=9)
    plt.ylim(0, 10)

    ax_radar.plot(angles, scores, 'o-', linewidth=2, color='#333333', alpha=0.7)
    ax_radar.fill(angles, scores, color=cmap((avg_score - 1)/9.0), alpha=0.25)

    for angle, score in zip(angles[:-1], scores[:-1]):
        ax_radar.plot(angle, score, 'o', markersize=8, color=cmap((score - 1)/9.0))
        ax_radar.annotate(
            f"{score:.1f}",
            xy=(angle, score + 0.3),
            textcoords="offset points", xytext=(0, 5),
            ha='center', fontsize=9, fontweight='bold',
            bbox=dict(boxstyle="round,pad=0.2", fc=cmap((score - 1)/9.0), ec="black", alpha=0.7)
        )

    ax_radar.annotate(
        f"Overall: {avg_score:.1f}/10",
        xy=(0.5, 0.5), xycoords='axes fraction', ha='center',
        fontsize=12, fontweight='bold',
        bbox=dict(boxstyle="round,pad=0.3", fc=cmap((avg_score - 1)/9.0), ec="black", alpha=0.8)
    )

    ax_radar.plot(angles, [5.5]*len(angles), '--', color='#ffaa00', alpha=0.7)
    ax_radar.plot(angles, [8.5]*len(angles), '--', color='#00aa00', alpha=0.7)
    ax_radar.set_title("Church Health Assessment", fontsize=15, pad=20, fontweight='bold')

    ax_cont = fig.add_subplot(gs[1])
    gradient = np.linspace(1, 10, 256).reshape(1, 256)
    ax_cont.imshow(gradient, aspect='auto', cmap=cmap, extent=[1, 10, 0, 1])
    ax_cont.set_xlim(1, 10)
    ax_cont.set_xticks([1, 5.5, 8.5, 10])
    ax_cont.set_xticklabels(["1", "5.5", "8.5", "10"], fontsize=9)
    ax_cont.set_yticks([])
    ax_cont.axvline(x=5.5, color='white', linestyle='-', linewidth=1.5, alpha=0.9)
    ax_cont.axvline(x=8.5, color='white', linestyle='-', linewidth=1.5, alpha=0.9)
    ax_cont.set_title("Health Continuum Reference", fontsize=10, pad=8)

    st.pyplot(fig)

def classify(average):
    if average >= 8.5:
        return ("Thriving Health",
                "Consistently reflects New Testament church characteristics")
    elif average >= 7.5:
        return ("Stable Health",
                "Healthy foundation with clear growth opportunities")
    elif average >= 6.5:
        return ("Moderate Concerns",
                "Several vulnerabilities requiring focused discipleship")
    elif average >= 5.5:
        return ("Significant Issues",
                "Multiple areas need urgent attention; sustainability concerns")
    else:
        return ("Critical Condition",
                "Comprehensive renewal needed; reflects fundamental spiritual health problems")

# =========================
# APP
# =========================
st.set_page_config(page_title="H.E.A.L.T.H.Y. Church Checklist", layout="centered")
st.title("🧭 H.E.A.L.T.H.Y. Church Checklist")
st.markdown("<div style='font-size:13px; color:gray;'>by Jason Richard Tan</div>", unsafe_allow_html=True)

st.markdown(
    """
For each area of church health, you’ll see **three descriptions**:

- One that reflects an **unhealthy pattern**  
- One that shows a **growing** or **developing** state  
- One that represents a **healthy, ideal** state

Please reflect on your church honestly, then rate your church from **1 to 10**:

- **1–3** → Closely resembles the unhealthy description  
- **4–7** → Somewhere in between; growing in this area  
- **8–10** → Strongly reflects the healthy description
"""
)

# If you bundle the PNG, keep the filename the same or update here.
st.image("health_continuum_dark_green.png", use_container_width=True)

# The 7 questions
questions = [
    {
        "label": "HUMILITY (Matt 5, meek; 1 Cor 13, not boastful, not proud, not self-seeking)",
        "anchors": [
            "There is a spirit of competition, boasting, and arrogance, especially in board meetings, planning, and events. No one offers an apology after a heated argument.",
            "There was a time when the leaders sought forgiveness as a community before God and with each other, but it was a long time ago. ",
            "People regard each other better than themselves (Phil. 2:3). There is genuine respect for each other’s place in the community."
        ]
    },
    {
        "label": "ENDURANCE in the Faith. (Gal. 5, patience, faithfulness; Matt 5, faithful in poverty, endures persecution; 1 Cor 13, always perseveres)",
        "anchors": [
            "People are ready to leave the church if they have an option, or they are willing to stay in the church as long as no one changes the status quo.",
            "People are willing to do ministry beyond Sunday worship for as long as it is convenient. ",
            "The community genuinely exemplifies faithfulness, sacrifice, and endurance in the faith despite persecution, poverty, or difficulty."
        ]
    },
    {
        "label": "AUTHENTICITY (1 Cor 13, kind, not envious, not boastful, not proud, not rude, not self-seeking; Gal. 5, joy gentleness, self-control; Matt 5, merciful)",
        "anchors": [
            "People come to church only to fulfill a religious expectation or because they are used to it. When the service ends, the worship hall is empty within a few minutes.",
            "A few people linger to have fellowship after the service for extended fellowship or prayer.",
            "People are genuinely kind, hospitable, gentle, and merciful. They share resources with each other and would go the extra mile to help someone in need. They even visit the sick and pray for those in need."
        ]
    },
    {
        "label": "LOVE (1 Cor. 13, …but have not love, I am nothing. Gal. 5, love)",
        "anchors": [
            "There is hostility, selfish ambition, factions, and discord within the community. There is hatred between leaders and members.",
            "Members are generally amicable to each other but lack the depth of friendship. If given a chance, they are willing to come together to build meaningful relationships.",
            "You sense that members, in general, truly love each other. They often linger for fellowship and prayer and even share meals after the service. There is much laughter, joy, and peace in the community, and they are excited to see each other in church."
        ]
    },
    {
        "label": "TRUSTWORTHINESS (Matt.5, pure in heart; 1 Cor.13, always trusts, always hopes)",
        "anchors": [
            "There is a general mistrust and suspicion between the members and leaders. There is open hostility and contempt against leaders and members.",
            "A few people sow discord, but a majority still affirm the pastor's leadership. The general mood of the congregation is to give the pastor the benefit of the doubt.",
            "The congregation fully trusts the church's leadership. The leaders seek to emulate a life consistent with God’s Word, living, leading, serving, and loving biblically as Christ intended them to do."
        ]
    },
    {
        "label": "HARMONY (Gal. 5, peace; Matt. 5, peacemaker; 1 Cor. 13, it keeps no record of wrongs)",
        "anchors": [
            "There is a spirit of discord, selfish ambition, jealousy, fighting, gossip, slander, and offensive language. People have left the church, but no one seems to care to reach out to them.",
            "Offenses have been made in the past, and there are no efforts to address them. However, the community is more sensitive about not repeating the same mistake they did.",
            "There is forgiveness, general peace, and harmony within the community. Although there are arguments and misunderstandings, they do not let these get in the way of their relationship. Leaders and members are quick to apologize and acknowledge their faults when necessary."
        ]
    },
    {
        "label": "YEARNING for truth (1 Cor. 13, love does not delight in evil, but rejoices with the truth, …but have not love, I am nothing)",
        "anchors": [
            "People do not care what is preached or taught in church. The majority of attendees do not practice personal time in reading, praying, or studying God’s word.",
            "People are into discipleship groups or care groups, but they are not willing to do anything new or beyond the four corners of the church.",
            "People are eager to learn from the Scriptures and to grow in the faith. They read and study on their own. There is excitement around the study of God’s word, disciple-making, serving the community, and living our lives as believers in their community."
        ]
    }
]

main_virtues = [re.match(r"[A-Z\s]+", q["label"]).group(0).strip() for q in questions]


# =========================
# LIVE SURVEY PATH (Church Code → Optional Control ID → Survey → Results)
# =========================

st.subheader("📋 Questionnaire")

# -------------------------
# Initialize session state
# -------------------------
if "stage" not in st.session_state:
    st.session_state.stage = "await_code"
if "church_code" not in st.session_state:
    st.session_state.church_code = ""
if "control_id" not in st.session_state:
    st.session_state.control_id = ""

def reset_session():
    """Reset session state to initial state."""
    st.session_state.stage = "await_code"
    st.session_state.church_code = ""
    st.session_state.control_id = ""

# -------------------------
# Stage: Await Church Code
# -------------------------
if st.session_state.stage == "await_code":
    code = st.text_input(
        "Enter your Church Code (existing or new; responses and results will be linked to this code).",
        value=st.session_state.church_code
    )
    st.caption("⚠️ Note: Codes are case-sensitive (e.g., ABC is not the same as Abc).")
    col1, col2 = st.columns([1, 1])
    with col1:
        survey_btn = st.button("➡️ Take the Survey")
    with col2:
        view_results_btn = st.button("📊 View Results Only")

    if survey_btn:
        if not code.strip():
            st.warning("⚠️ Please enter a Church Code before continuing.")
        else:
            st.session_state.church_code = code.strip()
            st.session_state.stage = "control_input"   # normal survey path
            st.rerun()

    if view_results_btn:
        if not code.strip():
            st.warning("⚠️ Please enter a Church Code before viewing results.")
        else:
            st.session_state.church_code = code.strip()
            st.session_state.stage = "results"   # jump directly to results stage
            st.rerun()

# -------------------------
# Stage: Optional Control ID
# -------------------------
elif st.session_state.stage == "control_input":
    st.info("Optional: Enter a Control ID provided by your church (leave blank for casual or personal survey).")
 
    with st.form("control_form"):
        control_id_input = st.text_input("Control ID", value=st.session_state.control_id)
        st.caption("⚠️ Note: Control IDs are case-sensitive (e.g., A123 is not the same as a123).")
        submit_control = st.form_submit_button("➡️ Submit and Continue")
        cancel_control = st.form_submit_button("❌ Cancel")

        if submit_control:
            church_code = st.session_state.church_code
            control_id_input = control_id_input.strip()

            if not control_id_input:
                # No Control ID → go to survey
                st.session_state.control_id = ""
                st.session_state.stage = "survey"
                st.rerun()

            try:
                data = sheet.get_all_records()
                df = pd.DataFrame(data)
                df["Control_ID"] = df["Control_ID"].astype(str).str.strip()
                df["Code"] = df["Code"].astype(str).str.strip()

                duplicate = df[(df["Code"] == church_code) & (df["Control_ID"] == control_id_input)]
            except Exception as e:
                st.error(f"Could not fetch existing responses: {e}")
                st.stop()

            if not duplicate.empty:
                st.warning(f"⚠️ Control ID '{control_id_input}' has already been used for Church Code '{church_code}'. You cannot proceed.")
            else:
                st.session_state.control_id = control_id_input
                st.session_state.stage = "survey"
                st.rerun()

        if cancel_control:
            reset_session()
            st.rerun()

# -------------------------
# Stage: Survey Form
# -------------------------
elif st.session_state.stage == "survey":
    church_code = st.session_state.church_code
    control_id = st.session_state.control_id

    with st.form("survey_form"):
        scores = []
        for q in questions:
            st.subheader(q["label"])
            st.markdown(f"**Unhealthy (1–3):** {q['anchors'][0]}")
            st.markdown(f"**Moderate (4–7):** {q['anchors'][1]}")
            st.markdown(f"**Healthy (8–10):** {q['anchors'][2]}")
            score = st.slider("Score (1–10)", 1, 10, 5, key=q["label"])
            scores.append(score)
            st.markdown("---")

        col1, col2 = st.columns([1, 1])
        with col1:
            submit_survey = st.form_submit_button("✅ Submit Response")
        with col2:
            discard_survey = st.form_submit_button("❌ Discard and Go Back")

        if discard_survey:
            reset_session()
            st.rerun()

        if submit_survey:
            # Philippine time timestamp
            ph_time = datetime.now(ZoneInfo("Asia/Manila")).strftime("%Y-%m-%d %H:%M:%S")
            
            new_row = [ph_time, church_code, control_id] + scores
            try:
                sheet.append_row(new_row)
                st.session_state.stage = "results"
                st.success("✅ Your response has been submitted!")
                st.rerun()
            except Exception as e:
                st.error(f"Could not submit response: {e}")

# -------------------------
# Stage: Results
# -------------------------
elif st.session_state.stage == "results":
    try:
        data = sheet.get_all_records()
        df = pd.DataFrame(data)

        # Normalize values before filtering
        df["Code"] = df["Code"].astype(str).str.strip()
        df["Control_ID"] = df["Control_ID"].astype(str).str.strip()

        church_code = st.session_state.church_code
        df_code = df[df["Code"] == church_code]

        if not df_code.empty:
            avg_scores = df_code[[f"Q{i}" for i in range(1, 8)]].mean().tolist()
            average = float(np.mean(avg_scores))
            classification, interpretation = classify(average)

            st.header("📊 Aggregated Results")
            st.markdown(f"**Number of Respondents (Code {church_code}):** {len(df_code)}")
            st.markdown(f"**Average Score (Q1–Q7):** {average:.2f}")
            st.write(f"**Health Status:** _{classification}_")
            st.write(f"**Interpretation:** {interpretation}")

            st.subheader("🕸️ Church Health Overview")
            draw_custom_radar(avg_scores, main_virtues)
        else:
            st.warning("⚠️ No responses yet for this Church Code.")

    except Exception as e:
        st.error(f"Could not fetch results: {e}")

    st.info(f"### 📌 Church Code used: **{st.session_state.church_code}**")
    if st.button("🔄 Go Back / Enter a new Church Code"):
        reset_session()
        st.rerun()

st.divider()

# =========================
# OTHER OPTIONS (Accordion)
# =========================
with st.expander("⚙️ Other Options for Viewing/Filtering Results (Optional)"):
    
    # ------------------------
    # 1. Upload Respondent List (Code & Control_ID)
    # ------------------------
    st.subheader("1️⃣ Filter Survey Results by Church Code and Control ID")
    uploaded_ids = st.file_uploader(
        "📂 Upload a file containing **Code** and **Control_ID** to filter results (e.g., official church survey)",
        type=["xlsx", "xls", "csv"],
        key="id_file"
    )

    st.caption("✅ Example format of the file:")
    sample_ids = pd.DataFrame({
        "Code": ["CH001", "CH001"],
        "Control_ID": ["A123", "A124"]
    })
    st.dataframe(sample_ids, hide_index=True)

    if uploaded_ids:
        if uploaded_ids.name.endswith(".csv"):
            df_upload = pd.read_csv(uploaded_ids)
        else:
            df_upload = pd.read_excel(uploaded_ids)

        df_upload.columns = df_upload.columns.str.strip().str.lower()
        if "church_code" in df_upload.columns and "code" not in df_upload.columns:
            df_upload.rename(columns={"church_code": "code"}, inplace=True)

        required_cols = {"code", "control_id"}
        if not required_cols.issubset(set(df_upload.columns)):
            st.error("⚠️ Invalid file. Must contain columns: Code (or Church_Code) and Control_ID.")
        else:
            st.success(f"✅ File accepted. {len(df_upload)} control IDs loaded.")

            # Fetch Google Sheet data
            data = sheet.get_all_records()
            df_sheet = pd.DataFrame(data)
            df_sheet.columns = df_sheet.columns.str.strip().str.lower()

            merged = df_sheet.merge(
                df_upload,
                on=["code", "control_id"],
                how="inner"
            )

            if merged.empty:
                st.warning("⚠️ No matching respondents found in Google Sheet.")
            else:
                q_cols = [f"q{i}" for i in range(1, 8)]
                avg_scores = merged[q_cols].mean().tolist()
                average = float(np.mean(avg_scores))
                classification, interpretation = classify(average)

                #ph_time = datetime.now(ZoneInfo("Asia/Manila")).strftime("%Y-%m-%d %H:%M:%S")
                code_counts = merged['code'].value_counts()
                formatted_codes = ", ".join([f"{code} ({count})" for code, count in code_counts.items()])
                
                st.header("📊 Results (Filtered by Uploaded List)")
                st.info(f"Church Code(s) used: **{formatted_codes}**")

                #st.info(f"Church Code(s) used: **{', '.join(merged['code'].unique())}**")
                st.write(f"Number of respondents: {len(merged)}")
                st.markdown(f"**Average Score (Q1–Q7):** {average:.2f}")
                st.write(f"**Health Status:** _{classification}_")
                st.write(f"**Interpretation:** {interpretation}")
                #st.write(f"📅 Timestamp: {ph_time}")

                st.subheader("🕸️ Church Health Overview")
                draw_custom_radar(avg_scores, main_virtues)

    st.divider()

    # ------------------------
    # 2. Upload Survey Results (Q1–Q7)
    # ------------------------
    st.subheader("2️⃣ View Direct Survey Results (Upload File)")
    uploaded_file = st.file_uploader(
        "📂 Upload a file (.xls, .xlsx, .csv) containing ONLY the columns Q1–Q7 (one row per respondent)",
        type=["xlsx", "xls", "csv"],
        key="survey_file"
    )

    st.caption("✅ Example format of the file (one row = one respondent):")
    sample_df = pd.DataFrame({
        "Q1": [4, 5],
        "Q2": [3, 4],
        "Q3": [5, 5],
        "Q4": [2, 3],
        "Q5": [4, 4],
        "Q6": [3, 2],
        "Q7": [5, 4],
    })
    st.dataframe(sample_df, hide_index=True)

    if uploaded_file:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        df.rename(columns=lambda x: x.strip().lower(), inplace=True)
        expected_cols = [f"q{i}" for i in range(1, 8)]

        if list(df.columns) != expected_cols:
            st.error(
                f"⚠️ Invalid file format. "
                f"The file must contain ONLY these columns in order: {', '.join([c.upper() for c in expected_cols])}"
            )
        else:
            df.columns = [c.upper() for c in df.columns]
            avg_scores = df[df.columns].mean().tolist()
            average = float(np.mean(avg_scores))
            classification, interpretation = classify(average)

            st.header("📊 Results (from uploaded file)")
            st.write(f"Number of respondents: {len(df)}")
            st.markdown(f"**Average Score (Q1–Q7):** {average:.2f}")
            st.write(f"**Health Status:** _{classification}_")
            st.write(f"**Interpretation:** {interpretation}")

            st.subheader("🕸️ Church Health Overview")
            draw_custom_radar(avg_scores, main_virtues)







