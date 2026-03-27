# 🧬 PLAGENOR 4.0

## Plateforme de Gouvernance Génomique — ESSBO · ORAN

**Institutional platform for governing genomic analysis requests, financing, and compliance.**

## 🚀 Quick Start

```bash
cd plagenor
streamlit run app.py
```

New users: self-register as CLIENT or submit as GUEST on home page.

## 🔁 Workflows

IBTIKAR: DRAFT → SUBMITTED → VALIDATION_PEDAGOGIQUE → VALIDATION_FINANCE → ASSIGNED → IN_PROGRESS → REPORT_UPLOADED → COMPLETED → CLOSED

GENOCLAB: REQUEST_CREATED → QUOTE_DRAFT → QUOTE_SENT → QUOTE_VALIDATED_BY_CLIENT → INVOICE_GENERATED → PAYMENT_CONFIRMED → ASSIGNED → ANALYSIS_IN_PROGRESS → REPORT_UPLOADED → COMPLETED → ARCHIVED

## 🔒 Governance

- All transitions enforced by state_machine.py (no skips)
- Budget cap 200,000 DZD/year enforced by budget_engine.py
- SUPER_ADMIN override requires justification (permanent log)
- Every action logged in audit_logs.json

## 🏗 27 modules, 4,708 lines

© 2026 Prof. Mohamed Merzoug — ESSBO, Oran, Algérie
