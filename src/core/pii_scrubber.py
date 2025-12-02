"""
InkSage Privacy Guard
=====================

A high-performance PII (Personally Identifiable Information) scrubber.
It sanitizes user input before it reaches the AI engine to ensure
sensitive data never leaves the privacy boundary, even locally.
"""

import re
import logging
from typing import Optional

from ..utils.config import config

class PIIScrubber:
    """
    Regex-based PII sanitizer.
    Replaces sensitive entities with generic tokens like [EMAIL] or [PHONE].
    """
    
    def __init__(self):
        self.logger = logging.getLogger("InkSage.Privacy")
        self.enabled = config.get('privacy.pii_scrubbing', True)
        
        # --- Pre-compiled Regex Patterns for Performance ---
        
        # 1. Email Address
        # Matches standard email formats
        self._email_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        )
        
        # 2. Phone Number (US & International formats)
        # Matches: +1-555-555-5555, 555-555-5555, (555) 555-5555
        self._phone_pattern = re.compile(
            r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
        )
        
        # 3. IPv4 Address
        # Matches valid IP ranges to prevent leaking server infrastructure
        self._ip_pattern = re.compile(
            r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        )
        
        # 4. Social Security Number (US)
        # Matches: 000-00-0000
        self._ssn_pattern = re.compile(
            r'\b\d{3}-\d{2}-\d{4}\b'
        )
        
        # 5. Credit Card Numbers
        # Matches groups of 4 digits: 0000-0000-0000-0000
        self._cc_pattern = re.compile(
            r'\b(?:\d{4}[-\s]?){3}\d{4}\b'
        )

    def scrub(self, text: str) -> str:
        """
        Sanitize the input text by replacing PII with placeholders.
        
        Args:
            text: Raw user input containing potential PII.
            
        Returns:
            Sanitized string safe for processing.
        """
        if not self.enabled or not text:
            return text

        original_text = text
        
        # Apply redactions sequentially
        # We use explicit tokens so the LLM understands context is preserved
        text = self._email_pattern.sub("[EMAIL]", text)
        text = self._phone_pattern.sub("[PHONE]", text)
        text = self._ip_pattern.sub("[IP_ADDRESS]", text)
        text = self._ssn_pattern.sub("[REDACTED_ID]", text)
        text = self._cc_pattern.sub("[CREDIT_CARD]", text)
        
        # Optional: Log if redaction occurred (for debugging/audit)
        if text != original_text:
            self.logger.debug("PII Detected and scrubbed from input.")
            
        return text

# Global Instance
scrubber = PIIScrubber()