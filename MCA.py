import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ---------- GOOGLE AUTH ----------
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_name(
    "credentials.json", scope
)

client = gspread.authorize(creds)

# ---------- OPEN SHEET ----------
sheet = client.open_by_key("1gDsOU5A3c1rdX-Q42OWxLzzq00u0jprj8dRXwriOH4A").sheet1

data = sheet.get_all_records()
df = pd.DataFrame(data)

# ---------- NUMERIC COLUMNS ----------
numeric_cols = [
    "Math_Score","Science_Score","English_Score",
    "Previous_Exam_Score","Attendance_Percent",
    "Homework_Completion_Percent",
    "Discipline_Issues","Late_Count",
    "Study_Hours_Per_Day","Classroom_Engagement_Score"
]

for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

# ---------- PERFORMANCE INDEX ----------
df["Performance_Index"] = df[numeric_cols[:6]].mean(axis=1)

# ---------- SUBJECT ANALYSIS ----------
def analyze_subject(row):
    weak = []
    strong = []

    for subject in ["Math","Science","English"]:
        score = row[f"{subject}_Score"]

        if score < 35:
            weak.append(subject)
        elif score > 60:
            strong.append(subject)

    return pd.Series([", ".join(weak), ", ".join(strong)])

df[["Weak_Subjects","Strong_Subjects"]] = df.apply(analyze_subject, axis=1)

# ---------- ENGAGEMENT RISK ----------
def engagement_risk(row):
    if row["Attendance_Percent"] < 60 or row["Homework_Completion_Percent"] < 50:
        return "High Risk"
    elif row["Classroom_Engagement_Score"] < 4:
        return "Medium Risk"
    else:
        return "Low Risk"

df["Engagement_Risk"] = df.apply(engagement_risk, axis=1)

# ---------- TEACHER RANK ----------
teacher_rank = df.groupby("Teacher_Name")["Classroom_Engagement_Score"].mean().sort_values(ascending=False)

top_teacher = teacher_rank.index[0]

# ---------- TEACHER SUGGESTION ----------
def suggest_teacher(row):
    if row["Performance_Index"] < 50:
        return top_teacher
    return row["Teacher_Name"]

df["Suggested_Teacher"] = df.apply(suggest_teacher, axis=1)

# ---------- SUPPORT LEVEL ----------
def support(score):
    if score < 40:
        return "High Support"
    elif score < 60:
        return "Medium Support"
    else:
        return "Low Support"

df["Support_Level"] = df["Performance_Index"].apply(support)

# ---------- WRITE BACK ----------
sheet.clear()
sheet.update([df.columns.values.tolist()] + df.values.tolist())

print("REAL TIME PREDICTION UPDATED SUCCESSFULLY")