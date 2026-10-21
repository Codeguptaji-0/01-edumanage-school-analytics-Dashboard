"""
Calculates exact KPI figures and answers key business questions from EduManage SQLite DB.
Outputs summary metrics for DAX validation and Executive Insights writing.
"""

import os
import sys
import sqlite3
import pandas as pd

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "edumanage.db")
conn = sqlite3.connect(DB_PATH)

print("="*60)
print("1. OVERALL OPERATIONAL & FINANCIAL KPIS")
print("="*60)

query_overall_fees = """
SELECT 
    COUNT(invoice_id) as total_invoices,
    ROUND(SUM(amount_due), 2) as total_receivable,
    ROUND(SUM(amount_paid), 2) as total_collected,
    ROUND(SUM(balance_due), 2) as total_overdue_defaulter_amount,
    ROUND(SUM(amount_paid) * 100.0 / SUM(amount_due), 2) as overall_collection_rate_pct
FROM fact_fees;
"""
df_fee_kpis = pd.read_sql(query_overall_fees, conn)
print(df_fee_kpis.to_string(index=False))

print("\n" + "="*60)
print("2. FEE DEFAULTERS BY CLASS & GRADE (Where are defaulters highest?)")
print("="*60)

query_class_defaulters = """
SELECT 
    c.grade_level,
    c.class_id,
    COUNT(f.invoice_id) as total_invoices,
    SUM(CASE WHEN f.payment_status = 'Overdue Defaulter' THEN 1 ELSE 0 END) as defaulter_invoices,
    ROUND(SUM(CASE WHEN f.payment_status = 'Overdue Defaulter' THEN 1 ELSE 0 END) * 100.0 / COUNT(f.invoice_id), 2) as defaulter_rate_pct,
    ROUND(SUM(f.balance_due), 2) as overdue_amount
FROM fact_fees f
JOIN dim_classes c ON f.class_id = c.class_id
GROUP BY c.grade_level, c.class_id
ORDER BY overdue_amount DESC
LIMIT 10;
"""
print(pd.read_sql(query_class_defaulters, conn).to_string(index=False))

print("\n" + "="*60)
print("3. FEE DEFAULTERS BY PARENT INCOME BRACKET")
print("="*60)

query_income_defaulters = """
SELECT 
    s.family_income_bracket,
    COUNT(DISTINCT s.student_id) as total_students,
    COUNT(f.invoice_id) as total_invoices,
    SUM(CASE WHEN f.payment_status = 'Overdue Defaulter' THEN 1 ELSE 0 END) as defaulter_count,
    ROUND(SUM(CASE WHEN f.payment_status = 'Overdue Defaulter' THEN 1 ELSE 0 END) * 100.0 / COUNT(f.invoice_id), 2) as default_rate_pct,
    ROUND(SUM(f.balance_due), 2) as total_uncollected_rupees
FROM fact_fees f
JOIN dim_students s ON f.student_id = s.student_id
GROUP BY s.family_income_bracket
ORDER BY total_uncollected_rupees DESC;
"""
print(pd.read_sql(query_income_defaulters, conn).to_string(index=False))

print("\n" + "="*60)
print("4. ATTENDANCE TRENDS & CHRONIC ABSENTEEISM")
print("="*60)

query_att_trends = """
SELECT 
    academic_month,
    ROUND(AVG(attendance_pct), 2) as avg_attendance_pct,
    SUM(is_chronic_absentee) as chronic_absentee_records,
    ROUND(SUM(is_chronic_absentee) * 100.0 / COUNT(*), 2) as chronic_rate_pct
FROM fact_attendance_monthly
GROUP BY academic_month
ORDER BY academic_month;
"""
print(pd.read_sql(query_att_trends, conn).to_string(index=False))

print("\n" + "="*60)
print("5. AT-RISK STUDENTS (Low Attendance + Fee Overdue)")
print("="*60)

query_at_risk = """
WITH student_att AS (
    SELECT student_id, AVG(attendance_pct) as avg_att
    FROM fact_attendance_monthly
    GROUP BY student_id
),
student_fees AS (
    SELECT student_id, SUM(balance_due) as total_unpaid,
           SUM(CASE WHEN payment_status = 'Overdue Defaulter' THEN 1 ELSE 0 END) as overdue_invoices
    FROM fact_fees
    GROUP BY student_id
)
SELECT 
    COUNT(s.student_id) as total_students,
    SUM(CASE WHEN a.avg_att < 75.0 AND f.overdue_invoices > 0 THEN 1 ELSE 0 END) as critical_at_risk_students,
    ROUND(SUM(CASE WHEN a.avg_att < 75.0 AND f.overdue_invoices > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(s.student_id), 2) as at_risk_pct
FROM dim_students s
JOIN student_att a ON s.student_id = a.student_id
JOIN student_fees f ON s.student_id = f.student_id;
"""
print(pd.read_sql(query_at_risk, conn).to_string(index=False))

print("\n" + "="*60)
print("6. ACADEMIC PERFORMANCE SUMMARY")
print("="*60)

query_academics = """
SELECT 
    subject,
    ROUND(AVG(marks_obtained), 2) as avg_marks,
    ROUND(SUM(CASE WHEN is_passed = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as pass_rate_pct,
    SUM(CASE WHEN grade_letter = 'F (Fail)' THEN 1 ELSE 0 END) as failed_exams_count
FROM fact_academic_performance
GROUP BY subject
ORDER BY avg_marks ASC;
"""
print(pd.read_sql(query_academics, conn).to_string(index=False))

conn.close()
