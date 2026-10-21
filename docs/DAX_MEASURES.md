# Power BI DAX Measures Library for EduManage

Ready-to-use DAX formulas designed for Power BI Desktop. Create a dedicated measure table called `_KeyMeasures` in Power BI to organize them cleanly.

---

## 💰 1. Financial & Fee Collection Measures

### [Total Fee Invoiced]
```dax
Total Fee Invoiced = SUM(fact_fees[amount_due])
```

### [Total Fee Collected]
```dax
Total Fee Collected = SUM(fact_fees[amount_paid])
```

### [Total Outstanding Due]
```dax
Total Outstanding Due = SUM(fact_fees[balance_due])
```

### [Fee Collection Rate %]
```dax
Fee Collection Rate % = 
DIVIDE(
    [Total Fee Collected],
    [Total Fee Invoiced],
    0
)
```
*(Format as Percentage: `94.6%`)*

### [Fee Defaulter Invoices Count]
```dax
Fee Defaulter Invoices Count = 
CALCULATE(
    COUNTROWS(fact_fees),
    fact_fees[payment_status] = "Overdue Defaulter"
)
```

### [Fee Defaulter Rate %]
```dax
Fee Defaulter Rate % = 
DIVIDE(
    [Fee Defaulter Invoices Count],
    COUNTROWS(fact_fees),
    0
)
```

---

## 📅 2. Attendance & Operations Measures

### [Total Student Headcount]
```dax
Total Students = DISTINCTCOUNT(dim_students[student_id])
```

### [Average Attendance %]
```dax
Average Attendance % = 
DIVIDE(
    SUM(fact_attendance_monthly[days_present]),
    SUM(fact_attendance_monthly[working_days]),
    0
)
```

### [Chronic Absentee Students Count]
*(Students with average annual attendance below 75%)*
```dax
Chronic Absentee Students Count = 
CALCULATE(
    DISTINCTCOUNT(fact_attendance_monthly[student_id]),
    FILTER(
        VALUES(dim_students[student_id]),
        [Average Attendance %] < 0.75
    )
)
```

### [Chronic Absenteeism Rate %]
```dax
Chronic Absenteeism Rate % = 
DIVIDE(
    [Chronic Absentee Students Count],
    [Total Students],
    0
)
```

---

## 🎓 3. Academic Performance Measures

### [Overall Average Marks]
```dax
Average Marks = AVERAGE(fact_academic_performance[marks_obtained])
```

### [Subject Pass Rate %]
```dax
Subject Pass Rate % = 
DIVIDE(
    CALCULATE(COUNTROWS(fact_academic_performance), fact_academic_performance[is_passed] = TRUE()),
    COUNTROWS(fact_academic_performance),
    0
)
```

### [Total Failed Examinations]
```dax
Total Failed Exams = 
CALCULATE(
    COUNTROWS(fact_academic_performance),
    fact_academic_performance[is_passed] = FALSE()
)
```

---

## 🚨 4. Cross-Functional Risk Measures (Retention & Defaulters)

### [At-Risk Students Count]
*(Students who have BOTH Attendance < 75% AND at least 1 Overdue Fee Invoice)*
```dax
At-Risk Students Count = 
COUNTROWS(
    FILTER(
        VALUES(dim_students[student_id]),
        [Average Attendance %] < 0.75 &&
        [Fee Defaulter Invoices Count] > 0
    )
)
```

---

## 🎨 Recommended Power BI Layout & Visualizations

| Visual Area | Visual Type | Fields / Measures Used |
|---|---|---|
| **Top KPI Cards Ribbon** | Multi-row Card / New Card | `Total Students`, `Total Fee Invoiced`, `Total Fee Collected`, `Fee Collection Rate %`, `Average Attendance %`, `At-Risk Students` |
| **Fee Collection by Quarter** | Clustered Column Chart | X-axis: `quarter`, Y-axis: `Total Fee Invoiced` & `Total Fee Collected` |
| **Defaulters by Grade & Class** | Horizontal Stacked Bar Chart | Y-axis: `class_id` or `grade_level`, X-axis: `Total Outstanding Due`, Legend: `payment_status` |
| **Attendance Monthly Trendline** | Area / Line Chart | X-axis: `academic_month`, Y-axis: `Average Attendance %` (with constant reference line at 75%) |
| **Academic Performance by Subject** | Bar Chart with Pass % line | X-axis: `subject`, Column: `Average Marks`, Line: `Subject Pass Rate %` |
| **Defaulters by Income Bracket** | Donut / Tree Map | Category: `family_income_bracket`, Values: `Total Outstanding Due` |
| **Interactive Slicers** | Dropdown / Tile Slicers | Grade Level (1-12), Stream (General/Sci/Comm), Income Bracket, Payment Mode |
