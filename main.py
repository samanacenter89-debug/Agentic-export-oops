"""
Streamlit UI for Agentic Export Ops
Pre-Shipment Export Invoice Risk Checker (Thiel-Level MVP)
"""

import streamlit as st
from io import BytesIO
import pandas as pd

from processor import InvoiceProcessor


# -----------------------------
# PAGE CONFIG (MUST BE FIRST)
# -----------------------------
st.set_page_config(
    page_title="Agentic Export Ops",
    page_icon="📄",
    layout="wide"
)


# -----------------------------
# SAFE UTILITIES
# -----------------------------
def safe_float(val, default=0.0):
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


# -----------------------------
# UI STYLES
# -----------------------------
st.markdown(
    """
    <style>
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    .stButton>button {
        background-color: #1F77B4;
        color: white;
        border-radius: 6px;
        border: none;
        padding: 0.6rem 1.2rem;
    }
    .decision-safe { background:#0f5132; padding:15px; border-radius:8px; }
    .decision-review { background:#664d03; padding:15px; border-radius:8px; }
    .decision-stop { background:#842029; padding:15px; border-radius:8px; }
    .signal-box { background:#111827; padding:15px; border-radius:8px; }
    </style>
    """,
    unsafe_allow_html=True
)


# -----------------------------
# LOAD PROCESSOR (CACHE SAFE)
# -----------------------------
@st.cache_resource
def get_processor():
    return InvoiceProcessor()


# -----------------------------
# SHIPMENT DECISION
# -----------------------------
def display_shipment_decision(decision: str, summary: str):
    st.markdown("## 🚦 Shipment Decision")

    if decision == "SAFE_TO_SHIP":
        st.markdown(
            f"<div class='decision-safe'>✅ <b>SAFE TO SHIP</b><br>{summary}</div>",
            unsafe_allow_html=True,
        )
    elif decision == "REVIEW_BEFORE_SHIPPING":
        st.markdown(
            f"<div class='decision-review'>⚠️ <b>REVIEW BEFORE SHIPPING</b><br>{summary}</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"<div class='decision-stop'>❌ <b>DO NOT SHIP</b><br>{summary}</div>",
            unsafe_allow_html=True,
        )


# -----------------------------
# RISK ASSESSMENT UI
# -----------------------------
def display_risk_assessment(risk: dict):
    st.header("🚨 Customs Outcome Risk")

    col1, col2, col3 = st.columns(3)

    col1.metric("Hold Probability", f"{risk.get('risk_score', 0)}%")
    col2.metric("Risk Level", risk.get("risk_level", "—"))
    col3.metric("Decision Confidence", risk.get("confidence", "—"))

    st.subheader("🧠 Why Customs Might Intervene")
    for r in risk.get("risk_reasons", []):
        st.write(f"• {r}")

    st.subheader("🔧 What You Can Fix")
    for f in risk.get("fix_suggestions", []):
        st.write(f"✔ {f}")


# -----------------------------
# CUSTOMS OFFICER EXPLANATION
# -----------------------------
def display_customs_explanation(explanation: str):
    st.markdown("---")
    st.header("🧑‍✈️ How a Customs Officer May See This")
    st.markdown(
        f"<div class='signal-box'>{explanation}</div>",
        unsafe_allow_html=True,
    )


# -----------------------------
# WHAT-IF SIMULATOR (CRASH-PROOF)
# -----------------------------
def display_what_if_simulator(base_invoice: dict, processor: InvoiceProcessor):
    st.markdown("---")
    st.header("🧪 What-If Risk Simulator")

    with st.expander("Simulate changes before shipping"):
        new_value = st.number_input(
            "Adjusted Invoice Value",
            value=safe_float(base_invoice.get("total_amount")),
            step=100.0,
            min_value=0.0
        )

        new_incoterm = st.selectbox(
            "Change Incoterm",
            ["UNCHANGED", "FOB", "CIF", "DAP", "EXW"]
        )

        if st.button("Recalculate Risk"):
            simulated = processor.simulate_changes(
                base_invoice,
                new_value,
                new_incoterm
            )

            st.metric("New Hold Probability", f"{simulated.get('risk_score', 0)}%")
            st.write(simulated.get("summary", "No summary available"))


# -----------------------------
# FEEDBACK LOOP
# -----------------------------
def display_outcome_feedback(invoice_id: str, processor: InvoiceProcessor):
    st.markdown("---")
    st.header("📬 Shipment Outcome Feedback")

    outcome = st.radio(
        "What happened after shipment?",
        [
            "Not shipped yet",
            "Cleared smoothly",
            "Queried by customs",
            "Held / Rejected",
        ],
    )

    if st.button("Submit Outcome"):
        processor.store_outcome_feedback(invoice_id, outcome)
        st.success("Outcome recorded. System will learn from this.")


# -----------------------------
# EVIDENCE DASHBOARD
# -----------------------------
def display_evidence_dashboard(stats: dict):
    st.markdown("---")
    st.header("📊 System Evidence")

    c1, c2, c3 = st.columns(3)
    c1.metric("Invoices Analyzed", stats.get("invoices_analyzed", 0))
    c2.metric("Risky Shipments Detected", stats.get("risky_shipments", 0))
    c3.metric("Holds Predicted", stats.get("holds_predicted", 0))


# -----------------------------
# INVOICE DATA
# -----------------------------
def display_invoice_data(invoice: dict):
    st.markdown("---")
    st.header("📦 Extracted Invoice Data")
    st.json(invoice)


# -----------------------------
# MAIN APP
# -----------------------------
def main():
    st.title("📄 Agentic Export Ops")
    st.markdown("### Predict customs risk *before* goods move.")
    st.markdown("---")

    processor = get_processor()

    uploaded_file = st.file_uploader(
        "Upload Commercial Invoice (PDF)",
        type=["pdf"],
    )

    demo_mode = st.checkbox("🎯 Use sample invoice")

    if (uploaded_file or demo_mode) and st.button("🔍 Analyze Shipment"):
        with st.spinner("Analyzing invoice intelligence..."):
            if demo_mode:
                with open("sample_invoice.pdf", "rb") as f:
                    pdf_bytes = BytesIO(f.read())
            else:
                pdf_bytes = BytesIO(uploaded_file.read())

            result = processor.process_pdf(pdf_bytes)

        display_shipment_decision(
            result["risk_assessment"]["shipment_decision"],
            result["risk_assessment"]["risk_summary"],
        )

        display_risk_assessment(result["risk_assessment"])
        display_customs_explanation(result["customs_officer_view"])
        display_what_if_simulator(result["invoice_data"], processor)
        display_outcome_feedback(result["invoice_id"], processor)
        display_evidence_dashboard(result["system_stats"])
        display_invoice_data(result["invoice_data"])

    st.caption(
        "⚠️ Risk signals only. Not legal or customs advice. Final responsibility remains with exporter."
    )


if __name__ == "__main__":
    main()
