-- ============================================================================
-- EduManage School Analytics - Production SQL Analytical Queries
-- Database: SQLite / PostgreSQL compatible
-- Purpose: Extract 10 Core KPIs & Answers to Management Questions
-- ============================================================================

-- ----------------------------------------------------------------------------
-- KPI 1: OVERALL FINANCIAL HEALTH (Revenue, Collections, Default Balance, Rate)
-- ----------------------------------------------------------------------------
SELECT 
    COUNT(invoice_id) AS total_invoices_issued,
    ROUND(SUM(amount_due), 2) AS total_billed_inr,
    ROUND(SUM(amount_paid), 2) AS total_collected_inr,
    ROUND(SUM(balance_due), 2) AS total_overdue_defaulter_inr,
    ROUND(SUM(amount_paid) * 100.0 / SUM(amount_due), 2) AS fee_collection_rate_pct
FROM fact_fees;

-- ----------------------------------------------------------------------------
-- KPI 2: QUARTERLY FEE COLLECTION RUN RATE & MOMENTUM
-- ----------------------------------------------------------------------------
SELECT 
    quarter,
    COUNT(invoice_id) AS total_invoices,
    ROUND(SUM(amount_due), 2) AS billed_amount,
    ROUND(SUM(amount_paid), 2) AS collected_amount,
    ROUND(SUM(balance_due), 2) AS overdue_balance,
    ROUND(SUM(amount_paid) * 100.0 / SUM(amount_due), 2) AS collection_efficiency_pct
FROM fact_fees
GROUP BY quarter
ORDER BY due_date;

-- ----------------------------------------------------------------------------
-- KPI 3: FEE DEFAULTERS BY CLASS & GRADE RANKING (Insight 1)
-- Identifies top 10 classes contributing highest revenue default
-- ----------------------------------------------------------------------------
SELECT 
    c.grade_level,
    c.class_id,
    c.stream,
    c.class_teacher,
    COUNT(f.invoice_id) AS total_invoices,
    SUM(CASE WHEN f.payment_status = 'Overdue Defaulter' THEN 1 ELSE 0 END) AS defaulter_invoices_count,
    ROUND(SUM(CASE WHEN f.payment_status = 'Overdue Defaulter' THEN 1 ELSE 0 END) * 100.0 / COUNT(f.invoice_id), 2) AS defaulter_percentage,
    ROUND(SUM(f.balance_due), 2) AS total_overdue_inr
FROM fact_fees f
JOIN dim_classes c ON f.class_id = c.class_id
GROUP BY c.grade_level, c.class_id, c.stream, c.class_teacher
ORDER BY total_overdue_inr DESC
LIMIT 10;

-- ----------------------------------------------------------------------------
-- KPI 4: PARENT INCOME BRACKET VS DEFAULT RISK (Insight 2)
-- Uncovers the 'Mid-Income Squeeze' phenomenon
-- ----------------------------------------------------------------------------
SELECT 
    s.family_income_bracket,
    COUNT(DISTINCT s.student_id) AS enrolled_students,
    COUNT(f.invoice_id) AS total_invoices,
    SUM(CASE WHEN f.payment_status = 'Overdue Defaulter' THEN 1 ELSE 0 END) AS defaulter_count,
    ROUND(SUM(CASE WHEN f.payment_status = 'Overdue Defaulter' THEN 1 ELSE 0 END) * 100.0 / COUNT(f.invoice_id), 2) AS default_rate_pct,
    ROUND(SUM(f.balance_due), 2) AS total_uncollected_inr,
    ROUND(SUM(f.balance_due) * 100.0 / (SELECT SUM(balance_due) FROM fact_fees), 2) AS pct_share_of_total_overdue
FROM fact_fees f
JOIN dim_students s ON f.student_id = s.student_id
GROUP BY s.family_income_bracket
ORDER BY total_uncollected_inr DESC;

-- ----------------------------------------------------------------------------
-- KPI 5: PREFERRED PAYMENT MODES & DEFAULT CORRELATION
-- ----------------------------------------------------------------------------
SELECT 
    COALESCE(payment_mode, 'Unpaid (Defaulter)') AS payment_channel,
    COUNT(*) AS transaction_count,
    ROUND(SUM(amount_paid), 2) AS volume_inr,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM fact_fees), 2) AS transaction_share_pct
FROM fact_fees
GROUP BY payment_channel
ORDER BY volume_inr DESC;

