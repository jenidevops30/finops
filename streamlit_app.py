import streamlit as st

from finops_platform.config import get_settings
from finops_platform.logging import configure_logging


settings = get_settings()
configure_logging(settings.log_level)

st.set_page_config(page_title="FinOps Platform", page_icon="💰", layout="wide")
st.title("AWS FinOps Intelligence Platform")
st.caption("Phase 1 foundation — read-only, evidence-driven architecture")

col1, col2, col3 = st.columns(3)
col1.metric("Environment", settings.environment)
col2.metric("AWS Region", settings.aws_region)
col3.metric("AWS Access", "Read-only" if settings.aws_read_only else "Configuration error")

st.info(
    "Phase 1 establishes the foundation. AWS collection and deterministic analysis are "
    "introduced in later phases. No infrastructure mutation operations are exposed here."
)
