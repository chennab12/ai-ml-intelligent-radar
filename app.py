from __future__ import annotations

from datetime import datetime, timezone
from time import perf_counter

import pandas as pd
import streamlit as st

from radar.config import SOURCES, TPM_KPIS
from radar.engine import fetch_news, ideas, load_demo, trends

APP_STARTED = perf_counter()
st.set_page_config(page_title="AI/ML TPM Radar", page_icon="🧭", layout="wide")

st.markdown("""
<style>
.block-container{padding-top:1.6rem;max-width:1500px}.hero{padding:1.4rem 1.6rem;border-radius:20px;color:white;background:linear-gradient(120deg,#172554,#4338ca 58%,#0891b2);margin-bottom:1rem}.hero h1{margin:0;font-size:2.1rem}.hero p{margin:.45rem 0 0;color:#dbeafe}.stMetric{background:white;border:1px solid #e5e7eb;padding:12px;border-radius:14px}.signal{border-left:5px solid #6366f1;background:white;padding:1rem 1.1rem;border-radius:12px;margin:.6rem 0;box-shadow:0 2px 10px #17203312}.muted{color:#64748b;font-size:.88rem}.pill{display:inline-block;background:#eef2ff;color:#4338ca;padding:.18rem .55rem;border-radius:999px;font-size:.78rem;font-weight:650}.takeaway{background:#ecfeff;padding:.65rem;border-radius:9px;margin-top:.5rem}.action{background:#f5f3ff;padding:.65rem;border-radius:9px;margin-top:.4rem}</style>
""", unsafe_allow_html=True)

st.markdown("<div class='hero'><h1>AI/ML TPM Intelligence Radar</h1><p>Trusted signals → simple meaning → measurable TPM action</p></div>", unsafe_allow_html=True)

with st.sidebar:
    st.header("Radar controls")
    days = st.select_slider("Look-back window", options=[7, 14, 30, 60, 90], value=30)
    live = st.toggle("Refresh trusted live feeds", value=False, help="Off by default for fast, reliable startup. Demo data shows the full experience.")
    max_items = st.slider("Maximum signals", 5, 50, 20)
    st.caption("Source policy: first-party labs, major cloud/accelerator vendors, research institutions, and established technical communities.")
    if st.button("Refresh now", width="stretch"):
        st.cache_data.clear()
        st.rerun()

@st.cache_data(ttl=1800, show_spinner=False)
def get_data(use_live: bool, lookback: int):
    if use_live:
        data, failures = fetch_news(lookback)
        if not data.empty:
            return data, failures, data.attrs.get("data_mode", "Live"), data.attrs.get("fetch_seconds", 0.0)
    return load_demo(), [], "Curated demo", 0.0

if live:
    with st.status("Refreshing trusted sources…", expanded=False) as refresh_status:
        df, failures, mode, fetch_seconds = get_data(live, days)
        refresh_status.update(label=f"Refresh completed in {fetch_seconds:.1f}s", state="complete")
else:
    df, failures, mode, fetch_seconds = get_data(live, days)
df["published"] = pd.to_datetime(df["published"], utc=True)

topics = sorted(df["topic"].unique())
selected_topics = st.sidebar.multiselect("Topics", topics, default=topics)
query = st.sidebar.text_input("Search", placeholder="vLLM, agents, GPU, safety…")
view = df[df["topic"].isin(selected_topics)].copy()
if query:
    mask = view[["title", "summary", "tpm_takeaway"]].fillna("").agg(" ".join, axis=1).str.contains(query, case=False, regex=False)
    view = view[mask]
view = view.head(max_items)

fresh = int((view["published"] >= pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=7)).sum())
cols = st.columns(5)
cols[0].metric("Mode", mode)
cols[1].metric("High-value signals", len(view))
cols[2].metric("Last 7 days", fresh)
cols[3].metric("Topics covered", view["topic"].nunique())
cols[4].metric("Avg relevance", f"{view['score'].mean():.0f}/100" if len(view) else "—")
if failures:
    st.warning(f"Some feeds were temporarily unavailable ({len(failures)}). Available sources are still shown.")

tabs = st.tabs(["Executive brief", "Signal feed", "Trend radar", "TPM KPI playbook", "Agentic ideas", "Sources & method"])

