from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.io as pio
import streamlit as st

pio.templates.default = "plotly_white"

st.set_page_config(page_title="EduPro | Teaching Quality Desk", page_icon="🎓", layout="wide")

# ---------- look & feel ----------
INK = "#1f2a44"
CLAY = "#d9653b"
SAND = "#f6f1e9"
TEAL = "#2a9d8f"
SEQ = ["#f3dcc9", "#e9a77b", "#d9653b", "#8c2f1b"]

st.markdown(
    f"""
    <style>
    .stApp {{ background-color: {SAND}; color: {INK}; }}
    .stApp p, .stApp label, .stApp li, .stApp span, .stApp div[data-testid="stMarkdownContainer"],
    .stApp div[data-testid="stCaptionContainer"], .stApp [data-testid="stMetricLabel"],
    .stApp [data-testid="stMetricValue"], .stApp button[role="tab"] {{ color: {INK} !important; }}
    section[data-testid="stSidebar"] * {{ color: {INK}; }}
    div[data-baseweb="select"] > div, section[data-testid="stFileUploaderDropzone"] {{
        background-color: white !important; color: {INK} !important; }}
    div[data-baseweb="select"] * {{ color: {INK} !important; }}
    h1, h2, h3 {{ color: {INK}; font-family: Georgia, serif; }}
    div[data-testid="stMetric"] {{
        background: white; border-left: 5px solid {CLAY};
        padding: 12px 16px; border-radius: 6px;
        box-shadow: 0 1px 3px rgba(0,0,0,.08);
    }}
    section[data-testid="stSidebar"] {{ background-color: #ece3d4; }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------- data ----------
def make_demo_data(seed=7):
    """Only used when no Excel file is supplied, so the dashboard still opens."""
    rng = np.random.default_rng(seed)
    expertise = ["Data Science", "Web Development", "Design", "Marketing", "Finance", "Cloud"]
    cats = ["Programming", "Business", "Creative", "Analytics"]
    levels = ["Beginner", "Intermediate", "Advanced"]
    n_t = 60
    exp = rng.integers(1, 25, n_t)
    t_rating = np.clip(3.2 + np.log1p(exp) * 0.3 + rng.normal(0, 0.3, n_t), 2.5, 5)
    teachers = pd.DataFrame({
        "TeacherID": range(1, n_t + 1),
        "TeacherName": [f"Teacher {i}" for i in range(1, n_t + 1)],
        "Age": rng.integers(26, 65, n_t),
        "Gender": rng.choice(["Male", "Female"], n_t),
        "Expertise": rng.choice(expertise, n_t),
        "YearsOfExperience": exp,
        "TeacherRating": t_rating.round(2),
    })
    n_c = 120
    courses = pd.DataFrame({
        "CourseID": range(1, n_c + 1),
        "CourseName": [f"Course {i}" for i in range(1, n_c + 1)],
        "CourseCategory": rng.choice(cats, n_c),
        "CourseLevel": rng.choice(levels, n_c),
        "CourseRating": np.clip(rng.normal(4.0, 0.4, n_c), 2.5, 5).round(2),
    })
    tx_t = rng.choice(teachers.TeacherID, 3000, p=(t_rating / t_rating.sum()))
    tx_c = rng.choice(courses.CourseID, 3000)
    tx = pd.DataFrame({"TransactionID": range(1, 3001), "CourseID": tx_c, "TeacherID": tx_t})
    return teachers, courses, tx


@st.cache_data(show_spinner=False)
def load_excel(file):
    xl = pd.ExcelFile(file)
    sheets = {s.strip().lower(): s for s in xl.sheet_names}
    def grab(name):
        return xl.parse(sheets[name]).rename(columns=lambda c: str(c).strip())
    return grab("teachers"), grab("courses"), grab("transactions")


@st.cache_data(show_spinner=False)
def integrate(teachers, courses, tx):
    t = teachers.drop_duplicates("TeacherID")
    c = courses.drop_duplicates("CourseID")
    m = tx.merge(c, on="CourseID", how="left").merge(t, on="TeacherID", how="left")
    return m


st.sidebar.title("🎓 EduPro")
up = st.sidebar.file_uploader("Upload a different Excel file (optional)", type=["xlsx"])

# if an .xlsx sits next to app.py, use it automatically
local_files = sorted(p for p in Path(__file__).parent.glob("*.xlsx") if not p.name.startswith("~$"))
source = up if up is not None else (local_files[0] if local_files else None)

if source is not None:
    try:
        teachers, courses, tx = load_excel(source)
        st.sidebar.success(f"Loaded {getattr(source, 'name', source)}")
    except Exception as e:
        st.sidebar.error(f"Couldn't read it ({e}). Need sheets: Teachers, Courses, Transactions.")
        st.stop()
else:
    teachers, courses, tx = make_demo_data()
    st.sidebar.warning("No Excel file found - showing made-up demo data.")

df = integrate(teachers, courses, tx)
unmapped = int(df["TeacherName"].isna().sum() + df["CourseName"].isna().sum())

# ---------- filters ----------
st.sidebar.markdown("---")
st.sidebar.subheader("Filters")
exp_sel = st.sidebar.multiselect("Instructor expertise", sorted(df.Expertise.dropna().unique()))
cat_sel = st.sidebar.multiselect("Course category", sorted(df.CourseCategory.dropna().unique()))
lvl_sel = st.sidebar.multiselect("Course level", sorted(df.CourseLevel.dropna().unique()))
tr = st.sidebar.slider("Teacher rating", 0.0, 5.0, (0.0, 5.0), 0.1)
cr = st.sidebar.slider("Course rating", 0.0, 5.0, (0.0, 5.0), 0.1)

f = df.dropna(subset=["TeacherID", "CourseID", "TeacherRating", "CourseRating"]).copy()
if exp_sel:
    f = f[f.Expertise.isin(exp_sel)]
if cat_sel:
    f = f[f.CourseCategory.isin(cat_sel)]
if lvl_sel:
    f = f[f.CourseLevel.isin(lvl_sel)]
f = f[f.TeacherRating.between(*tr) & f.CourseRating.between(*cr)]

if f.empty:
    st.title("EduPro Teaching Quality Desk")
    st.info("Nothing matches those filters. Loosen them a bit.")
    st.stop()

# one row per teacher-course pair (used for ratings), enrollments = transaction count
pairs = f.drop_duplicates(["TeacherID", "CourseID"])
per_teacher = (
    f.groupby(["TeacherID", "TeacherName", "Expertise", "YearsOfExperience", "Age", "Gender", "TeacherRating"])
    .agg(Enrollments=("TransactionID", "count"), Courses=("CourseID", "nunique"))
    .reset_index()
)
cr_stats = pairs.groupby("TeacherID").CourseRating.agg(AvgCourseRating="mean", CourseStd="std").reset_index()
per_teacher = per_teacher.merge(cr_stats, on="TeacherID")
per_teacher["CourseStd"] = per_teacher["CourseStd"].fillna(0)
# consistency: 100 = every course rated the same, drops as spread grows (5 point scale)
per_teacher["Consistency"] = (100 * (1 - per_teacher.CourseStd / 5)).clip(0, 100)

# tiers by rank so ties don't break qcut
ranks = per_teacher.TeacherRating.rank(method="first")
per_teacher["Tier"] = pd.qcut(ranks, 3, labels=["Low", "Mid", "High"]) if len(per_teacher) >= 3 else "Mid"

# ---------- header + KPIs ----------
st.title("EduPro Teaching Quality Desk")
st.caption("Who teaches well, does experience matter, and where should the platform invest in training?")

corr_exp = per_teacher[["YearsOfExperience", "TeacherRating"]].corr().iloc[0, 1] if len(per_teacher) > 2 else np.nan
tier_enr = per_teacher.groupby("Tier", observed=True).Enrollments.mean()
eir = (tier_enr.get("High", np.nan) / tier_enr.get("Low", np.nan)) if "Low" in tier_enr and "High" in tier_enr else np.nan

med = per_teacher.groupby("Tier", observed=True).Enrollments.median()
eir_med = (med.get("High", np.nan) / med.get("Low", np.nan)) if "Low" in med and "High" in med else np.nan

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Avg teacher rating", f"{per_teacher.TeacherRating.mean():.2f}")
k2.metric("Avg course rating", f"{pairs.CourseRating.mean():.2f}")
k3.metric("Rating consistency", f"{per_teacher.Consistency.mean():.0f}/100")
k4.metric("Experience impact", "n/a" if np.isnan(corr_exp) else f"{corr_exp:+.2f}",
          help="Correlation between years of experience and teacher rating")
k5.metric("Enrollment influence", "n/a" if np.isnan(eir) else f"{eir:.2f}x",
          help="Avg enrollments of top-third rated teachers divided by bottom third. Mean-based, so a few very popular teachers can inflate it; see the median ratio in Takeaways.")

if unmapped:
    st.warning(f"{unmapped} transaction fields didn't map to a teacher/course and were left out.")

tabs = st.tabs(["Leaderboard", "Experience", "Course quality", "Instructor impact", "Expertise", "Takeaways"])

# ---- leaderboard
with tabs[0]:
    c1, c2 = st.columns([1, 1.4])
    with c1:
        st.subheader("How ratings are spread")
        fig = px.histogram(per_teacher, x="TeacherRating", nbins=20, color_discrete_sequence=[CLAY])
        fig.update_layout(bargap=0.05, yaxis_title="Teachers", plot_bgcolor="white", paper_bgcolor=SAND, font_color=INK)
        st.plotly_chart(fig, use_container_width=True, theme=None)
    with c2:
        st.subheader("Leaderboard")
        n = st.slider("Show top / bottom", 5, 25, 10)
        side = st.radio("View", ["Top performers", "Needs attention"], horizontal=True)
        asc = side == "Needs attention"
        board = per_teacher.sort_values(["TeacherRating", "Enrollments"], ascending=[asc, asc]).head(n)
        st.dataframe(
            board[["TeacherName", "Expertise", "YearsOfExperience", "TeacherRating",
                   "AvgCourseRating", "Consistency", "Courses", "Enrollments"]].round(2),
            hide_index=True, use_container_width=True,
        )

# ---- experience
with tabs[1]:
    st.subheader("Does more experience mean better ratings?")
    a, b = st.columns(2)
    with a:
        fig = px.scatter(per_teacher, x="YearsOfExperience", y="TeacherRating", color="Expertise",
                         size="Enrollments", hover_name="TeacherName", trendline="ols" if len(per_teacher) > 2 else None,
                         trendline_scope="overall", trendline_color_override=INK)
        fig.update_layout(plot_bgcolor="white", paper_bgcolor=SAND, font_color=INK, title="Experience vs teacher rating")
        st.plotly_chart(fig, use_container_width=True, theme=None)
    with b:
        fig = px.scatter(per_teacher, x="YearsOfExperience", y="AvgCourseRating", color="Expertise",
                         hover_name="TeacherName", trendline="ols" if len(per_teacher) > 2 else None,
                         trendline_scope="overall", trendline_color_override=INK)
        fig.update_layout(plot_bgcolor="white", paper_bgcolor=SAND, font_color=INK, title="Experience vs course rating")
        st.plotly_chart(fig, use_container_width=True, theme=None)

    bins = [-1, 2, 5, 10, 15, 20, 100]
    labels = ["0-2", "3-5", "6-10", "11-15", "16-20", "20+"]
    per_teacher["ExpBand"] = pd.cut(per_teacher.YearsOfExperience, bins=bins, labels=labels)
    band = per_teacher.groupby("ExpBand", observed=True).agg(
        Teacher=("TeacherRating", "mean"), Course=("AvgCourseRating", "mean"), Teachers=("TeacherID", "count")
    ).reset_index()
    fig = px.line(band.melt(id_vars=["ExpBand", "Teachers"], var_name="Rating", value_name="Avg"),
                  x="ExpBand", y="Avg", color="Rating", markers=True,
                  color_discrete_map={"Teacher": CLAY, "Course": TEAL})
    fig.update_layout(plot_bgcolor="white", paper_bgcolor=SAND, font_color=INK, xaxis_title="Years of experience",
                      title="Where the curve flattens (diminishing returns)")
    st.plotly_chart(fig, use_container_width=True, theme=None)
    corr_c = per_teacher[["YearsOfExperience", "AvgCourseRating"]].corr().iloc[0, 1]
    st.write(f"Correlation with teacher rating: **{corr_exp:+.2f}** | with course rating: **{corr_c:+.2f}**")

# ---- course quality
with tabs[2]:
    st.subheader("Course quality by category and level")
    heat = pairs.pivot_table(index="CourseCategory", columns="CourseLevel", values="CourseRating", aggfunc="mean")
    fig = px.imshow(heat.round(2), text_auto=True, color_continuous_scale=SEQ, aspect="auto")
    fig.update_layout(paper_bgcolor=SAND, font_color=INK, title="Average course rating heatmap")
    st.plotly_chart(fig, use_container_width=True, theme=None)

    a, b = st.columns(2)
    with a:
        cat = pairs.groupby("CourseCategory").CourseRating.agg(["mean", "std", "count"]).reset_index().sort_values("mean")
        fig = px.bar(cat, x="mean", y="CourseCategory", orientation="h", error_x="std",
                     color_discrete_sequence=[TEAL], labels={"mean": "Avg course rating"})
        fig.update_layout(plot_bgcolor="white", paper_bgcolor=SAND, font_color=INK, title="Category averages (bars = spread)")
        st.plotly_chart(fig, use_container_width=True, theme=None)
    with b:
        g = pairs.groupby(["CourseLevel", "Gender"]).CourseRating.mean().reset_index()
        fig = px.bar(g, x="CourseLevel", y="CourseRating", color="Gender", barmode="group",
                     color_discrete_sequence=[CLAY, INK])
        fig.update_layout(plot_bgcolor="white", paper_bgcolor=SAND, font_color=INK, title="Gender vs course level")
        fig.update_yaxes(range=[max(0, g.CourseRating.min() - 0.5), 5])
        st.plotly_chart(fig, use_container_width=True, theme=None)

# ---- instructor impact
with tabs[3]:
    st.subheader("Do top-rated instructors draw more learners?")
    tier = per_teacher.groupby("Tier", observed=True).agg(
        Teachers=("TeacherID", "count"), AvgCourseRating=("AvgCourseRating", "mean"),
        AvgEnrollments=("Enrollments", "mean"), TotalEnrollments=("Enrollments", "sum")).reset_index()
    a, b = st.columns(2)
    with a:
        fig = px.bar(tier, x="Tier", y="AvgCourseRating", color="Tier", text_auto=".2f",
                     color_discrete_sequence=["#e9a77b", "#d9653b", "#8c2f1b"])
        fig.update_layout(plot_bgcolor="white", paper_bgcolor=SAND, font_color=INK, showlegend=False, title="Course rating by instructor tier")
        st.plotly_chart(fig, use_container_width=True, theme=None)
    with b:
        fig = px.bar(tier, x="Tier", y="AvgEnrollments", color="Tier", text_auto=".0f",
                     color_discrete_sequence=["#e9a77b", "#d9653b", "#8c2f1b"])
        fig.update_layout(plot_bgcolor="white", paper_bgcolor=SAND, font_color=INK, showlegend=False, title="Avg enrollments per instructor")
        st.plotly_chart(fig, use_container_width=True, theme=None)
    fig = px.scatter(per_teacher, x="TeacherRating", y="AvgCourseRating", color="Tier", hover_name="TeacherName",
                     trendline="ols" if len(per_teacher) > 2 else None, trendline_scope="overall",
                     trendline_color_override=INK)
    fig.update_layout(plot_bgcolor="white", paper_bgcolor=SAND, font_color=INK, title="Teacher rating vs course rating")
    st.plotly_chart(fig, use_container_width=True, theme=None)
    corr_tc = per_teacher[["TeacherRating", "AvgCourseRating"]].corr().iloc[0, 1]
    st.write(f"Teacher vs course rating correlation: **{corr_tc:+.2f}**")
    st.dataframe(tier.round(2), hide_index=True, use_container_width=True)

# ---- expertise
with tabs[4]:
    st.subheader("Expertise-wise performance")
    ex = per_teacher.groupby("Expertise").agg(
        Teachers=("TeacherID", "count"), TeacherRating=("TeacherRating", "mean"),
        CourseRating=("AvgCourseRating", "mean"), Enrollments=("Enrollments", "sum")).reset_index()
    fig = px.bar(ex.sort_values("CourseRating"), x="CourseRating", y="Expertise", orientation="h",
                 color="TeacherRating", color_continuous_scale=SEQ, text_auto=".2f")
    fig.update_layout(plot_bgcolor="white", paper_bgcolor=SAND, font_color=INK, title="Avg course rating by expertise (colour = teacher rating)")
    st.plotly_chart(fig, use_container_width=True, theme=None)

    dep = []
    for k, g in pairs.groupby("CourseCategory"):
        if len(g) > 5 and g.TeacherRating.nunique() > 1:
            dep.append({"CourseCategory": k, "TeacherVsCourseCorr": g.TeacherRating.corr(g.CourseRating)})
    if dep:
        dep = pd.DataFrame(dep).sort_values("TeacherVsCourseCorr", ascending=False)
        fig = px.bar(dep, x="CourseCategory", y="TeacherVsCourseCorr", color_discrete_sequence=[INK])
        fig.update_layout(plot_bgcolor="white", paper_bgcolor=SAND, font_color=INK,
                          title="Which categories lean hardest on instructor quality?")
        st.plotly_chart(fig, use_container_width=True, theme=None)

    platform = pairs.CourseRating.mean()
    gaps = ex[ex.CourseRating < platform].sort_values("CourseRating")
    st.markdown("**Training-need flags** (expertise areas below platform average course rating):")
    if gaps.empty:
        st.write("None under the current filters.")
    else:
        st.dataframe(gaps.round(2), hide_index=True, use_container_width=True)

# ---- takeaways
with tabs[5]:
    st.subheader("Auto-written takeaways")
    best_cat = pairs.groupby("CourseCategory").CourseRating.mean().idxmax()
    worst_cat = pairs.groupby("CourseCategory").CourseRating.mean().idxmin()
    best_ex = ex.sort_values("CourseRating").iloc[-1].Expertise
    strength = "weak" if abs(corr_exp) < 0.3 else "moderate" if abs(corr_exp) < 0.6 else "strong"
    st.markdown(
        f"""
- Experience vs teacher rating is a **{strength}** relationship (r = {corr_exp:+.2f}). Check the band chart for where gains level off.
- Teacher rating and course rating move together with r = {corr_tc:+.2f}.
- Highest rated category: **{best_cat}**; lowest: **{worst_cat}**.
- Strongest expertise area by course rating: **{best_ex}**.
- Top-third instructors average **{eir:.2f}x** the enrollments of the bottom third (median-based ratio: **{eir_med:.2f}x**; a big gap between the two means a few teachers drive most demand).
- Rating consistency across the platform averages {per_teacher.Consistency.mean():.0f}/100.
"""
    )
    st.download_button("Download teacher-level table (CSV)",
                       per_teacher.round(3).to_csv(index=False), "edupro_teacher_summary.csv")