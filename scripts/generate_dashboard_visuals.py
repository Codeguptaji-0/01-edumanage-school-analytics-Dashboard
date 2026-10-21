"""
High-Resolution Power BI Dashboard Simulator & Visual Generator for EduManage
Renders 3 pixel-perfect 1920x1080 dashboard screens:
1. Executive KPI Overview
2. Fee Collections & Defaulters Deep Dive
3. Academic Performance & Dual-Risk Matrix
Also exports a unified executive PDF presentation report.
"""

import os
import sys
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.gridspec import GridSpec
from reportlab.lib.pagesizes import landscape, letter
from reportlab.pdfgen import canvas
from PIL import Image

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), "data")
DASHBOARD_DIR = os.path.join(os.path.dirname(BASE_DIR), "dashboards")
SCREENSHOTS_DIR = os.path.join(DASHBOARD_DIR, "screenshots")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, "edumanage.db")
conn = sqlite3.connect(DB_PATH)

# Styling Palette (Modern Dark Slate / Power BI Theme)
BG_COLOR = "#0B0F19"
PANEL_COLOR = "#151E32"
TEXT_COLOR = "#F8FAFC"
MUTED_TEXT = "#94A3B8"
ACCENT_BLUE = "#38BDF8"
ACCENT_CYAN = "#06B6D4"
ACCENT_INDIGO = "#6366F1"
ACCENT_EMERALD = "#10B981"
ACCENT_AMBER = "#F59E0B"
ACCENT_ROSE = "#F43F5E"
GRID_COLOR = "#1E293B"

plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['text.color'] = TEXT_COLOR
plt.rcParams['axes.labelcolor'] = TEXT_COLOR
plt.rcParams['xtick.color'] = MUTED_TEXT
plt.rcParams['ytick.color'] = MUTED_TEXT


# Helper to draw KPI Card
def draw_kpi_card(ax, title, value, subtitle, border_color=ACCENT_BLUE):
    ax.set_facecolor(PANEL_COLOR)
    for spine in ax.spines.values():
        spine.set_color(border_color)
        spine.set_linewidth(1.5)
        spine.set_alpha(0.6)
    ax.set_xticks([])
    ax.set_yticks([])
    
    # Title
    ax.text(0.08, 0.76, title.upper(), color=MUTED_TEXT, fontsize=10, weight='bold', transform=ax.transAxes)
    # Main Value
    ax.text(0.08, 0.40, value, color=TEXT_COLOR, fontsize=19, weight='bold', transform=ax.transAxes)
    # Subtitle / Delta
    ax.text(0.08, 0.16, subtitle, color=border_color, fontsize=9.5, weight='semibold', transform=ax.transAxes)


# ==============================================================================
# SCREEN 1: EXECUTIVE KPI OVERVIEW
# ==============================================================================
print("🎨 Rendering Screen 1: Executive KPI Overview...")
fig = plt.figure(figsize=(19.2, 10.8), dpi=100, facecolor=BG_COLOR)
gs = GridSpec(10, 12, figure=fig, hspace=0.6, wspace=0.45, left=0.04, right=0.96, top=0.92, bottom=0.06)

# Header Title
fig.text(0.04, 0.955, "EDUMANAGE ANALYTICS  |  EXECUTIVE OVERVIEW DASHBOARD", 
         fontsize=18, weight='bold', color=TEXT_COLOR)
fig.text(0.04, 0.935, "Academic Year 2024–2025  •  1,183 Students  •  Delhi NCR Campus  •  Interactive Power BI View", 
         fontsize=10.5, color=ACCENT_BLUE)

# KPI Cards (Row 0 to 1)
ax_kpi1 = fig.add_subplot(gs[0:2, 0:2])
draw_kpi_card(ax_kpi1, "Total Invoiced", "₹7.77 Cr", "4,732 Invoices Issued", ACCENT_BLUE)

ax_kpi2 = fig.add_subplot(gs[0:2, 2:4])
draw_kpi_card(ax_kpi2, "Total Collected", "₹7.36 Cr", "94.63% Collection Rate", ACCENT_EMERALD)

ax_kpi3 = fig.add_subplot(gs[0:2, 4:6])
draw_kpi_card(ax_kpi3, "Outstanding Due", "₹41.76 L", "148 Overdue Invoices", ACCENT_ROSE)

