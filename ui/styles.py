# ui/styles.py — PLAGENOR 4.0 Design System (Modern SaaS — Flat Clean Professional)

def get_global_css() -> str:
    return """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* ── Global Reset ─────────────────────────────────── */
.stApp {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    background: #F8FAFC !important;
}
.stApp > header { background: transparent !important; }

/* ── Base Typography ──────────────────────────────── */
.stApp .stMarkdown p, .stApp .stMarkdown li {
    font-size: 15px !important;
    line-height: 1.7 !important;
    color: #334155 !important;
}
.stApp .stMarkdown h1 {
    font-size: 32px !important;
    font-weight: 800 !important;
    color: #0F172A !important;
    letter-spacing: -0.5px !important;
}
.stApp .stMarkdown h2 {
    font-size: 26px !important;
    font-weight: 700 !important;
    color: #0F172A !important;
    letter-spacing: -0.3px !important;
}
.stApp .stMarkdown h3 {
    font-size: 20px !important;
    font-weight: 700 !important;
    color: #1E293B !important;
}
.stApp .stMarkdown h4 {
    font-size: 17px !important;
    font-weight: 600 !important;
    color: #1E293B !important;
}

/* ── Sidebar — Dark clean modern ──────────────────── */
section[data-testid="stSidebar"] {
    background: #1E293B !important;
    border-right: none;
    box-shadow: 4px 0 24px rgba(0,0,0,0.08);
    min-width: 280px !important;
}
section[data-testid="stSidebar"] * {
    color: #CBD5E1 !important;
}
section[data-testid="stSidebar"] .stMarkdown h1,
section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] .stMarkdown h3 {
    color: #F8FAFC !important;
}
section[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.08) !important;
    margin: 16px 0 !important;
}
section[data-testid="stSidebar"] .stButton button {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    color: #CBD5E1 !important;
    border-radius: 10px !important;
}
section[data-testid="stSidebar"] .stButton button:hover {
    background: rgba(255,255,255,0.12) !important;
    border-color: rgba(255,255,255,0.15) !important;
    color: #F8FAFC !important;
    transform: none !important;
    box-shadow: none !important;
}

/* ── KPI Cards — Elevated with colored accent ─────── */
.kpi-card {
    background: #FFFFFF;
    border-radius: 16px;
    padding: 24px;
    border: 1px solid #F1F5F9;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 4px 16px rgba(0,0,0,0.02);
    transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
    position: relative;
    overflow: hidden;
}
.kpi-card:hover {
    box-shadow: 0 8px 30px rgba(0,0,0,0.08);
    transform: translateY(-2px);
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
    border-radius: 16px 16px 0 0;
}
.kpi-card.blue::before   { background: linear-gradient(90deg, #3B82F6, #60A5FA); }
.kpi-card.green::before  { background: linear-gradient(90deg, #10B981, #34D399); }
.kpi-card.purple::before { background: linear-gradient(90deg, #8B5CF6, #A78BFA); }
.kpi-card.orange::before { background: linear-gradient(90deg, #F59E0B, #FBBF24); }
.kpi-card.red::before    { background: linear-gradient(90deg, #EF4444, #F87171); }
.kpi-card.teal::before   { background: linear-gradient(90deg, #0E8C7F, #14B8A6); }

.kpi-icon-box {
    width: 48px;
    height: 48px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    margin-bottom: 14px;
}
.kpi-value {
    font-size: 32px;
    font-weight: 800;
    color: #0F172A;
    line-height: 1.1;
    margin: 6px 0;
    font-family: 'Inter', sans-serif;
    letter-spacing: -0.5px;
}
.kpi-label {
    font-size: 13px;
    color: #64748B;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 1px;
}

/* ── Status Badges — Pill shape, soft colors ──────── */
.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    border-radius: 24px;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.2px;
    line-height: 1.4;
}
.status-submitted     { background: #EFF6FF; color: #1D4ED8; border: 1px solid #BFDBFE; }
.status-validated     { background: #ECFDF5; color: #059669; border: 1px solid #A7F3D0; }
.status-approved      { background: #F5F3FF; color: #7C3AED; border: 1px solid #DDD6FE; }
.status-rejected      { background: #FEF2F2; color: #DC2626; border: 1px solid #FECACA; }
.status-assigned      { background: #EFF6FF; color: #1E40AF; border: 1px solid #BFDBFE; }
.status-in-progress   { background: #FFF7ED; color: #C2410C; border: 1px solid #FED7AA; }
.status-completed     { background: #ECFDF5; color: #059669; border: 1px solid #A7F3D0; }
.status-quote         { background: #F5F3FF; color: #6D28D9; border: 1px solid #DDD6FE; }
.status-invoice       { background: #F0FDFA; color: #0F766E; border: 1px solid #99F6E4; }
.status-default       { background: #F8FAFC; color: #475569; border: 1px solid #E2E8F0; }

/* ── Channel Badges ──────────────────────────────── */
.channel-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 4px 12px;
    border-radius: 8px;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.8px;
}
.channel-ibtikar  { background: #EFF6FF; color: #1D4ED8; border: 1px solid #BFDBFE; }
.channel-genoclab { background: #ECFDF5; color: #059669; border: 1px solid #A7F3D0; }

/* ── Role Badges — Modern gradient pills ─────────── */
.role-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 16px;
    border-radius: 10px;
    font-size: 13px;
    font-weight: 600;
}
.role-super-admin    { background: linear-gradient(135deg, #F59E0B, #D97706); color: white; }
.role-platform-admin { background: linear-gradient(135deg, #4F46E5, #6366F1); color: white; }
.role-member         { background: linear-gradient(135deg, #10B981, #059669); color: white; }
.role-finance        { background: linear-gradient(135deg, #8B5CF6, #7C3AED); color: white; }
.role-requester      { background: linear-gradient(135deg, #3B82F6, #2563EB); color: white; }
.role-client         { background: linear-gradient(135deg, #10B981, #047857); color: white; }

/* ── Progress Bar ────────────────────────────────── */
.progress-container {
    background: #F1F5F9;
    border-radius: 12px;
    height: 10px;
    overflow: hidden;
    margin: 8px 0;
}
.progress-bar {
    height: 100%;
    border-radius: 12px;
    transition: width 0.8s cubic-bezier(0.4,0,0.2,1);
}
.progress-blue   { background: linear-gradient(90deg, #3B82F6, #60A5FA); }
.progress-green  { background: linear-gradient(90deg, #10B981, #34D399); }
.progress-orange { background: linear-gradient(90deg, #F59E0B, #FBBF24); }
.progress-red    { background: linear-gradient(90deg, #EF4444, #F87171); }
.progress-purple { background: linear-gradient(90deg, #8B5CF6, #A78BFA); }

/* ── Section Headers ─────────────────────────────── */
.section-header {
    font-size: 20px;
    font-weight: 700;
    color: #0F172A;
    margin: 28px 0 16px 0;
    padding-bottom: 12px;
    border-bottom: 2px solid #F1F5F9;
}

/* ── Data Cards ──────────────────────────────────── */
.data-card {
    background: #FFFFFF;
    border: 1px solid #F1F5F9;
    border-radius: 14px;
    padding: 20px 24px;
    margin-bottom: 10px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    transition: all 0.2s ease;
}
.data-card:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.06);
}

/* ── Pipeline Steps — Clean flat design ──────────── */
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
    padding: 10px 8px;
    font-size: 12px;
    font-weight: 600;
    border-radius: 10px;
    min-width: 75px;
    white-space: nowrap;
    transition: all 0.2s ease;
}
.pipeline-done {
    background: #ECFDF5;
    color: #059669;
}
.pipeline-current {
    background: #4F46E5;
    color: white;
    box-shadow: 0 4px 12px rgba(79,70,229,0.3);
}
.pipeline-pending {
    background: #F8FAFC;
    color: #94A3B8;
    border: 1px solid #E2E8F0;
}

/* ── Tabs — Clean pill tabs ──────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: #F1F5F9;
    padding: 4px;
    border-radius: 14px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    padding: 10px 18px !important;
    color: #64748B !important;
    transition: all 0.2s ease !important;
}
.stTabs [aria-selected="true"] {
    background: #FFFFFF !important;
    color: #0F172A !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06) !important;
}

/* ── Table Styling ───────────────────────────────── */
.stDataFrame {
    border-radius: 12px !important;
    overflow: hidden;
    border: 1px solid #F1F5F9 !important;
}

/* ── Sidebar User Card ───────────────────────────── */
.sidebar-user-card {
    background: rgba(255,255,255,0.06);
    border-radius: 14px;
    padding: 20px;
    margin-bottom: 16px;
    border: 1px solid rgba(255,255,255,0.08);
}
.sidebar-user-name {
    font-size: 16px;
    font-weight: 700;
    color: #F8FAFC !important;
    margin-bottom: 6px;
}
.sidebar-user-role {
    font-size: 13px;
    color: #94A3B8 !important;
}

/* ── Empty State ─────────────────────────────────── */
.empty-state {
    text-align: center;
    padding: 60px 24px;
    color: #94A3B8;
}
.empty-state-icon {
    font-size: 56px;
    margin-bottom: 16px;
    display: block;
    opacity: 0.6;
}
.empty-state-text {
    font-size: 16px;
    font-weight: 500;
    color: #94A3B8;
}

/* ── Metric override ─────────────────────────────── */
[data-testid="stMetricValue"] {
    font-family: 'Inter', sans-serif !important;
    font-weight: 800 !important;
    font-size: 28px !important;
    color: #0F172A !important;
}

/* ── Buttons — Modern gradient ───────────────────── */
.stApp .stButton button {
    font-weight: 600 !important;
    font-size: 14px !important;
    border-radius: 12px !important;
    padding: 10px 20px !important;
    transition: all 0.2s ease !important;
    border: 1px solid #E2E8F0 !important;
}
.stApp .stButton button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08) !important;
}
.stApp .stButton button[data-testid="baseButton-primary"],
.stApp [data-testid="stFormSubmitButton"] button {
    background: linear-gradient(135deg, #4F46E5, #6366F1) !important;
    color: white !important;
    border: none !important;
    font-weight: 700 !important;
    font-size: 15px !important;
    padding: 10px 24px !important;
}
.stApp .stButton button[data-testid="baseButton-primary"]:hover,
.stApp [data-testid="stFormSubmitButton"] button:hover {
    box-shadow: 0 4px 16px rgba(79,70,229,0.3) !important;
    transform: translateY(-1px) !important;
}

/* ── Form inputs — Larger, rounder ───────────────── */
.stApp .stTextInput input,
.stApp .stNumberInput input {
    font-size: 15px !important;
    padding: 12px 16px !important;
    border-radius: 12px !important;
    border: 1.5px solid #E2E8F0 !important;
    transition: border-color 0.2s ease !important;
}
.stApp .stTextArea textarea {
    font-size: 15px !important;
    border-radius: 12px !important;
    border: 1.5px solid #E2E8F0 !important;
    transition: border-color 0.2s ease !important;
}
.stApp .stTextInput input:focus,
.stApp .stTextArea textarea:focus,
.stApp .stNumberInput input:focus {
    border-color: #4F46E5 !important;
    box-shadow: 0 0 0 3px rgba(79,70,229,0.1) !important;
}
.stApp label,
.stApp [data-testid="stWidgetLabel"] {
    font-size: 14px !important;
    font-weight: 600 !important;
    color: #374151 !important;
}

/* ── Selectbox ───────────────────────────────────── */
.stApp .stSelectbox > div > div {
    border-radius: 12px !important;
    border: 1.5px solid #E2E8F0 !important;
}

/* ── Expanders — Cleaner ─────────────────────────── */
.stApp details[data-testid="stExpander"] {
    border: 1px solid #F1F5F9 !important;
    border-radius: 14px !important;
    background: #FFFFFF !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.02) !important;
}
.stApp details[data-testid="stExpander"] summary {
    font-weight: 600 !important;
    font-size: 15px !important;
    padding: 16px 20px !important;
}

/* ── Scrollbar styling ───────────────────────────── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #CBD5E1; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #94A3B8; }

/* ── Alert boxes ─────────────────────────────────── */
.stApp .stAlert {
    border-radius: 12px !important;
    border: none !important;
    font-size: 14px !important;
}

/* ── Download button ─────────────────────────────── */
.stApp .stDownloadButton button {
    border-radius: 12px !important;
    font-weight: 600 !important;
    border: 1.5px solid #E2E8F0 !important;
    background: #FFFFFF !important;
    color: #334155 !important;
}
.stApp .stDownloadButton button:hover {
    border-color: #4F46E5 !important;
    color: #4F46E5 !important;
    background: #F5F3FF !important;
}
</style>
"""


