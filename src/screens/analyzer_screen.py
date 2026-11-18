"""
Smart Attendance Analyzer
=========================
Renders an analytics dashboard inside the Teacher Dashboard's new tab.

Thresholds:
  Safe     → attendance_pct >= 85 %
  Warning  → 75 % <= attendance_pct < 85 %
  Critical → attendance_pct < 75 %
"""

import streamlit as st
import pandas as pd

from src.database.db import get_attendance_with_students_for_teacher

# ── Thresholds ──────────────────────────────────────────────────────────────
SAFE_THRESHOLD    = 85.0
WARNING_THRESHOLD = 75.0


# ── Helpers ──────────────────────────────────────────────────────────────────

def _status_label(pct: float) -> str:
    if pct >= SAFE_THRESHOLD:
        return "✅ Safe"
    if pct >= WARNING_THRESHOLD:
        return "⚠️ Warning"
    return "🔴 Critical"


def _status_color(pct: float) -> str:
    if pct >= SAFE_THRESHOLD:
        return "#22c55e"
    if pct >= WARNING_THRESHOLD:
        return "#f59e0b"
    return "#ef4444"


def _status_bg(pct: float) -> str:
    if pct >= SAFE_THRESHOLD:
        return "#f0fdf4"
    if pct >= WARNING_THRESHOLD:
        return "#fffbeb"
    return "#fef2f2"


def _classes_to_recover(attended: int, total: int, target: float = 75.0) -> int:
    """
    How many *consecutive* classes must a student attend so that
    their overall percentage reaches `target` %?
    """
    t = target / 100.0
    # (attended + x) / (total + x) >= t  →  x >= (t*total - attended) / (1 - t)
    if t >= 1.0:
        return 0
    x = (t * total - attended) / (1.0 - t)
    return max(0, int(x) + (1 if x > int(x) else 0))


def _build_dataframe(records: list) -> pd.DataFrame:
    """Convert raw Supabase rows into a tidy DataFrame."""
    rows = []
    for r in records:
        student = r.get("students") or {}
        subject = r.get("subjects") or {}
        if not student or not subject:
            continue
        rows.append(
            {
                "student_id":   r.get("student_id"),
                "student_name": student.get("name", "Unknown"),
                "subject_id":   r.get("subject_id"),
                "subject_name": subject.get("name", "Unknown"),
                "subject_code": subject.get("subject_code", ""),
                "timestamp":    r.get("timestamp"),
                "is_present":   bool(r.get("is_present", False)),
            }
        )
    return pd.DataFrame(rows)


def _student_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Per-student aggregate (across ALL subjects of this teacher)."""
    s = (
        df.groupby(["student_id", "student_name"], as_index=False)
        .agg(total=("is_present", "count"), attended=("is_present", "sum"))
    )
    s["missed"]     = s["total"] - s["attended"]
    s["percentage"] = (s["attended"] / s["total"] * 100).round(1)
    s["status"]     = s["percentage"].apply(_status_label)
    s["color"]      = s["percentage"].apply(_status_color)
    s["bg"]         = s["percentage"].apply(_status_bg)
    return s.sort_values("percentage")


def _subject_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Per-subject aggregate."""
    s = (
        df.groupby(["subject_id", "subject_name", "subject_code"], as_index=False)
        .agg(total=("is_present", "count"), attended=("is_present", "sum"))
    )
    s["avg_pct"] = (s["attended"] / s["total"] * 100).round(1)
    s["label"]   = s["subject_name"] + "\n(" + s["subject_code"] + ")"
    return s


# ── UI helpers ────────────────────────────────────────────────────────────────

