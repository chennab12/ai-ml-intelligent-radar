from __future__ import annotations

import hashlib
import html
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import feedparser
import pandas as pd
import requests
from dateutil import parser as date_parser

from .config import SOURCES, TOPICS

UA = {"User-Agent": "AI-ML-TPM-Radar/1.0 (+educational dashboard)"}
CACHE_DIR = Path("/tmp/ai_ml_tpm_radar")
CACHE_FILE = CACHE_DIR / "last_good_live.csv"


def _text(value: str) -> str:
    value = html.unescape(re.sub(r"<[^>]+>", " ", value or ""))
    return re.sub(r"\s+", " ", value).strip()


def _date(entry) -> datetime:
    raw = entry.get("published") or entry.get("updated") or ""
    try:
        parsed = date_parser.parse(raw)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)


def classify(text: str) -> str:
    lower = text.lower()
    scores = {topic: sum(1 for word in words if word in lower) for topic, words in TOPICS.items()}
    return max(scores, key=scores.get) if max(scores.values(), default=0) else "AI/ML General"


def score_item(title: str, summary: str, age_days: int, tier: int) -> int:
    text = f"{title} {summary}".lower()
    recency = max(0, 35 - min(age_days, 35))
    technical = min(25, 5 * sum(k in text for k in ["benchmark", "latency", "inference", "agent", "model", "gpu", "evaluation"]))
    action = min(20, 5 * sum(k in text for k in ["release", "launch", "open source", "available", "framework", "guide"]))
    authority = 20 if tier == 1 else 10
    return min(100, recency + technical + action + authority)


def explain(title: str, summary: str, topic: str) -> tuple[str, str, str]:
    body = _text(summary)
    sentence = re.split(r"(?<=[.!?])\s+", body)[0][:280] or title
    takeaway = {
        "Agentic AI": "Track autonomy, tool-call success, guardrails, and human escalation—not just model quality.",
        "Inference": "Translate the change into latency, throughput, reliability, and cost-per-request impact.",
        "Accelerators": "Validate software compatibility and price/performance on your real workload before committing.",
        "MLOps": "Treat repeatability, observability, rollback, and evaluation gates as delivery requirements.",
        "Governance": "Add the new risk to acceptance criteria, red-team coverage, and release governance.",
        "Deep Learning": "Separate model-quality gains from added training, serving, and maintenance cost.",
    }.get(topic, "Identify the customer outcome, measurable KPI shift, dependency, and delivery risk.")
    action = f"TPM action: ask for one reproducible {topic.lower()} test with owner, baseline, target, and decision date."
    return sentence, takeaway, action


def _fetch_source(source: dict, days: int, per_source: int, now: datetime) -> list[dict]:
    """Fetch one source. Designed to run in a bounded worker thread."""
    response = requests.get(source["url"], headers=UA, timeout=(2, 4))
    response.raise_for_status()
    feed = feedparser.parse(response.content)
    if feed.bozo and not feed.entries:
        raise ValueError(str(feed.bozo_exception))
    rows = []
    for entry in feed.entries[:per_source]:
        published = _date(entry)
        age_days = max(0, (now - published.astimezone(timezone.utc)).days)
        if age_days > days:
            continue
        title = _text(entry.get("title", "Untitled"))
        summary = _text(entry.get("summary") or entry.get("description") or "")
        topic = classify(f"{title} {summary}")
        meaning, takeaway, action = explain(title, summary, topic)
        rows.append({
            "id": hashlib.sha1((title + entry.get("link", "")).encode()).hexdigest()[:12],
            "published": published,
            "source": source["name"], "source_type": source["kind"], "tier": source["tier"],
            "topic": topic, "title": title, "summary": meaning,
            "tpm_takeaway": takeaway, "recommended_action": action,
            "link": entry.get("link", ""), "score": score_item(title, summary, age_days, source["tier"]),
        })
    return rows


