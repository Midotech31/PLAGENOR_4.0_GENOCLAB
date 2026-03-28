# config.py — PLAGENOR 4.0 Global Configuration
import os as _os

# ═══════════════════════════════════════════════════════════════════════════
# PLATFORM IDENTITY
# ═══════════════════════════════════════════════════════════════════════════
APP_TITLE            = "PLAGENOR 4.0"
APP_SUBTITLE         = "Plateforme d'Analyse Génomique d'Oran — ESSBO"
PLATFORM_NAME        = APP_TITLE
PLATFORM_SUBTITLE    = APP_SUBTITLE
PLATFORM_INSTITUTION = "ESSBO — École Supérieure des Sciences Biologiques d'Oran"
PLATFORM_AUTHOR      = "Prof. Mohamed Merzoug"
CONTACT_EMAIL        = "mohamed.merzoug.essbo@gmail.com"
PLATFORM_EMAIL       = CONTACT_EMAIL
PLATFORM_ADDRESS     = "Cité Emir Abdelkader (Ex-INESSMO), 31000 Oran — Algérie"
PLATFORM_PHONE       = "041 24 63 59"
PLATFORM_VERSION     = "4.0.0"
PLATFORM_YEAR        = 2026

# ═══════════════════════════════════════════════════════════════════════════
# ROLES
# ═══════════════════════════════════════════════════════════════════════════
ROLE_SUPER_ADMIN    = "SUPER_ADMIN"
ROLE_PLATFORM_ADMIN = "PLATFORM_ADMIN"
ROLE_MEMBER         = "MEMBER"
ROLE_FINANCE        = "FINANCE"
ROLE_REQUESTER      = "REQUESTER"
ROLE_CLIENT         = "CLIENT"

ALL_ROLES = [ROLE_SUPER_ADMIN, ROLE_PLATFORM_ADMIN, ROLE_MEMBER,
             ROLE_FINANCE, ROLE_REQUESTER, ROLE_CLIENT]

ROLE_LABELS = {
    ROLE_SUPER_ADMIN:    "Super Administrateur",
    ROLE_PLATFORM_ADMIN: "Administrateur Plateforme",
    ROLE_MEMBER:         "Analyste / Membre",
    ROLE_FINANCE:        "Responsable Financier",
    ROLE_REQUESTER:      "Demandeur IBTIKAR",
    ROLE_CLIENT:         "Client GENOCLAB",
}

ROLE_ICONS = {
    ROLE_SUPER_ADMIN:    "👑",
    ROLE_PLATFORM_ADMIN: "⚙️",
    ROLE_MEMBER:         "🔬",
    ROLE_FINANCE:        "💰",
    ROLE_REQUESTER:      "📋",
    ROLE_CLIENT:         "🏢",
}

# ═══════════════════════════════════════════════════════════════════════════
# CHANNELS
# ═══════════════════════════════════════════════════════════════════════════
CHANNEL_IBTIKAR  = "IBTIKAR"
CHANNEL_GENOCLAB = "GENOCLAB"
ALL_CHANNELS     = [CHANNEL_IBTIKAR, CHANNEL_GENOCLAB]

CHANNEL_LABELS = {
    CHANNEL_IBTIKAR:  "IBTIKAR — Financement DGRSDT",
    CHANNEL_GENOCLAB: "GENOCLAB — Service Commercial",
}

CHANNEL_COLORS = {
    CHANNEL_IBTIKAR:  "#1B4F72",
    CHANNEL_GENOCLAB: "#117A65",
}

# ═══════════════════════════════════════════════════════════════════════════
# FILE SYSTEM
# ═══════════════════════════════════════════════════════════════════════════
BASE_DIR = _os.path.dirname(_os.path.abspath(__file__))
DATA_DIR = _os.environ.get("PLAGENOR_DATA_DIR", _os.path.join(BASE_DIR, "data"))
_os.makedirs(DATA_DIR, exist_ok=True)

USERS_FILE             = _os.path.join(DATA_DIR, "users.json")
MEMBERS_FILE           = _os.path.join(DATA_DIR, "members.json")
SERVICES_FILE          = _os.path.join(DATA_DIR, "services.json")
ACTIVE_REQUESTS_FILE   = _os.path.join(DATA_DIR, "active_requests.json")
ARCHIVED_REQUESTS_FILE = _os.path.join(DATA_DIR, "archived_requests.json")
INVOICES_FILE          = _os.path.join(DATA_DIR, "invoices.json")
INVOICE_SEQUENCE_FILE  = _os.path.join(DATA_DIR, "invoice_sequence.json")
REQUEST_SEQUENCE_FILE  = _os.path.join(DATA_DIR, "request_sequence.json")
REVENUE_ARCHIVES_FILE  = _os.path.join(DATA_DIR, "revenue_archives.json")
AUDIT_LOGS_FILE        = _os.path.join(DATA_DIR, "audit_logs.json")
DOCUMENTS_FILE         = _os.path.join(DATA_DIR, "documents.json")
NOTIFICATIONS_FILE     = _os.path.join(DATA_DIR, "notifications.json")
OVERRIDE_LOG_FILE      = _os.path.join(DATA_DIR, "override_logs.json")
DATABASE_FILE          = _os.path.join(DATA_DIR, "plagenor.db")

UPLOADS_DIR  = _os.path.join(DATA_DIR, "uploads")
REPORTS_DIR  = _os.path.join(DATA_DIR, "reports")
INVOICES_DIR = _os.path.join(DATA_DIR, "invoices_pdf")
BACKUPS_DIR  = _os.path.join(DATA_DIR, "backups")

for _d in [UPLOADS_DIR, REPORTS_DIR, INVOICES_DIR, BACKUPS_DIR]:
    _os.makedirs(_d, exist_ok=True)

# ═══════════════════════════════════════════════════════════════════════════
# FINANCIAL
# ═══════════════════════════════════════════════════════════════════════════
VAT_RATE           = float(_os.environ.get("PLAGENOR_VAT_RATE",   "0.19"))
IBTIKAR_ANNUAL_CAP = float(_os.environ.get("PLAGENOR_BUDGET_CAP", "200000.0"))
IBTIKAR_BUDGET_CAP = IBTIKAR_ANNUAL_CAP
INVOICE_PREFIX     = _os.environ.get("PLAGENOR_INV_PREFIX", "GENOCLAB-INV")

# ═══════════════════════════════════════════════════════════════════════════
# SLA
# ═══════════════════════════════════════════════════════════════════════════
SLA_DAYS_IBTIKAR  = int(_os.environ.get("PLAGENOR_SLA_IBTIKAR",  "21"))
SLA_DAYS_GENOCLAB = int(_os.environ.get("PLAGENOR_SLA_GENOCLAB", "14"))

# ═══════════════════════════════════════════════════════════════════════════
# ASSIGNMENT
# ═══════════════════════════════════════════════════════════════════════════
DEFAULT_MAX_LOAD        = 5
DEFAULT_MEMBER_MAX_LOAD = DEFAULT_MAX_LOAD

ASSIGNMENT_WEIGHTS = {
    "skill":        40.0,
    "load":         30.0,
    "productivity": 20.0,
    "availability": 10.0,
}

# ═══════════════════════════════════════════════════════════════════════════
# PRODUCTIVITY
# ═══════════════════════════════════════════════════════════════════════════
PRODUCTIVITY_THRESHOLDS = {
    "EXCELLENT": 85.0,
    "GOOD":      70.0,
    "NORMAL":    50.0,
    "LOW":        0.0,
}
SCORE_EXCELLENT = PRODUCTIVITY_THRESHOLDS["EXCELLENT"]
SCORE_GOOD      = PRODUCTIVITY_THRESHOLDS["GOOD"]
SCORE_NORMAL    = PRODUCTIVITY_THRESHOLDS["NORMAL"]

PRODUCTIVITY_EMOJI = {
    "EXCELLENT": "🟢",
    "GOOD":      "🔵",
    "NORMAL":    "🟡",
    "LOW":       "🔴",
}

# ═══════════════════════════════════════════════════════════════════════════
# SECURITY
# ═══════════════════════════════════════════════════════════════════════════
SESSION_TIMEOUT_MINUTES = int(_os.environ.get("PLAGENOR_SESSION_TIMEOUT", "480"))
SESSION_TIMEOUT_SECONDS = SESSION_TIMEOUT_MINUTES * 60
MAX_LOGIN_ATTEMPTS      = int(_os.environ.get("PLAGENOR_MAX_LOGIN",        "5"))
MAX_UPLOAD_SIZE_MB      = int(_os.environ.get("PLAGENOR_MAX_UPLOAD_MB",   "50"))
MIN_PASSWORD_LENGTH     = 8

# ═══════════════════════════════════════════════════════════════════════════
# UI
# ═══════════════════════════════════════════════════════════════════════════
ITEMS_PER_PAGE           = 15
AUDIT_LOG_MAX_DISPLAY    = 200
NOTIFICATION_MAX_DISPLAY = 50

ALLOWED_REPORT_EXTENSIONS   = {".pdf",".docx",".xlsx",".csv",".zip",".fastq",".fasta",".gz"}
ALLOWED_DOCUMENT_EXTENSIONS = {".pdf",".docx",".xlsx",".png",".jpg",".jpeg"}

# ═══════════════════════════════════════════════════════════════════════════
# WORKFLOW STATES (authoritative transitions in core/state_machine.py)
# ═══════════════════════════════════════════════════════════════════════════
TERMINAL_STATES = {"REJECTED", "COMPLETED", "QUOTE_REJECTED_BY_CLIENT", "CLOSED", "ARCHIVED"}

REJECTION_STATES = {"REJECTED", "QUOTE_REJECTED_BY_CLIENT", "CLOSED"}

# ARCH-02: Single source of truth for role-based transition permissions
IBTIKAR_TRANSITION_ROLES = {
    "SUBMITTED": [ROLE_REQUESTER],
    "VALIDATION_PEDAGOGIQUE": [ROLE_PLATFORM_ADMIN],
    "VALIDATION_FINANCE": [ROLE_FINANCE, ROLE_PLATFORM_ADMIN],
    "PLATFORM_NOTE_GENERATED": [ROLE_PLATFORM_ADMIN],
    "ASSIGNED": [ROLE_PLATFORM_ADMIN],
    "SAMPLE_RECEIVED": [ROLE_MEMBER, ROLE_PLATFORM_ADMIN],
    "ANALYSIS_STARTED": [ROLE_MEMBER],
    "ANALYSIS_FINISHED": [ROLE_MEMBER],
    "REPORT_UPLOADED": [ROLE_MEMBER],
    "REPORT_VALIDATED": [ROLE_PLATFORM_ADMIN],
    "COMPLETED": [ROLE_PLATFORM_ADMIN],
    "CLOSED": [ROLE_PLATFORM_ADMIN],
    "REJECTED": [ROLE_PLATFORM_ADMIN, ROLE_FINANCE],
}
GENOCLAB_TRANSITION_ROLES = {
    "REQUEST_CREATED": [ROLE_CLIENT],
    "QUOTE_DRAFT": [ROLE_PLATFORM_ADMIN],
    "QUOTE_SENT": [ROLE_PLATFORM_ADMIN],
    "QUOTE_VALIDATED_BY_CLIENT": [ROLE_CLIENT],
    "QUOTE_REJECTED_BY_CLIENT": [ROLE_CLIENT],
    "INVOICE_GENERATED": [ROLE_FINANCE, ROLE_PLATFORM_ADMIN],
    "PAYMENT_CONFIRMED": [ROLE_FINANCE],
    "ASSIGNED": [ROLE_PLATFORM_ADMIN],
    "SAMPLE_RECEIVED": [ROLE_MEMBER, ROLE_PLATFORM_ADMIN],
    "ANALYSIS_STARTED": [ROLE_MEMBER],
    "ANALYSIS_FINISHED": [ROLE_MEMBER],
    "REPORT_UPLOADED": [ROLE_MEMBER],
    "REPORT_VALIDATED": [ROLE_PLATFORM_ADMIN],
    "COMPLETED": [ROLE_PLATFORM_ADMIN],
    "ARCHIVED": [ROLE_PLATFORM_ADMIN],
    "REJECTED": [ROLE_PLATFORM_ADMIN, ROLE_FINANCE],
}