-- ----------------------------------------------------------------------------
-- KPI 6: MONTHLY ATTENDANCE TRAJECTORY & CHRONIC ABSENTEEISM (Insight 3)
-- ----------------------------------------------------------------------------
SELECT 
    academic_month,
    SUM(days_present) AS total_days_attended,
    SUM(working_days) AS total_scheduled_days,
    ROUND(SUM(days_present) * 100.0 / SUM(working_days), 2) AS overall_attendance_pct,
    SUM(is_chronic_absentee) AS chronic_absentee_instances,
    ROUND(SUM(is_chronic_absentee) * 100.0 / COUNT(*), 2) AS chronic_absentee_rate_pct
FROM fact_attendance_monthly
GROUP BY academic_month
ORDER BY academic_month ASC;

-- ----------------------------------------------------------------------------
-- KPI 7: GRADE-WISE ATTENDANCE STABILITY
-- ----------------------------------------------------------------------------
SELECT 
    c.grade_level,
    ROUND(AVG(a.attendance_pct), 2) AS avg_attendance_pct,
    SUM(a.is_chronic_absentee) AS chronic_absentee_records,
    ROUND(SUM(a.days_late) * 1.0 / COUNT(DISTINCT a.student_id), 2) AS avg_late_days_per_student
FROM fact_attendance_monthly a
JOIN dim_classes c ON a.class_id = c.class_id
GROUP BY c.grade_level
ORDER BY c.grade_level ASC;

-- ----------------------------------------------------------------------------
-- KPI 8: CROSS-FUNCTIONAL AT-RISK STUDENTS (Attendance < 75% + Fee Defaulter)
-- Identifies critical students needing immediate pastoral intervention (Insight 4)
-- ----------------------------------------------------------------------------
WITH student_att_summary AS (
    SELECT 
        student_id, 
        ROUND(AVG(attendance_pct), 2) AS annual_avg_att_pct
    FROM fact_attendance_monthly
    GROUP BY student_id
),
student_fee_summary AS (
    SELECT 
        student_id, 
        ROUND(SUM(balance_due), 2) AS total_pending_fee,
        SUM(CASE WHEN payment_status = 'Overdue Defaulter' THEN 1 ELSE 0 END) AS overdue_invoices
    FROM fact_fees
    GROUP BY student_id
)
SELECT 
    s.student_id,
    s.first_name || ' ' || s.last_name AS student_name,
    s.class_id,
    s.family_income_bracket,
    s.parent_name,
    s.contact_phone,
    att.annual_avg_att_pct,
    fee.total_pending_fee,
    fee.overdue_invoices
FROM dim_students s
JOIN student_att_summary att ON s.student_id = att.student_id
JOIN student_fee_summary fee ON s.student_id = fee.student_id
WHERE att.annual_avg_att_pct < 75.0 
  AND fee.overdue_invoices > 0
ORDER BY fee.total_pending_fee DESC;

-- ----------------------------------------------------------------------------
-- KPI 9: ACADEMIC PERFORMANCE & SUBJECT BOTTLENECKS (Insight 5)
-- ----------------------------------------------------------------------------
SELECT 
    subject,
    COUNT(exam_id) AS total_papers_evaluated,
    ROUND(AVG(marks_obtained), 2) AS average_score,
    ROUND(MIN(marks_obtained), 1) AS min_score,
    ROUND(MAX(marks_obtained), 1) AS max_score,
    SUM(CASE WHEN is_passed = 1 THEN 1 ELSE 0 END) AS passed_count,
    SUM(CASE WHEN is_passed = 0 THEN 1 ELSE 0 END) AS failed_count,
    ROUND(SUM(CASE WHEN is_passed = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(exam_id), 2) AS pass_percentage
FROM fact_academic_performance
GROUP BY subject
ORDER BY average_score ASC;

-- ----------------------------------------------------------------------------
-- KPI 10: TERM-OVER-TERM ACADEMIC TRAJECTORY (Term 1 vs Term 2)
-- ----------------------------------------------------------------------------
SELECT 
    term,
    ROUND(AVG(marks_obtained), 2) AS term_avg_marks,
    ROUND(SUM(CASE WHEN is_passed = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(exam_id), 2) AS term_pass_rate_pct,
    SUM(CASE WHEN marks_obtained >= 80.0 THEN 1 ELSE 0 END) AS distinction_count
FROM fact_academic_performance
GROUP BY term
ORDER BY term ASC;
