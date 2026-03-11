"""
Feature flag service for managing feature toggles.
"""

from app.config import settings


class FeatureFlagService:
    """
    Service for checking feature flag states.

    Provides centralized feature flag management with environment-based defaults
    and runtime checks.
    """

    def __init__(self, flags: dict[str, bool] | None = None):
        """
        Initialize feature flag service.

        Args:
            flags: Optional dict of feature flags. If None, uses settings.feature_flags.
        """
        self._flags = flags or getattr(settings, "feature_flags", {})

    def is_enabled(self, name: str) -> bool:
        """
        Check if a feature flag is enabled.

        Args:
            name: Feature flag name

        Returns:
            True if feature is enabled, False otherwise.
            Returns False if flag is not defined (safe default).
        """
        return self._flags.get(name, False)

    def is_disabled(self, name: str) -> bool:
        """
        Check if a feature flag is disabled.

        Args:
            name: Feature flag name

        Returns:
            True if feature is disabled or not defined.
        """
        return not self.is_enabled(name)


_feature_flag_service: FeatureFlagService | None = None


def get_feature_flag_service() -> FeatureFlagService:
    """
    Returns singleton FeatureFlagService instance.
    """
    global _feature_flag_service
    if _feature_flag_service is None:
        _feature_flag_service = FeatureFlagService()
    return _feature_flag_service