ax_kpi4 = fig.add_subplot(gs[0:2, 6:8])
draw_kpi_card(ax_kpi4, "Total Enrollment", "1,183", "34 Active Classes", ACCENT_CYAN)

ax_kpi5 = fig.add_subplot(gs[0:2, 8:10])
draw_kpi_card(ax_kpi5, "Avg Attendance", "86.9%", "Target: >= 85%", ACCENT_AMBER)

ax_kpi6 = fig.add_subplot(gs[0:2, 10:12])
draw_kpi_card(ax_kpi6, "Dual At-Risk", "8 Students", "Attn <75% + Fee Default", ACCENT_ROSE)

# Chart 1: Monthly Attendance Trajectory (Row 2 to 6, Col 0 to 7)
ax_att = fig.add_subplot(gs[2:6, 0:7])
ax_att.set_facecolor(PANEL_COLOR)
for spine in ax_att.spines.values():
    spine.set_color(GRID_COLOR)

df_att = pd.read_sql("SELECT academic_month, ROUND(AVG(attendance_pct), 2) as avg_att FROM fact_attendance_monthly GROUP BY academic_month ORDER BY academic_month", conn)
months = [m.replace("2024-", "").replace("2025-", "Jan ") if "2025" in m else m.replace("2024-", "M") for m in df_att['academic_month']]
x_coords = np.arange(len(months))

ax_att.plot(x_coords, df_att['avg_att'], color=ACCENT_BLUE, marker='o', linewidth=3, markersize=7, label="Monthly Avg Attendance %")
ax_att.fill_between(x_coords, df_att['avg_att'], 70, color=ACCENT_BLUE, alpha=0.15)
ax_att.axhline(75.0, color=ACCENT_ROSE, linestyle='--', linewidth=1.8, label="Chronic Absentee Threshold (75%)")

# Annotate Winter Dip
ax_att.annotate("Winter Slump (83.8%)\nAQI & Cold Wave", xy=(7, 83.77), xytext=(6.2, 78.5),
                arrowprops=dict(arrowstyle="->", color=ACCENT_AMBER, lw=1.5),
                color=ACCENT_AMBER, fontsize=9.5, weight='bold')

ax_att.set_title("Monthly Attendance Trajectory & Winter Seasonality Analysis", fontsize=12, weight='bold', pad=12, loc='left')
ax_att.set_xticks(x_coords)
ax_att.set_xticklabels(df_att['academic_month'], fontsize=8.5, rotation=25)
ax_att.set_ylim(70, 95)
ax_att.set_ylabel("Attendance Rate (%)", fontsize=9.5, color=MUTED_TEXT)
ax_att.grid(True, color=GRID_COLOR, linestyle=':', alpha=0.7)
ax_att.legend(loc="upper right", facecolor=PANEL_COLOR, edgecolor=GRID_COLOR, fontsize=8.5)

# Chart 2: Quarterly Fee Collection vs Target (Row 2 to 6, Col 7 to 12)
ax_fee_q = fig.add_subplot(gs[2:6, 7:12])
ax_fee_q.set_facecolor(PANEL_COLOR)
for spine in ax_fee_q.spines.values():
    spine.set_color(GRID_COLOR)

df_q = pd.read_sql("""
SELECT quarter, 
       ROUND(SUM(amount_due)/100000.0, 2) as invoiced_lakhs, 
       ROUND(SUM(amount_paid)/100000.0, 2) as collected_lakhs,
       ROUND(SUM(balance_due)/100000.0, 2) as overdue_lakhs
FROM fact_fees GROUP BY quarter ORDER BY due_date
""", conn)

bar_w = 0.35
q_x = np.arange(len(df_q))
ax_fee_q.bar(q_x - bar_w/2, df_q['invoiced_lakhs'], width=bar_w, label="Billed (₹ Lakhs)", color=ACCENT_INDIGO, alpha=0.9)
ax_fee_q.bar(q_x + bar_w/2, df_q['collected_lakhs'], width=bar_w, label="Collected (₹ Lakhs)", color=ACCENT_EMERALD, alpha=0.9)

for i in range(len(df_q)):
    ax_fee_q.text(q_x[i] + bar_w/2, df_q['collected_lakhs'][i] + 3, f"₹{df_q['collected_lakhs'][i]:.1f}L", 
                  ha='center', fontsize=8, color=TEXT_COLOR, weight='semibold')

