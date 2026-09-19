TOPICS = {
    "Agentic AI": ["agent", "agentic", "tool use", "mcp", "multi-agent"],
    "Inference": ["inference", "serving", "latency", "throughput", "vllm", "triton", "quantization"],
    "Deep Learning": ["training", "neural", "transformer", "fine-tuning", "multimodal"],
    "Accelerators": ["gpu", "accelerator", "cuda", "gaudi", "xeon", "npu", "tpu"],
    "MLOps": ["mlops", "kubernetes", "observability", "evaluation", "benchmark", "deployment"],
    "Governance": ["safety", "security", "responsible ai", "regulation", "governance"],
}

# First-party research/product blogs and widely used technical communities.
SOURCES = [
    {"name": "OpenAI", "url": "https://openai.com/news/rss.xml", "tier": 1, "kind": "Vendor"},
    {"name": "Google AI", "url": "https://blog.google/technology/ai/rss/", "tier": 1, "kind": "Vendor"},
    {"name": "Microsoft Research", "url": "https://www.microsoft.com/en-us/research/feed/", "tier": 1, "kind": "Research"},
    {"name": "NVIDIA", "url": "https://blogs.nvidia.com/feed/", "tier": 1, "kind": "Vendor"},
    {"name": "Hugging Face", "url": "https://huggingface.co/blog/feed.xml", "tier": 1, "kind": "Community"},
    {"name": "AWS Machine Learning", "url": "https://aws.amazon.com/blogs/machine-learning/feed/", "tier": 1, "kind": "Cloud"},
    {"name": "MIT News AI", "url": "https://news.mit.edu/rss/topic/artificial-intelligence2", "tier": 1, "kind": "Research"},
]

TPM_KPIS = [
    ("Latency", "Time per request/token", "p50/p95/p99; TTFT; inter-token latency"),
    ("Throughput", "Useful work per second", "requests/s; tokens/s; batch efficiency"),
    ("Quality", "Task correctness", "accuracy; pass@k; groundedness; human win rate"),
    ("Reliability", "Service consistency", "availability; error rate; timeout rate"),
    ("Cost", "Spend per useful outcome", "$ / 1M tokens; GPU-hours; cost/request"),
    ("Capacity", "Headroom at peak", "GPU utilization; concurrency; queue depth"),
    ("Safety", "Risk-control effectiveness", "policy violation; jailbreak; leakage rate"),
    ("Delivery", "Execution predictability", "lead time; escaped defects; rollback rate"),
]

