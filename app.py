# -*- coding: utf-8 -*-
# Copyright (c) 2025 Wendell Q. Campano
# All rights reserved; code may not be copied or used without written permission.
"""
Created on Wed Jul 30 16:56:21 2025

@author: wqcampano
"""
# -*- coding: utf-8 -*-
#"""
#H.E.A.L.T.H.Y. Church Checklist by Jason Richard Tan and Wendell Q. Campano
#- Excel upload path (Q1..Q7), OR
#- Live survey path gated by Church Code (writes to Google Sheets)
#"""

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import re
import pandas as pd
import base64
import time
import gspread
#from google.oauth2.service_account import Credentials
from datetime import datetime
from zoneinfo import ZoneInfo
#import qrcode
from PIL import Image
#from io import BytesIO

from google.oauth2.service_account import Credentials

def clean_label(label: str) -> str:
    # 1. Remove HTML tags like <b>...</b>, <i>...</i>
    text = re.sub(r"<.*?>", "", label)
    # 2. Remove Markdown bold/italic markers ** and _
    text = text.replace("**", "").replace("*", "").replace("_", "")
    return text.strip()
    
def append_response(row_data):
    retries = 3
    for attempt in range(retries):
        try:
            sheet = get_sheet()  # get fresh sheet each time
            sheet.append_row(row_data)
            st.cache_data.clear()  # clear cached data so load_data() sees updates
            return True
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2)
            else:
                st.error("Submission failed. Please try again.")
                print("Google Sheets write error:", e)
                return False
                
# =========================
# GOOGLE SHEETS SETUP
# =========================
def get_sheet():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
    )
    client = gspread.authorize(creds)
    return client.open_by_url(st.secrets["app"]["sheet_url"]).sheet1

@st.cache_data(ttl=15)  # caches the actual rows for 15 seconds
def load_data():
    sheet = get_sheet()  # fresh credentials every call
    return sheet.get_all_records()
    
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
# APP SETUP
# =========================
st.set_page_config(page_title="H.E.A.L.T.H.Y. Church Checklist", layout="centered")

# --- Centered Logo (PNG, works locally) ---
with open("GCMTC_LogoTeal.png", "rb") as f:
    img_data = f.read()
encoded = base64.b64encode(img_data).decode()

st.markdown(
    f"""
    <div style="text-align: center;">
        <img src="data:image/png;base64,{encoded}" alt="Organization Logo" width="300">
    </div>
    """,
    unsafe_allow_html=True
)

# --- Title and subtitle ---
st.title("🧭 H.E.A.L.T.H.Y. Church Checklist")
st.markdown(
    "<div style='font-size:13px; color:gray;'>by Jason Richard Tan (jason.tan@bsop.edu.ph) and Wendell Q. Campano (wqcampano@gmail.com)</div>",
    unsafe_allow_html=True
)
st.divider()