def _metric_card(label: str, value: str, icon: str, bg: str = "#E0E3FF", color: str = "#1e293b"):
    st.markdown(
        f"""
        <div style="
            background:{bg};
            border-radius:16px;
            padding:18px 20px;
            text-align:center;
            border: 1px solid #e2e8f0;
        ">
            <div style="font-size:1.8rem;">{icon}</div>
            <div style="font-size:1.5rem; font-weight:700; color:{color};">{value}</div>
            <div style="font-size:0.85rem; color:#64748b; margin-top:4px;">{label}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _progress_row(student_name: str, pct: float, attended: int, total: int, missed: int):
    color  = _status_color(pct)
    label  = _status_label(pct)
    pct_clamped = min(max(pct / 100.0, 0.0), 1.0)

    col_name, col_bar, col_badge, col_numbers = st.columns([2.5, 3.5, 1.5, 2])

    with col_name:
        st.markdown(
            f"<div style='padding-top:6px; font-weight:600; font-size:0.95rem;'>{student_name}</div>",
            unsafe_allow_html=True,
        )

    with col_bar:
        st.progress(pct_clamped, text=f"{pct}%")

    with col_badge:
        st.markdown(
            f"""<div style="
                display:inline-block;
                background:{_status_bg(pct)};
                color:{color};
                border:1px solid {color};
                border-radius:20px;
                padding:3px 10px;
                font-size:0.78rem;
                font-weight:700;
                margin-top:4px;
            ">{label}</div>""",
            unsafe_allow_html=True,
        )

    with col_numbers:
        st.markdown(
            f"<div style='padding-top:6px; font-size:0.85rem; color:#64748b;'>"
            f"✅ {attended} &nbsp;|&nbsp; ❌ {missed} &nbsp;/ {total}</div>",
            unsafe_allow_html=True,
        )


