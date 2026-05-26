"""
Celery configuration for PROJ-02 Document Pipeline.

Handles async PDF processing tasks:
  - compress_pdf: Downscale and recompress PDF images
  - split_pdf:   Split a PDF into individual pages
  - merge_pdfs:  Merge multiple PDFs into one

Broker & result backend: Redis
Max task runtime: 300 seconds
"""

import os
from celery import Celery

# ── Redis connection ────────────────────────────────────────────
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

app = Celery(
    "document-pipeline",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

# ── Celery Config ───────────────────────────────────────────────
app.conf.update(
    # Timeouts
    task_time_limit=300,            # Hard limit: 5 minutes
    task_soft_time_limit=270,      # Soft limit: 4.5 min (graceful shutdown)

    # Retries
    task_acks_late=True,           # Ack after execution (don't lose on crash)
    worker_prefetch_multiplier=1,  # Fetch one task at a time

    # Serialization
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],

    # Retry policy
    broker_transport_options={
        "visibility_timeout": 3600,  # 1 hour task visibility
    },

    # Result expiry
    result_expires=86400,  # 24 hours

    # Logging
    worker_log_format="%(asctime)s %(levelname)s %(message)s",
)


# ── Task: compress_pdf ──────────────────────────────────────────
@app.task(bind=True, max_retries=3)
def compress_pdf(self, input_path: str, output_path: str, dpi: int = 150) -> dict:
    """Compress embedded images in a PDF by downscaling."""
    from main import compress_pdf_images as _compress

    try:
        result_path = _compress(input_path, output_path, dpi=dpi)
        return {
            "status": "completed",
            "output": result_path,
            "input": input_path,
            "dpi": dpi,
        }
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


# ── Task: split_pdf ──────────────────────────────────────────────
@app.task(bind=True, max_retries=3)
def split_pdf(self, input_path: str, output_dir: str) -> dict:
    """Split a PDF into individual page files."""
    from main import split_pdf as _split

    try:
        files = _split(input_path, output_dir)
        return {
            "status": "completed",
            "pages": len(files),
            "output_files": files,
            "input": input_path,
        }
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


# ── Task: merge_pdfs ─────────────────────────────────────────────
@app.task(bind=True, max_retries=3)
def merge_pdfs(self, input_paths: list[str], output_path: str) -> dict:
    """Merge multiple PDFs into one."""
    from main import merge_pdfs as _merge

    try:
        result_path = _merge(input_paths, output_path)
        return {
            "status": "completed",
            "output": result_path,
            "input_count": len(input_paths),
        }
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
