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

# ═══════════════════════════════════════════════════════════════════════════
# UI
# ═══════════════════════════════════════════════════════════════════════════
ITEMS_PER_PAGE           = 15
AUDIT_LOG_MAX_DISPLAY    = 200
NOTIFICATION_MAX_DISPLAY = 50

ALLOWED_REPORT_EXTENSIONS   = {".pdf",".docx",".xlsx",".csv",".zip",".fastq",".fasta",".gz"}
ALLOWED_DOCUMENT_EXTENSIONS = {".pdf",".docx",".xlsx",".png",".jpg",".jpeg"}

# ═══════════════════════════════════════════════════════════════════════════
# IBTIKAR WORKFLOW
# ═══════════════════════════════════════════════════════════════════════════
class IbtikarState:
    SUBMITTED             = "SUBMITTED"
    VALIDATION            = "VALIDATION"
    VALIDATED             = "VALIDATION"
    APPROVED              = "APPROVED"
    REJECTED              = "REJECTED"
    APPOINTMENT_SCHEDULED = "APPOINTMENT_SCHEDULED"
    SAMPLE_RECEIVED       = "SAMPLE_RECEIVED"
    SAMPLE_VERIFIED       = "SAMPLE_VERIFIED"
    ASSIGNED              = "ASSIGNED"
    PENDING_ACCEPTANCE    = "PENDING_ACCEPTANCE"
    ANALYSIS_IN_PROGRESS  = "ANALYSIS_IN_PROGRESS"
    IN_PROGRESS           = "ANALYSIS_IN_PROGRESS"
    ANALYSIS_FINISHED     = "ANALYSIS_FINISHED"
    REPORT_UPLOADED       = "REPORT_UPLOADED"
    ADMIN_REVIEW          = "ADMIN_REVIEW"
    REPORT_VALIDATED      = "REPORT_VALIDATED"
    SENT_TO_REQUESTER     = "SENT_TO_REQUESTER"
    COMPLETED             = "COMPLETED"

    @classmethod
    def all_states(cls):
        return {v for k,v in vars(cls).items() if not k.startswith("_") and isinstance(v,str)}

    @classmethod
    def terminal_states(cls):
        return {cls.REJECTED, cls.COMPLETED}

IBTIKAR_TRANSITIONS = {
    IbtikarState.SUBMITTED:             IbtikarState.VALIDATED,
    IbtikarState.VALIDATED:             IbtikarState.APPROVED,
    IbtikarState.APPROVED:              IbtikarState.APPOINTMENT_SCHEDULED,
    IbtikarState.APPOINTMENT_SCHEDULED: IbtikarState.SAMPLE_RECEIVED,
    IbtikarState.SAMPLE_RECEIVED:       IbtikarState.SAMPLE_VERIFIED,
    IbtikarState.SAMPLE_VERIFIED:       IbtikarState.ASSIGNED,
    IbtikarState.ASSIGNED:              IbtikarState.PENDING_ACCEPTANCE,
    IbtikarState.PENDING_ACCEPTANCE:    IbtikarState.IN_PROGRESS,
    IbtikarState.IN_PROGRESS:           IbtikarState.ANALYSIS_FINISHED,
    IbtikarState.ANALYSIS_FINISHED:     IbtikarState.REPORT_UPLOADED,
    IbtikarState.REPORT_UPLOADED:       IbtikarState.ADMIN_REVIEW,
    IbtikarState.ADMIN_REVIEW:          IbtikarState.REPORT_VALIDATED,
    IbtikarState.REPORT_VALIDATED:      IbtikarState.SENT_TO_REQUESTER,
    IbtikarState.SENT_TO_REQUESTER:     IbtikarState.COMPLETED,
    IbtikarState.REJECTED:              None,
    IbtikarState.COMPLETED:             None,
}