def _at_risk_card(row: pd.Series):
    pct      = row["percentage"]
    attended = int(row["attended"])
    total    = int(row["total"])
    missed   = int(row["missed"])
    color    = _status_color(pct)
    bg       = _status_bg(pct)
    classes_needed = _classes_to_recover(attended, total, WARNING_THRESHOLD)

    recs = []
    if pct < 50:
        recs.append(f"🚨 Attendance is critically low — immediate action is required.")
        recs.append(
            f"Must attend the next **{classes_needed}** consecutive classes without a single absence to reach 75 %."
        )
        recs.append("Consider an urgent discussion with the teacher or academic counselor.")
    elif pct < WARNING_THRESHOLD:
        recs.append(
            f"Must attend the next **{classes_needed}** consecutive classes to cross the 75 % threshold."
        )
        recs.append("Avoid missing even one class from this point forward.")
        recs.append("Contact classmates for notes from every missed session.")

    if missed >= 5:
        recs.append(f"Already missed **{missed}** classes — consistent attendance is now essential.")

    recs.append("Set a reminder 15 minutes before each class to stay on track.")

    st.markdown(
        f"""
        <div style="
            background:{bg};
            border-left: 5px solid {color};
            border-radius:12px;
            padding:16px 20px;
            margin-bottom:12px;
        ">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-size:1.1rem; font-weight:700; color:#1e293b;">{row['student_name']}</span>
                <span style="font-size:1.6rem; font-weight:800; color:{color};">{pct} %</span>
            </div>
            <div style="color:#64748b; font-size:0.85rem; margin-top:4px;">
                Attended {attended} of {total} classes &nbsp;|&nbsp; Missed {missed}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # progress bar
    st.progress(min(pct / 100.0, 1.0))

    # recommendations
    with st.expander("📌 View Personalized Recommendations", expanded=True):
        for rec in recs:
            st.markdown(f"- {rec}")


# ── Main render function (called from teacher_screen.py) ─────────────────────

def render_smart_analyzer(teacher_id: int):
    st.markdown(
        """
        <div style="margin-bottom:4px;">
            <h2 style="color:#1e293b; margin-bottom:0;">📊 Smart Attendance Analyzer</h2>
            <p style="color:#64748b; margin-top:4px;">
                AI-powered insights into student attendance patterns across all your subjects.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Fetch data ──────────────────────────────────────────────────────────
    with st.spinner("Loading attendance data…"):
        records = get_attendance_with_students_for_teacher(teacher_id)

    if not records:
        st.info(
            "📭 No attendance data found yet. "
            "Take attendance in the **Take Attendance** tab first, then come back here for insights!"
        )
        return

    df = _build_dataframe(records)

    if df.empty:
        st.info("No valid attendance records found. Data may be incomplete.")
        return

    all_student_stats = _student_stats(df)
    subj_stats        = _subject_stats(df)

    total_students = len(all_student_stats)
    avg_pct        = round(all_student_stats["percentage"].mean(), 1)
    at_risk_count  = int((all_student_stats["percentage"] < WARNING_THRESHOLD).sum())
    warning_count  = int(
        ((all_student_stats["percentage"] >= WARNING_THRESHOLD) &
         (all_student_stats["percentage"] < SAFE_THRESHOLD)).sum()
    )
    safe_count     = int((all_student_stats["percentage"] >= SAFE_THRESHOLD).sum())

    # ── Overview cards ───────────────────────────────────────────────────────
    st.markdown("#### 📋 Overview")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        _metric_card("Total Students Analyzed", str(total_students), "👥", "#E0E3FF", "#5865F2")
    with c2:
        avg_color = _status_color(avg_pct)
        avg_bg    = _status_bg(avg_pct)
        _metric_card("Average Attendance", f"{avg_pct}%", "📈", avg_bg, avg_color)
    with c3:
        _metric_card("Students at Risk (<75%)", str(at_risk_count), "🔴", "#fef2f2", "#ef4444")
    with c4:
        _metric_card("Safe Students (≥85%)", str(safe_count), "✅", "#f0fdf4", "#22c55e")

    st.divider()

    # ── Subject-wise attendance bar chart ────────────────────────────────────
    st.markdown("#### 📚 Subject-Wise Average Attendance")

    if len(subj_stats) == 1:
        # Single subject: show a plain metric instead of a bar chart
        row = subj_stats.iloc[0]
        subj_color = _status_color(row["avg_pct"])
        st.markdown(
            f"""
            <div style="
                background:{_status_bg(row['avg_pct'])};
                border-left:5px solid {subj_color};
                border-radius:12px;
                padding:16px 20px;
            ">
                <b style="font-size:1rem;">{row['subject_name']} ({row['subject_code']})</b><br/>
                <span style="font-size:1.5rem; font-weight:800; color:{subj_color};">{row['avg_pct']}%</span>
                <span style="color:#64748b;"> average attendance</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        chart_df = (
            subj_stats
            .set_index("label")[["avg_pct"]]
            .rename(columns={"avg_pct": "Avg Attendance %"})
        )
        st.bar_chart(chart_df, y_label="Avg Attendance %", x_label="Subject", height=280)

    # Legend row
    leg1, leg2, leg3, leg4 = st.columns(4)
    with leg1:
        st.markdown(
            "<span style='background:#f0fdf4;color:#22c55e;border:1px solid #22c55e;"
            "border-radius:20px;padding:3px 10px;font-size:0.78rem;font-weight:700;'>"
            "✅ Safe ≥ 85%</span>",
            unsafe_allow_html=True,
        )
    with leg2:
        st.markdown(
            "<span style='background:#fffbeb;color:#f59e0b;border:1px solid #f59e0b;"
            "border-radius:20px;padding:3px 10px;font-size:0.78rem;font-weight:700;'>"
            "⚠️ Warning 75–84%</span>",
            unsafe_allow_html=True,
        )
    with leg3:
        st.markdown(
            "<span style='background:#fef2f2;color:#ef4444;border:1px solid #ef4444;"
            "border-radius:20px;padding:3px 10px;font-size:0.78rem;font-weight:700;'>"
            "🔴 Critical < 75%</span>",
            unsafe_allow_html=True,
        )
    with leg4:
        st.markdown(
            f"<span style='color:#64748b;font-size:0.82rem;'>"
            f"⚠️ Warning zone: {warning_count} student(s)</span>",
            unsafe_allow_html=True,
        )

    st.divider()

    # ── Full student attendance list ─────────────────────────────────────────
    st.markdown("#### 🎓 Student Attendance Report")

    # Filter controls
    fc1, fc2 = st.columns(2)
    with fc1:
        filter_status = st.selectbox(
            "Filter by Status",
            ["All Students", "✅ Safe", "⚠️ Warning", "🔴 Critical"],
            key="analyzer_status_filter",
        )
    with fc2:
        subject_names   = ["All Subjects"] + sorted(df["subject_name"].unique().tolist())
        filter_subject  = st.selectbox(
            "Filter by Subject",
            subject_names,
            key="analyzer_subject_filter",
        )

    # Recompute stats per chosen subject scope
    if filter_subject != "All Subjects":
        scope_df    = df[df["subject_name"] == filter_subject]
        scope_stats = _student_stats(scope_df)
    else:
        scope_stats = all_student_stats.copy()

    # Apply status filter
    if filter_status == "✅ Safe":
        scope_stats = scope_stats[scope_stats["percentage"] >= SAFE_THRESHOLD]
    elif filter_status == "⚠️ Warning":
        scope_stats = scope_stats[
            (scope_stats["percentage"] >= WARNING_THRESHOLD) &
            (scope_stats["percentage"] < SAFE_THRESHOLD)
        ]
    elif filter_status == "🔴 Critical":
        scope_stats = scope_stats[scope_stats["percentage"] < WARNING_THRESHOLD]

    if scope_stats.empty:
        st.info("No students match the selected filters.")
    else:
        # Column headers
        hc1, hc2, hc3, hc4 = st.columns([2.5, 3.5, 1.5, 2])
        with hc1:
            st.markdown("<small style='color:#64748b;font-weight:600;'>STUDENT</small>", unsafe_allow_html=True)
        with hc2:
            st.markdown("<small style='color:#64748b;font-weight:600;'>ATTENDANCE PROGRESS</small>", unsafe_allow_html=True)
        with hc3:
            st.markdown("<small style='color:#64748b;font-weight:600;'>STATUS</small>", unsafe_allow_html=True)
        with hc4:
            st.markdown("<small style='color:#64748b;font-weight:600;'>✅ ATTENDED | ❌ MISSED / TOTAL</small>", unsafe_allow_html=True)

        st.markdown("<hr style='margin:4px 0 8px;border-color:#e2e8f0;'>", unsafe_allow_html=True)

        for _, row in scope_stats.iterrows():
            _progress_row(
                row["student_name"],
                row["percentage"],
                int(row["attended"]),
                int(row["total"]),
                int(row["missed"]),
            )

    st.divider()

    # ── At-risk deep-dive panel ──────────────────────────────────────────────
    at_risk_df = all_student_stats[all_student_stats["percentage"] < WARNING_THRESHOLD].sort_values("percentage")

    if not at_risk_df.empty:
        st.markdown(
            f"#### ⚠️ Students Needing Immediate Attention &nbsp;"
            f"<span style='background:#fef2f2;color:#ef4444;border:1px solid #ef4444;"
            f"border-radius:20px;padding:2px 10px;font-size:0.8rem;font-weight:700;'>"
            f"{len(at_risk_df)} student(s)</span>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p style='color:#64748b;font-size:0.88rem;margin-top:-8px;'>"
            "These students are below the 75% threshold and require personalised guidance.</p>",
            unsafe_allow_html=True,
        )

        for _, row in at_risk_df.iterrows():
            _at_risk_card(row)

    else:
        st.markdown(
            """
            <div style="
                background:#f0fdf4;
                border:1px solid #22c55e;
                border-radius:14px;
                padding:20px;
                text-align:center;
            ">
                <div style="font-size:2rem;">🎉</div>
                <b style="color:#15803d;">All students are above 75% attendance!</b><br/>
                <span style="color:#64748b;font-size:0.88rem;">
                    Keep encouraging consistent attendance to maintain this record.
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )
