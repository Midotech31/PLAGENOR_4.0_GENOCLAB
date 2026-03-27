# ui/styles.py — PLAGENOR 4.0 Design System (Professional Light Theme)

def get_global_css() -> str:
    return """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* ── Global Reset ─────────────────────────────────── */
.stApp {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    background: #F5F7FA !important;
}
.stApp > header { background: transparent !important; }

/* ── Base Typography — LARGER ────────────────────── */
.stApp .stMarkdown p, .stApp .stMarkdown li {
    font-size: 15px !important;
    line-height: 1.7 !important;
    color: #2D3748 !important;
}
.stApp .stMarkdown h1 { font-size: 32px !important; font-weight: 800 !important; color: #1A202C !important; }
.stApp .stMarkdown h2 { font-size: 26px !important; font-weight: 700 !important; color: #1A202C !important; }
.stApp .stMarkdown h3 { font-size: 20px !important; font-weight: 700 !important; color: #2D3748 !important; }
.stApp .stMarkdown h4 { font-size: 17px !important; font-weight: 600 !important; color: #2D3748 !important; }

/* ── Sidebar — Premium dark gradient ─────────────── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0F2B3D 0%, #1A365D 40%, #1B2838 100%) !important;
    border-right: none;
    box-shadow: 4px 0 24px rgba(0,0,0,0.15);
    min-width: 280px !important;
}
section[data-testid="stSidebar"] * {
    color: #CBD5E0 !important;
}
section[data-testid="stSidebar"] .stMarkdown h1,
section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] .stMarkdown h3 {
    color: #FFFFFF !important;
}
section[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.1) !important;
    margin: 16px 0 !important;
}

/* ── KPI Cards — Elevated ────────────────────────── */
.kpi-card {
    background: #FFFFFF;
    border-radius: 16px;
    padding: 24px 20px;
    border: 1px solid #E2E8F0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04), 0 8px 24px rgba(0,0,0,0.02);
    transition: all 0.25s cubic-bezier(0.4,0,0.2,1);
    position: relative;
    overflow: hidden;
}
.kpi-card:hover {
    box-shadow: 0 8px 30px rgba(0,0,0,0.10);
    transform: translateY(-3px);
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
}
.kpi-card.blue::before   { background: linear-gradient(90deg, #1B4F72, #2E86C1); }
.kpi-card.green::before  { background: linear-gradient(90deg, #0E8C7F, #27AE60); }
.kpi-card.purple::before { background: linear-gradient(90deg, #6C3483, #AF7AC5); }
.kpi-card.orange::before { background: linear-gradient(90deg, #D35400, #F39C12); }
.kpi-card.red::before    { background: linear-gradient(90deg, #C0392B, #E74C3C); }
.kpi-card.teal::before   { background: linear-gradient(90deg, #0E8C7F, #1ABC9C); }

.kpi-icon {
    font-size: 32px;
    margin-bottom: 8px;
    display: block;
}
.kpi-value {
    font-size: 34px;
    font-weight: 800;
    color: #1A202C;
    line-height: 1.1;
    margin: 6px 0;
    font-family: 'JetBrains Mono', monospace;
}
.kpi-label {
    font-size: 13px;
    color: #718096;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}

/* ── Status Badges — Pill shaped ─────────────────── */
.status-badge {
    display: inline-block;
    padding: 5px 14px;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.3px;
    line-height: 1.4;
}
.status-submitted     { background: #DBEAFE; color: #1E40AF; }
.status-validated     { background: #D1FAE5; color: #065F46; }
.status-approved      { background: #EDE9FE; color: #5B21B6; }
.status-rejected      { background: #FEE2E2; color: #991B1B; }
.status-assigned      { background: #DBEAFE; color: #1E3A5F; }
.status-in-progress   { background: #FEF3C7; color: #92400E; }
.status-completed     { background: #D1FAE5; color: #065F46; }
.status-quote         { background: #EDE9FE; color: #6D28D9; }
.status-invoice       { background: #CCFBF1; color: #0F766E; }
.status-default       { background: #F1F5F9; color: #475569; }

/* ── Channel Badges ───────────────────────────────── */
.channel-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 8px;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.8px;
}
.channel-ibtikar  { background: #1B4F72; color: white; }
.channel-genoclab { background: #0E8C7F; color: white; }

/* ── Role Badges ──────────────────────────────────── */
.role-badge {
    display: inline-block;
    padding: 6px 16px;
    border-radius: 10px;
    font-size: 13px;
    font-weight: 600;
}
.role-super-admin    { background: linear-gradient(135deg, #F59E0B, #D97706); color: white; }
.role-platform-admin { background: linear-gradient(135deg, #3B82F6, #1D4ED8); color: white; }
.role-member         { background: linear-gradient(135deg, #10B981, #059669); color: white; }
.role-finance        { background: linear-gradient(135deg, #8B5CF6, #6D28D9); color: white; }
.role-requester      { background: linear-gradient(135deg, #3B82F6, #2563EB); color: white; }
.role-client         { background: linear-gradient(135deg, #10B981, #047857); color: white; }

/* ── Progress Bar ─────────────────────────────────── */
.progress-container {
    background: #E2E8F0;
    border-radius: 12px;
    height: 14px;
    overflow: hidden;
    margin: 8px 0;
}
.progress-bar {
    height: 100%;
    border-radius: 12px;
    transition: width 0.8s cubic-bezier(0.4,0,0.2,1);
}
.progress-blue   { background: linear-gradient(90deg, #2563EB, #3B82F6); }
.progress-green  { background: linear-gradient(90deg, #059669, #10B981); }
.progress-orange { background: linear-gradient(90deg, #D97706, #F59E0B); }
.progress-red    { background: linear-gradient(90deg, #DC2626, #EF4444); }
.progress-purple { background: linear-gradient(90deg, #7C3AED, #A78BFA); }

/* ── Section Headers ──────────────────────────────── */
.section-header {
    font-size: 22px;
    font-weight: 700;
    color: #1A202C;
    margin: 32px 0 20px 0;
    padding-bottom: 10px;
    border-bottom: 3px solid #E2E8F0;
}

/* ── Data Cards ───────────────────────────────────── */
.data-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 14px;
    padding: 20px 24px;
    margin-bottom: 12px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    transition: box-shadow 0.2s ease;
}
.data-card:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}

/* ── Pipeline Steps ───────────────────────────────── */
.pipeline-container {
    display: flex;
    align-items: center;
    gap: 3px;
    padding: 10px 0;
    overflow-x: auto;
}
.pipeline-step {
    flex: 1;
    text-align: center;
    padding: 10px 6px;
    font-size: 11px;
    font-weight: 600;
    border-radius: 8px;
    min-width: 75px;
    white-space: nowrap;
}
.pipeline-done {
    background: #D1FAE5;
    color: #065F46;
}
.pipeline-current {
    background: linear-gradient(135deg, #1B4F72, #2563EB);
    color: white;
    box-shadow: 0 3px 12px rgba(27,79,114,0.35);
}
.pipeline-pending {
    background: #F1F5F9;
    color: #94A3B8;
}

/* ── Tabs — Polished ─────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: #EDF2F7;
    padding: 5px;
    border-radius: 14px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    padding: 8px 16px !important;
}
.stTabs [aria-selected="true"] {
    background: #FFFFFF !important;
    box-shadow: 0 2px 6px rgba(0,0,0,0.10) !important;
    color: #1A202C !important;
}

/* ── Table Styling ────────────────────────────────── */
.stDataFrame { border-radius: 12px !important; overflow: hidden; }

/* ── Sidebar User Card ────────────────────────────── */
.sidebar-user-card {
    background: rgba(255,255,255,0.08);
    border-radius: 14px;
    padding: 20px;
    margin-bottom: 16px;
    border: 1px solid rgba(255,255,255,0.10);
    backdrop-filter: blur(10px);
}
.sidebar-user-name {
    font-size: 17px;
    font-weight: 700;
    color: #FFFFFF !important;
    margin-bottom: 6px;
}
.sidebar-user-role {
    font-size: 13px;
    color: #94A3B8 !important;
}

/* ── Empty State ──────────────────────────────────── */
.empty-state {
    text-align: center;
    padding: 60px 24px;
    color: #94A3B8;
}
.empty-state-icon {
    font-size: 56px;
    margin-bottom: 16px;
    display: block;
}
.empty-state-text {
    font-size: 16px;
    font-weight: 500;
}

/* ── Metric override ──────────────────────────────── */
[data-testid="stMetricValue"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 700 !important;
    font-size: 28px !important;
}

/* ── Buttons — Polished ──────────────────────────── */
.stApp .stButton button {
    font-weight: 600 !important;
    font-size: 14px !important;
    border-radius: 10px !important;
    padding: 8px 20px !important;
    transition: all 0.2s ease !important;
}
.stApp .stButton button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.10) !important;
}
.stApp .stButton button[data-testid="baseButton-primary"],
.stApp [data-testid="stFormSubmitButton"] button {
    background: linear-gradient(135deg, #0E8C7F, #1ABC9C) !important;
    color: white !important;
    border: none !important;
    font-weight: 700 !important;
    font-size: 15px !important;
}

/* ── Form inputs — Larger ────────────────────────── */
.stApp .stTextInput input,
.stApp .stNumberInput input {
    font-size: 15px !important;
    padding: 10px 14px !important;
    border-radius: 10px !important;
}
.stApp .stTextArea textarea {
    font-size: 15px !important;
    border-radius: 10px !important;
}
.stApp label,
.stApp [data-testid="stWidgetLabel"] {
    font-size: 14px !important;
    font-weight: 600 !important;
    color: #374151 !important;
}

/* ── Expanders — Cleaner ─────────────────────────── */
.stApp details[data-testid="stExpander"] {
    border: 1px solid #E2E8F0 !important;
    border-radius: 12px !important;
    background: #FFFFFF !important;
}
.stApp details[data-testid="stExpander"] summary {
    font-weight: 600 !important;
    font-size: 15px !important;
}
</style>
"""