# =========================
# SURVEY QUESTIONS
# =========================
questions = [
    {
        "label": "<b>HUMILITY</b> (<i>Mababang loob o Mapagpakumbaba</i>)",
        "description": "The posture of the heart that recognizes one’s complete dependence on God, placing His will above personal pride, ambition, or self-sufficiency. It is the acknowledgement that all wisdom, strength, and provision come from Him (James 4:6; Philippians 2:3–8; Matthew 5:5), and therefore one lives not for self-exaltation but for God’s glory and the good of others. Humility is expressed through obedience to God, service to others, a teachable spirit, and a willingness to submit rather than dominate. It reflects the character of Christ, who, though equal with God, emptied Himself and became a servant, ultimately modeling perfect humility in His life, death, and resurrection.",
        "anchors": [
            "A spirit of competition, boasting, or arrogance dominates, especially in board meetings. Members rarely apologize or seek reconciliation when conflicts arise.",
            "Leaders and members sometimes seek forgiveness and reconciliation, though these behaviors are rarely noticed.",
            "Members consistently value others above themselves, act with gentleness, respect, and courtesy, and seek reconciliation when conflicts arise."
        ]
    },
    {
        "label": "<b>ENDURANCE in the Faith</b> (<i>Matiyagang nagpapatuloy, Nananatiling tapat, o Nagtitiyaga hanggang wakas</i>)",
        "description": "Endurance in the faith is the steadfast perseverance to remain faithful to God and His promises despite trials, suffering, or opposition. It is the spiritual strength to press on in obedience and hope, trusting that God is working all things for good and that His reward is sure. Scripture exhorts believers to “run with perseverance the race marked out for us, fixing our eyes on Jesus” (Hebrews 12:1–2), to “rejoice in our sufferings, knowing that suffering produces endurance” (Romans 5:3–4), and to remain steadfast under trial, for “when he has stood the test he will receive the crown of life” (James 1:12, 1Corinthians 13:7). Endurance, therefore, is both a gift of God’s sustaining grace and the believer’s faithful response to keep walking with Christ until the end.",
        "anchors": [
            "People leave or disengage when challenges arise. Ministry participation is minimal or conditional.",
            "Members tend to participate only when convenient and rarely persevere through difficulties or changes.",
            "The community demonstrates consistent faithfulness, perseverance, adaptability, and willingness to serve despite difficulty or personal sacrifice."
        ]
    },
    {
        "label": "<b>AUTHENTICITY</b> (<i>Pusong Dalisay, malinis na budhi, at tapat na pananampalataya o mabuting loob</i>)",
        "description": "Authenticity is living with integrity and sincerity before God and others, where one’s inner life aligns with outward actions. It is the opposite of hypocrisy, calling believers to be genuine in faith, speech, and conduct, reflecting the truth of Christ within them. Scripture reminds us to live in the light, for “whoever lives by the truth comes into the light, so that it may be seen plainly that what they have done has been done in the sight of God” (John 3:21), and to “let love be genuine” (Romans 12:9). Authenticity means walking in truth (3 John 1:4, 1 Timothy 1:5), confessing weaknesses honestly, and allowing God’s Spirit to shape a life that is real, transparent, and consistent with the gospel.",
        "anchors": [
            "Attendance is mostly habitual or for appearances; kindness, generosity, and public testimonies are minimal.",
            "Members show support, encouragement, and eagerness to have fellowship with one another, though these behaviors are not yet consistent.",
            "Members show kindness, hospitality, and mercy. They support, encourage, and pray for one another, visit the sick, and assist those in need."
        ]
    },
    {
        "label": "<b>LOVE</b> (<i>Pag-ibig</i>)",
        "description": "Love is the highest virtue and the defining mark of the Christian life, as beautifully described in 1 Corinthians 13. It is not merely an emotion but a selfless commitment to seek the good of others, grounded in God’s own love. Paul teaches that love is patient and kind; it does not envy, boast, or act with pride. It is not rude, self-seeking, or easily angered, and it keeps no record of wrongs. Love rejoices with the truth, always protects, always trusts, always hopes, and always perseveres (1 Corinthians 13:4–7). Unlike gifts or accomplishments that will pass away, love is eternal, for “the greatest of these is love” (1 Corinthians 13:13).",
        "anchors": [
            "Hostility, factions, or selfish ambition are present; relationships are strained or divisive.",
            "Members are generally amicable and respectful, but relationships lack depth or sustained care.",
            "Members show love for one another, enjoy fellowship, share resources, pray for each other, and participate in communal activities beyond the confines of the church building."
        ]
    },
    {
        "label": "<b>TRUSTWORTHINESS</b> (<i>Mapagkakatiwalaan</i>)",
        "description": "Trustworthiness is the quality of being faithful, reliable, and dependable in character and action, reflecting the steadfastness of God Himself. Scripture calls believers to let their “Yes” be yes and their “No” be no (Matthew 5:37), showing integrity in word and deed. A trustworthy person keeps promises, fulfills responsibilities, and acts with honesty, echoing the wisdom of Proverbs 12:22: “The Lord detests lying lips, but he delights in people who are trustworthy.” Ultimately, trustworthiness is rooted in God’s faithfulness (Lamentations 3:22–23), and believers are called to mirror His character by living with integrity so that others may confidently depend on their word and witness.",
        "anchors": [
            "Mistrust and suspicion dominate; contempt or open criticism is common.",
            "Some discord exists, but most members generally respect and affirm leadership.",
            "The congregation fully trusts leadership, and leaders consistently demonstrate integrity and biblical alignment in life and ministry."
        ]
    },
    {
        "label": "<b>HARMONY</b> (<i>Pakikiisa at Nagkaisa</i>)",
        "description": "Harmony or peace within a community of believers is the unity and mutual love that flows from Christ’s reconciling work, binding diverse people together as one body under His lordship. Believers are called to “make every effort to keep the unity of the Spirit through the bond of peace” (Ephesians 4:3) and to “live in harmony with one another” (Romans 12:16), showing patience, forgiveness, and compassion. This peace is not merely the absence of conflict but the active presence of reconciliation, encouragement, and shared life in Christ, who Himself is our peace (Ephesians 2:14). When believers “let the peace of Christ rule in [their] hearts” (Colossians 3:15), the church becomes a living testimony of God’s kingdom marked by love, unity, and mutual upbuilding.",
        "anchors": [
            "Gossip, jealousy, unresolved conflicts, or division are common.",
            "Past conflicts may remain unresolved, but members are increasingly sensitive to reconciliation and avoiding repeated mistakes.",
            "Conflicts are addressed with forgiveness and understanding. Members and leaders apologize readily, maintain peace, and cultivate strong relational bonds."
        ]
    },
    {
        "label": "<b>YEARNING for Truth</b> (<i>Kinagagalak ang katotohanan</i>)",
        "description": "Yearning for truth is the deep longing of the heart to know, embrace, and live according to God’s Word, for He Himself is the source of all truth. Scripture teaches that Jesus is “the way, the truth, and the life” (John 14:6), and those who belong to Him are called to seek His truth earnestly, like the psalmist who prays, “Teach me your way, Lord, that I may rely on your faithfulness; give me an undivided heart, that I may fear your name” (Psalm 86:11, 1 Corinthians 13:6). This yearning is expressed in a hunger for God’s Word (Psalm 119:105, 160), a desire to walk in integrity, and a willingness to reject falsehood and deception. It is the Spirit of truth (John 16:13) who guides believers into a deeper knowledge of Christ, shaping them to love truth and live by it in every aspect of life.",
        "anchors": [
            "Members show little interest in Scripture, prayer, or personal spiritual growth.",
            "Members engage in discipleship, and other faith-building activities, though their participation and personal practice are not yet consistent.",
            "Members actively seek to learn, study Scripture, grow in faith, disciple others, and apply biblical principles in daily life."
        ]
    }
]

