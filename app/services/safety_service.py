"""
Safety service for content filtering.

Handles safety checks and content filtering for generated images.
"""

from typing import Optional, Any

from app.safety import is_blocked, is_blocked_forced


class SafetyService:
    """Service for handling safety and content filtering."""
    
    def check_content_safety(
        self, 
        prompt: str, 
        negative_prompt: Optional[str] = None,
        user: Optional[Any] = None
    ) -> tuple[bool, str]:
        """
        Check if content is safe for generation.
        
        Args:
            prompt: Main generation prompt
            negative_prompt: Optional negative prompt
            user: Optional authenticated user
            
        Returns:
            Tuple of (is_safe, reason)
        """
        from app.config import settings
        
        # Determine if NSFW is allowed
        allow_global = settings.nsfw_allow
        allow_user = True
        
        if user is not None and hasattr(user, "nsfw_allow"):
            allow_user = bool(user.nsfw_allow)
        
        # Apply safety checks based on global and user settings
        if not allow_global:
            # Global ban: forced blocklist applies to everyone
            if is_blocked_forced(prompt):
                return False, "Blocked by global safety policy"
        else:
            # Global allow: apply blocklist only to users with NSFW disabled
            if not allow_user and is_blocked_forced(prompt):
                return False, "Blocked by user safety policy"
        
        # Check regular blocklist for both prompts
        if is_blocked(prompt):
            return False, "Main prompt blocked by safety rules"
        
        if negative_prompt and is_blocked(negative_prompt):
            return False, "Negative prompt blocked by safety rules"
        
        return True, "Content is safe"
    
    def log_safety_violation(
        self, 
        prompt: str, 
        negative_prompt: Optional[str], 
        reason: str
    ) -> None:
        """
        Log a safety violation.
        
        Args:
            prompt: Main generation prompt
            negative_prompt: Optional negative prompt
            reason: Reason for the violation
        """
        from app.logging_setup import lg
        from app.utils import prompt_hash
        
        lg("error").bind(
            scope="safety",
            prompt_hash=prompt_hash(prompt, negative_prompt),
            reason=reason,
        ).error("safety.blocked")
