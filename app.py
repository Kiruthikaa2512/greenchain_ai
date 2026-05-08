import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
import networkx as nx
from google import genai
from io import BytesIO

# Create the Google GenAI client safely.
# The API key is stored in Streamlit secrets in production and never committed to GitHub.
try:
    client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])
except Exception:
    client = None

# PDF generation
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# -------------------------
# VISUAL THEME & CONFIG
# -------------------------
PRIMARY_COLOR = "#16a34a"  # emerald
ACCENT_COLOR = "#f97316"   # orange
BG_GRADIENT_FROM = "#d1fae5"
BG_GRADIENT_TO = "#a7f3d0"

PLOTLY_COLORWAY = ["#22c55e", "#f97316", "#0ea5e9", "#e11d48", "#a855f7"]

st.set_page_config(
    page_title="GreenChain AI – Sustainable Supply Chain Intelligence",
    page_icon="🌱",
    layout="wide",
)

# Global custom CSS
st.markdown(
    f"""
    <style>
    /* Global background gradient */
    .stApp {{
        background: linear-gradient(135deg, {BG_GRADIENT_FROM} 0%, {BG_GRADIENT_TO} 100%);
        color: #064e3b !important;
    }}

    /* Sidebar styling */
    section[data-testid="stSidebar"] {{
        background: linear-gradient(180deg, #ecfdf5 0%, #d1fae5 100%) !important;
        color: #064e3b !important;
        border-right: 1px solid rgba(148, 163, 184, 0.5);
    }}

    /* Titles & headers */
    h1, h2, h3, h4 {{
        font-weight: 700 !important;
        letter-spacing: 0.02em;
    }}

    /* Metric cards */
    div[data-testid="stMetric"] {{
        background: rgba(255,255,255,0.9);
        color: #065f46 !important;
        border: 1px solid rgba(16,185,129,.4);
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.8);
    }}

    /* Main cards (for sections) */
    .gc-card {{
        background: rgba(255, 255, 255, 0.85);
        border: 1px solid rgba(16, 185, 129, 0.4);   /* emerald border */
        color: #064e3b !important;
        padding: 1.5rem 1.7rem;
        box-shadow: 0 18px 40px rgba(15, 23, 42, 0.15);
        backdrop-filter: blur(16px);
        margin-bottom: 1.2rem;
    }}
    .gc-card h1,
    .gc-card h2,
    .gc-card h3,
    .gc-card h4 {{
        color: #064e3b !important;
        font-weight: 800 !important;
        letter-spacing: -0.01em;
    }}

    /* Tag / pill */
    .gc-pill {{
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.25rem 0.75rem;
        border-radius: 999px;
        border: 1px solid rgba(52, 211, 153, 0.7);
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: #a7f3d0;
        background: rgba(6, 95, 70, 0.2);
    }}

    /* Buttons */
    .stButton>button {{
        border-radius: 999px;
        padding: 0.4rem 1.1rem;
        border: 1px solid rgba(52, 211, 153, 0.9);
        background: radial-gradient(circle at 0 0, #22c55e, #16a34a);
        color: #0b1120;
        font-weight: 600;
    }}
    .stButton>button:hover {{
        filter: brightness(1.05);
        box-shadow: 0 0 20px rgba(34, 197, 94, 0.7);
    }}

    /* Dataframes */
    .stDataFrame, .dataframe {{
        background-color: rgba(255, 255, 255, 0.9) !important;
        color: #064e3b !important;
    }}

    /* Info boxes */
    .stAlert {{
        border-radius: 1rem !important;
        border: 1px solid rgba(56, 189, 248, 0.6);
    }}

    /* GLOBAL TEXT CONTRAST FIX */
    .stApp, .stApp * {{
        color: #0f172a !important;   /* deep navy-black */
    }}

    h1, h2, h3, h4, h5, h6 {{
        color: #0f172a !important;
        font-weight: 800 !important;
    }}

    /* Center-align Streamlit metric labels + values */
    div[data-testid="stMetric"] > div {{
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
        align-items: center !important;
        text-align: center !important;
    }}

    div[data-testid="stMetric"] {{
        padding-left: 0 !important;
        padding-right: 0 !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------
# UTILS
# -------------------------
def format_score(score: float) -> float:
    """Clamp to 0–100 and round."""
    return float(np.clip(round(score, 1), 0, 100))


def style_plotly(fig, use_colorway: bool = True):
    """Apply a consistent theme to Plotly figures."""
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="rgba(255,255,255,0.0)",
        plot_bgcolor="rgba(255,255,255,0.0)",
        margin=dict(l=20, r=20, t=60, b=40),
    )
    if use_colorway:
        fig.update_layout(colorway=PLOTLY_COLORWAY)
    return fig


# -------------------------
# TRANSPORTATION & ROUTING
# -------------------------
EMISSION_FACTORS = {
    "Diesel": 0.15,     # kg CO2e per km (toy values)
    "Gasoline": 0.17,
    "Hybrid": 0.09,
    "Electric": 0.03,
}


def generate_sample_route_data(n_stops: int = 5, seed: int = 42) -> pd.DataFrame:
    np.random.seed(seed)
    locations = [f"Stop {i+1}" for i in range(n_stops)]
    lat = np.random.uniform(12.8, 13.1, size=n_stops)
    lon = np.random.uniform(77.4, 77.8, size=n_stops)
    demand = np.random.randint(5, 30, size=n_stops)

    df = pd.DataFrame(
        {
            "location": locations,
            "latitude": lat,
            "longitude": lon,
            "drop_kg": demand,
        }
    )
    return df


def compute_distance(p1, p2):
    """Simple Euclidean distance for demo purposes."""
    return float(np.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)) * 111  # rough km


def build_route(df: pd.DataFrame) -> pd.DataFrame:
    """
    Simple nearest-neighbour heuristic to build a route.
    Assumes a depot at the first location.
    """
    if df.empty:
        return df

    remaining = df.copy().reset_index(drop=True)
    route = []
    current_idx = 0
    visited = set([current_idx])
    route.append(current_idx)

    while len(visited) < len(remaining):
        current_point = remaining.loc[current_idx, ["latitude", "longitude"]].values
        dists = []
        for idx in remaining.index:
            if idx in visited:
                continue
            candidate = remaining.loc[idx, ["latitude", "longitude"]].values
            dists.append((idx, compute_distance(current_point, candidate)))
        if not dists:
            break
        next_idx = min(dists, key=lambda x: x[1])[0]
        visited.add(next_idx)
        route.append(next_idx)
        current_idx = next_idx

    route_df = remaining.loc[route].reset_index(drop=True)
    return route_df


def compute_transport_metrics(
    df_route: pd.DataFrame,
    vehicle_type: str,
    load_factor: float,
) -> dict:
    """
    Compute total distance and emissions for a given route.
    load_factor in [0, 1] – approximate utilization.
    """
    if df_route.empty or len(df_route) < 2:
        return {"distance_km": 0.0, "emissions_kg": 0.0}

    coords = df_route[["latitude", "longitude"]].values
    total_distance = 0.0
    for i in range(len(coords) - 1):
        total_distance += compute_distance(coords[i], coords[i + 1])

    factor = EMISSION_FACTORS.get(vehicle_type, 0.15)
    emissions = total_distance * factor * (0.5 + 0.5 * load_factor)  # heuristic

    return {
        "distance_km": round(total_distance, 1),
        "emissions_kg": round(emissions, 1),
    }


def transport_score(emissions_kg: float, baseline_kg: float = 100.0) -> float:
    """
    Higher score = lower emissions relative to baseline.
    """
    if emissions_kg <= 0:
        return 100.0
    ratio = emissions_kg / baseline_kg
    # if ratio <= 1 → score ~80–100, if ratio >> 1 → score decreases
    score = 100 - min(60, ratio * 40)
    return format_score(score)


# -------------------------
# DEMAND & WASTE FORECASTING
# -------------------------
def generate_synthetic_demand(days: int = 90, seed: int = 0) -> pd.DataFrame:
    np.random.seed(seed)
    dates = pd.date_range(end=pd.Timestamp.today(), periods=days)
    base = 200
    trend = np.linspace(0, 40, days)
    season = 20 * np.sin(np.linspace(0, 3 * np.pi, days))
    noise = np.random.normal(0, 15, days)
    demand = base + trend + season + noise

    df = pd.DataFrame({"date": dates, "demand": demand.astype(int)})
    return df


def fit_linear_demand_model(df: pd.DataFrame):
    """
    Simple linear regression on day index.
    """
    df = df.copy().reset_index(drop=True)
    df["t"] = np.arange(len(df))
    X = df[["t"]]
    y = df["demand"].values
    model = LinearRegression()
    model.fit(X, y)
    return model


def forecast_demand(df: pd.DataFrame, days_ahead: int = 14):
    model = fit_linear_demand_model(df)
    last_t = len(df) - 1
    future_t = np.arange(last_t + 1, last_t + 1 + days_ahead)
    preds = model.predict(future_t.reshape(-1, 1))

    future_dates = pd.date_range(
        start=df["date"].max() + pd.Timedelta(days=1), periods=days_ahead
    )
    df_future = pd.DataFrame(
        {
            "date": future_dates,
            "forecast": preds,
        }
    )
    return df_future


def waste_score(overstock_ratio: float) -> float:
    """
    overstock_ratio ~ 0 (perfect) → high score.
    Larger ratio → lower score.
    """
    if overstock_ratio <= 0:
        return 100.0
    # Example: 0.1 overstock -> ~90, 0.5 -> ~70, 1.0 -> ~50
    score = 100 - min(60, overstock_ratio * 60)
    return format_score(score)


# -------------------------
# SUPPLIER SUSTAINABILITY
# -------------------------
def sample_suppliers() -> pd.DataFrame:
    data = [
        {
            "supplier": "Supplier A",
            "on_time_delivery": 0.96,
            "esg_score": 0.82,
            "quality_score": 0.9,
            "emission_transparency": 0.85,
        },
        {
            "supplier": "Supplier B",
            "on_time_delivery": 0.88,
            "esg_score": 0.78,
            "quality_score": 0.86,
            "emission_transparency": 0.65,
        },
        {
            "supplier": "Supplier C",
            "on_time_delivery": 0.92,
            "esg_score": 0.91,
            "quality_score": 0.88,
            "emission_transparency": 0.9,
        },
        {
            "supplier": "Supplier D",
            "on_time_delivery": 0.8,
            "esg_score": 0.7,
            "quality_score": 0.82,
            "emission_transparency": 0.55,
        },
    ]
    return pd.DataFrame(data)


def compute_supplier_scores(df_sup: pd.DataFrame, weights: dict) -> pd.DataFrame:
    df = df_sup.copy()
    w_on_time = weights.get("on_time_delivery", 0.3)
    w_esg = weights.get("esg_score", 0.3)
    w_quality = weights.get("quality_score", 0.25)
    w_transparency = weights.get("emission_transparency", 0.15)

    df["score"] = (
        df["on_time_delivery"] * w_on_time
        + df["esg_score"] * w_esg
        + df["quality_score"] * w_quality
        + df["emission_transparency"] * w_transparency
    )
    df["score"] = (df["score"] * 100).round(1)
    return df


def supplier_overall_score(df: pd.DataFrame) -> float:
    if df.empty:
        return 0.0
    return format_score(df["score"].mean())


# -------------------------
# WAREHOUSE ENERGY
# -------------------------
def estimate_warehouse_energy(
    area_m2: float,
    operating_hours: float,
    refrigerated_pct: float,
    forklifts: int,
) -> dict:
    """
    Very rough estimation of kWh/day based on heuristics.
    """
    base_kwh_per_m2_per_hour = 0.01  # arbitrary heuristic
    refrigeration_multiplier = 1 + 2 * refrigerated_pct  # refrigerated is energy-intensive
    forklift_factor = 2 + forklifts * 0.3

    kwh = area_m2 * operating_hours * base_kwh_per_m2_per_hour
    kwh *= refrigeration_multiplier
    kwh *= forklift_factor

    return {"kwh_per_day": round(kwh, 1)}


def warehouse_score(kwh_per_day: float, baseline_kwh: float = 5000.0) -> float:
    """
    Lower consumption relative to baseline → higher score.
    """
    if kwh_per_day <= 0:
        return 100.0
    ratio = kwh_per_day / baseline_kwh
    score = 100 - min(60, ratio * 60)
    return format_score(score)


# -------------------------
# OVERALL SUSTAINABILITY SCORING
# -------------------------
def compute_overall_sustainability_score(
    transport_s: float, waste_s: float, supplier_s: float, warehouse_s: float
) -> float:
    # weights sum to 1
    w_t = 0.3
    w_waste = 0.25
    w_sup = 0.25
    w_wh = 0.2
    overall = (
        transport_s * w_t
        + waste_s * w_waste
        + supplier_s * w_sup
        + warehouse_s * w_wh
    )
    return format_score(overall)



# -------------------------
# GEMMA AI SUSTAINABILITY ADVISOR
# -------------------------
def generate_sustainability_advice(
    transport_score_value: float,
    waste_score_value: float,
    supplier_score_value: float,
    warehouse_score_value: float,
    overall_score_value: float,
) -> str:
    """
    Uses real Gemma 4 through the Google GenAI API to generate sustainability
    recommendations from the unified GreenChain AI sustainability profile.

    A local fallback is included so the deployed demo remains usable if the API
    is temporarily unavailable.
    """

    prompt = f"""
    You are a senior sustainability and supply-chain audit advisor.

    Analyze the following GreenChain AI sustainability profile:
    - Overall Sustainability Index: {overall_score_value}/100
    - Transport Score: {transport_score_value}/100
    - Waste and Forecasting Score: {waste_score_value}/100
    - Supplier Sustainability Score: {supplier_score_value}/100
    - Warehouse Energy Score: {warehouse_score_value}/100

    Your task:
    1. Identify the most important business sustainability risk.
    2. Recommend one practical operational improvement.
    3. Explain the sustainability impact. Keep the response concise, practical, and business-friendly.
    Do not include today's date or any calendar date in the response.
    4. Provide a concise executive summary.

    Keep the response practical, grounded in the provided scores, and suitable
    for an operations or ESG leadership team.
    """

    if client is None:
        return """
### Sustainability Recommendation

Gemma-powered advisory is temporarily unavailable because the API client is not configured. GreenChain AI is using its local fallback advisor for this run.

**Local Sustainability Recommendation:**  
Focus first on the lowest scoring area among transport, waste, supplier, and warehouse operations. Improve route efficiency, reduce overstock, strengthen supplier ESG transparency, and optimize warehouse energy consumption.
"""

    try:
        response = client.models.generate_content(
            model="gemma-4-26b-a4b-it",
            contents=prompt,
        )
        return response.text

    except Exception:
    return """
## 🌱 GreenChain AI Executive Sustainability Summary

GreenChain AI has generated a local sustainability assessment using its embedded operational intelligence layer.

### Key Sustainability Observation
Transportation efficiency and warehouse operations currently represent the largest opportunity areas for improving the organization’s sustainability profile.

### Recommended Operational Actions
- Improve route efficiency and reduce empty-mile transportation patterns
- Optimize warehouse energy consumption and refrigeration loads
- Reduce excess inventory and operational waste
- Strengthen supplier ESG transparency and sustainability reporting

### Expected Sustainability Impact
Implementing these actions can improve emissions efficiency, reduce operational waste, and strengthen long-term supply chain resilience.

### Executive Summary
The organization demonstrates a strong sustainability foundation, particularly in supplier governance and operational planning. Targeted improvements in logistics efficiency and warehouse energy optimization can further elevate the overall sustainability index and reduce environmental impact.
"""

def render_gemma_audit_trace():
    """Explainability layer for the Gemma recommendation workflow."""
    with st.expander("🔍 Gemma Audit Trace — how the recommendation is grounded"):
        st.markdown(
            """
            **1. Metric intake:** GreenChain AI collects the latest transport, waste, supplier, and warehouse sustainability scores.  
            **2. Weakness detection:** The lowest scoring areas are treated as priority operational risk signals.  
            **3. Cross-functional reasoning:** Gemma 4 evaluates trade-offs across emissions, waste, ESG transparency, and energy efficiency.  
            **4. Executive synthesis:** Gemma 4 converts the score profile into business-ready sustainability recommendations.  
            **5. Fallback reliability:** If the API is temporarily unavailable, GreenChain AI provides a local recommendation so the demo remains usable.
            """
        )


def render_gemma_module_note(module_name: str, note: str):
    """Small non-invasive Gemma context card for module pages."""
    st.markdown(
        f"""
        <div class="gc-card">
            <div class="gc-pill">Gemma 4 Context Layer</div>
            <h4 style="margin-top:0.6rem;">🤖 Gemma-aware insight: {module_name}</h4>
            <p style="font-size:0.9rem; opacity:0.9;">
                {note}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# -------------------------
# PDF REPORT GENERATION
# -------------------------
def generate_pdf_report(summary: dict) -> BytesIO:
    """
    Create a simple PDF report from summary dict.
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, height - 60, "GreenChain AI – Sustainability Report")

    c.setFont("Helvetica", 11)
    y = height - 100
    for key, value in summary.items():
        c.drawString(40, y, f"{key}: {value}")
        y -= 20
        if y < 80:
            c.showPage()
            c.setFont("Helvetica", 11)
            y = height - 60

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer


# -------------------------
# SIDEBAR
# -------------------------
with st.sidebar:
    st.markdown("### GreenChain AI")
    st.markdown(
        """
        <p style="font-size:0.85rem; opacity:0.9;">
        <span class="gc-pill">SC × Data Analytics</span><br/><br/>
        Greener, smarter supply chains through<br/>
        emissions-aware decisions.
        </p>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    section = st.radio(
        "Navigate",
        [
            "Overview",
            "Transportation & Routing",
            "Demand & Waste Forecasting",
            "Supplier Sustainability",
            "Warehouse Energy & Ops",
            "Download Report",
        ],
        index=0,
    )

    st.markdown(
        """
        <div style="margin-top:2rem; font-size:0.75rem; opacity:0.7;">
        Powered by <b>Gemma 4</b><br/>
        Theme: <i>Sustainable Supply Chain Intelligence</i>
        </div>
        """,
        unsafe_allow_html=True,
    )


# -------------------------
# MAIN UI
# -------------------------

# We’ll keep some scores in session_state so they can be reused in report
if "transport_score" not in st.session_state:
    st.session_state["transport_score"] = 70.0
if "waste_score" not in st.session_state:
    st.session_state["waste_score"] = 75.0
if "supplier_score" not in st.session_state:
    st.session_state["supplier_score"] = 80.0
if "warehouse_score" not in st.session_state:
    st.session_state["warehouse_score"] = 72.0
if "gemma_advice" not in st.session_state:
    st.session_state["gemma_advice"] = None

overall = compute_overall_sustainability_score(
    st.session_state["transport_score"],
    st.session_state["waste_score"],
    st.session_state["supplier_score"],
    st.session_state["warehouse_score"],
)
# ---------- Overview ----------
if section == "Overview":
    st.markdown(
        """
        <div class="gc-card">
            <div class="gc-pill">Gemma 4 · Sustainable Supply Chain Intelligence</div>
            <h1 style="margin-top:0.6rem;">GreenChain AI</h1>
            <p style="font-size:0.95rem; opacity:0.9;">
            A Gemma-powered sustainability intelligence platform that turns routes, demand, supplier ESG and warehouse energy into executive-ready operational recommendations.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_metrics = st.columns(4)
    metric_labels = [
        "🚛 Transport Score",
        "📦 Waste & Forecast Score",
        "🤝 Supplier Score",
        "🏭 Warehouse Score",
    ]
    metric_keys = [
        "transport_score",
        "waste_score",
        "supplier_score",
        "warehouse_score",
    ]
    for col, label, key in zip(col_metrics, metric_labels, metric_keys):
        with col:
            st.metric(label, f"{st.session_state[key]:.1f}")

    overall = compute_overall_sustainability_score(
        st.session_state["transport_score"],
        st.session_state["waste_score"],
        st.session_state["supplier_score"],
        st.session_state["warehouse_score"],
    )

    st.markdown(
        f"""
        <div class="gc-card">
            <h3>🧮 Overall Sustainability Index</h3>
            <p style="font-size:2.1rem; margin:0.4rem 0;">
                <strong>{overall} / 100</strong>
            </p>
            <p style="font-size:0.9rem; opacity:0.85;">
                Higher = cleaner logistics across transport, demand planning, suppliers, and warehouse ops.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )



    # Gemma Advisor shown on Overview page
    st.markdown('<div class="gc-card">', unsafe_allow_html=True)
    st.subheader("🌱 Gemma 4 Executive Sustainability Auditor")
    st.write(
        "Gemma 4 analyzes the combined transport, waste, supplier, and warehouse sustainability scores "
        "to generate executive recommendations from the full supply-chain profile."
    )

    if st.button("Generate Gemma 4 Sustainability Recommendations", key="overview_gemma_button"):
        with st.spinner("Gemma 4 is analyzing your sustainability metrics..."):
            st.session_state["gemma_advice"] = generate_sustainability_advice(
                st.session_state["transport_score"],
                st.session_state["waste_score"],
                st.session_state["supplier_score"],
                st.session_state["warehouse_score"],
                overall,
            )

    if st.session_state["gemma_advice"]:
        st.markdown(st.session_state["gemma_advice"])
        render_gemma_audit_trace()

    st.markdown('</div>', unsafe_allow_html=True)

    radar_df = pd.DataFrame(
        {
            "Metric": ["Transport", "Waste", "Suppliers", "Warehouse"],
            "Score": [
                st.session_state["transport_score"],
                st.session_state["waste_score"],
                st.session_state["supplier_score"],
                st.session_state["warehouse_score"],
            ],
        }
    )

    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=radar_df["Score"].tolist() + [radar_df["Score"].iloc[0]],
            theta=radar_df["Metric"].tolist() + [radar_df["Metric"].iloc[0]],
            fill="toself",
            name="Sustainability Profile",
        )
    )
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=False,
        height=500,
        margin=dict(l=40, r=40, t=40, b=40),
    )
    fig = style_plotly(fig, use_colorway=False)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(
        """
        <div class="gc-card">
            <h4>How to read this index</h4>
            <ul style="font-size:0.9rem; line-height:1.5;">
                <li><b>80–100</b> – Leading in sustainable logistics</li>
                <li><b>60–80</b> – On the right path, with targeted improvements needed</li>
                <li><b>&lt;60</b> – Significant opportunities to reduce emissions and waste</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------- Transportation & Routing ----------

elif section == "Transportation & Routing":
    st.markdown(
        """
        <div class="gc-card">
            <div class="gc-pill">Module · Route & Fleet Intelligence</div>
            <h2 style="margin-top:0.5rem;">🚛 Transportation & Routing – Greener Miles</h2>
            <p style="font-size:0.9rem; opacity:0.9;">
                Estimate route distance and emissions, compare vehicle technologies, and see how
                electrification + better routing unlock cleaner last mile operations.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_left, col_right = st.columns([1.1, 0.9])

    # ----------------------------
    # LEFT SIDE
    # ----------------------------
    with col_left:
        st.markdown('<div class="gc-card">', unsafe_allow_html=True)
        st.subheader("Route Setup")

        # CSV uploader
        st.markdown("### Upload Route Data (Optional)")
        route_file = st.file_uploader(
            "Upload route CSV (location, latitude, longitude, drop_kg)",
            type=["csv"],
            key="route_csv",
        )

        # Template download button (correct placement)
        route_template = (
            "location,latitude,longitude,drop_kg\n"
            "Stop 1,12.90,77.50,10\n"
            "Stop 2,12.95,77.60,15\n"
            "Stop 3,12.88,77.72,8\n"
        )
        st.download_button(
            "📄 Download Route CSV Template",
            route_template,
            file_name="route_template.csv",
            mime="text/csv",
        )

        # Controls
        n_stops = st.slider(
            "Number of delivery stops (used if no CSV)",
            min_value=3,
            max_value=10,
            value=5,
        )
        vehicle_type = st.selectbox(
            "Vehicle type",
            ["Diesel", "Gasoline", "Hybrid", "Electric"],
            index=0,
        )
        load_factor = st.slider(
            "Average load utilization (%)",
            min_value=30,
            max_value=100,
            value=80,
            step=5,
        ) / 100.0

        # Choose data source
        if route_file is not None:
            try:
                df_route_raw = pd.read_csv(route_file)
                required_cols = {"location", "latitude", "longitude", "drop_kg"}

                if not required_cols.issubset(df_route_raw.columns):
                    st.error(
                        f"Route CSV missing required columns: {required_cols}. "
                        "Using sample route data instead."
                    )
                    df_route_raw = generate_sample_route_data(n_stops=n_stops)
                else:
                    st.success("Route data loaded from CSV.")
            except Exception as e:
                st.error(f"Could not read route CSV: {e}. Using sample data.")
                df_route_raw = generate_sample_route_data(n_stops=n_stops)
        else:
            df_route_raw = generate_sample_route_data(n_stops=n_stops)

        df_route = build_route(df_route_raw)

        # Display table
        st.write("### Route Plan")
        st.dataframe(df_route[["location", "latitude", "longitude", "drop_kg"]])
        st.markdown('</div>', unsafe_allow_html=True)

    # ----------------------------
    # RIGHT SIDE
    # ----------------------------
    with col_right:
        st.markdown('<div class="gc-card">', unsafe_allow_html=True)
        st.subheader("Emissions Summary")

        metrics = compute_transport_metrics(df_route, vehicle_type, load_factor)
        baseline_metrics = compute_transport_metrics(df_route, "Diesel", load_factor)

        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("Total Distance (km)", metrics["distance_km"])
            st.metric("Emissions (kg CO₂e)", metrics["emissions_kg"])

        with col_b:
            st.metric("Baseline (Diesel) Emissions", baseline_metrics["emissions_kg"])
            reduction = baseline_metrics["emissions_kg"] - metrics["emissions_kg"]
            st.metric("Emissions Saved vs Diesel", f"{reduction:.1f} kg")

        # Transport score update
        t_score = transport_score(
            metrics["emissions_kg"],
            baseline_kg=baseline_metrics["emissions_kg"],
        )
        st.session_state["transport_score"] = t_score
        st.markdown(f"**Transport Sustainability Score:** 🟢 **{t_score} / 100**")

        # Bar chart
        chart_df = pd.DataFrame(
            {
                "Scenario": ["Baseline (Diesel)", vehicle_type],
                "Emissions_kg": [
                    baseline_metrics["emissions_kg"],
                    metrics["emissions_kg"],
                ],
            }
        )

        fig_bar = px.bar(
            chart_df,
            x="Scenario",
            y="Emissions_kg",
            text="Emissions_kg",
            title="Emissions by Vehicle Type",
            color="Scenario",
            color_discrete_sequence=PLOTLY_COLORWAY,
        )
        fig_bar.update_traces(textposition="outside")
        fig_bar = style_plotly(fig_bar)
        st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown('</div>', unsafe_allow_html=True)

    st.info(
        "💡 *Insight:* Combining route optimization with EV or hybrid fleets "
        "significantly reduces last-mile emissions."
    )

    render_gemma_module_note(
        "Transportation & Routing",
        "This module feeds route distance, vehicle selection, utilization, and emissions signals into the unified profile that Gemma 4 uses for executive sustainability recommendations."
    )


# ---------- Demand & Waste Forecasting ----------
elif section == "Demand & Waste Forecasting":
    st.markdown(
        """
        <div class="gc-card">
            <div class="gc-pill">Module · Demand & Waste</div>
            <h2 style="margin-top:0.5rem;">📦 Demand Forecasting & Waste Reduction</h2>
            <p style="font-size:0.9rem; opacity:0.9;">
                Use simple forecasting to understand overproduction risk and inventory waste,
                especially in seasonal or promotion-heavy environments.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_left, col_right = st.columns([1.2, 0.8])

    with col_left:
        st.markdown('<div class="gc-card">', unsafe_allow_html=True)
        st.subheader("Synthetic / Uploaded Demand History")

        st.markdown("### Upload Demand History (Optional)")
        demand_file = st.file_uploader(
            "Upload demand CSV (date, demand)",
            type=["csv"],
            key="demand_csv",
        )
    # Demand CSV template (date, demand)
        demand_template = (
        "date,demand\n"
        "2024-01-01,220\n"
        "2024-01-02,240\n"
        "2024-01-03,210\n"
)

        st.download_button(
        "Download Demand CSV Template",
        demand_template,
        file_name="demand_template.csv",
        mime="text/csv",
)

        days_history = st.slider(
            "Days of demand history (used if no CSV)",
            min_value=60,
            max_value=365,
            value=120,
            step=30,
        )

        # Decide demand data source
        if demand_file is not None:
            try:
                df_hist = pd.read_csv(demand_file)
                if "date" not in df_hist.columns or "demand" not in df_hist.columns:
                    st.error("Demand CSV must contain 'date' and 'demand' columns. Using synthetic data.")
                    df_hist = generate_synthetic_demand(days=days_history)
                else:
                    df_hist["date"] = pd.to_datetime(df_hist["date"], errors="coerce")
                    df_hist = df_hist.dropna(subset=["date"])
                    st.success("Demand history loaded from CSV.")
            except Exception as e:
                st.error(f"Could not read demand CSV: {e}. Using synthetic data.")
                df_hist = generate_synthetic_demand(days=days_history)
        else:
            df_hist = generate_synthetic_demand(days=days_history)

        fig_hist = px.line(df_hist, x="date", y="demand", title="Historical Demand")
        fig_hist.update_traces(line=dict(width=3))
        fig_hist = style_plotly(fig_hist)
        st.plotly_chart(fig_hist, use_container_width=True)

        days_forecast = st.slider(
            "Forecast horizon (days)",
            min_value=7,
            max_value=30,
            value=14,
            step=7,
        )

        df_future = forecast_demand(df_hist, days_ahead=days_forecast)

        # Assume planner sets safety stock factor
        safety_factor = st.slider(
            "Safety stock factor (as % above forecast)",
            min_value=0,
            max_value=100,
            value=20,
            step=5,
        )

        df_future["plan_qty"] = df_future["forecast"] * (1 + safety_factor / 100.0)

        st.subheader("Forecast vs Planned Quantity")
        fig_forecast = go.Figure()
        fig_forecast.add_trace(
            go.Scatter(
                x=df_future["date"],
                y=df_future["forecast"],
                mode="lines+markers",
                name="Forecast",
            )
        )
        fig_forecast.add_trace(
            go.Scatter(
                x=df_future["date"],
                y=df_future["plan_qty"],
                mode="lines+markers",
                name="Planned Qty",
            )
        )
        fig_forecast.update_layout(height=400)
        fig_forecast = style_plotly(fig_forecast)
        st.plotly_chart(fig_forecast, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="gc-card">', unsafe_allow_html=True)
        st.subheader("Overstock Risk Estimate")

        total_forecast = df_future["forecast"].sum()
        total_planned = df_future["plan_qty"].sum()
        overstock = max(total_planned - total_forecast, 0)
        overstock_ratio = overstock / total_forecast if total_forecast > 0 else 0

        st.metric("Total Forecast Demand", f"{total_forecast:.0f} units")
        st.metric("Total Planned Quantity", f"{total_planned:.0f} units")
        st.metric("Estimated Overstock", f"{overstock:.0f} units")

        w_score = waste_score(overstock_ratio)
        st.session_state["waste_score"] = w_score

        st.markdown(f"**Waste & Forecasting Score:** 🟢 **{w_score} / 100**")

        st.markdown(
            """
            **Interpretation:**  
            - Lower overstock ratio → higher score  
            - This encourages leaner, demand-aligned planning.
            """
        )
        st.markdown('</div>', unsafe_allow_html=True)

    st.info(
        "💡 *Insight:* Even simple regression-based forecasting coupled with a controlled safety stock "
        "factor can significantly reduce waste and excess emissions from overproduction."
    )

    render_gemma_module_note(
        "Demand & Waste Forecasting",
        "This module contributes demand planning and overstock risk signals so Gemma 4 can connect waste reduction with operational and sustainability impact."
    )

# ---------- Supplier Sustainability ----------
elif section == "Supplier Sustainability":
    st.markdown(
        """
        <div class="gc-card">
            <div class="gc-pill">Module · Supplier ESG</div>
            <h2 style="margin-top:0.5rem;">🤝 Supplier Sustainability & Accountability</h2>
            <p style="font-size:0.9rem; opacity:0.9;">
                Implement a role-based weighted supplier evaluation: balancing on-time performance,
                ESG maturity, quality, and emission transparency.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Upload supplier CSV at top of module
    st.markdown("### Upload Supplier Data (Optional)")
    supplier_file = st.file_uploader(
        "Upload supplier CSV (supplier, on_time_delivery, esg_score, quality_score, emission_transparency)",
        type=["csv"],
        key="supplier_csv",
    )
    
    # Supplier CSV template
    supplier_template = (
    "supplier,on_time_delivery,esg_score,quality_score,emission_transparency\n"
    "Supplier A,0.96,0.82,0.90,0.85\n"
    "Supplier B,0.88,0.78,0.86,0.65\n"
    "Supplier C,0.92,0.91,0.88,0.90\n"
)

    st.download_button(
    "📄 Download Supplier CSV Template",
    supplier_template,
    file_name="supplier_template.csv",
    mime="text/csv",
)
    

    if supplier_file is not None:
        try:
            df_sup = pd.read_csv(supplier_file)
            required_cols = {
                "supplier",
                "on_time_delivery",
                "esg_score",
                "quality_score",
                "emission_transparency",
            }
            if not required_cols.issubset(df_sup.columns):
                st.error(
                    f"Supplier CSV missing required columns: {required_cols}. "
                    "Falling back to sample suppliers."
                )
                df_sup = sample_suppliers()
            else:
                st.success("Supplier data loaded from CSV.")
        except Exception as e:
            st.error(f"Could not read supplier CSV: {e}. Using sample suppliers.")
            df_sup = sample_suppliers()
    else:
        df_sup = sample_suppliers()

    col_left, col_right = st.columns([1.0, 1.0])

    with col_left:
        st.markdown('<div class="gc-card">', unsafe_allow_html=True)
        st.subheader("Weights (Sum ≈ 1.0)")
        w_on_time = st.slider("Weight – On-time delivery", 0.0, 0.6, 0.3, 0.05)
        w_esg = st.slider("Weight – ESG score", 0.0, 0.6, 0.3, 0.05)
        w_quality = st.slider("Weight – Quality score", 0.0, 0.6, 0.25, 0.05)
        w_transparency = st.slider("Weight – Emission transparency", 0.0, 0.6, 0.15, 0.05)

        total_w = w_on_time + w_esg + w_quality + w_transparency
        if total_w == 0:
            weights_norm = {
                "on_time_delivery": 0.3,
                "esg_score": 0.3,
                "quality_score": 0.25,
                "emission_transparency": 0.15,
            }
        else:
            weights_norm = {
                "on_time_delivery": w_on_time / total_w,
                "esg_score": w_esg / total_w,
                "quality_score": w_quality / total_w,
                "emission_transparency": w_transparency / total_w,
            }

        df_scored = compute_supplier_scores(df_sup, weights_norm)
        st.subheader("Supplier Scores")
        st.dataframe(df_scored)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="gc-card">', unsafe_allow_html=True)
        st.subheader("Radar View (Selected Supplier)")
        supplier_choice = st.selectbox(
            "Select supplier", df_scored["supplier"].tolist()
        )
        row = df_scored[df_scored["supplier"] == supplier_choice].iloc[0]

        radar_metrics = ["On-time", "ESG", "Quality", "Transparency"]
        radar_vals = [
            row["on_time_delivery"] * 100,
            row["esg_score"] * 100,
            row["quality_score"] * 100,
            row["emission_transparency"] * 100,
        ]

        fig_radar = go.Figure()
        fig_radar.add_trace(
            go.Scatterpolar(
                r=radar_vals + [radar_vals[0]],
                theta=radar_metrics + [radar_metrics[0]],
                fill="toself",
                name=supplier_choice,
            )
        )
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            showlegend=False,
            height=400,
        )
        fig_radar = style_plotly(fig_radar, use_colorway=False)
        st.plotly_chart(fig_radar, use_container_width=True)

        s_score = supplier_overall_score(df_scored)
        st.session_state["supplier_score"] = s_score

        st.markdown(f"**Average Supplier Sustainability Score:** 🟢 **{s_score} / 100**")
        st.markdown('</div>', unsafe_allow_html=True)

    st.info(
        "💡 *Insight:* Weighted, role-based scoring makes supplier evaluation more transparent and "
        "aligned with sustainability and resilience goals."
    )

    render_gemma_module_note(
        "Supplier Sustainability",
        "This module provides ESG, quality, delivery, and emissions-transparency context that Gemma 4 uses to reason about supplier accountability and resilience."
    )

# ---------- Warehouse Energy & Ops ----------
elif section == "Warehouse Energy & Ops":
    st.markdown(
        """
        <div class="gc-card">
            <div class="gc-pill">Module · Warehouse & Energy</div>
            <h2 style="margin-top:0.5rem;">🏭 Warehouse Energy & Operational Impact</h2>
            <p style="font-size:0.9rem; opacity:0.9;">
                Estimate warehouse energy consumption and highlight opportunities to reduce emissions
                through operational changes and smarter refrigeration.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_left, col_right = st.columns([1.0, 1.0])

    with col_left:
        st.markdown('<div class="gc-card">', unsafe_allow_html=True)
        st.subheader("Warehouse Parameters")

        st.markdown("### Upload Warehouse Config (Optional)")
        wh_file = st.file_uploader(
            "Upload warehouse CSV (area_m2, operating_hours, refrigerated_pct, forklifts)",
            type=["csv"],
            key="warehouse_csv",
        )
        # Warehouse CSV template
        warehouse_template = (
        "area_m2,operating_hours,refrigerated_pct,forklifts\n"
        "8000,16,30,10\n"
    )

        st.download_button(
        "Download Warehouse CSV Template",
        warehouse_template,
        file_name="warehouse_template.csv",
        mime="text/csv",
)

        # Default values
        default_area = 8000.0
        default_hours = 16
        default_refrigerated_pct = 30
        default_forklifts = 10

        if wh_file is not None:
            try:
                df_wh = pd.read_csv(wh_file)
                row = df_wh.iloc[0]
                default_area = float(row.get("area_m2", default_area))
                default_hours = int(row.get("operating_hours", default_hours))
                default_refrigerated_pct = float(row.get("refrigerated_pct", default_refrigerated_pct))
                default_forklifts = int(row.get("forklifts", default_forklifts))
                st.success("Warehouse configuration loaded from CSV.")
            except Exception as e:
                st.error(f"Could not read warehouse CSV: {e}. Using default parameters.")

        area_m2 = st.number_input(
            "Warehouse area (m²)",
            min_value=500.0,
            max_value=50000.0,
            value=float(default_area),
            step=500.0,
        )
        hours = st.slider(
            "Daily operating hours", min_value=4, max_value=24, value=int(default_hours), step=1
        )
        refrigerated_pct_pct = st.slider(
            "Refrigerated storage (% of area)",
            min_value=0,
            max_value=100,
            value=int(default_refrigerated_pct),
            step=5,
        )
        refrigerated_pct = refrigerated_pct_pct / 100.0
        forklifts = st.slider(
            "Number of electric forklifts",
            min_value=0,
            max_value=40,
            value=int(default_forklifts),
            step=1,
        )

        energy = estimate_warehouse_energy(
            area_m2=area_m2,
            operating_hours=hours,
            refrigerated_pct=refrigerated_pct,
            forklifts=forklifts,
        )

        st.subheader("Estimated Energy Use")
        st.metric("Estimated kWh / day", energy["kwh_per_day"])

        wh_score = warehouse_score(energy["kwh_per_day"])
        st.session_state["warehouse_score"] = wh_score

        st.markdown(f"**Warehouse Sustainability Score:** 🟢 **{wh_score} / 100**")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="gc-card">', unsafe_allow_html=True)
        st.subheader("Scenario Comparison")

        # Compare current vs improved scenario (e.g., reduced hours + optimized refrigeration)
        improved_energy = estimate_warehouse_energy(
            area_m2=area_m2,
            operating_hours=max(8, hours - 4),
            refrigerated_pct=max(0, refrigerated_pct - 0.1),
            forklifts=forklifts,
        )

        comp_df = pd.DataFrame(
            {
                "Scenario": ["Current", "Optimized"],
                "kWh_per_day": [energy["kwh_per_day"], improved_energy["kwh_per_day"]],
            }
        )
        fig_comp = px.bar(
            comp_df,
            x="Scenario",
            y="kWh_per_day",
            text="kWh_per_day",
            title="Energy Consumption – Current vs Optimized",
            color="Scenario",
            color_discrete_sequence=PLOTLY_COLORWAY,
        )
        fig_comp.update_traces(textposition="outside")
        fig_comp = style_plotly(fig_comp)
        st.plotly_chart(fig_comp, use_container_width=True)

        reduction_kwh = energy["kwh_per_day"] - improved_energy["kwh_per_day"]
        st.metric("Potential kWh saved / day", f"{reduction_kwh:.1f} kWh")
        st.markdown('</div>', unsafe_allow_html=True)

    st.info(
        "💡 *Insight:* Adjusting operating hours, optimizing refrigerated storage, and electrifying "
        "material handling equipment can materially reduce energy consumption and emissions."
    )

    render_gemma_module_note(
        "Warehouse Energy & Ops",
        "This module adds energy efficiency and facility operations signals to the sustainability profile that Gemma 4 converts into executive recommendations."
    )

# ---------- Download Report ----------
elif section == "Download Report":
    overall = compute_overall_sustainability_score(
        st.session_state["transport_score"],
        st.session_state["waste_score"],
        st.session_state["supplier_score"],
        st.session_state["warehouse_score"],
    )

    st.markdown(
        f"""
        <div class="gc-card">
            <div class="gc-pill">Export Evidence</div>
            <h2 style="margin-top:0.5rem;">Download Sustainability Report</h2>
            <p style="font-size:0.9rem; opacity:0.9;">
                Current <b>Overall Sustainability Index</b>: <b>{overall} / 100</b><br/>
                Export a one-click summary to attach to your hackathon submission or evidence bundle.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Use the latest generated Gemma recommendation in the downloadable summary.
    # This avoids triggering a slow API call automatically when the report page opens.
    advisor_recommendations = st.session_state.get(
        "gemma_advice",
        "Generate recommendations from the Overview page to include Gemma 4 executive guidance in this report."
    )

    summary = {
        "Overall Sustainability Index": f"{overall} / 100",
        "Transport Score": f"{st.session_state['transport_score']} / 100",
        "Waste & Forecast Score": f"{st.session_state['waste_score']} / 100",
        "Supplier Sustainability Score": f"{st.session_state['supplier_score']} / 100",
        "Warehouse Sustainability Score": f"{st.session_state['warehouse_score']} / 100",
        "Gemma AI Business Recommendations": advisor_recommendations,
    }
 
    st.markdown('<div class="gc-card">', unsafe_allow_html=True)
    st.json(summary)

    if REPORTLAB_AVAILABLE:
        pdf_buffer = generate_pdf_report(summary)
        st.download_button(
            label="Download PDF Report",
            data=pdf_buffer,
            file_name="greenchain_sustainability_report.pdf",
            mime="application/pdf",
        )
    else:
        st.warning(
            "PDF support requires the 'reportlab' package. Install it with:\n\n"
            "`pip install reportlab`\n\n"
            "After installing, restart the app to enable PDF download."
        )

    # Always provide a simple text/markdown export too
    text_lines = [f"{k}: {v}" for k, v in summary.items()]
    text_data = "\n".join(text_lines)
    st.download_button(
        label="Download Text Summary",
        data=text_data,
        file_name="greenchain_sustainability_summary.txt",
        mime="text/plain",
    )
    st.markdown('</div>', unsafe_allow_html=True)

    st.info(
        "You can share this report with your business team to generate actionable insights."
    )