with tabs[0]:
    st.subheader("What matters now")
    trend_df = trends(view)
    if trend_df.empty:
        st.info("No signals match the current filters.")
    else:
        top = trend_df.iloc[0]
        st.success(f"Strongest current cluster: **{top.topic}** — {int(top.signals)} relevant signals, {top.momentum}× recent-to-older momentum.")
        st.markdown("#### TPM interpretation")
        st.markdown("Focus on decisions, not headlines: ask what changed, which customer/workload is affected, which KPI should move, what can regress, and what evidence changes the roadmap.")
        st.markdown("#### This week's 3 moves")
        st.markdown("1. Select one signal and connect it to an active roadmap item or customer POC.\n2. Request a reproducible baseline with quality, latency, throughput, reliability, and cost.\n3. Record one decision, owner, risk, and follow-up date in the program log.")

with tabs[1]:
    st.subheader("Ranked, simplified signals")
    for _, row in view.iterrows():
        date = row.published.strftime("%b %d, %Y")
        link = f"<a href='{row.link}' target='_blank'>Open source ↗</a>" if str(row.link).startswith("http") else ""
        st.markdown(f"<div class='signal'><span class='pill'>{row.topic}</span> <span class='muted'>{row.source} · {date} · relevance {row.score}/100</span><h4>{row.title}</h4><div>{row.summary}</div><div class='takeaway'><b>Why a TPM should care:</b> {row.tpm_takeaway}</div><div class='action'><b>Use it:</b> {row.recommended_action}</div><div class='muted' style='margin-top:.55rem'>{link}</div></div>", unsafe_allow_html=True)

with tabs[2]:
    st.subheader("Emerging trend radar")
    trend_df = trends(view)
    if not trend_df.empty:
        chart_data = trend_df.rename(columns={"signals":"Signal volume", "momentum":"7-day momentum", "avg_score":"Relevance", "topic":"Topic"})
        st.scatter_chart(chart_data, x="Signal volume", y="7-day momentum", size="Relevance", color="Topic", height=440)
        st.dataframe(trend_df.rename(columns={"topic":"Trend", "signals":"Signals", "avg_score":"Avg relevance", "momentum":"Momentum"}), hide_index=True, width="stretch")
        st.caption("Projection is directional, not a forecast: momentum compares recent signal volume with older items in the selected window.")

with tabs[3]:
    st.subheader("KPI translation playbook")
    kpi = pd.DataFrame(TPM_KPIS, columns=["KPI", "Plain-English meaning", "Measures to request"])
    st.dataframe(kpi, hide_index=True, width="stretch")
    st.info("Golden rule: never accept a performance claim without workload, hardware, software versions, precision, batch/concurrency, prompt/output lengths, quality constraint, baseline, and repeated-run variance.")

with tabs[4]:
    st.subheader("Top agentic AI ideas worth piloting")
    st.caption("Ranked for a beginner AI/ML customer-engineering TPM: high value, bounded scope, measurable outcome, and human approval.")
    idea_df = pd.DataFrame(ideas(view))
    st.dataframe(idea_df.rename(columns={"idea":"Idea", "trigger":"Signal area", "value":"What it does", "effort":"Effort", "impact":"Potential impact", "first_step":"Safe first pilot"}), hide_index=True, width="stretch")
    st.warning("Keep agents advisory until evaluation proves reliability. Require citations, least-privilege tools, audit logs, human approval for consequential actions, and a kill switch.")

with tabs[5]:
    st.subheader("Trust and ranking method")
    st.markdown("**Ranking score (0–100):** source authority + recency + technical depth + actionability. This is a prioritization aid, not an objective truth or investment forecast.")
    st.dataframe(pd.DataFrame(SOURCES).rename(columns={"name":"Source", "url":"Feed URL", "tier":"Trust tier", "kind":"Type"}), hide_index=True, width="stretch")
    st.markdown("**Top 1% interpretation:** a deliberately small allowlist of primary or established technical sources, followed by deduplication and relevance ranking. It does not claim a mathematically measured percentile of the entire web.")
    st.markdown("**Quality controls:** visible source links, no fabricated citations, transparent score factors, graceful feed failure, and separate facts from directional projections.")

render_seconds = perf_counter() - APP_STARTED
st.caption(f"Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} · Page render {render_seconds:.2f}s · Educational decision support; verify important claims at the linked primary source.")