main_virtues = []
for q in questions:
    cleaned = clean_label(q["label"])
    # if you only want the first part (before parentheses)
    virtue = cleaned.split("(")[0].strip()
    main_virtues.append(virtue)

# Detailed instructions above the input
with st.expander("📖 How to Use the App"):
    st.markdown("""
**For Casual Church Surveys:**

1. **Assign a common Church Code** to all participants (e.g., ABC2025Q1).  
2. **Instruct participants to open the app, enter the Church Code**, and click **➡️ Take the Survey**.  
   - The optional **Control ID** field will appear – leave it blank for casual or personal surveys.  
3. **Have each participant complete the survey** and submit their responses.  
4. **View results:** Aggregated results appear automatically after submission.  
   - Anyone with the Church Code can view them by returning to the main page and clicking **📊 View Results Only**.

**For Official Church Surveys:**

1. **Assign a common Church Code** for your church (e.g., ABC2025Q1).  
2. **Provide each participant with a unique Control ID** (e.g., A001, A002…).  
3. **Instruct participants to open the app, enter the Church Code**, and click **➡️ Take the Survey**.  
   - Enter the assigned **Control ID** in the optional field.
   - Each Control ID can only be used **once**; duplicate entries will not be accepted by the system.
4. **Have each participant complete the survey** and submit their responses.  
5. **View results:** Aggregated results appear automatically after submission.  
   - Anyone with the Church Code can view them by returning to the main page and clicking **📊 View Results Only**.  
   - To view **official survey results only**, go to **⚙️ Other Options for Viewing/Filtering Results (Optional)** and upload a file containing the assigned **Church Code(s) and Control IDs** under **2️⃣ Filter Survey Results by Church Code and Control ID**.  
     - Only the uploaded respondents are included in the aggregated results.

**Additional Options:**

1. **Filter Survey Results by Church Code and Date**  
   - Aggregated results for a Church Code will reflect only responses submitted within the selected date range.  

2. **Filter Survey Results by Church Code and Control ID**  
   - Upload a file containing Church Code(s) and Control IDs to view aggregated results for selected respondents only.  

3. **View Direct Survey Results (Upload File)**  
   - Upload a file with Q1–Q7 responses for each participant.  
   - Aggregated results will reflect only the respondents included in the uploaded file.
""")

    st.markdown("**📱 Scan QR code to open the app directly:**")
    img = Image.open("app_qr.png")
    img = img.resize((250, 250))  # width x height in pixels

    # Display the static QR code image
    st.image(img, caption="H.E.A.L.T.H.Y. Church App")
    #st.image("app_qr.png", caption="Scan to open the H.E.A.L.T.H.Y. Church Checklist App", use_container_width=True)
       
