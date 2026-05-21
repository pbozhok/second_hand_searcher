"""
Reviewers module - review search and summarization.

This module provides review aggregation functionality for the second-hand research agent.
All reviewers inherit from BaseReviewer which implements the Module interface.

Available reviewers:
- ReviewSearcher: Searches for product reviews from various sources (DuckDuckGo, SerpAPI)
- ReviewSummarizer: Summarizes reviews using LLM

Usage:
    from reviewers import ReviewSearcher, ReviewSummarizer
    
    searcher = ReviewSearcher()
    reviews = await searcher.search_duckduckgo("iPhone 15", max_results=3)
"""

from .base import BaseReviewer
from .search import ReviewSearcher
from .summarizer import ReviewSummarizer

__all__ = ["BaseReviewer", "ReviewSearcher", "ReviewSummarizer"]
