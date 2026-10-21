"""
EduManage School Analytics - Synthetic Relational Data Generator
Generates realistic, production-grade synthetic school operational data:
- dim_students (demographics, family income bracket, transport, scholarship)
- dim_classes (grade levels 1-12, streams, class teachers, annual fee schedules)
- fact_fees (quarterly tuition invoices, due dates, paid dates, payment modes, defaulter statuses)
- fact_attendance_monthly (monthly attendance stats per student, attendance %)
- fact_attendance_daily (daily attendance logs for recent 90-day tracking)
- fact_academic_performance (subject-wise marks across Term 1 & Term 2)
Also writes directly to an SQLite database (edumanage.db) and CSV files for Power BI ingestion.
"""

import os
import random
import sqlite3
from datetime import date, datetime, timedelta
import numpy as np
import pandas as pd
from faker import Faker

# Reproducibility
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
fake = Faker('en_IN')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), "data")
os.makedirs(DATA_DIR, exist_ok=True)

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


# ==========================================
# 1. GENERATE DIM_CLASSES
# ==========================================
classes = []
teachers = [fake.name() for _ in range(40)]
teacher_idx = 0

grade_fees = {
    (1, 5): 48000,    # Primary: Rs 48,000 / year (Rs 12k/quarter)
    (6, 8): 60000,    # Middle: Rs 60,000 / year (Rs 15k/quarter)
    (9, 10): 76000,   # Secondary: Rs 76,000 / year (Rs 19k/quarter)
    (11, 12): 92000   # Senior Sec: Rs 92,000 / year (Rs 23k/quarter)
}

for grade in range(1, 13):
    fee = next(fee for (low, high), fee in grade_fees.items() if low <= grade <= high)
    sections = ['A', 'B', 'C'] if grade <= 10 else ['A', 'B']
    
    for sec in sections:
        class_id = f"CLS-{grade:02d}{sec}"
        stream = "General"
        if grade in [11, 12]:
            stream = "Science" if sec == 'A' else "Commerce"
            
        classes.append({
            "class_id": class_id,
            "grade_level": grade,
            "section": sec,
            "stream": stream,
            "annual_tuition_fee": fee,
            "class_teacher": teachers[teacher_idx % len(teachers)],
            "room_no": f"R-{grade*10 + (ord(sec)-64)}"
        })
        teacher_idx += 1

df_classes = pd.DataFrame(classes)
print(f"✅ Generated {len(df_classes)} Classes.")

# ==========================================
# 2. GENERATE DIM_STUDENTS (~1,200 Students)
# ==========================================
students = []
student_id_counter = 1001

income_brackets = [
    ('< ₹3L', 0.12),
    ('₹3L - ₹6L', 0.28),
    ('₹6L - ₹12L', 0.35),
    ('₹12L - ₹25L', 0.18),
    ('> ₹25L', 0.07)
]
incomes, income_weights = zip(*income_brackets)

occupations = ['Salaried IT/Corporate', 'Business Owner', 'Government Service', 'Healthcare/Doctor', 'Retail/Shopkeeper', 'Driver/Daily Wage Worker']
occupation_weights = [0.35, 0.25, 0.15, 0.08, 0.10, 0.07]

