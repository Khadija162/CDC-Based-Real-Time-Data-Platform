"""Streamlit CDC operations dashboard."""
import os
import requests
import pandas as pd
import streamlit as st
st.set_page_config(page_title="CDC Operations", layout="wide")
st.title("CDC · Real-Time Data Platform")
st.caption("PostgreSQL → Debezium → Kafka-compatible Redpanda → SQLite materialized view")
api = os.getenv("API_URL", "http://localhost:8000")
try:
    response = requests.get(api + "/api/metrics", timeout=5)
    response.raise_for_status()
    report = response.json()
    a, b = st.columns(2)
    a.metric("Active orders", report["orders"])
    b.metric("CDC events applied", report["events"])
    if report["recent_events"]:
        frame = pd.DataFrame(report["recent_events"])
        st.bar_chart(frame.set_index("type")["count"])
    if not report["configured"]:
        st.info("No stream materialization yet. Configure Debezium and launch worker.")
    if st.button("Explain operational state (AI)"):
        r = requests.post(api + "/api/ai/investigate", timeout=100)
        r.raise_for_status()
        st.json(r.json())
except requests.RequestException as exc:
    st.error(f"Backend unavailable: {exc}")