ax_fee_q.set_title("Quarterly Cash Flow: Billed vs Collected (₹ Lakhs)", fontsize=12, weight='bold', pad=12, loc='left')
ax_fee_q.set_xticks(q_x)
ax_fee_q.set_xticklabels(df_q['quarter'], fontsize=8.5)
ax_fee_q.set_ylabel("Amount in ₹ Lakhs", fontsize=9.5, color=MUTED_TEXT)
ax_fee_q.set_ylim(0, 240)
ax_fee_q.grid(True, color=GRID_COLOR, linestyle=':', alpha=0.7)
ax_fee_q.legend(loc="upper right", facecolor=PANEL_COLOR, edgecolor=GRID_COLOR, fontsize=8.5)

# Chart 3: Class-wise Overdue Balance (Row 6 to 10, Col 0 to 7)
ax_def_bar = fig.add_subplot(gs[6:10, 0:7])
ax_def_bar.set_facecolor(PANEL_COLOR)
for spine in ax_def_bar.spines.values():
    spine.set_color(GRID_COLOR)

df_top_cls = pd.read_sql("""
SELECT class_id, ROUND(SUM(balance_due)/1000.0, 1) as overdue_k
FROM fact_fees GROUP BY class_id ORDER BY overdue_k DESC LIMIT 8
""", conn)

colors = [ACCENT_ROSE if k >= 200 else ACCENT_AMBER for k in df_top_cls['overdue_k']]
bars = ax_def_bar.barh(df_top_cls['class_id'], df_top_cls['overdue_k'], color=colors, height=0.6)
ax_def_bar.invert_yaxis()

for bar in bars:
    w = bar.get_width()
    ax_def_bar.text(w + 5, bar.get_y() + bar.get_height()/2, f"₹{w:.1f}k", 
                    va='center', fontsize=8.5, color=TEXT_COLOR, weight='bold')

ax_def_bar.set_title("Top Classes by Outstanding Due (₹ in Thousands)", fontsize=12, weight='bold', pad=12, loc='left')
ax_def_bar.set_xlabel("Uncollected Amount (₹ Thousands)", fontsize=9.5, color=MUTED_TEXT)
ax_def_bar.set_xlim(0, 360)
ax_def_bar.grid(True, color=GRID_COLOR, linestyle=':', alpha=0.7)

# Chart 4: Stream and Board Enrollment Breakdown (Row 6 to 10, Col 7 to 12)
ax_donut = fig.add_subplot(gs[6:10, 7:12])
ax_donut.set_facecolor(PANEL_COLOR)
for spine in ax_donut.spines.values():
    spine.set_color(GRID_COLOR)

df_stream = pd.read_sql("""
SELECT 
    CASE 
        WHEN grade_level <= 5 THEN 'Primary (Grades 1-5)'
        WHEN grade_level <= 8 THEN 'Middle (Grades 6-8)'
        WHEN grade_level <= 10 THEN 'Secondary (Grades 9-10)'
        ELSE 'Senior Sec (Grades 11-12)'
    END as wing,
    COUNT(student_id) as student_count
FROM dim_students GROUP BY wing ORDER BY student_count DESC
""", conn)

donut_colors = [ACCENT_BLUE, ACCENT_INDIGO, ACCENT_CYAN, ACCENT_AMBER]
wedges, texts, autotexts = ax_donut.pie(
    df_stream['student_count'], labels=df_stream['wing'], autopct='%1.1f%%',
    startangle=140, colors=donut_colors, pctdistance=0.75,
    textprops=dict(color=TEXT_COLOR, fontsize=8.5),
    wedgeprops=dict(width=0.45, edgecolor=BG_COLOR, linewidth=2)
)
for at in autotexts:
    at.set_color("#0B0F19")
    at.set_weight("bold")
    at.set_fontsize(8.5)

ax_donut.set_title("Student Headcount Distribution by Academic Wing", fontsize=12, weight='bold', pad=12, loc='left')

screen1_path = os.path.join(SCREENSHOTS_DIR, "executive_overview.png")
fig.savefig(screen1_path, facecolor=BG_COLOR, bbox_inches='tight')
plt.close(fig)
print(f"✅ Saved Screen 1: {screen1_path}")


# ==============================================================================
# SCREEN 2: FEE COLLECTIONS & DEFAULTERS DEEP DIVE
# ==============================================================================
print("🎨 Rendering Screen 2: Fee Collections & Defaulters Deep Dive...")
fig2 = plt.figure(figsize=(19.2, 10.8), dpi=100, facecolor=BG_COLOR)
gs2 = GridSpec(10, 12, figure=fig2, hspace=0.6, wspace=0.45, left=0.04, right=0.96, top=0.92, bottom=0.06)