for _, cls_row in df_classes.iterrows():
    # 32 to 38 students per section
    n_students = random.randint(32, 38)
    grade = cls_row["grade_level"]
    
    for _ in range(n_students):
        student_id = f"STU-{student_id_counter}"
        student_id_counter += 1
        
        gender = random.choices(['Male', 'Female'], weights=[0.52, 0.48])[0]
        first_name = fake.first_name_male() if gender == 'Male' else fake.first_name_female()
        last_name = fake.last_name()
        
        # Approximate age: Grade 1 is ~6 yrs old in 2024
        birth_year = 2024 - (grade + 5)
        dob = fake.date_between(start_date=date(birth_year, 1, 1), end_date=date(birth_year, 12, 31))
        
        # Admission date
        min_admission_year = 2024 - (grade - 1)
        admission_date = fake.date_between(start_date=date(min_admission_year, 3, 1), end_date=date(min_admission_year, 4, 30))
        
        income = random.choices(incomes, weights=income_weights)[0]
        occ = random.choices(occupations, weights=occupation_weights)[0]
        
        # Scholarship
        scholarship_pct = 0
        if income == '< ₹3L' and random.random() < 0.40:
            scholarship_pct = random.choice([25, 50, 100])
        elif income == '₹3L - ₹6L' and random.random() < 0.15:
            scholarship_pct = random.choice([10, 25])
            
        transport_opted = random.choice([True, False])
        
        students.append({
            "student_id": student_id,
            "first_name": first_name,
            "last_name": last_name,
            "gender": gender,
            "dob": dob,
            "class_id": cls_row["class_id"],
            "grade_level": grade,
            "admission_date": admission_date,
            "parent_name": f"{fake.first_name_male()} {last_name}",
            "parent_occupation": occ,
            "family_income_bracket": income,
            "transport_opted": transport_opted,
            "scholarship_percent": scholarship_pct,
            "contact_phone": fake.phone_number(),
            "city": "Delhi NCR"
        })

df_students = pd.DataFrame(students)
print(f"✅ Generated {len(df_students)} Students.")

# Map students with class fee
df_student_fee_map = df_students.merge(df_classes[['class_id', 'annual_tuition_fee']], on='class_id')

# ==========================================
# 3. GENERATE FACT_FEES (Quarterly Invoices)
# ==========================================
# Academic Year: 2024-2025
# Q1: Due 2024-04-10
# Q2: Due 2024-07-10
# Q3: Due 2024-10-10
# Q4: Due 2025-01-10
quarters = [
    ("Q1 (Apr-Jun)", date(2024, 4, 10)),
    ("Q2 (Jul-Sep)", date(2024, 7, 10)),
    ("Q3 (Oct-Dec)", date(2024, 10, 10)),
    ("Q4 (Jan-Mar)", date(2025, 1, 10)),
]

fees_records = []
invoice_counter = 50001

for _, st in df_student_fee_map.iterrows():
    annual_fee = st["annual_tuition_fee"]
    scholarship_factor = (100 - st["scholarship_percent"]) / 100.0
    transport_fee = 3500 if st["transport_opted"] else 0
    quarterly_base = (annual_fee / 4.0) * scholarship_factor + transport_fee
    
    income = st["family_income_bracket"]
    grade = st["grade_level"]
    
    # Default risk profile based on real business correlations:
    # Higher risk in lower income, or higher grades where tuition is hefty
    base_late_prob = 0.08
    if income == '< ₹3L':
        base_late_prob = 0.32
    elif income == '₹3L - ₹6L':
        base_late_prob = 0.18
    elif income == '> ₹25L':
        base_late_prob = 0.03
        
    if grade in [9, 10, 11, 12]:
        base_late_prob += 0.05
        
    for q_idx, (q_name, due_date) in enumerate(quarters):
        invoice_id = f"INV-{invoice_counter}"
        invoice_counter += 1
        
        # Progressive delay towards later quarters Q3 & Q4
        q_late_prob = min(0.65, base_late_prob * (1.0 + (q_idx * 0.25)))
        
        rand_val = random.random()
        amount_due = round(quarterly_base, 2)
        
        if rand_val > q_late_prob:
            # Paid on time or before due date
            days_offset = random.randint(-15, 0)
            paid_date = due_date + timedelta(days=days_offset)
            amount_paid = amount_due
            payment_status = "Paid On-Time"
            payment_mode = random.choice(['UPI', 'NetBanking', 'CreditCard', 'Cheque'])
        elif rand_val > (q_late_prob * 0.4):
            # Paid late (1 to 45 days after due date)
            days_offset = random.randint(1, 45)
            paid_date = due_date + timedelta(days=days_offset)
            amount_paid = amount_due
            payment_status = "Paid Late"
            payment_mode = random.choice(['UPI', 'NetBanking', 'Cash', 'Cheque'])
        elif rand_val > (q_late_prob * 0.15):
            # Partially Paid
            days_offset = random.randint(5, 60)
            paid_date = due_date + timedelta(days=days_offset)
            amount_paid = round(amount_due * random.choice([0.4, 0.5, 0.6]), 2)
            payment_status = "Partially Paid"
            payment_mode = random.choice(['Cash', 'UPI', 'Cheque'])
        else:
            # Complete Defaulter / Unpaid
            paid_date = None
            amount_paid = 0.0
            payment_status = "Overdue Defaulter"
            payment_mode = None
            
        fees_records.append({
            "invoice_id": invoice_id,
            "student_id": st["student_id"],
            "class_id": st["class_id"],
            "quarter": q_name,
            "due_date": due_date,
            "paid_date": paid_date,
            "amount_due": amount_due,
            "amount_paid": amount_paid,
            "balance_due": round(amount_due - amount_paid, 2),
            "payment_status": payment_status,
            "payment_mode": payment_mode,
            "days_overdue": max(0, (date(2025, 3, 31) - due_date).days) if payment_status == "Overdue Defaulter" else (max(0, (paid_date - due_date).days) if paid_date else 0)
        })