# =========================
# SESSION STATE INITIALIZATION
# =========================
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

# =========================
# STAGE: Await Church Code
# =========================
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
            st.session_state.stage = "control_input"
            st.rerun()

    if view_results_btn:
        if not code.strip():
            st.warning("⚠️ Please enter a Church Code before viewing results.")
        else:
            st.session_state.church_code = code.strip()
            st.session_state.stage = "results"
            st.rerun()

# =========================
# STAGE: Optional Control ID
# =========================
elif st.session_state.stage == "control_input":
    st.info("Optional: Enter a Control ID provided by your church (leave blank for casual or personal survey).")

    with st.form("control_form"):
        control_id_input = st.text_input("Control ID", value=st.session_state.control_id)
        st.caption("⚠️ Note: Control IDs are case-sensitive (e.g., A123 ≠ a123).")
        submit_control = st.form_submit_button("➡️ Proceed to Questionnaire")
        cancel_control = st.form_submit_button("❌ Cancel")

        if submit_control:
            control_id_input = control_id_input.strip()
            if not control_id_input:
                st.session_state.control_id = ""
                st.session_state.stage = "survey"
                st.rerun()
            else:
                # Check for duplicate
                try:
                    data = load_data()
                    df = pd.DataFrame(data)
                    df["Control_ID"] = df["Control_ID"].astype(str).str.strip()
                    df["Code"] = df["Code"].astype(str).str.strip()
                    duplicate = df[(df["Code"] == st.session_state.church_code) & (df["Control_ID"] == control_id_input)]
                except Exception as e:
                    st.error(f"Could not fetch existing responses: {e}")
                    st.stop()

                if not duplicate.empty:
                    st.warning(f"⚠️ Control ID '{control_id_input}' has already been used for Church Code '{st.session_state.church_code}'.")
                else:
                    st.session_state.control_id = control_id_input
                    st.session_state.stage = "survey"
                    st.rerun()

        if cancel_control:
            reset_session()
            st.rerun()