IBTIKAR_TRANSITION_ROLES = {
    IbtikarState.SUBMITTED:             [ROLE_REQUESTER, ROLE_CLIENT],
    IbtikarState.VALIDATED:             [ROLE_PLATFORM_ADMIN, ROLE_SUPER_ADMIN],
    IbtikarState.REJECTED:              [ROLE_PLATFORM_ADMIN, ROLE_SUPER_ADMIN],
    IbtikarState.APPROVED:              [ROLE_PLATFORM_ADMIN, ROLE_SUPER_ADMIN],
    IbtikarState.APPOINTMENT_SCHEDULED: [ROLE_PLATFORM_ADMIN, ROLE_MEMBER, ROLE_SUPER_ADMIN],
    IbtikarState.SAMPLE_RECEIVED:       [ROLE_PLATFORM_ADMIN, ROLE_MEMBER, ROLE_SUPER_ADMIN],
    IbtikarState.SAMPLE_VERIFIED:       [ROLE_MEMBER, ROLE_PLATFORM_ADMIN, ROLE_SUPER_ADMIN],
    IbtikarState.ASSIGNED:              [ROLE_PLATFORM_ADMIN, ROLE_SUPER_ADMIN],
    IbtikarState.PENDING_ACCEPTANCE:    [ROLE_MEMBER],
    IbtikarState.IN_PROGRESS:           [ROLE_MEMBER],
    IbtikarState.ANALYSIS_FINISHED:     [ROLE_MEMBER],
    IbtikarState.REPORT_UPLOADED:       [ROLE_MEMBER, ROLE_PLATFORM_ADMIN],
    IbtikarState.ADMIN_REVIEW:          [ROLE_PLATFORM_ADMIN, ROLE_SUPER_ADMIN],
    IbtikarState.REPORT_VALIDATED:      [ROLE_PLATFORM_ADMIN, ROLE_SUPER_ADMIN],
    IbtikarState.SENT_TO_REQUESTER:     [ROLE_PLATFORM_ADMIN, ROLE_SUPER_ADMIN],
    IbtikarState.COMPLETED:             [ROLE_PLATFORM_ADMIN, ROLE_SUPER_ADMIN],
}

# ═══════════════════════════════════════════════════════════════════════════
# GENOCLAB WORKFLOW
# ═══════════════════════════════════════════════════════════════════════════
class GenoClabState:
    SUBMITTED                  = "SUBMITTED"
    VALIDATED                  = "VALIDATED"
    REJECTED                   = "REJECTED"
    QUOTE_DRAFT                = "QUOTE_DRAFT"
    QUOTE_SENT                 = "QUOTE_SENT"
    QUOTE_VALIDATED_BY_CLIENT  = "QUOTE_VALIDATED_BY_CLIENT"
    QUOTE_REJECTED_BY_CLIENT   = "QUOTE_REJECTED_BY_CLIENT"
    INVOICE_GENERATED          = "INVOICE_GENERATED"
    ASSIGNED                   = "ASSIGNED"
    PENDING_ACCEPTANCE         = "PENDING_ACCEPTANCE"
    IN_PROGRESS                = "IN_PROGRESS"
    ANALYSIS_FINISHED          = "ANALYSIS_FINISHED"
    REPORT_UPLOADED            = "REPORT_UPLOADED"
    ADMIN_REVIEW               = "ADMIN_REVIEW"
    REPORT_VALIDATED           = "REPORT_VALIDATED"
    SENT_TO_CLIENT             = "SENT_TO_CLIENT"
    COMPLETED                  = "COMPLETED"

    @classmethod
    def all_states(cls):
        return {v for k,v in vars(cls).items() if not k.startswith("_") and isinstance(v,str)}

    @classmethod
    def terminal_states(cls):
        return {cls.REJECTED, cls.QUOTE_REJECTED_BY_CLIENT, cls.COMPLETED}

