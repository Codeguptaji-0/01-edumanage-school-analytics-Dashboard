"""
Generates a valid Power BI Template (.pbit) and .pbix archive for EduManage.
Includes DataModelSchema (BIM JSON) with tables, relationships, and DAX measures.
"""

import os
import sys
import json
import zipfile

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DASHBOARDS_DIR = os.path.join(os.path.dirname(BASE_DIR), "dashboards")
os.makedirs(DASHBOARDS_DIR, exist_ok=True)

PBIT_PATH = os.path.join(DASHBOARDS_DIR, "EduManage_School_Analytics.pbit")
PBIX_PATH = os.path.join(DASHBOARDS_DIR, "EduManage_School_Analytics.pbix")

# 1. Content Types XML
content_types_xml = """<?xml version="1.0" encoding="utf-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="json" ContentType="application/json" />
  <Default Extension="xml" ContentType="application/xml" />
  <Override PartName="/DataModelSchema" ContentType="application/json" />
  <Override PartName="/Report/Layout" ContentType="application/json" />
  <Override PartName="/Settings" ContentType="application/xml" />
  <Override PartName="/Version" ContentType="text/plain" />
</Types>"""

# 2. Version
version_text = "2.128.1380.0"

# 3. Settings XML
settings_xml = """<?xml version="1.0" encoding="utf-8"?>
<Settings>
  <HideReportSettings>false</HideReportSettings>
</Settings>"""

# 4. Report Layout JSON
report_layout = {
    "id": 1,
    "theme": "Dark",
    "pages": [
        {
            "id": 1,
            "name": "ReportSection1",
            "displayName": "Executive KPI Overview",
            "visuals": [
                {"name": "kpi_ribbon", "type": "card", "x": 20, "y": 20, "width": 1240, "height": 120},
                {"name": "attendance_trend", "type": "lineChart", "x": 20, "y": 160, "width": 720, "height": 340},
                {"name": "quarterly_fees", "type": "columnChart", "x": 760, "y": 160, "width": 500, "height": 340},
                {"name": "top_defaulter_classes", "type": "barChart", "x": 20, "y": 520, "width": 720, "height": 340},
                {"name": "wing_breakdown", "type": "donutChart", "x": 760, "y": 520, "width": 500, "height": 340}
            ]
        },
        {
            "id": 2,
            "name": "ReportSection2",
            "displayName": "Fee Collections & Defaulters Deep Dive",
            "visuals": [
                {"name": "income_bracket_chart", "type": "columnChart", "x": 20, "y": 20, "width": 600, "height": 350},
                {"name": "payment_channel_chart", "type": "barChart", "x": 640, "y": 20, "width": 600, "height": 350},
                {"name": "top_10_defaulter_classes", "type": "comboChart", "x": 20, "y": 390, "width": 1220, "height": 450}
            ]
        },
        {
            "id": 3,
            "name": "ReportSection3",
            "displayName": "Academic & Dual-Risk Matrix",
            "visuals": [
                {"name": "subject_performance", "type": "barChart", "x": 20, "y": 20, "width": 600, "height": 350},
                {"name": "term_comparison", "type": "columnChart", "x": 640, "y": 20, "width": 600, "height": 350},
                {"name": "dual_risk_scatter", "type": "scatterChart", "x": 20, "y": 390, "width": 1220, "height": 450}
            ]
        }
    ]
}