def get_login_css() -> str:
    return """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* ── Light Home Page Theme ────────────────────────── */
.stApp {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    background: linear-gradient(135deg, #F8FAFC 0%, #EFF6FF 50%, #F0F9FF 100%) !important;
}
.stApp > header { background: transparent !important; }

/* Sidebar — consistent dark look */
section[data-testid="stSidebar"] {
    background: #1E293B !important;
    box-shadow: 4px 0 24px rgba(0,0,0,0.08);
}

/* Text stays dark on light background */
.stApp .stMarkdown, .stApp .stMarkdown p, .stApp .stMarkdown span,
.stApp .stMarkdown li, .stApp .stMarkdown h1, .stApp .stMarkdown h2,
.stApp .stMarkdown h3, .stApp .stMarkdown h4 {
    color: #0F172A !important;
}

/* Form labels */
.stApp label, .stApp .stTextInput label, .stApp .stTextArea label,
.stApp .stSelectbox label, .stApp .stNumberInput label,
.stApp .stRadio label, .stApp .stCheckbox label,
.stApp [data-testid="stWidgetLabel"] {
    color: #374151 !important;
    font-weight: 600 !important;
    font-size: 14px !important;
}

/* Input fields */
.stApp .stTextInput input, .stApp .stTextArea textarea,
.stApp .stNumberInput input {
    color: #0F172A !important;
    background: #FFFFFF !important;
    border: 1.5px solid #E2E8F0 !important;
    border-radius: 12px !important;
    font-size: 15px !important;
    padding: 12px 16px !important;
}
.stApp .stTextInput input:focus, .stApp .stTextArea textarea:focus {
    border-color: #4F46E5 !important;
    box-shadow: 0 0 0 3px rgba(79,70,229,0.1) !important;
}

/* Selectbox */
.stApp .stSelectbox > div > div {
    background: #FFFFFF !important;
    color: #0F172A !important;
    border: 1.5px solid #E2E8F0 !important;
    border-radius: 12px !important;
}

/* Tab text */
.stApp .stTabs [data-baseweb="tab-list"] {
    background: #F1F5F9 !important;
    padding: 4px !important;
    border-radius: 14px !important;
}
.stApp .stTabs [data-baseweb="tab"] {
    color: #64748B !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    border-radius: 10px !important;
    padding: 10px 18px !important;
}
.stApp .stTabs [aria-selected="true"] {
    background: #FFFFFF !important;
    color: #0F172A !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06) !important;
}

/* Buttons */
.stApp .stButton button {
    border-radius: 12px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    padding: 10px 20px !important;
    transition: all 0.2s ease !important;
}
.stApp .stButton button[data-testid="baseButton-primary"],
.stApp [data-testid="stFormSubmitButton"] button {
    background: linear-gradient(135deg, #4F46E5, #6366F1) !important;
    color: white !important;
    border: none !important;
    font-weight: 700 !important;
    font-size: 15px !important;
}
.stApp .stButton button[data-testid="baseButton-primary"]:hover {
    box-shadow: 0 4px 16px rgba(79,70,229,0.3) !important;
    transform: translateY(-1px) !important;
}

/* Info/warning/error boxes */
.stApp .stAlert {
    color: #0F172A !important;
    border-radius: 12px !important;
}

/* Cards on login page */
.data-card, .kpi-card {
    background: #FFFFFF;
    border: 1px solid #F1F5F9;
    border-radius: 16px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 4px 16px rgba(0,0,0,0.02);
}
</style>
"""
