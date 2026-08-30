"""Learning evidence, mastery estimation, and curriculum recommendations."""

from backend.learning.service import (
    build_learning_profile,
    get_recommendations,
    submit_learning_event,
)

__all__ = ["build_learning_profile", "get_recommendations", "submit_learning_event"]