GENOCLAB_TRANSITIONS = {
    GenoClabState.SUBMITTED:                 GenoClabState.VALIDATED,
    GenoClabState.VALIDATED:                 GenoClabState.QUOTE_DRAFT,
    GenoClabState.QUOTE_DRAFT:               GenoClabState.QUOTE_SENT,
    GenoClabState.QUOTE_SENT:                GenoClabState.QUOTE_VALIDATED_BY_CLIENT,
    GenoClabState.QUOTE_VALIDATED_BY_CLIENT: GenoClabState.INVOICE_GENERATED,
    GenoClabState.INVOICE_GENERATED:         GenoClabState.ASSIGNED,
    GenoClabState.ASSIGNED:                  GenoClabState.PENDING_ACCEPTANCE,
    GenoClabState.PENDING_ACCEPTANCE:        GenoClabState.IN_PROGRESS,
    GenoClabState.IN_PROGRESS:               GenoClabState.ANALYSIS_FINISHED,
    GenoClabState.ANALYSIS_FINISHED:         GenoClabState.REPORT_UPLOADED,
    GenoClabState.REPORT_UPLOADED:           GenoClabState.ADMIN_REVIEW,
    GenoClabState.ADMIN_REVIEW:              GenoClabState.REPORT_VALIDATED,
    GenoClabState.REPORT_VALIDATED:          GenoClabState.SENT_TO_CLIENT,
    GenoClabState.SENT_TO_CLIENT:            GenoClabState.COMPLETED,
    GenoClabState.REJECTED:                  None,
    GenoClabState.QUOTE_REJECTED_BY_CLIENT:  None,
    GenoClabState.COMPLETED:                 None,
}

GENOCLAB_TRANSITION_ROLES = {
    GenoClabState.SUBMITTED:                 [ROLE_REQUESTER, ROLE_CLIENT],
    GenoClabState.VALIDATED:                 [ROLE_PLATFORM_ADMIN, ROLE_SUPER_ADMIN],
    GenoClabState.REJECTED:                  [ROLE_PLATFORM_ADMIN, ROLE_SUPER_ADMIN],
    GenoClabState.QUOTE_DRAFT:               [ROLE_PLATFORM_ADMIN, ROLE_SUPER_ADMIN],
    GenoClabState.QUOTE_SENT:                [ROLE_PLATFORM_ADMIN, ROLE_SUPER_ADMIN],
    GenoClabState.QUOTE_VALIDATED_BY_CLIENT: [ROLE_CLIENT, ROLE_REQUESTER],
    GenoClabState.QUOTE_REJECTED_BY_CLIENT:  [ROLE_CLIENT, ROLE_REQUESTER],
    GenoClabState.INVOICE_GENERATED:         [],
    GenoClabState.ASSIGNED:                  [ROLE_PLATFORM_ADMIN, ROLE_SUPER_ADMIN],
    GenoClabState.PENDING_ACCEPTANCE:        [ROLE_MEMBER],
    GenoClabState.IN_PROGRESS:               [ROLE_MEMBER],
    GenoClabState.ANALYSIS_FINISHED:         [ROLE_MEMBER],
    GenoClabState.REPORT_UPLOADED:           [ROLE_MEMBER, ROLE_PLATFORM_ADMIN],
    GenoClabState.ADMIN_REVIEW:              [ROLE_PLATFORM_ADMIN, ROLE_SUPER_ADMIN],
    GenoClabState.REPORT_VALIDATED:          [ROLE_PLATFORM_ADMIN, ROLE_SUPER_ADMIN],
    GenoClabState.SENT_TO_CLIENT:            [ROLE_PLATFORM_ADMIN, ROLE_SUPER_ADMIN],
    GenoClabState.COMPLETED:                 [ROLE_PLATFORM_ADMIN, ROLE_SUPER_ADMIN],
}

TERMINAL_STATES = {
    IbtikarState.REJECTED, IbtikarState.COMPLETED,
    GenoClabState.REJECTED, GenoClabState.QUOTE_REJECTED_BY_CLIENT, GenoClabState.COMPLETED,
}

REJECTION_STATES = {
    IbtikarState.REJECTED, GenoClabState.REJECTED, GenoClabState.QUOTE_REJECTED_BY_CLIENT,
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
    "SAMPLE_RECEIVED":        ("📦","Échantillon Reçu","#16A085"),
    "ANALYSIS_STARTED":       ("🔬","Analyse Démarrée","#D35400"),
    "ANALYSIS_FINISHED":      ("🧪","Analyse Terminée","#117A65"),
    "REPORT_VALIDATED":       ("📋","Rapport Validé","#1E8449"),
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