# =========================
# STAGE: Survey Form
# =========================
elif st.session_state.stage == "survey":
    st.subheader("📋 Questionnaire")

    # Survey instructions and visual
    st.markdown(
        """
For each area of church health, you’ll see **three reference descriptions**:

- One that reflects an **unhealthy pattern**  
- One that shows a **growing** or **developing** state  
- One that represents a **healthy, ideal** state

Please reflect on your church honestly, then rate your church from **1 to 10**:

- **1–3** → Closely resembles the unhealthy description  
- **4–7** → Somewhere in between; growing in this area  
- **8–10** → Strongly reflects the healthy description

Within each range, lower numbers mean worse health and higher numbers mean better health. For example, in the 1–3 range, 1 is more unhealthy than 2, and 2 is more unhealthy than 3. This same principle applies across the scale (4–7 and 8–10): higher numbers always indicate better health.
"""
    )
    st.image("health_continuum_dark_green.png", use_container_width=True)

    with st.form("survey_form"):
        scores = []
        for q in questions:
            col1, col2 = st.columns([10, 1])
            with col1:
                # st.subheader(q["label"])
                # custom label rendering: big text but not fully bold
                 st.markdown(
                        f"<div style='font-size:26px; font-weight:normal; margin-top:0.8em; margin-bottom:0.4em;'>{q['label']}</div>",
                    unsafe_allow_html=True
                )
            with col2:
                with st.popover("❓"):
                    st.markdown(q["description"])
    
            # keep anchors displayed as before
            st.markdown(f"**Unhealthy (1–3):** {q['anchors'][0]}")
            st.markdown(f"**Moderate/Developing (4–7):** {q['anchors'][1]}")
            st.markdown(f"**Healthy (8–10):** {q['anchors'][2]}")
    
            score = st.slider("Score: 1 (worst) → 10 (best)", 1, 10, 5, key=q["label"])
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
            ph_time = datetime.now(ZoneInfo("Asia/Manila")).strftime("%Y-%m-%d %H:%M:%S")
            new_row = [ph_time, st.session_state.church_code, st.session_state.control_id] + scores
            
            success = append_response(new_row)

            if success:
                st.success("✅ Your response has been submitted!")
                # Clear cached data so next read fetches updated Google Sheet
                st.cache_data.clear()
                st.session_state.stage = "results"
                st.rerun()

# =========================
# STAGE: Results
# =========================
elif st.session_state.stage == "results":
    try:
        data = load_data()
        df = pd.DataFrame(data)
        df["Code"] = df["Code"].astype(str).str.strip()
        df["Control_ID"] = df["Control_ID"].astype(str).str.strip()
        df_code = df[df["Code"] == st.session_state.church_code]

        if not df_code.empty:
            avg_scores = df_code[[f"Q{i}" for i in range(1, 8)]].mean().tolist()
            average = float(np.mean(avg_scores))
            classification, interpretation = classify(average)

            st.header("📊 Aggregated Results")
            st.markdown(f"**Number of Respondents (Code {st.session_state.church_code}):** {len(df_code)}")
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
if "expander_open" not in st.session_state:
    st.session_state.expander_open = False

