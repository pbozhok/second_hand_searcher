"""
Processors module - pipeline stage implementations.

This module provides data processing functionality for the second-hand research agent.
All processors inherit from BaseProcessor which implements the Module interface.

Available processors:
- PriceConverter: Converts listing prices between currencies (EUR, DKK, SEK)
- ModelExtractor: Extracts product model names from listing titles using LLM
- DescriptionFetcher: Fetches full descriptions from product pages
- QueryPreprocessor: Pre-processes and expands search queries

Usage:
    from processors import PriceConverter, ModelExtractor, DescriptionFetcher
    
    processor = PriceConverter(debug=True)
    processed_listings = await processor.process(listings, config)
"""

from .base import BaseProcessor
from .price_converter import PriceConverter
from .model_extractor import ModelExtractor
from .description_fetcher import DescriptionFetcher
from .query_preprocessor import QueryPreprocessor, preprocess_query

# Auto-register processors with the global registry
from core.registry import registry

# Create instances and register (only those that inherit from BaseProcessor)
try:
    if issubclass(PriceConverter, BaseProcessor):
        registry.register(PriceConverter(debug=False))
except:
    pass

try:
    if issubclass(ModelExtractor, BaseProcessor):
        registry.register(ModelExtractor())
except:
    pass

try:
    if issubclass(DescriptionFetcher, BaseProcessor):
        registry.register(DescriptionFetcher())
except:
    pass

__all__ = [
    "BaseProcessor",
    "PriceConverter", 
    "ModelExtractor", 
    "DescriptionFetcher", 
    "QueryPreprocessor", 
    "preprocess_query"
]