fig2.text(0.04, 0.955, "EDUMANAGE ANALYTICS  |  FEE COLLECTIONS & DEFAULTER INTELLIGENCE", 
          fontsize=18, weight='bold', color=TEXT_COLOR)
fig2.text(0.04, 0.935, "Root Cause Diagnostics  •  Parent Income Segmentation  •  Late Payment Trajectory", 
          fontsize=10.5, color=ACCENT_ROSE)

# Top KPI Cards
ax2_kpi1 = fig2.add_subplot(gs2[0:2, 0:3])
draw_kpi_card(ax2_kpi1, "Senior Default Share", "₹14.54 Lakhs", "34.8% of Total Overdue", ACCENT_ROSE)

ax2_kpi2 = fig2.add_subplot(gs2[0:2, 3:6])
draw_kpi_card(ax2_kpi2, "Mid-Income Squeeze", "₹16.73 Lakhs", "₹3L-₹6L Bracket: 40.1% Share", ACCENT_AMBER)

ax2_kpi3 = fig2.add_subplot(gs2[0:2, 6:9])
draw_kpi_card(ax2_kpi3, "Peak Delay Invoices", "148 Defaulters", "Overdue > 60 Days", ACCENT_ROSE)

ax2_kpi4 = fig2.add_subplot(gs2[0:2, 9:12])
draw_kpi_card(ax2_kpi4, "Dominant Payment Mode", "UPI & NetBanking", "78.4% Total Volume", ACCENT_CYAN)

# Visual 1: Defaulters by Income Bracket (Row 2 to 6, Col 0 to 6)
ax_inc = fig2.add_subplot(gs2[2:6, 0:6])
ax_inc.set_facecolor(PANEL_COLOR)
for spine in ax_inc.spines.values():
    spine.set_color(GRID_COLOR)

df_inc = pd.read_sql("""
SELECT family_income_bracket, 
       ROUND(SUM(balance_due)/100000.0, 2) as overdue_lakhs,
       SUM(CASE WHEN payment_status = 'Overdue Defaulter' THEN 1 ELSE 0 END) as defaulters
FROM fact_fees f JOIN dim_students s ON f.student_id = s.student_id
GROUP BY family_income_bracket ORDER BY overdue_lakhs DESC
""", conn)

bars_inc = ax_inc.bar(df_inc['family_income_bracket'], df_inc['overdue_lakhs'], color=[ACCENT_ROSE, ACCENT_AMBER, ACCENT_BLUE, ACCENT_INDIGO, ACCENT_EMERALD], width=0.55)
for bar in bars_inc:
    h = bar.get_height()
    ax_inc.text(bar.get_x() + bar.get_width()/2, h + 0.3, f"₹{h:.2f}L", ha='center', fontsize=9, color=TEXT_COLOR, weight='bold')

ax_inc.set_title("Insight 2: Outstanding Fee by Parent Income Bracket (The Mid-Income Squeeze)", fontsize=11.5, weight='bold', pad=12, loc='left')
ax_inc.set_ylabel("Overdue Amount (₹ Lakhs)", fontsize=9.5, color=MUTED_TEXT)
ax_inc.set_ylim(0, 20)
ax_inc.grid(True, color=GRID_COLOR, linestyle=':', alpha=0.7)

# Visual 2: Payment Mode Breakdown (Row 2 to 6, Col 6 to 12)
ax_pay = fig2.add_subplot(gs2[2:6, 6:12])
ax_pay.set_facecolor(PANEL_COLOR)
for spine in ax_pay.spines.values():
    spine.set_color(GRID_COLOR)

df_pay = pd.read_sql("""
SELECT COALESCE(payment_mode, 'Unpaid (Defaulter)') as pmode,
       ROUND(SUM(amount_paid)/100000.0, 2) as collected_lakhs
FROM fact_fees GROUP BY pmode ORDER BY collected_lakhs DESC
""", conn)

bars_pay = ax_pay.barh(df_pay['pmode'], df_pay['collected_lakhs'], color=ACCENT_CYAN, height=0.55)
ax_pay.invert_yaxis()
for bar in bars_pay:
    w = bar.get_width()
    ax_pay.text(w + 3, bar.get_y() + bar.get_height()/2, f"₹{w:.1f}L", va='center', fontsize=9, color=TEXT_COLOR, weight='semibold')

