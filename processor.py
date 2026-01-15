import os
import json
import re
import uuid
from io import BytesIO
from typing import Dict, Optional

import pdfplumber
import PyPDF2
import google.generativeai as genai


# =================================================
# IN-MEMORY MVP STORAGE (DEMO SAFE)
# =================================================
SYSTEM_STATS = {
    "invoices_analyzed": 0,
    "risky_shipments": 0,
    "holds_predicted": 0,
}

OUTCOME_FEEDBACK = []


# =================================================
# UTILITIES
# =================================================
def safe_number(val):
    if val is None:
        return None
    try:
        return float(str(val).replace(",", "").strip())
    except Exception:
        return None


def extract_json_safe(text: str):
    try:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1:
            return None
        return json.loads(text[start:end + 1])
    except Exception:
        return None


# =================================================
# CORE PROCESSOR
# =================================================
class InvoiceProcessor:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found")

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel("models/gemini-1.5-flash")

    # -------------------------------------------------
    # PDF TEXT EXTRACTION
    # -------------------------------------------------
    def extract_text_from_pdf(self, pdf_file: BytesIO) -> str:
        pdf_file.seek(0)
        text = ""

        try:
            with pdfplumber.open(pdf_file) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""
        except Exception:
            pass

        if len(text.strip()) > 100:
            return text.strip()

        try:
            pdf_file.seek(0)
            reader = PyPDF2.PdfReader(pdf_file)
            for page in reader.pages:
                text += page.extract_text() or ""
        except Exception:
            pass

        return text.strip()

    # -------------------------------------------------
    # RULE-BASED FIELD EXTRACTION
    # -------------------------------------------------
    def _basic_field_extract(self, text: str) -> Dict:
        def find(pattern):
            m = re.search(pattern, text, re.IGNORECASE)
            return m.group(1).strip() if m else None

        return {
            "invoice_number": find(r"invoice\s*no[:\-]?\s*([A-Z0-9\-\/]+)"),
            "invoice_date": find(r"date[:\-]?\s*([0-9\/\-\.]+)"),
            "seller_name": None,
            "buyer_name": None,
            "gstin": find(r"GSTIN[:\-]?\s*([A-Z0-9]{15})"),
            "iec_code": find(r"IEC[:\-]?\s*([0-9]{10})"),
            "currency": find(r"\b(USD|EUR|GBP|INR)\b"),
            "subtotal": None,
            "tax_amount": None,
            "total_amount": None,
            "hsn_code": find(r"\bHSN[:\-]?\s*([0-9]{6,8})\b"),
            "incoterms": find(r"\b(EXW|FOB|CIF|DAP|DDP|CFR)\b"),
            "lut_reference": None,
            "line_items": [],
        }

    # -------------------------------------------------
    # AI STRUCTURING (HARDENED)
    # -------------------------------------------------
    def _ai_structure(self, text: str) -> Optional[Dict]:
        prompt = f"""
Return ONLY valid JSON.
All keys must exist. Use null if unknown.

Schema:
{{
  "seller_name": null,
  "buyer_name": null,
  "currency": null,
  "subtotal": null,
  "tax_amount": null,
  "total_amount": null,
  "hsn_code": null,
  "incoterms": null,
  "gstin": null,
  "iec_code": null,
  "lut_reference": null
}}

Invoice Text:
{text[:6000]}
"""

        try:
            response = self.model.generate_content(prompt)
            return extract_json_safe(response.text)
        except Exception:
            return None

    # -------------------------------------------------
    # RISK ENGINE (REAL)
    # -------------------------------------------------
    def assess_export_risk(self, invoice: Dict) -> Dict:
        score = 0
        reasons, fixes = [], []

        def penalize(points, reason, fix):
            nonlocal score
            score += points
            reasons.append(reason)
            fixes.append(fix)

        if not invoice.get("iec_code"):
            penalize(25, "IEC missing", "Add valid IEC")

        if not invoice.get("hsn_code"):
            penalize(20, "HSN missing", "Declare correct HSN")

        if not invoice.get("incoterms"):
            penalize(15, "Incoterms missing", "Specify FOB / CIF")

        if invoice.get("currency") == "INR":
            penalize(20, "Export invoiced in INR", "Use permitted foreign currency")

        total = safe_number(invoice.get("total_amount"))
        if total is None or total <= 0:
            penalize(20, "Invoice value invalid", "Correct invoice total")

        score = min(score, 100)

        level = "Low" if score < 30 else "Medium" if score < 60 else "High"
        decision = (
            "SAFE_TO_SHIP" if level == "Low"
            else "REVIEW_BEFORE_SHIPPING" if level == "Medium"
            else "DO_NOT_SHIP"
        )

        if level in ["Medium", "High"]:
            SYSTEM_STATS["risky_shipments"] += 1
        if score >= 70:
            SYSTEM_STATS["holds_predicted"] += 1

        return {
            "risk_score": score,
            "risk_level": level,
            "confidence": "Medium",
            "shipment_decision": decision,
            "risk_reasons": reasons,
            "fix_suggestions": fixes,
            "risk_summary": f"{level} customs risk based on compliance signals",
        }

    # -------------------------------------------------
    # WHAT-IF SIMULATOR (REQUIRED BY UI)
    # -------------------------------------------------
    def simulate_changes(self, invoice: Dict, new_value, new_incoterm):
        simulated = invoice.copy()

        if new_value:
            simulated["total_amount"] = new_value

        if new_incoterm != "UNCHANGED":
            simulated["incoterms"] = new_incoterm

        risk = self.assess_export_risk(simulated)

        return {
            "risk_score": risk["risk_score"],
            "summary": risk["risk_summary"],
        }

    # -------------------------------------------------
    # CUSTOMS OFFICER VIEW
    # -------------------------------------------------
    def customs_officer_view(self, invoice: Dict) -> str:
        issues = []

        if not invoice.get("hsn_code"):
            issues.append("HSN not declared")
        if not invoice.get("incoterms"):
            issues.append("Incoterms missing")
        if invoice.get("currency") == "INR":
            issues.append("Export invoiced in INR")

        return (
            "A customs officer may question this shipment because "
            + "; ".join(issues)
            if issues
            else "Invoice appears standard with no obvious red flags."
        )

    # -------------------------------------------------
    # FEEDBACK LOOP
    # -------------------------------------------------
    def store_outcome_feedback(self, invoice_id: str, outcome: str):
        OUTCOME_FEEDBACK.append(
            {"invoice_id": invoice_id, "outcome": outcome}
        )

    # -------------------------------------------------
    # MAIN PIPELINE
    # -------------------------------------------------
    def process_pdf(self, pdf_file: BytesIO) -> Dict:
        SYSTEM_STATS["invoices_analyzed"] += 1
        invoice_id = str(uuid.uuid4())

        text = self.extract_text_from_pdf(pdf_file)
        invoice = self._basic_field_extract(text)

        ai_data = self._ai_structure(text)
        if ai_data:
            for k, v in ai_data.items():
                if v not in (None, "", []):
                    invoice[k] = v

        risk = self.assess_export_risk(invoice)

        return {
            "invoice_id": invoice_id,
            "invoice_type": "Commercial",
            "invoice_quality": "Good" if len(text) > 300 else "Poor",
            "invoice_data": invoice,
            "risk_assessment": risk,
            "customs_officer_view": self.customs_officer_view(invoice),
            "system_stats": SYSTEM_STATS,
            "extraction_method": "ai+rules",
        }