def _save_last_good(df: pd.DataFrame) -> None:
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        temporary = CACHE_FILE.with_suffix(".tmp")
        df.to_csv(temporary, index=False)
        temporary.replace(CACHE_FILE)
    except OSError:
        pass  # Cache is an optimization, never a reason to fail the dashboard.


def _load_last_good() -> pd.DataFrame:
    try:
        return pd.read_csv(CACHE_FILE, parse_dates=["published"])
    except (OSError, ValueError, pd.errors.EmptyDataError):
        return pd.DataFrame()


def fetch_news(days: int = 30, per_source: int = 12) -> tuple[pd.DataFrame, list[str]]:
    """Fetch trusted feeds concurrently; worst-case wait is about one timeout window."""
    started = time.perf_counter()
    now = datetime.now(timezone.utc)
    rows, errors = [], []
    with ThreadPoolExecutor(max_workers=min(6, len(SOURCES))) as pool:
        futures = {pool.submit(_fetch_source, source, days, per_source, now): source for source in SOURCES}
        for future in as_completed(futures):
            source = futures[future]
            try:
                rows.extend(future.result())
            except Exception as exc:
                errors.append(f"{source['name']}: {type(exc).__name__}")
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.drop_duplicates(subset=["title"]).sort_values(["score", "published"], ascending=False)
        df.attrs["data_mode"] = "Live"
        _save_last_good(df)
    else:
        df = _load_last_good()
        if not df.empty:
            df.attrs["data_mode"] = "Last successful live refresh"
            errors.append("All current feeds unavailable; showing last successful refresh")
    df.attrs["fetch_seconds"] = round(time.perf_counter() - started, 2)
    return df, errors


def load_demo() -> pd.DataFrame:
    path = Path(__file__).resolve().parent.parent / "data" / "demo_news.csv"
    df = pd.read_csv(path, parse_dates=["published"])
    return df


def trends(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["topic", "signals", "avg_score", "momentum"])
    recent_cut = pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=7)
    values = []
    for topic, group in df.groupby("topic"):
        published = pd.to_datetime(group["published"], utc=True)
        recent = int((published >= recent_cut).sum())
        older = max(1, len(group) - recent)
        momentum = round(recent / older, 1)
        values.append({"topic": topic, "signals": len(group), "avg_score": round(group["score"].mean()), "momentum": momentum})
    return pd.DataFrame(values).sort_values(["momentum", "signals"], ascending=False)


def ideas(df: pd.DataFrame) -> list[dict]:
    present = set(df["topic"]) if not df.empty else set()
    candidates = [
        ("AI release-impact copilot", "Agentic AI", "Maps new releases to roadmap, dependencies, risks, owners, and customer impact.", "Medium", "High"),
        ("Benchmark regression triage agent", "Inference", "Compares baseline vs candidate runs and drafts a reproducible Jira ticket.", "Medium", "Very high"),
        ("Customer POC readiness agent", "MLOps", "Checks environment, model, driver, framework, tests, and exit criteria before kickoff.", "Low", "Very high"),
        ("Model qualification evidence pack", "Inference", "Collects functional, performance, quality, and stability evidence into a sign-off pack.", "Medium", "Very high"),
        ("AI risk and dependency radar", "Governance", "Turns external signals into risk-register entries with severity and mitigation owners.", "Low", "High"),
        ("Weekly executive brief agent", "AI/ML General", "Produces a cited one-page brief: what changed, why it matters, and decisions needed.", "Low", "High"),
        ("Hardware/software compatibility scout", "Accelerators", "Tracks model-framework-driver-hardware compatibility and flags breaking changes.", "Medium", "High"),
        ("Evaluation gap finder", "Deep Learning", "Suggests missing quality, safety, and edge-case tests from model and product changes.", "Medium", "High"),
    ]
    ranked = sorted(candidates, key=lambda x: (x[1] in present, x[4] == "Very high"), reverse=True)
    return [{"idea": a, "trigger": b, "value": c, "effort": d, "impact": e, "first_step": "Create a 10-ticket or 10-run pilot; require citations, human approval, and a measurable KPI."} for a,b,c,d,e in ranked]
