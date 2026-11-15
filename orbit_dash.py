import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# =========================================================
# ORBIT | Astronaut Sleep Monitor
# Interactive dashboard for a synthetic astronaut dataset
# =========================================================

# -----------------------------
# Page configuration and theme
# -----------------------------
st.set_page_config(
    page_title="ORBIT | Astronaut Sleep Monitor",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)

NAVY = "#08111F"
SIDEBAR = "#0D1929"
PANEL = "#111E30"
BLUE = "#55A7FF"
CYAN = "#43D9E8"
PURPLE = "#A78BFA"
MUTED = "#9AAEC4"
TEXT = "#F3F7FC"
GRID = "#26384E"

st.markdown(
    f"""
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

      html, body, [class*="css"] {{
          font-family: 'Inter', sans-serif;
      }}
      .stApp {{
          background: {NAVY};
          color: {TEXT};
      }}
      [data-testid="stHeader"] {{
          background: rgba(8, 17, 31, 0.92);
      }}
      [data-testid="stSidebar"] {{
          background: {SIDEBAR};
          border-right: 1px solid #22344B;
      }}
      [data-testid="stMetric"] {{
          background: {PANEL};
          border: 1px solid #23364D;
          padding: 16px 18px;
          border-radius: 12px;
      }}
      [data-testid="stMetricLabel"] p {{
          color: {MUTED};
          font-size: 0.82rem;
      }}
      [data-testid="stMetricValue"] {{
          color: {TEXT};
      }}
      .eyebrow {{
          color: {CYAN};
          letter-spacing: 2px;
          font-size: 0.72rem;
          font-weight: 700;
      }}
      .main-title {{
          font-size: 2rem;
          font-weight: 800;
          color: {TEXT};
          margin: 0;
      }}
      .sub-title {{
          color: {MUTED};
          margin-top: 4px;
          font-size: 0.92rem;
      }}
      .section-title {{
          color: {TEXT};
          font-weight: 700;
          font-size: 1.05rem;
          margin: 8px 0 2px 0;
      }}
      .small-note {{
          color: {MUTED};
          font-size: 0.78rem;
      }}
      div[data-testid="stPlotlyChart"] {{
          background: {PANEL};
          border: 1px solid #23364D;
          border-radius: 12px;
          padding: 8px 8px 0 8px;
      }}
      .stTabs [data-baseweb="tab-list"] {{
          gap: 8px;
      }}
      .stTabs [data-baseweb="tab"] {{
          background: {PANEL};
          border-radius: 8px 8px 0 0;
      }}
      div[data-testid="stAlert"] {{
          border-radius: 10px;
      }}
      hr {{
          border-color: {GRID};
      }}
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Dataset configuration
# -----------------------------
REQUIRED_COLUMNS = [
    "Mission_Day",
    "Astronaut_ID",
    "Sleep_Duration_Hours",
    "Deep_Sleep_Percentage",
    "REM_Sleep_Percentage",
    "Resting_Heart_Rate_BPM",
    "Stress_Score_1_100",
    "Ambient_CO2_PPM",
    "Daily_Radiation_mSv",
    "Morning_Alertness_1_10",
]

NUMERIC_COLUMNS = [
    column for column in REQUIRED_COLUMNS if column != "Astronaut_ID"
]


@st.cache_data
def load_data(uploaded_file=None):
    """Load the included CSV or a user-uploaded compatible CSV."""
    if uploaded_file is not None:
        data = pd.read_csv(uploaded_file)
    else:
        csv_path = (
            Path(__file__).resolve().parent
            / "nasa_spaceapps_astronaut_sleep_health.csv"
        )
        if not csv_path.exists():
            return None
        data = pd.read_csv(csv_path)

    missing_columns = [
        column for column in REQUIRED_COLUMNS if column not in data.columns
    ]
    if missing_columns:
        raise ValueError(
            "The CSV is missing required columns: "
            + ", ".join(missing_columns)
        )

    data = data.copy()

    # Convert expected numeric fields. Invalid strings become NaN and are
    # caught by the validation check below.
    for column in NUMERIC_COLUMNS:
        data[column] = pd.to_numeric(data[column], errors="coerce")

    if data["Astronaut_ID"].isna().any():
        raise ValueError("Astronaut_ID contains blank values.")

    if data[NUMERIC_COLUMNS].isna().any().any():
        bad_columns = data[NUMERIC_COLUMNS].columns[
            data[NUMERIC_COLUMNS].isna().any()
        ].tolist()
        raise ValueError(
            "Missing or non-numeric values were found in: "
            + ", ".join(bad_columns)
        )

    if data.duplicated(["Astronaut_ID", "Mission_Day"]).any():
        raise ValueError(
            "Duplicate records found for the same astronaut and mission day."
        )

    # Basic plausibility checks for bounded fields.
    bounds = {
        "Mission_Day": (1, None),
        "Sleep_Duration_Hours": (0, 24),
        "Deep_Sleep_Percentage": (0, 100),
        "REM_Sleep_Percentage": (0, 100),
        "Stress_Score_1_100": (1, 100),
        "Morning_Alertness_1_10": (1, 10),
    }

    for column, (lower, upper) in bounds.items():
        if lower is not None and not data[column].ge(lower).all():
            raise ValueError(f"{column} contains values below {lower}.")
        if upper is not None and not data[column].le(upper).all():
            raise ValueError(f"{column} contains values above {upper}.")

    # Keep mission day as an integer for filters and axis labels.
    if not (data["Mission_Day"] % 1 == 0).all():
        raise ValueError("Mission_Day must contain whole-number day values.")
    data["Mission_Day"] = data["Mission_Day"].astype(int)
    data["Astronaut_ID"] = data["Astronaut_ID"].astype(str)

    return data


# -----------------------------
# Reusable chart styling
# -----------------------------
def style_chart(fig, height=340):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=TEXT, size=11),
        height=height,
        margin=dict(l=18, r=18, t=48, b=18),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            title_text="",
        ),
        hoverlabel=dict(bgcolor="#17263B", font_color=TEXT),
    )
    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        linecolor="#30445C",
    )
    fig.update_yaxes(
        gridcolor=GRID,
        zeroline=False,
    )
    return fig


def astronaut_colors(astronauts):
    palette = [BLUE, CYAN, PURPLE, "#F59E0B", "#F472B6", "#34D399"]
    return {
        astronaut: palette[index % len(palette)]
        for index, astronaut in enumerate(astronauts)
    }


def safe_correlation(data, x_column, y_column):
    """Return correlation only when enough non-constant observations exist."""
    pair = data[[x_column, y_column]].dropna()
    if len(pair) < 3:
        return None
    if pair[x_column].nunique() < 2 or pair[y_column].nunique() < 2:
        return None
    value = pair[x_column].corr(pair[y_column])
    return None if pd.isna(value) else float(value)


# -----------------------------
# Header
# -----------------------------
st.markdown(
    '<div class="eyebrow">SPACE HABITAT HEALTH // SYNTHETIC DATA</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="main-title">ORBIT | Astronaut Sleep Monitor</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="sub-title">'
    "Explore sleep, alertness, and environmental patterns across a simulated "
    "space mission."
    "</div>",
    unsafe_allow_html=True,
)
st.write("")

# -----------------------------
# Sidebar and filters
# -----------------------------
with st.sidebar:
    st.markdown("## 🛰️ Mission controls")
    st.caption("Filter the observations shown throughout the dashboard.")

    uploaded_file = st.file_uploader(
        "Upload a compatible CSV",
        type=["csv"],
        help="Use a CSV with the same columns as the supplied dataset.",
    )

    try:
        df_all = load_data(uploaded_file)
    except Exception as error:
        st.error(f"Dataset validation failed: {error}")
        st.stop()

    if df_all is None:
        st.warning(
            "The dataset file was not found. Place "
            "'nasa_spaceapps_astronaut_sleep_health.csv' beside app.py "
            "or upload it here."
        )
        st.stop()

    astronaut_list = sorted(df_all["Astronaut_ID"].unique().tolist())
    selected_astronauts = st.multiselect(
        "Astronauts",
        options=astronaut_list,
        default=astronaut_list,
    )

    minimum_day = int(df_all["Mission_Day"].min())
    maximum_day = int(df_all["Mission_Day"].max())

    if minimum_day == maximum_day:
        selected_day_range = (minimum_day, maximum_day)
        st.caption(f"Mission day: {minimum_day}")
    else:
        selected_day_range = st.slider(
            "Mission day range",
            min_value=minimum_day,
            max_value=maximum_day,
            value=(minimum_day, maximum_day),
        )

    st.markdown("---")
    st.caption("ORBIT dashboard • Hackathon prototype")
    st.caption("Dataset: synthetic astronaut sleep and health observations")

# -----------------------------
# Apply filters
# -----------------------------
df = df_all[
    df_all["Astronaut_ID"].isin(selected_astronauts)
    & df_all["Mission_Day"].between(
        selected_day_range[0], selected_day_range[1]
    )
].copy()

if df.empty:
    st.info(
        "No observations match the selected filters. Select at least one "
        "astronaut or expand the mission-day range."
    )
    st.stop()

colors = astronaut_colors(sorted(df["Astronaut_ID"].unique()))

# -----------------------------
# KPI cards
# -----------------------------
average_sleep = df["Sleep_Duration_Hours"].mean()
average_alertness = df["Morning_Alertness_1_10"].mean()
average_stress = df["Stress_Score_1_100"].mean()
average_heart_rate = df["Resting_Heart_Rate_BPM"].mean()

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("AVG. SLEEP", f"{average_sleep:.2f} hrs")
kpi2.metric("MORNING ALERTNESS", f"{average_alertness:.1f} / 10")
kpi3.metric("STRESS SCORE", f"{average_stress:.1f} / 100")
kpi4.metric("RESTING HEART RATE", f"{average_heart_rate:.0f} BPM")

st.markdown(
    f'<div class="small-note">Showing {len(df)} observations · '
    f'Mission days {selected_day_range[0]}–{selected_day_range[1]} · '
    f'{df["Astronaut_ID"].nunique()} astronaut(s)</div>',
    unsafe_allow_html=True,
)
st.write("")

# -----------------------------
# Mission intelligence insights
# -----------------------------
st.markdown("### MISSION INTELLIGENCE")

correlation = safe_correlation(
    df,
    "Sleep_Duration_Hours",
    "Morning_Alertness_1_10",
)

crew_insights = df.groupby("Astronaut_ID").agg(
    average_sleep=("Sleep_Duration_Hours", "mean"),
    average_stress=("Stress_Score_1_100", "mean"),
    average_alertness=("Morning_Alertness_1_10", "mean"),
)

insight1, insight2, insight3 = st.columns(3)

with insight1:
    if correlation is None:
        st.metric("SLEEP / ALERTNESS CORRELATION", "N/A")
        st.caption("Not enough variation or observations in the current selection.")
    else:
        st.metric("SLEEP / ALERTNESS CORRELATION", f"{correlation:+.2f}")
        st.caption(
            "Positive values mean the two measures tend to increase together. "
            "Correlation does not establish causation."
        )

with insight2:
    lowest_sleep_astronaut = crew_insights["average_sleep"].idxmin()
    lowest_sleep_value = crew_insights["average_sleep"].min()
    st.metric(
        "LOWEST AVG. SLEEP",
        f"{lowest_sleep_value:.2f} hrs",
        help=f"Astronaut: {lowest_sleep_astronaut}",
    )
    st.caption(f"Lowest average sleep: {lowest_sleep_astronaut}")

with insight3:
    highest_stress_astronaut = crew_insights["average_stress"].idxmax()
    highest_stress_value = crew_insights["average_stress"].max()
    st.metric(
        "HIGHEST AVG. STRESS",
        f"{highest_stress_value:.1f}",
        help=f"Astronaut: {highest_stress_astronaut}",
    )
    st.caption(f"Highest average stress: {highest_stress_astronaut}")

st.write("")

# -----------------------------
# Dashboard tabs
# -----------------------------
tab_sleep, tab_crew, tab_environment, tab_risk, tab_data = st.tabs(
    [
        "◉ Sleep & alertness",
        "◎ Crew comparison",
        "⌁ Environment",
        "⚠ Risk explorer",
        "▤ Data explorer",
    ]
)

# =========================================================
# TAB 1: Sleep and alertness
# =========================================================
with tab_sleep:
    st.markdown(
        '<div class="section-title">Sleep duration across the mission</div>',
        unsafe_allow_html=True,
    )

    sleep_chart = px.line(
        df.sort_values(["Astronaut_ID", "Mission_Day"]),
        x="Mission_Day",
        y="Sleep_Duration_Hours",
        color="Astronaut_ID",
        markers=True,
        color_discrete_map=colors,
        labels={
            "Mission_Day": "Mission day",
            "Sleep_Duration_Hours": "Sleep (hours)",
            "Astronaut_ID": "Astronaut",
        },
        hover_data={"Mission_Day": True, "Sleep_Duration_Hours": ":.2f"},
    )
    sleep_chart.add_hline(
        y=8,
        line_dash="dot",
        line_color="#6B7F96",
        annotation_text="8-hour reference",
        annotation_position="bottom right",
    )
    sleep_chart.update_traces(
        line=dict(width=2.5),
        marker=dict(size=6),
    )
    st.plotly_chart(
        style_chart(sleep_chart, 360),
        use_container_width=True,
    )

    left_column, right_column = st.columns(2)

    with left_column:
        st.markdown(
            '<div class="section-title">'
            "Sleep duration vs. morning alertness</div>",
            unsafe_allow_html=True,
        )
        scatter_chart = px.scatter(
            df,
            x="Sleep_Duration_Hours",
            y="Morning_Alertness_1_10",
            color="Astronaut_ID",
            size="Stress_Score_1_100",
            hover_data=[
                "Mission_Day",
                "Stress_Score_1_100",
            ],
            color_discrete_map=colors,
            labels={
                "Sleep_Duration_Hours": "Sleep (hours)",
                "Morning_Alertness_1_10": "Alertness (1–10)",
                "Astronaut_ID": "Astronaut",
                "Stress_Score_1_100": "Stress score",
            },
        )
        st.plotly_chart(
            style_chart(scatter_chart, 340),
            use_container_width=True,
        )

    with right_column:
        st.markdown(
            '<div class="section-title">'
            "Average sleep-stage composition</div>",
            unsafe_allow_html=True,
        )

        stage_data = df.groupby("Astronaut_ID", as_index=False).agg(
            deep_sleep=("Deep_Sleep_Percentage", "mean"),
            rem_sleep=("REM_Sleep_Percentage", "mean"),
        )
        stage_data["other_sleep"] = (
            100 - stage_data["deep_sleep"] - stage_data["rem_sleep"]
        ).clip(lower=0)

        stage_long = stage_data.melt(
            id_vars="Astronaut_ID",
            value_vars=["deep_sleep", "rem_sleep", "other_sleep"],
            var_name="Sleep stage",
            value_name="Average share (%)",
        )
        stage_labels = {
            "deep_sleep": "Deep sleep",
            "rem_sleep": "REM sleep",
            "other_sleep": "Other sleep",
        }
        stage_long["Sleep stage"] = stage_long["Sleep stage"].map(stage_labels)

        stage_chart = px.bar(
            stage_long,
            x="Astronaut_ID",
            y="Average share (%)",
            color="Sleep stage",
            barmode="stack",
            color_discrete_map={
                "Deep sleep": BLUE,
                "REM sleep": CYAN,
                "Other sleep": "#52677F",
            },
        )
        stage_chart.update_layout(
            xaxis_title="",
            yaxis_title="Average share (%)",
        )
        st.plotly_chart(
            style_chart(stage_chart, 340),
            use_container_width=True,
        )
        st.caption(
            "The 'other sleep' segment assumes deep and REM percentages are "
            "parts of total sleep. Confirm this definition against your "
            "dataset documentation."
        )

# =========================================================
# TAB 2: Crew comparison
# =========================================================
with tab_crew:
    st.markdown(
        '<div class="section-title">How does the crew compare?</div>',
        unsafe_allow_html=True,
    )

    crew = df.groupby("Astronaut_ID", as_index=False).agg(
        Average_sleep=("Sleep_Duration_Hours", "mean"),
        Average_alertness=("Morning_Alertness_1_10", "mean"),
        Average_stress=("Stress_Score_1_100", "mean"),
        Average_heart_rate=("Resting_Heart_Rate_BPM", "mean"),
    )

    chart_specs = [
        (
            "Average sleep duration",
            "Average_sleep",
            "Average sleep (hours)",
            ".2f",
            330,
        ),
        (
            "Average morning alertness",
            "Average_alertness",
            "Average alertness (1–10)",
            ".1f",
            330,
        ),
        (
            "Average stress score",
            "Average_stress",
            "Average stress (1–100)",
            ".1f",
            320,
        ),
        (
            "Average resting heart rate",
            "Average_heart_rate",
            "Average resting heart rate (BPM)",
            ".0f",
            320,
        ),
    ]

    for row_start in (0, 2):
        first_column, second_column = st.columns(2)
        for column, spec in zip(
            (first_column, second_column),
            chart_specs[row_start : row_start + 2],
        ):
            title, metric_column, y_label, number_format, chart_height = spec
            with column:
                st.markdown(
                    f'<div class="section-title">{title}</div>',
                    unsafe_allow_html=True,
                )
                crew_chart = px.bar(
                    crew,
                    x="Astronaut_ID",
                    y=metric_column,
                    color="Astronaut_ID",
                    text=metric_column,
                    color_discrete_map=colors,
                    labels={
                        "Astronaut_ID": "Astronaut",
                        metric_column: y_label,
                    },
                )
                crew_chart.update_traces(
                    texttemplate=f"%{{text:{number_format}}}",
                    textposition="outside",
                    cliponaxis=False,
                )
                crew_chart.update_layout(
                    showlegend=False,
                    xaxis_title="",
                )
                st.plotly_chart(
                    style_chart(crew_chart, chart_height),
                    use_container_width=True,
                )

    st.markdown("#### Crew summary")
    st.dataframe(
        crew.round(2),
        use_container_width=True,
        hide_index=True,
    )

# =========================================================
# TAB 3: Environment
# =========================================================
with tab_environment:
    st.markdown(
        '<div class="section-title">'
        "Environmental conditions during the mission</div>",
        unsafe_allow_html=True,
    )

    environment_left, environment_right = st.columns(2)

    with environment_left:
        co2_chart = px.line(
            df.sort_values(["Astronaut_ID", "Mission_Day"]),
            x="Mission_Day",
            y="Ambient_CO2_PPM",
            color="Astronaut_ID",
            markers=True,
            color_discrete_map=colors,
            labels={
                "Mission_Day": "Mission day",
                "Ambient_CO2_PPM": "CO₂ (ppm)",
                "Astronaut_ID": "Astronaut",
            },
        )
        st.plotly_chart(
            style_chart(co2_chart, 340),
            use_container_width=True,
        )

    with environment_right:
        radiation_chart = px.line(
            df.sort_values(["Astronaut_ID", "Mission_Day"]),
            x="Mission_Day",
            y="Daily_Radiation_mSv",
            color="Astronaut_ID",
            markers=True,
            color_discrete_map=colors,
            labels={
                "Mission_Day": "Mission day",
                "Daily_Radiation_mSv": "Radiation (mSv)",
                "Astronaut_ID": "Astronaut",
            },
        )
        st.plotly_chart(
            style_chart(radiation_chart, 340),
            use_container_width=True,
        )

    st.markdown(
        '<div class="section-title">Explore environmental relationships</div>',
        unsafe_allow_html=True,
    )

    selected_outcome = st.selectbox(
        "Compare environmental measure with",
        [
            "Stress score",
            "Sleep duration",
            "Morning alertness",
            "Resting heart rate",
        ],
    )

    outcome_columns = {
        "Stress score": "Stress_Score_1_100",
        "Sleep duration": "Sleep_Duration_Hours",
        "Morning alertness": "Morning_Alertness_1_10",
        "Resting heart rate": "Resting_Heart_Rate_BPM",
    }

    selected_environment = st.radio(
        "Environmental measure",
        ["CO₂ concentration", "Daily radiation"],
        horizontal=True,
    )

    x_column = (
        "Ambient_CO2_PPM"
        if selected_environment == "CO₂ concentration"
        else "Daily_Radiation_mSv"
    )
    y_column = outcome_columns[selected_outcome]

    relationship_chart = px.scatter(
        df,
        x=x_column,
        y=y_column,
        color="Astronaut_ID",
        hover_data=["Mission_Day"],
        color_discrete_map=colors,
        labels={
            x_column: (
                "CO₂ concentration (ppm)"
                if x_column == "Ambient_CO2_PPM"
                else "Daily radiation (mSv)"
            ),
            y_column: selected_outcome,
            "Astronaut_ID": "Astronaut",
        },
    )
    st.plotly_chart(
        style_chart(relationship_chart, 350),
        use_container_width=True,
    )
    st.caption(
        "These charts show associations in the supplied synthetic dataset. "
        "They do not establish that an environmental measure causes a "
        "change in sleep, stress, or alertness."
    )

# =========================================================
# TAB 4: Exploratory flag explorer
# =========================================================
with tab_risk:
    st.markdown(
        '<div class="section-title">Sleep and wellness flag explorer</div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Explore observations that meet one or more selected thresholds. "
        "These are user-defined analysis flags, not medical risk scores."
    )

    threshold_left, threshold_middle, threshold_right = st.columns(3)

    with threshold_left:
        sleep_threshold = st.slider(
            "Flag sleep below (hours)",
            min_value=3.0,
            max_value=8.0,
            value=6.0,
            step=0.5,
        )

    with threshold_middle:
        stress_threshold = st.slider(
            "Flag stress above",
            min_value=20,
            max_value=100,
            value=60,
            step=5,
        )

    with threshold_right:
        alertness_threshold = st.slider(
            "Flag alertness below",
            min_value=1,
            max_value=10,
            value=5,
            step=1,
        )

    flagged = df.copy()
    flagged["Low sleep"] = (
        flagged["Sleep_Duration_Hours"] < sleep_threshold
    )
    flagged["High stress"] = (
        flagged["Stress_Score_1_100"] > stress_threshold
    )
    flagged["Low alertness"] = (
        flagged["Morning_Alertness_1_10"] < alertness_threshold
    )

    flag_columns = ["Low sleep", "High stress", "Low alertness"]
    flagged["Flag reasons"] = flagged[flag_columns].apply(
        lambda row: ", ".join(
            label for label in flag_columns if bool(row[label])
        ),
        axis=1,
    )

    flagged = flagged[flagged[flag_columns].any(axis=1)].copy()

    metric_col1, metric_col2 = st.columns(2)
    metric_col1.metric("FLAGGED OBSERVATIONS", len(flagged))
    metric_col2.metric(
        "SHARE OF FILTERED OBSERVATIONS",
        f"{(len(flagged) / len(df) * 100):.1f}%",
    )

    if flagged.empty:
        st.success(
            "No observations meet the selected thresholds in the current "
            "filtered dataset."
        )
    else:
        display_columns = [
            "Mission_Day",
            "Astronaut_ID",
            "Sleep_Duration_Hours",
            "Stress_Score_1_100",
            "Morning_Alertness_1_10",
            "Flag reasons",
        ]
        st.dataframe(
            flagged[display_columns].sort_values(
                ["Mission_Day", "Astronaut_ID"]
            ),
            use_container_width=True,
            hide_index=True,
        )

        flagged_csv = flagged.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇ Download flagged observations",
            data=flagged_csv,
            file_name="orbit_flagged_observations.csv",
            mime="text/csv",
        )

    st.caption(
        "An observation is flagged if it meets at least one threshold. "
        "Thresholds are adjustable for exploration and are not validated "
        "clinical cutoffs."
    )

# =========================================================
# TAB 5: Data explorer
# =========================================================
with tab_data:
    st.markdown(
        '<div class="section-title">Filtered mission observations</div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Use the sidebar filters to narrow the table, then download the "
        "selected observations."
    )

    display_df = df.sort_values(
        ["Mission_Day", "Astronaut_ID"]
    ).reset_index(drop=True)

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
    )

    filtered_csv = display_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇ Download filtered data",
        data=filtered_csv,
        file_name="orbit_filtered_astronaut_sleep_data.csv",
        mime="text/csv",
    )

# -----------------------------
# Footer
# -----------------------------
st.markdown("---")
st.markdown(
    '<div class="small-note">'
    "ORBIT is a hackathon visualization prototype. The supplied dataset is "
    "synthetic and should not be interpreted as real astronaut medical "
    "measurements or operational NASA data."
    "</div>",
    unsafe_allow_html=True,
)
