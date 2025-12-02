"""
InkSage Background Workers
==========================

This package manages asynchronous processing threads (like AI generation)
to keep the main application interface responsive and fluid.
"""

from .generation_worker import GenerationWorker, GenerationRequest

__all__ = [
    "GenerationWorker",
    "GenerationRequest",
]