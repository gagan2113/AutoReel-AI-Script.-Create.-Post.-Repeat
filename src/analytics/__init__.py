"""Analytics package for platform engagement metrics."""

from .instagram_analytics import fetch_instagram_metrics
from .facebook_analytics import fetch_facebook_metrics
from .youtube_analytics import fetch_youtube_metrics
from .twitter_analytics import fetch_twitter_metrics

__all__ = [
    "fetch_instagram_metrics",
    "fetch_facebook_metrics",
    "fetch_youtube_metrics",
    "fetch_twitter_metrics",
]