# 5. DataModelSchema JSON (BIM format)
data_model_schema = {
    "name": "EduManage_Model",
    "compatibilityLevel": 1550,
    "model": {
        "culture": "en-IN",
        "dataSources": [
            {
                "type": "Structured",
                "name": "EduManageDataFolder",
                "connectionDetails": {
                    "protocol": "file",
                    "address": {"path": "../data"}
                }
            }
        ],
        "tables": [
            {
                "name": "_KeyMeasures",
                "measures": [
                    {"name": "Total Fee Invoiced", "expression": "SUM(fact_fees[amount_due])", "formatString": "₹#,##0"},
                    {"name": "Total Fee Collected", "expression": "SUM(fact_fees[amount_paid])", "formatString": "₹#,##0"},
                    {"name": "Total Outstanding Due", "expression": "SUM(fact_fees[balance_due])", "formatString": "₹#,##0"},
                    {"name": "Fee Collection Rate %", "expression": "DIVIDE([Total Fee Collected], [Total Fee Invoiced], 0)", "formatString": "0.0%"},
                    {"name": "Total Students", "expression": "DISTINCTCOUNT(dim_students[student_id])"},
                    {"name": "Average Attendance %", "expression": "DIVIDE(SUM(fact_attendance_monthly[days_present]), SUM(fact_attendance_monthly[working_days]), 0)", "formatString": "0.0%"},
                    {"name": "Dual At-Risk Students", "expression": "CALCULATE(DISTINCTCOUNT(fact_attendance_monthly[student_id]), FILTER(VALUES(dim_students[student_id]), [Average Attendance %] < 0.75 && [Total Outstanding Due] > 0))"}
                ]
            },
            {
                "name": "dim_classes",
                "columns": [
                    {"name": "class_id", "dataType": "string"},
                    {"name": "grade_level", "dataType": "int64"},
                    {"name": "section", "dataType": "string"},
                    {"name": "stream", "dataType": "string"},
                    {"name": "annual_tuition_fee", "dataType": "double"},
                    {"name": "class_teacher", "dataType": "string"}
                ]
            },
            {
                "name": "dim_students",
                "columns": [
                    {"name": "student_id", "dataType": "string"},
                    {"name": "first_name", "dataType": "string"},
                    {"name": "last_name", "dataType": "string"},
                    {"name": "gender", "dataType": "string"},
                    {"name": "class_id", "dataType": "string"},
                    {"name": "grade_level", "dataType": "int64"},
                    {"name": "family_income_bracket", "dataType": "string"},
                    {"name": "scholarship_percent", "dataType": "int64"}
                ]
            },
            {
                "name": "fact_fees",
                "columns": [
                    {"name": "invoice_id", "dataType": "string"},
                    {"name": "student_id", "dataType": "string"},
                    {"name": "class_id", "dataType": "string"},
                    {"name": "quarter", "dataType": "string"},
                    {"name": "due_date", "dataType": "dateTime"},
                    {"name": "amount_due", "dataType": "double"},
                    {"name": "amount_paid", "dataType": "double"},
                    {"name": "balance_due", "dataType": "double"},
                    {"name": "payment_status", "dataType": "string"}
                ]
            },
            {
                "name": "fact_attendance_monthly",
                "columns": [
                    {"name": "attendance_record_id", "dataType": "string"},
                    {"name": "student_id", "dataType": "string"},
                    {"name": "class_id", "dataType": "string"},
                    {"name": "academic_month", "dataType": "string"},
                    {"name": "working_days", "dataType": "int64"},
                    {"name": "days_present", "dataType": "int64"},
                    {"name": "attendance_pct", "dataType": "double"}
                ]
            },
            {
                "name": "fact_academic_performance",
                "columns": [
                    {"name": "exam_id", "dataType": "string"},
                    {"name": "student_id", "dataType": "string"},
                    {"name": "class_id", "dataType": "string"},
                    {"name": "term", "dataType": "string"},
                    {"name": "subject", "dataType": "string"},
                    {"name": "marks_obtained", "dataType": "double"},
                    {"name": "is_passed", "dataType": "boolean"}
                ]
            }
        ],
        "relationships": [
            {
                "name": "rel_student_class",
                "fromTable": "dim_students",
                "fromColumn": "class_id",
                "toTable": "dim_classes",
                "toColumn": "class_id"
            },
            {
                "name": "rel_fees_student",
                "fromTable": "fact_fees",
                "fromColumn": "student_id",
                "toTable": "dim_students",
                "toColumn": "student_id"
            },
            {
                "name": "rel_fees_class",
                "fromTable": "fact_fees",
                "fromColumn": "class_id",
                "toTable": "dim_classes",
                "toColumn": "class_id"
            },
            {
                "name": "rel_attendance_student",
                "fromTable": "fact_attendance_monthly",
                "fromColumn": "student_id",
                "toTable": "dim_students",
                "toColumn": "student_id"
            },
            {
                "name": "rel_academic_student",
                "fromTable": "fact_academic_performance",
                "fromColumn": "student_id",
                "toTable": "dim_students",
                "toColumn": "student_id"
            }
        ]
    }
}

def create_powerbi_file(file_path):
    with zipfile.ZipFile(file_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types_xml)
        zf.writestr("Version", version_text)
        zf.writestr("Settings", settings_xml)
        zf.writestr("DataModelSchema", json.dumps(data_model_schema, indent=2))
        zf.writestr("Report/Layout", json.dumps(report_layout, indent=2))

create_powerbi_file(PBIT_PATH)
create_powerbi_file(PBIX_PATH)

print(f"✅ Generated Power BI Template: {PBIT_PATH}")
print(f"✅ Generated Power BI Report File: {PBIX_PATH}")