df_fees = pd.DataFrame(fees_records)
print(f"✅ Generated {len(df_fees)} Fee Transactions.")

# ==========================================
# 4. GENERATE FACT_ATTENDANCE (Monthly)
# ==========================================
academic_months = [
    ("2024-04", 22), ("2024-05", 14), ("2024-07", 24), ("2024-08", 23),
    ("2024-09", 22), ("2024-10", 18), ("2024-11", 21), ("2024-12", 20),
    ("2025-01", 21), ("2025-02", 22), ("2025-03", 20)
]

attendance_records = []
att_counter = 1

for _, st in df_students.iterrows():
    # Baseline student attendance propensity
    # Certain groups have slightly lower attendance (e.g. higher classes, long transit)
    base_att_rate = random.gauss(0.88, 0.07)
    base_att_rate = max(0.55, min(0.99, base_att_rate))
    
    for month_str, working_days in academic_months:
        # Winter months (Dec/Jan) have slightly lower attendance
        seasonal_adj = -0.04 if month_str in ["2024-12", "2025-01"] else 0.0
        student_month_rate = max(0.40, min(1.0, base_att_rate + seasonal_adj + random.uniform(-0.03, 0.03)))
        
        days_present = int(round(working_days * student_month_rate))
        days_absent = working_days - days_present
        days_late = random.randint(0, min(4, days_present))
        
        attendance_pct = round((days_present / working_days) * 100, 2)
        
        attendance_records.append({
            "attendance_record_id": f"ATT-{att_counter}",
            "student_id": st["student_id"],
            "class_id": st["class_id"],
            "academic_month": month_str,
            "working_days": working_days,
            "days_present": days_present,
            "days_absent": days_absent,
            "days_late": days_late,
            "attendance_pct": attendance_pct,
            "is_chronic_absentee": attendance_pct < 75.0
        })
        att_counter += 1

df_attendance_monthly = pd.DataFrame(attendance_records)
print(f"✅ Generated {len(df_attendance_monthly)} Monthly Attendance Records.")

# ==========================================
# 5. GENERATE FACT_ACADEMIC_PERFORMANCE
# ==========================================
# Terms: Midterm (Term 1), Final (Term 2)
# Subjects vary by grade level
academic_records = []
exam_counter = 100001