# ═══════════════════════════════════════════════════════════════════════════
# STATUS DISPLAY
# ═══════════════════════════════════════════════════════════════════════════
STATUS_LABELS = {
    "SUBMITTED":              ("📨","Soumis","#3498DB"),
    "VALIDATION":             ("🔍","En validation","#5D6D7E"),
    "VALIDATED":              ("✅","Validé","#27AE60"),
    "REJECTED":               ("❌","Rejeté","#E74C3C"),
    "APPROVED":               ("🏦","Approuvé","#8E44AD"),
    "APPOINTMENT_SCHEDULED":  ("📅","RDV Planifié","#1ABC9C"),
    "SAMPLE_RECEIVED":        ("📦","Échantillons Reçus","#16A085"),
    "SAMPLE_VERIFIED":        ("🔍","Échantillons Vérifiés","#1A5276"),
    "ASSIGNED":               ("👤","Assigné","#2471A3"),
    "PENDING_ACCEPTANCE":     ("⚡","En Attente Acceptation","#F39C12"),
    "IN_PROGRESS":            ("🔬","En Cours","#D35400"),
    "ANALYSIS_IN_PROGRESS":   ("🔬","Analyse en cours","#D35400"),
    "ANALYSIS_FINISHED":      ("🧪","Analyse Terminée","#117A65"),
    "REPORT_UPLOADED":        ("📄","Rapport Généré","#1F618D"),
    "ADMIN_REVIEW":           ("🔎","Révision Admin","#6C3483"),
    "REPORT_VALIDATED":       ("📋","Rapport Validé","#1E8449"),
    "SENT_TO_REQUESTER":      ("📬","Transmis Demandeur","#196F3D"),
    "COMPLETED":              ("🎉","Complété","#117A65"),
    "QUOTE_DRAFT":            ("💵","Devis En Cours","#9B59B6"),
    "QUOTE_SENT":             ("📧","Devis Envoyé","#2980B9"),
    "QUOTE_VALIDATED_BY_CLIENT":("🤝","Devis Accepté","#27AE60"),
    "QUOTE_REJECTED_BY_CLIENT": ("🚫","Devis Refusé","#E74C3C"),
    "INVOICE_GENERATED":      ("🧾","Facture Émise","#1ABC9C"),
    "SENT_TO_CLIENT":         ("📬","Transmis Client","#196F3D"),
    # Official state names from briefing
    "DRAFT":                  ("📝","Brouillon","#95A5A6"),
    "VALIDATION_PEDAGOGIQUE": ("🎓","Validation Pédagogique","#F39C12"),
    "VALIDATION_FINANCE":     ("💰","Validation Finance","#8E44AD"),
    "PLATFORM_NOTE_GENERATED":("📋","Note Générée","#2471A3"),
    "CLOSED":                 ("🔒","Clôturé","#566573"),
    "REQUEST_CREATED":        ("📥","Demande Créée","#3498DB"),
    "PAYMENT_CONFIRMED":      ("💳","Paiement Confirmé","#27AE60"),
    "ARCHIVED":               ("📦","Archivé","#95A5A6"),
    "ANALYSIS_STARTED":       ("🔬","Analyse Démarrée","#D35400"),
}

