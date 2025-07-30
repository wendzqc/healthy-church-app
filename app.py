# -*- coding: utf-8 -*-
"""
Created on Wed Jul 30 16:56:21 2025

@author: Desktop
"""

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import os

# === Global Color Map for Chart ===
colors = [
    "#ff0000", "#ff4500", "#ff8c00", "#ffaa00", "#ffff00", "#ffff00", "#ffff00",
    "#aaff00", "#55ff00", "#00ff00", "#008800"
]
cmap = LinearSegmentedColormap.from_list("health_scale", colors, N=256)

# === Generate and Save Health Scale Image ===
def generate_scale_image():
    if not os.path.exists("health_continuum_dark_green.png"):
        fig, ax = plt.subplots(figsize=(10, 2))
        fig.subplots_adjust(top=0.7, bottom=0.3)
        gradient = np.linspace(1, 10, 256).reshape(1, 256)
        ax.imshow(gradient, aspect='auto', cmap=cmap, extent=[1, 10, 0, 1])
        ax.set_xlim(1, 10)
        ax.set_xticks(range(1, 11))
        ax.set_yticks([])
        ax.axvline(x=3.5, color='black', linestyle='-', linewidth=1)
        ax.axvline(x=7.5, color='black', linestyle='-', linewidth=1)
        ax.text(5.5, -0.8, "Increasing Health →", ha='center', fontsize=10, fontweight='bold', color='#333333')
        plt.title("Church Health Assessment Scale", fontsize=14, pad=25)
        plt.tight_layout()
        plt.savefig("health_continuum_dark_green.png", dpi=120, bbox_inches='tight')
        plt.close()

# === Draw Radar Chart ===
def draw_custom_radar(scores, categories):
    avg_score = np.mean(scores)
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

    for i, (angle, score) in enumerate(zip(angles[:-1], scores[:-1])):
        ax_radar.plot(angle, score, 'o', markersize=8, color=cmap((score - 1)/9.0))
        ax_radar.annotate(f"{score:.1f}", xy=(angle, score + 0.3), textcoords="offset points", xytext=(0, 5),
                          ha='center', fontsize=9, fontweight='bold',
                          bbox=dict(boxstyle="round,pad=0.2", fc=cmap((score - 1)/9.0), ec="black", alpha=0.7))

    ax_radar.annotate(f"Overall: {avg_score:.1f}/10", xy=(0.5, 0.5), xycoords='axes fraction', ha='center',
                      fontsize=12, fontweight='bold',
                      bbox=dict(boxstyle="round,pad=0.3", fc=cmap((avg_score - 1)/9.0), ec="black", alpha=0.8))

    ax_radar.plot(angles, [5.5]*len(angles), '--', color='#ffaa00', alpha=0.7)
    ax_radar.plot(angles, [8.5]*len(angles), '--', color='#00aa00', alpha=0.7)
    ax_radar.set_title("Church Health Assessment - Radar Chart", fontsize=15, pad=20, fontweight='bold')

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

# === STREAMLIT APP ===

st.set_page_config(page_title="H.E.A.L.T.H.Y. Church Checklist", layout="centered")
st.title("🧭 H.E.A.L.T.H.Y. Church Checklist")

st.markdown("""
For each area of church health, you’ll see **three descriptions**:

- One that reflects an **unhealthy pattern**  
- One that shows a **growing** or **developing** state  
- One that represents a **healthy, ideal** state

Please reflect on your church honestly, then rate your church from **1 to 10**:

- **1–3** → Closely resembles the unhealthy description  
- **4–7** → Somewhere in between; growing in this area  
- **8–10** → Strongly reflects the healthy description
""")

# Generate and display scale
generate_scale_image()
st.image("health_continuum_dark_green.png", use_container_width=True)

# Questionnaire with anchors
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
        "label": "Trustworthiness (Matt.5, pure in heart; 1 Cor.13, always trusts, always hopes)",
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

scores = []
st.subheader("📋 Questionnaire")
for q in questions:
    st.subheader(q["label"])
    st.markdown(f"**Unhealthy (1–3):** {q['anchors'][0]}")
    st.markdown(f"**Moderate (4–7):** {q['anchors'][1]}")
    st.markdown(f"**Healthy (8–10):** {q['anchors'][2]}")
    score = st.slider("Score (1–10)", 1, 10, 5, key=q["label"])
    scores.append(score)
    st.markdown("---")

# Scoring
total = sum(scores)
average = total / len(scores)
if average >= 8.5:
    classification = "Thriving Health"
elif average >= 7.5:
    classification = "Stable Health"
elif average >= 6.5:
    classification = "Moderate Concerns"
elif average >= 5.5:
    classification = "Significant Issues"
else:
    classification = "Critical Condition"

# Results
st.header("📊 Results")
st.markdown(f"**Total Score:** {total} / 70")
st.markdown(f"**Average Score:** {average:.2f}")
st.markdown(f"**Health Status:** `{classification}`")

# Radar Chart
st.subheader("🕸️ Radar Chart")
import re

# Extract main virtue: uppercase word(s) from the start of each label
main_virtues = [re.match(r"[A-Z\s]+", q["label"]).group(0).strip() for q in questions]

draw_custom_radar(scores[:], main_virtues)

#draw_custom_radar(scores[:], [q["label"] for q in questions])