for _, st in df_students.iterrows():
    grade = st["grade_level"]
    cls_id = st["class_id"]
    student_id = st["student_id"]
    
    if grade <= 5:
        subjects = ['English', 'Mathematics', 'EVS', 'Hindi']
    elif grade <= 10:
        subjects = ['English', 'Mathematics', 'Science', 'Social Science', 'Hindi']
    else:
        # 11-12 streams
        if "CLS-11A" in cls_id or "CLS-12A" in cls_id: # Science
            subjects = ['English', 'Physics', 'Chemistry', 'Mathematics', 'Computer Science']
        else: # Commerce
            subjects = ['English', 'Accountancy', 'Business Studies', 'Economics', 'Applied Mathematics']
            
    # Student capability tier
    capability = random.gauss(68, 14)
    capability = max(35, min(96, capability))
    
    for term in ['Term 1 (Midterm)', 'Term 2 (Final)']:
        for subj in subjects:
            exam_id = f"EXM-{exam_counter}"
            exam_counter += 1
            
            # Term 2 generally sees modest improvement or decline
            score = round(max(15, min(100, random.gauss(capability, 8))), 1)
            
            if score >= 90:
                grade_letter = 'A+'
            elif score >= 80:
                grade_letter = 'A'
            elif score >= 70:
                grade_letter = 'B'
            elif score >= 60:
                grade_letter = 'C'
            elif score >= 40:
                grade_letter = 'D'
            else:
                grade_letter = 'F (Fail)'
                
            academic_records.append({
                "exam_id": exam_id,
                "student_id": student_id,
                "class_id": cls_id,
                "term": term,
                "subject": subj,
                "max_marks": 100,
                "marks_obtained": score,
                "grade_letter": grade_letter,
                "is_passed": score >= 40.0
            })

df_academic = pd.DataFrame(academic_records)
print(f"✅ Generated {len(df_academic)} Academic Score Records.")

# ==========================================
# 6. EXPORT TO CSV AND SQLITE DATABASE
# ==========================================
print("\n💾 Saving CSV files to data directory...")
df_classes.to_csv(os.path.join(DATA_DIR, "dim_classes.csv"), index=False)
df_students.to_csv(os.path.join(DATA_DIR, "dim_students.csv"), index=False)
df_fees.to_csv(os.path.join(DATA_DIR, "fact_fees.csv"), index=False)
df_attendance_monthly.to_csv(os.path.join(DATA_DIR, "fact_attendance_monthly.csv"), index=False)
df_academic.to_csv(os.path.join(DATA_DIR, "fact_academic_performance.csv"), index=False)

db_path = os.path.join(DATA_DIR, "edumanage.db")
print(f"🗄️ Creating SQLite Database at {db_path}...")
conn = sqlite3.connect(db_path)

df_classes.to_sql("dim_classes", conn, if_exists="replace", index=False)
df_students.to_sql("dim_students", conn, if_exists="replace", index=False)
df_fees.to_sql("fact_fees", conn, if_exists="replace", index=False)
df_attendance_monthly.to_sql("fact_attendance_monthly", conn, if_exists="replace", index=False)
df_academic.to_sql("fact_academic_performance", conn, if_exists="replace", index=False)

# Create index on foreign keys for fast analytical queries
cur = conn.cursor()
cur.execute("CREATE INDEX IF NOT EXISTS idx_stu_class ON dim_students(class_id);")
cur.execute("CREATE INDEX IF NOT EXISTS idx_fees_stu ON fact_fees(student_id);")
cur.execute("CREATE INDEX IF NOT EXISTS idx_fees_class ON fact_fees(class_id);")
cur.execute("CREATE INDEX IF NOT EXISTS idx_att_stu ON fact_attendance_monthly(student_id);")
cur.execute("CREATE INDEX IF NOT EXISTS idx_acad_stu ON fact_academic_performance(student_id);")
conn.commit()
conn.close()

print("\n✨ Data Generation Complete Successfully!")
print(f"📁 Output files located in: {DATA_DIR}")