def get_login_css() -> str:
    return """
<style>
/* ── Light Home Page Theme ────────────────────────── */
.stApp {
    background: linear-gradient(135deg, #F5F7FA 0%, #E8ECF1 50%, #DBEAFE 100%) !important;
}
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0F2B3D 0%, #1A365D 40%, #1B2838 100%) !important;
}
/* Text stays dark on light background */
.stApp .stMarkdown, .stApp .stMarkdown p, .stApp .stMarkdown span,
.stApp .stMarkdown li, .stApp .stMarkdown h1, .stApp .stMarkdown h2,
.stApp .stMarkdown h3, .stApp .stMarkdown h4 {
    color: #1A202C !important;
}
/* Form labels */
.stApp label, .stApp .stTextInput label, .stApp .stTextArea label,
.stApp .stSelectbox label, .stApp .stNumberInput label,
.stApp .stRadio label, .stApp .stCheckbox label,
.stApp [data-testid="stWidgetLabel"] {
    color: #374151 !important;
}
/* Input fields */
.stApp .stTextInput input, .stApp .stTextArea textarea,
.stApp .stNumberInput input {
    color: #1A202C !important;
    background: #FFFFFF !important;
    border: 1px solid #D1D5DB !important;
    border-radius: 10px !important;
}
/* Selectbox */
.stApp .stSelectbox > div > div {
    background: #FFFFFF !important;
    color: #1A202C !important;
    border: 1px solid #D1D5DB !important;
    border-radius: 10px !important;
}
/* Tab text */
.stApp .stTabs [data-baseweb="tab-list"] {
    background: #E5E7EB !important;
}
.stApp .stTabs [data-baseweb="tab"] {
    color: #4B5563 !important;
    font-size: 15px !important;
}
.stApp .stTabs [aria-selected="true"] {
    background: #FFFFFF !important;
    color: #1A202C !important;
}
/* Info/warning/error boxes */
.stApp .stAlert { color: #1A202C !important; }
</style>
"""
