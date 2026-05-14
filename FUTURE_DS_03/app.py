import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Marketing Funnel Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --------------------------------------------------
# CSS
# --------------------------------------------------
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

.stApp {
    background-color: #f4f7fb;
}

section[data-testid="stSidebar"] {
    background: #eef4ff;
    border-right: 1px solid #d6e2ff;
}

/* Sidebar text black */
section[data-testid="stSidebar"] * {
    color: black !important;
}

.block-container {
    padding-top: 0.7rem;
    padding-bottom: 1rem;
    max-width: 100%;
}

.title {
    font-size: 32px;
    font-weight: 700;
    color: #1e3a8a;
    margin-bottom: 0.2rem;
}

.subtitle {
    font-size: 14px;
    color: #64748b;
    margin-bottom: 1rem;
}

.kpi-box {
    background: #ffffff;
    border-radius: 18px;
    padding: 14px 16px;
    box-shadow: 0 4px 14px rgba(0,0,0,0.06);
    border: 1px solid #e5e7eb;
    min-height: 110px;
}

.kpi-label {
    font-size: 12px;
    color: #64748b;
    font-weight: 600;
}

.kpi-value {
    font-size: 25px;
    font-weight: 700;
    color: #2563eb;
    margin-top: 8px;
}

.kpi-note {
    font-size: 11px;
    color: #94a3b8;
    margin-top: 6px;
}

.tile {
    background: #ffffff;
    border-radius: 18px;
    padding: 6px 8px 2px 8px;
    box-shadow: 0 4px 14px rgba(0,0,0,0.06);
    border: 1px solid #e5e7eb;
    margin-bottom: 14px;
}

div[data-testid="stPlotlyChart"] {
    padding-top: 0px !important;
    margin-top: 0px !important;
}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("data/marketing_funnel.csv")
    df.columns = df.columns.str.strip()

    # make duplicate column names unique
    seen = {}
    new_cols = []
    for col in df.columns:
        c = col.lower()
        if c in seen:
            seen[c] += 1
            new_cols.append(f"{c}_{seen[c]}")
        else:
            seen[c] = 0
            new_cols.append(c)
    df.columns = new_cols

    rename_map = {}
    for col in df.columns:
        if col == "channel":
            rename_map[col] = "Channel"
        elif col == "month":
            rename_map[col] = "Month"
        elif col == "leads":
            rename_map[col] = "Leads"
        elif "proposal" in col:
            rename_map[col] = "Proposals"
        elif "customer" in col:
            rename_map[col] = "Customers"
        elif "spend" in col:
            rename_map[col] = "Spend"

    df = df.rename(columns=rename_map)

    required_cols = ["Channel", "Leads", "Proposals", "Customers", "Spend"]
    for col in required_cols:
        if col not in df.columns:
            st.error(f"Missing column: {col}")
            st.write("Detected columns:", df.columns.tolist())
            st.stop()

    for col in ["Leads", "Proposals", "Customers", "Spend"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["Channel", "Leads", "Proposals", "Customers", "Spend"])

    if "Month" in df.columns:
        df["Month"] = df["Month"].astype(str)

    df["Lead to Proposal %"] = (df["Proposals"] / df["Leads"]) * 100
    df["Proposal to Customer %"] = (df["Customers"] / df["Proposals"]) * 100
    df["Lead to Customer %"] = (df["Customers"] / df["Leads"]) * 100
    df["Cost per Lead"] = df["Spend"] / df["Leads"]
    df["Cost per Customer"] = df["Spend"] / df["Customers"]

    return df

df = load_data()

# --------------------------------------------------
# CHART STYLE FUNCTION
# --------------------------------------------------
def style_chart(fig, height=300):
    fig.update_layout(
        height=height,
        font=dict(
            family="Arial",
            size=13,
            color="#111827"
        ),
        title_font=dict(
            size=16,
            color="#1e3a8a"
        ),
        xaxis=dict(
            title_font=dict(color="#111827"),
            tickfont=dict(color="#111827"),
            showline=True,
            linecolor="black"
        ),
        yaxis=dict(
            title_font=dict(color="#111827"),
            tickfont=dict(color="#111827"),
            showline=True,
            linecolor="black"
        ),
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(l=10, r=10, t=35, b=10)
    )
    return fig

# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------
st.sidebar.title("Filters")

selected_channels = []
for ch in sorted(df["Channel"].unique()):
    if st.sidebar.checkbox(ch, value=True, key=f"channel_{ch}"):
        selected_channels.append(ch)

filtered_df = df[df["Channel"].isin(selected_channels)]

if filtered_df.empty:
    st.warning("No data available for selected filters.")
    st.stop()

# --------------------------------------------------
# KPI CALCULATIONS
# --------------------------------------------------
total_leads = filtered_df["Leads"].sum()
total_proposals = filtered_df["Proposals"].sum()
total_customers = filtered_df["Customers"].sum()
total_spend = filtered_df["Spend"].sum()

lead_to_proposal = (total_proposals / total_leads * 100) if total_leads != 0 else 0
proposal_to_customer = (total_customers / total_proposals * 100) if total_proposals != 0 else 0
lead_to_customer = (total_customers / total_leads * 100) if total_leads != 0 else 0

cost_per_lead = (total_spend / total_leads) if total_leads != 0 else 0
cost_per_customer = (total_spend / total_customers) if total_customers != 0 else 0

best_channel = filtered_df.loc[filtered_df["Lead to Customer %"].idxmax(), "Channel"]
lowest_channel = filtered_df.loc[filtered_df["Lead to Customer %"].idxmin(), "Channel"]

drop_leads_to_proposals = total_leads - total_proposals
drop_proposals_to_customers = total_proposals - total_customers

# --------------------------------------------------
# HEADER
# --------------------------------------------------
st.markdown("<div class='title'>Marketing Funnel Dashboard</div>", unsafe_allow_html=True)

# --------------------------------------------------
# ALL BOXES TOGETHER - ROW 1
# --------------------------------------------------
r1 = st.columns(6)

kpis_row1 = [
    ("Total Leads", f"{total_leads:,.0f}", "Top funnel"),
    ("Total Proposals", f"{total_proposals:,.0f}", "Mid funnel"),
    ("Customers", f"{total_customers:,.0f}", "Bottom funnel"),
    ("Lead → Proposal", f"{lead_to_proposal:.1f}%", "Stage conversion"),
    ("Lead → Customer", f"{lead_to_customer:.1f}%", "Final conversion"),
    ("Total Spend", f"{total_spend:,.0f}", "Marketing investment"),
]

for col, (label, value, note) in zip(r1, kpis_row1):
    with col:
        st.markdown(f"""
        <div class='kpi-box'>
            <div class='kpi-label'>{label}</div>
            <div class='kpi-value'>{value}</div>
            <div class='kpi-note'>{note}</div>
        </div>
        """, unsafe_allow_html=True)

# --------------------------------------------------
# ALL BOXES TOGETHER - ROW 2
# --------------------------------------------------
r2 = st.columns(6)

kpis_row2 = [
    ("Best Channel", best_channel, "Highest lead to customer conversion"),
    ("Lowest Channel", lowest_channel, "Lowest lead to customer conversion"),
    ("Drop: Leads → Proposals", f"{drop_leads_to_proposals:,.0f}", "Upper funnel loss"),
    ("Drop: Proposals → Customers", f"{drop_proposals_to_customers:,.0f}", "Bottom funnel loss"),
    ("Cost per Lead", f"{cost_per_lead:.2f}", "Spend efficiency"),
    ("Cost per Customer", f"{cost_per_customer:.2f}", "Acquisition efficiency"),
]

for col, (label, value, note) in zip(r2, kpis_row2):
    with col:
        st.markdown(f"""
        <div class='kpi-box'>
            <div class='kpi-label'>{label}</div>
            <div class='kpi-value' style='font-size:22px;'>{value}</div>
            <div class='kpi-note'>{note}</div>
        </div>
        """, unsafe_allow_html=True)

# --------------------------------------------------
# CHART ROW 1
# --------------------------------------------------
c1, c2 = st.columns([1.2, 1.8])

with c1:
    fig1 = px.bar(
        filtered_df.sort_values(by="Customers", ascending=False),
        x="Channel",
        y="Customers",
        color="Channel",
        title="Customers by Channel",
        color_discrete_sequence=["#1d4ed8", "#2563eb", "#60a5fa", "#93c5fd", "#bfdbfe"]
    )
    fig1.update_layout(showlegend=False)
    fig1 = style_chart(fig1, height=340)

    st.markdown("<div class='tile'>", unsafe_allow_html=True)
    st.plotly_chart(fig1, use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)

