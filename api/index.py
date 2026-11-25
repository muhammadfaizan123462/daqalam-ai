"""Vercel serverless entry point for Da Qalam AI.

Re-exports the FastAPI app from server.py so Vercel can serve it as a
serverless function. No Qwen key is required: without QWEN_API_KEY the
app runs in clearly-labelled demo mode.
"""

from server import app  # noqa: F401  (Vercel serves this ASGI app)