# ═══════════════════════════════════════════════════════════════════════════
# URGENCY LEVELS
# ═══════════════════════════════════════════════════════════════════════════
URGENCY_LEVELS = ["Normal", "Urgent", "Très urgent"]
URGENCY_COLORS = {
    "Normal":      "#27AE60",
    "Urgent":      "#F39C12",
    "Très urgent": "#E74C3C",
}
URGENCY_ICONS = {
    "Normal":      "🟢",
    "Urgent":      "🟠",
    "Très urgent": "🔴",
}

# ═══════════════════════════════════════════════════════════════════════════
# CHEERS / POINTS SYSTEM
# ═══════════════════════════════════════════════════════════════════════════
CHEERS_MIN_POINTS = 1
CHEERS_MAX_POINTS = 100

# ═══════════════════════════════════════════════════════════════════════════
# SMTP / EMAIL
# ═══════════════════════════════════════════════════════════════════════════
SMTP_ENABLED  = _os.environ.get("PLAGENOR_SMTP_ENABLED", "false").lower() == "true"
SMTP_HOST     = _os.environ.get("PLAGENOR_SMTP_HOST", "smtp.gmail.com")
SMTP_PORT     = int(_os.environ.get("PLAGENOR_SMTP_PORT", "587"))
SMTP_USER     = _os.environ.get("PLAGENOR_SMTP_USER", "")
SMTP_PASSWORD  = _os.environ.get("PLAGENOR_SMTP_PASSWORD", "")
SMTP_FROM_NAME = _os.environ.get("PLAGENOR_SMTP_FROM_NAME", "PLAGENOR 4.0")
SMTP_FROM_EMAIL = _os.environ.get("PLAGENOR_SMTP_FROM_EMAIL", CONTACT_EMAIL)

# ═══════════════════════════════════════════════════════════════════════════
# PAYMENT METHODS
# ═══════════════════════════════════════════════════════════════════════════
PAYMENT_METHODS_FILE = _os.path.join(DATA_DIR, "payment_methods.json")
DEFAULT_PAYMENT_METHODS = ["Virement bancaire", "Chèque", "Espèces"]

# ═══════════════════════════════════════════════════════════════════════════
# OFFICIAL STATE LISTS (from briefing Section 11)
# ═══════════════════════════════════════════════════════════════════════════
IBTIKAR_STATES = [
    "DRAFT", "SUBMITTED", "VALIDATION_PEDAGOGIQUE", "VALIDATION_FINANCE",
    "PLATFORM_NOTE_GENERATED", "ASSIGNED", "SAMPLE_RECEIVED",
    "ANALYSIS_STARTED", "ANALYSIS_FINISHED", "REPORT_UPLOADED",
    "REPORT_VALIDATED", "COMPLETED", "CLOSED", "REJECTED",
]

GENOCLAB_STATES = [
    "REQUEST_CREATED", "QUOTE_DRAFT", "QUOTE_SENT", "QUOTE_VALIDATED_BY_CLIENT",
    "INVOICE_GENERATED", "PAYMENT_CONFIRMED", "ASSIGNED", "SAMPLE_RECEIVED",
    "ANALYSIS_STARTED", "ANALYSIS_FINISHED", "REPORT_UPLOADED",
    "REPORT_VALIDATED", "COMPLETED", "ARCHIVED", "REJECTED",
]


# ═══════════════════════════════════════════════════════════════════════════
# STARTUP VALIDATION
# ═══════════════════════════════════════════════════════════════════════════
def validate_config():
    """Validate configuration at startup. Logs warnings for common misconfigurations."""
    import logging
    _clog = logging.getLogger("plagenor.config")
    warnings = []
    if SMTP_ENABLED and not SMTP_PASSWORD:
        warnings.append("SMTP enabled but PLAGENOR_SMTP_PASSWORD not set — emails will fail")
    if not _os.access(DATA_DIR, _os.W_OK):
        raise RuntimeError(f"DATA_DIR {DATA_DIR} is not writable")
    for w in warnings:
        _clog.warning("Config warning: %s", w)
