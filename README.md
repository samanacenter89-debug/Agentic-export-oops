# Agentic Export Ops

## 🇮🇳 AI-Powered Pre-Shipment Invoice Risk Intelligence for Indian Exporters

**Agentic Export Ops** is an AI-powered pre-shipment compliance and risk-intelligence tool designed for Indian exporters.

It analyzes commercial invoice PDFs *before shipment*, extracts critical export data, evaluates compliance risks, and explains **why an invoice may be delayed, queried, or rejected by customs** — along with clear fix suggestions.

This MVP focuses on **invoice understanding + early risk detection**, helping exporters avoid costly mistakes *before goods leave the factory*.

---

## The Problem 

Indian exporters frequently face:
-  Missing IEC, GSTIN, HSN, or Incoterms
-  Incorrect invoice currency usage
-  GST / LUT conflicts
-  Manual checks with no risk visibility
-  Customs queries, shipment delays, and refund blocks

 Even a single invoice error can delay or block an entire shipment.

---

##MVP Solution

Agentic Export Ops acts as a **defensive AI assistant** for exporters:

- Extracts structured data from invoice PDFs
- Identifies export-critical compliance fields
- Calculates a **customs risk score**
- Explains *what is wrong* and *what to fix*
- Predicts **likely customs actions** (query, delay, rejection)

>  The system flags risk — **final decisions remain with the exporter** (compliance-safe by design).

---

##  MVP Features (Feb Launch Scope)

### Invoice Data Extraction
- Invoice number & date
- Seller & buyer details (when available)
- Currency, subtotal, tax, total (AI-assisted)
- Structured JSON output

###  Export-Critical Fields
- **IEC Code**
- **GSTIN**
- **HSN Code**
- **Incoterms** (FOB, CIF, EXW, etc.)
- **LUT reference** (if present)

### Risk Assessment (Core Differentiator)
- Risk score (0–100)
- Risk level: Low / Medium / High
- Clear, human-readable risk reasons
- Actionable fix suggestions

### Customs Impact Intelligence
- Predicts likely customs actions:
  - Shipment rejection
  - Customs query
  - Clearance delay
  - Refund blockage
- Severity-based alerts (High / Medium)

### Clean Streamlit UI
- Dark-theme interface
- One-click PDF upload
- Instant feedback
- Download extracted invoice JSON

---

##  How It Works

1. Exporter uploads a commercial invoice PDF  
2. System extracts text using defensive PDF parsing  
3. AI structures invoice data (safe & optional)  
4. Rule-based fallback ensures zero failure  
5. Risk engine evaluates export compliance  
6. Customs impact is explained in plain language  

---

##  Tech Stack

- **Python**
- **Streamlit** (UI)
- **Google Gemini API** (AI structuring)
- **pdfplumber & PyPDF2** (PDF extraction)
- **Pandas** (data handling)

---

##  Project Structure