# Render the expander
with st.expander(
    "⚙️ Other Options for Viewing/Filtering Results (Optional)",
    expanded=st.session_state.expander_open
) as exp:
    
    # Update session_state whenever user toggles the expander
    #st.session_state.expander_open = exp.expanded  # works in Streamlit >=1.25

    # ------------------------
    # 1️⃣ Filter by Date
    # ------------------------
    st.subheader("1️⃣ Filter Survey Results by Date")
    st.info("View aggregated results for a Church Code within a specific date range.")

    date_filter_code = st.text_input(
        "Enter Church Code to filter",
        value=st.session_state.church_code,
        key="date_filter_code"
    )
    start_date = st.date_input("Select start date (yyyy/mm/dd)", value=datetime(2025, 1, 1), key="start_date")
    end_date = st.date_input("Select end date (yyyy/mm/dd)", value=datetime.today(), key="end_date")

    if st.button("📊 View Date-Filtered Results", key="date_filter_btn"):
        if not date_filter_code.strip():
            st.warning("⚠️ Please enter a Church Code before filtering.")
        elif start_date > end_date:
            st.warning("⚠️ Please select a valid date range (start date must be before end date).")
        else:
            try:
                data = load_data()
                df = pd.DataFrame(data)
                df["Code"] = df["Code"].astype(str).str.strip()
                df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")

                df_code = df[df["Code"] == date_filter_code.strip()]
                start_dt = pd.to_datetime(start_date)
                end_dt = pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
                df_filtered = df_code[(df_code["Timestamp"] >= start_dt) & (df_code["Timestamp"] <= end_dt)]

                if df_filtered.empty:
                    st.warning("⚠️ No responses found for this Church Code in the selected date range.")
                else:
                    avg_scores = df_filtered[[f"Q{i}" for i in range(1, 8)]].mean().tolist()
                    average = float(np.mean(avg_scores))
                    classification, interpretation = classify(average)

                    st.header(f"📊 Aggregated Results for {date_filter_code.strip()}")
                    st.markdown(f"**Date Range:** {start_date.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')}")
                    st.markdown(f"**Number of respondents:** {len(df_filtered)}")
                    st.markdown(f"**Average Score (Q1–Q7):** {average:.2f}")
                    st.write(f"**Health Status:** _{classification}_")
                    st.write(f"**Interpretation:** {interpretation}")
                    st.subheader("🕸️ Church Health Overview")
                    draw_custom_radar(avg_scores, main_virtues)
            except Exception:
                st.warning("⚠️ Please select a valid range.")

    st.divider()

    # ------------------------
    # 2️⃣ Filter by Church Code & Control ID
    # ------------------------
    st.subheader("2️⃣ Filter Survey Results by Church Code and Control ID")
    uploaded_ids = st.file_uploader(
        "📂 Upload a file containing **Code** (for Church Code) and **Control_ID**",
        type=["xlsx", "xls", "csv"],
        key="id_file"
    )

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
            st.error("⚠️ Invalid file. Must contain columns: Code and Control_ID.")
        else:
            st.success(f"✅ File accepted. {len(df_upload)} control IDs loaded.")
            data = load_data()
            df_sheet = pd.DataFrame(data)
            df_sheet.columns = df_sheet.columns.str.strip().str.lower()
            merged = df_sheet.merge(df_upload, on=["code", "control_id"], how="inner")

            if merged.empty:
                st.warning("⚠️ No matching respondents found in Google Sheet.")
            else:
                q_cols = [f"q{i}" for i in range(1, 8)]
                avg_scores = merged[q_cols].mean().tolist()
                average = float(np.mean(avg_scores))
                classification, interpretation = classify(average)
                code_counts = merged['code'].value_counts()
                formatted_codes = ", ".join([f"{code} ({count})" for code, count in code_counts.items()])

                st.header("📊 Results (Filtered by Uploaded List)")
                st.info(f"Church Code(s) used: **{formatted_codes}**")
                st.write(f"Number of respondents: {len(merged)}")
                st.markdown(f"**Average Score (Q1–Q7):** {average:.2f}")
                st.write(f"**Health Status:** _{classification}_")
                st.write(f"**Interpretation:** {interpretation}")
                st.subheader("🕸️ Church Health Overview")
                draw_custom_radar(avg_scores, main_virtues)

    st.divider()

    # ------------------------
    # 3️⃣ Upload Survey Results (Q1–Q7)
    # ------------------------
    st.subheader("3️⃣ View Direct Survey Results (Upload File)")
    uploaded_file = st.file_uploader(
        "📂 Upload a file (.xls, .xlsx, .csv) containing ONLY the columns Q1–Q7",
        type=["xlsx", "xls", "csv"],
        key="survey_file"
    )

    if uploaded_file:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        df.rename(columns=lambda x: x.strip().lower(), inplace=True)
        expected_cols = [f"q{i}" for i in range(1, 8)]

        if list(df.columns) != expected_cols:
            st.error(
                f"⚠️ Invalid file format. Must contain ONLY these columns in order: {', '.join([c.upper() for c in expected_cols])}"
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