ax_pay.set_title("Collection Channel Mix (₹ Lakhs Settled)", fontsize=11.5, weight='bold', pad=12, loc='left')
ax_pay.set_xlabel("Settled Amount (₹ Lakhs)", fontsize=9.5, color=MUTED_TEXT)
ax_pay.set_xlim(0, 270)
ax_pay.grid(True, color=GRID_COLOR, linestyle=':', alpha=0.7)

# Visual 3: Top 10 Defaulter Classes (Row 6 to 10, Col 0 to 12)
ax_cls_def = fig2.add_subplot(gs2[6:10, 0:12])
ax_cls_def.set_facecolor(PANEL_COLOR)
for spine in ax_cls_def.spines.values():
    spine.set_color(GRID_COLOR)

df_top10 = pd.read_sql("""
SELECT c.class_id || ' (Gr ' || c.grade_level || ')' as class_label,
       ROUND(SUM(f.balance_due)/1000.0, 1) as overdue_k,
       SUM(CASE WHEN f.payment_status = 'Overdue Defaulter' THEN 1 ELSE 0 END) as defaulters
FROM fact_fees f JOIN dim_classes c ON f.class_id = c.class_id
GROUP BY c.class_id ORDER BY overdue_k DESC LIMIT 10
""", conn)

x_cls = np.arange(len(df_top10))
ax_cls_def.bar(x_cls, df_top10['overdue_k'], color=ACCENT_ROSE, width=0.5, alpha=0.9, label="Overdue Amount (₹k)")
ax_cls_def.plot(x_cls, df_top10['defaulters'] * 25, color=ACCENT_AMBER, marker='o', linewidth=2, label="Defaulter Invoices Count (scaled)")

for i in range(len(df_top10)):
    ax_cls_def.text(x_cls[i], df_top10['overdue_k'][i] + 7, f"₹{df_top10['overdue_k'][i]:.0f}k", 
                    ha='center', fontsize=8.5, color=TEXT_COLOR, weight='bold')

ax_cls_def.set_title("Insight 1: Top 10 Defaulter Classes Ranked by Total Unpaid Balance (Class 12A & 10B Lead)", 
                     fontsize=12, weight='bold', pad=12, loc='left')
ax_cls_def.set_xticks(x_cls)
ax_cls_def.set_xticklabels(df_top10['class_label'], fontsize=9, rotation=15)
ax_cls_def.set_ylabel("Overdue Balance (₹ in Thousands)", fontsize=9.5, color=MUTED_TEXT)
ax_cls_def.set_ylim(0, 360)
ax_cls_def.grid(True, color=GRID_COLOR, linestyle=':', alpha=0.7)
ax_cls_def.legend(loc="upper right", facecolor=PANEL_COLOR, edgecolor=GRID_COLOR, fontsize=9)

screen2_path = os.path.join(SCREENSHOTS_DIR, "fee_defaulters_deepdive.png")
fig2.savefig(screen2_path, facecolor=BG_COLOR, bbox_inches='tight')
plt.close(fig2)
print(f"✅ Saved Screen 2: {screen2_path}")


# ==============================================================================
# SCREEN 3: ACADEMIC PERFORMANCE & DUAL-RISK MATRIX
# ==============================================================================
print("🎨 Rendering Screen 3: Academic Performance & Dual-Risk Matrix...")
fig3 = plt.figure(figsize=(19.2, 10.8), dpi=100, facecolor=BG_COLOR)
gs3 = GridSpec(10, 12, figure=fig3, hspace=0.6, wspace=0.45, left=0.04, right=0.96, top=0.92, bottom=0.06)

fig3.text(0.04, 0.955, "EDUMANAGE ANALYTICS  |  ACADEMIC PERFORMANCE & DUAL AT-RISK MATRIX", 
          fontsize=18, weight='bold', color=TEXT_COLOR)
fig3.text(0.04, 0.935, "Cross-Domain Early Warning System  •  Subject Scoring Trajectories  •  Intervention Priorities", 
          fontsize=10.5, color=ACCENT_EMERALD)

# Top KPI Cards
ax3_kpi1 = fig3.add_subplot(gs3[0:2, 0:3])
draw_kpi_card(ax3_kpi1, "Overall Pass Rate", "96.2%", "10,766 Papers Evaluated", ACCENT_EMERALD)