with c2:
    fig2 = go.Figure(go.Funnel(
        y=["Leads", "Proposals", "Customers"],
        x=[total_leads, total_proposals, total_customers],
        textinfo="value+percent previous",
        textfont=dict(
            color="black",
            size=16
        )
    ))
    fig2.update_traces(marker=dict(color=["#93c5fd", "#2563eb", "#0f766e"]))
    fig2.update_layout(
        title="Overall Funnel",
        height=340,
        font=dict(
            family="Arial",
            size=13,
            color="black"
        ),
        title_font=dict(
            size=16,
            color="#1e3a8a"
        ),
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(l=10, r=10, t=35, b=10)
    )

    st.markdown("<div class='tile'>", unsafe_allow_html=True)
    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)

# --------------------------------------------------
# CHART ROW 2
# --------------------------------------------------
c3, c4, c5 = st.columns(3)

with c3:
    fig3 = px.bar(
        filtered_df.sort_values(by="Lead to Proposal %", ascending=False),
        x="Channel",
        y="Lead to Proposal %",
        title="Lead to Proposal Rate",
        color="Lead to Proposal %",
        color_continuous_scale="Blues"
    )
    fig3.update_layout(coloraxis_showscale=False)
    fig3 = style_chart(fig3, height=300)

    st.markdown("<div class='tile'>", unsafe_allow_html=True)
    st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)

with c4:
    fig4 = px.bar(
        filtered_df.sort_values(by="Lead to Customer %", ascending=False),
        x="Channel",
        y="Lead to Customer %",
        title="Lead to Customer Rate",
        color="Lead to Customer %",
        color_continuous_scale="Tealgrn"
    )
    fig4.update_layout(coloraxis_showscale=False)
    fig4 = style_chart(fig4, height=300)

    st.markdown("<div class='tile'>", unsafe_allow_html=True)
    st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)

with c5:
    fig5 = px.scatter(
        filtered_df,
        x="Spend",
        y="Customers",
        size="Leads",
        color="Channel",
        title="Spend vs Customers",
        size_max=40,
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    fig5.update_traces(marker=dict(opacity=0.85))
    fig5 = style_chart(fig5, height=300)

    st.markdown("<div class='tile'>", unsafe_allow_html=True)
    st.plotly_chart(fig5, use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)

# --------------------------------------------------
# CHART ROW 3
# --------------------------------------------------
c6, c7 = st.columns(2)

with c6:
    if "Month" in filtered_df.columns:
        month_stage = filtered_df.groupby("Month", as_index=False)[["Leads", "Proposals", "Customers"]].sum()
        month_melt = month_stage.melt(
            id_vars="Month",
            value_vars=["Leads", "Proposals", "Customers"],
            var_name="Stage",
            value_name="Count"
        )

        fig6 = px.line(
            month_melt,
            x="Month",
            y="Count",
            color="Stage",
            markers=True,
            title="Stage Trend by Month",
            color_discrete_sequence=["#93c5fd", "#2563eb", "#0f766e"]
        )
    else:
        compare_df = filtered_df.melt(
            id_vars="Channel",
            value_vars=["Leads", "Proposals", "Customers"],
            var_name="Stage",
            value_name="Count"
        )

        fig6 = px.line(
            compare_df,
            x="Stage",
            y="Count",
            color="Channel",
            markers=True,
            title="Stage-wise Channel Comparison"
        )

    fig6 = style_chart(fig6, height=300)

    st.markdown("<div class='tile'>", unsafe_allow_html=True)
    st.plotly_chart(fig6, use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)

with c7:
    fig7 = px.bar(
        filtered_df,
        x="Channel",
        y="Spend",
        title="Spend by Channel",
        color="Channel",
        color_discrete_sequence=["#bfdbfe", "#93c5fd", "#60a5fa", "#2563eb", "#1d4ed8"]
    )
    fig7.update_layout(showlegend=False)
    fig7 = style_chart(fig7, height=300)

    st.markdown("<div class='tile'>", unsafe_allow_html=True)
    st.plotly_chart(fig7, use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)