ax3_kpi2 = fig3.add_subplot(gs3[0:2, 3:6])
draw_kpi_card(ax3_kpi2, "Average Score", "67.8 / 100", "Across All Grades & Subjects", ACCENT_BLUE)

ax3_kpi3 = fig3.add_subplot(gs3[0:2, 6:9])
draw_kpi_card(ax3_kpi3, "Math & Science Failures", "179 Exams", "Highest Failure Subjects", ACCENT_ROSE)

ax3_kpi4 = fig3.add_subplot(gs3[0:2, 9:12])
draw_kpi_card(ax3_kpi4, "Immediate Counseling", "8 Students", "Critical Dual-Risk Cohort", ACCENT_ROSE)

# Visual 1: Subject Average Marks & Pass % (Row 2 to 6, Col 0 to 6)
ax_subj = fig3.add_subplot(gs3[2:6, 0:6])
ax_subj.set_facecolor(PANEL_COLOR)
for spine in ax_subj.spines.values():
    spine.set_color(GRID_COLOR)

df_subj = pd.read_sql("""
SELECT subject, ROUND(AVG(marks_obtained), 1) as avg_score
FROM fact_academic_performance GROUP BY subject ORDER BY avg_score ASC LIMIT 8
""", conn)

bars_s = ax_subj.barh(df_subj['subject'], df_subj['avg_score'], color=ACCENT_BLUE, height=0.55)
for bar in bars_s:
    w = bar.get_width()
    ax_subj.text(w + 1, bar.get_y() + bar.get_height()/2, f"{w:.1f}", va='center', fontsize=9, color=TEXT_COLOR, weight='semibold')

ax_subj.set_title("Insight 5: STEM Scoring Bottleneck (Lowest Subject Averages)", fontsize=11.5, weight='bold', pad=12, loc='left')
ax_subj.set_xlabel("Average Marks (Out of 100)", fontsize=9.5, color=MUTED_TEXT)
ax_subj.set_xlim(50, 80)
ax_subj.grid(True, color=GRID_COLOR, linestyle=':', alpha=0.7)

# Visual 2: Term 1 vs Term 2 Marks Comparison (Row 2 to 6, Col 6 to 12)
ax_term = fig3.add_subplot(gs3[2:6, 6:12])
ax_term.set_facecolor(PANEL_COLOR)
for spine in ax_term.spines.values():
    spine.set_color(GRID_COLOR)

df_term = pd.read_sql("""
SELECT term, ROUND(AVG(marks_obtained), 2) as avg_marks,
       SUM(CASE WHEN grade_letter = 'A+' THEN 1 ELSE 0 END) as a_plus_count,
       SUM(CASE WHEN is_passed = 0 THEN 1 ELSE 0 END) as fail_count
FROM fact_academic_performance GROUP BY term
""", conn)

t_x = np.array([0, 1])
ax_term.bar(t_x - 0.15, df_term['avg_marks'], width=0.3, label="Term Avg Marks", color=ACCENT_INDIGO)
ax_term.bar(t_x + 0.15, df_term['a_plus_count'] / 10.0, width=0.3, label="A+ Distinctions (/10)", color=ACCENT_EMERALD)

for i in range(len(df_term)):
    ax_term.text(t_x[i] - 0.15, df_term['avg_marks'][i] + 1.5, f"{df_term['avg_marks'][i]:.1f}", ha='center', fontsize=9, color=TEXT_COLOR, weight='bold')

ax_term.set_title("Term-over-Term Progression (Midterm vs Final)", fontsize=11.5, weight='bold', pad=12, loc='left')
ax_term.set_xticks(t_x)
ax_term.set_xticklabels(df_term['term'], fontsize=9.5)
ax_term.set_ylim(0, 85)
ax_term.grid(True, color=GRID_COLOR, linestyle=':', alpha=0.7)
ax_term.legend(loc="upper right", facecolor=PANEL_COLOR, edgecolor=GRID_COLOR, fontsize=9)

# Visual 3: Dual At-Risk Quad Matrix (Scatter Plot of Attendance vs Academic Marks) (Row 6 to 10, Col 0 to 12)
ax_scatter = fig3.add_subplot(gs3[6:10, 0:12])
ax_scatter.set_facecolor(PANEL_COLOR)
for spine in ax_scatter.spines.values():
    spine.set_color(GRID_COLOR)

df_matrix = pd.read_sql("""
WITH att AS (SELECT student_id, AVG(attendance_pct) as att_rate FROM fact_attendance_monthly GROUP BY student_id),
     acad AS (SELECT student_id, AVG(marks_obtained) as acad_score FROM fact_academic_performance GROUP BY student_id),
     fees AS (SELECT student_id, SUM(balance_due) as overdue, SUM(CASE WHEN payment_status = 'Overdue Defaulter' THEN 1 ELSE 0 END) as def_count FROM fact_fees GROUP BY student_id)
SELECT s.student_id, att.att_rate, acad.acad_score, fees.overdue, fees.def_count,
       CASE WHEN att.att_rate < 75.0 AND fees.def_count > 0 THEN 1 ELSE 0 END as is_critical_dual_risk
FROM dim_students s
JOIN att ON s.student_id = att.student_id
JOIN acad ON s.student_id = acad.student_id
JOIN fees ON s.student_id = fees.student_id
""", conn)

# Plot Normal vs At-Risk
normal = df_matrix[df_matrix['is_critical_dual_risk'] == 0]
critical = df_matrix[df_matrix['is_critical_dual_risk'] == 1]

ax_scatter.scatter(normal['att_rate'], normal['acad_score'], color=ACCENT_BLUE, alpha=0.45, s=28, label="Standard Cohort")
ax_scatter.scatter(critical['att_rate'], critical['acad_score'], color=ACCENT_ROSE, s=130, edgecolors='#FFFFFF', linewidth=2, label="Critical Dual-Risk Cohort (8 Students)", zorder=5)

# Quadrant Lines
ax_scatter.axvline(75.0, color=ACCENT_ROSE, linestyle='--', linewidth=1.5, alpha=0.8)
ax_scatter.axhline(50.0, color=ACCENT_AMBER, linestyle='--', linewidth=1.5, alpha=0.8)

# Highlight Red Danger Zone
rect = patches.Rectangle((40, 20), 35, 30, linewidth=0, facecolor=ACCENT_ROSE, alpha=0.15)
ax_scatter.add_patch(rect)
ax_scatter.text(57, 30, "CRITICAL INTERVENTION ZONE\n(Low Attendance + Fee Defaulters)", color=ACCENT_ROSE, fontsize=10, weight='bold', ha='center')

ax_scatter.set_title("Insight 4: Cross-Domain Dual-Risk Quadrant (Attendance % vs Academic Performance)", fontsize=12, weight='bold', pad=12, loc='left')
ax_scatter.set_xlabel("Annual Attendance Percentage (%)", fontsize=10, color=MUTED_TEXT)
ax_scatter.set_ylabel("Academic Marks Average", fontsize=10, color=MUTED_TEXT)
ax_scatter.set_xlim(45, 100)
ax_scatter.set_ylim(25, 95)
ax_scatter.grid(True, color=GRID_COLOR, linestyle=':', alpha=0.7)
ax_scatter.legend(loc="upper left", facecolor=PANEL_COLOR, edgecolor=GRID_COLOR, fontsize=9.5)

screen3_path = os.path.join(SCREENSHOTS_DIR, "academic_and_at_risk.png")
fig3.savefig(screen3_path, facecolor=BG_COLOR, bbox_inches='tight')
plt.close(fig3)
print(f"✅ Saved Screen 3: {screen3_path}")

conn.close()

# ==============================================================================
# 4. COMPILE INTO HIGH-RESOLUTION EXECUTIVE PDF REPORT
# ==============================================================================
print("📄 Generating Unified Executive Dashboard PDF...")
pdf_path = os.path.join(DASHBOARD_DIR, "EduManage_School_Analytics_Dashboard.pdf")

# Standard Letter Landscape: 792 x 612 pt
pdf_canvas = canvas.Canvas(pdf_path, pagesize=landscape(letter))
page_w, page_h = landscape(letter)

screens = [
    ("Executive KPI Overview", screen1_path),
    ("Fee Collections & Defaulters Deep Dive", screen2_path),
    ("Academic Performance & Dual At-Risk Matrix", screen3_path)
]

for title, img_path in screens:
    # Draw image fitted to page
    pdf_canvas.drawImage(img_path, 0, 0, width=page_w, height=page_h)
    pdf_canvas.showPage()

pdf_canvas.save()
print(f"✅ Successfully compiled Executive PDF: {pdf_path}")
