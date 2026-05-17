"""
Utility functions for JSON extraction, price parsing, and text processing.
"""

import json
import re
from typing import Any, Optional


def extract_json(text: str) -> Optional[dict | list]:
    """
    Robustly extract JSON from a model response that may include
    markdown fences or surrounding prose.
    
    Args:
        text: The text potentially containing JSON
        
    Returns:
        Parsed JSON object/list or None if extraction fails
    """
    # Try to extract from markdown fences
    fenced = re.search(r"```(?:json)?\s*([\s\S]+?)```", text)
    if fenced:
        text = fenced.group(1)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find JSON by braces/brackets
    for start_char, end_char in [("{", "}"), ("[", "]")]:
        start = text.find(start_char)
        end = text.rfind(end_char)
        if start != -1 and end != -1:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                pass

    return None


def parse_price(text: str) -> float:
    """
    Extract price amount from text like '4999 kr', '3.200 kr', '3 200 kr', '900 SEK', etc.
    
    Args:
        text: The text containing price information
        
    Returns:
        The parsed price as a float, or 0.0 if no valid price found
    """
    if not text:
        return 0.0
    
    # Try to match pattern: digits (with optional separators) followed by kr/dkk/sek/eur
    match = re.search(r'(\d+[\.\s,]?)*\d+\s*(?:kr|dkk|sek|eur)?', text, re.IGNORECASE)
    if match:
        # Extract the matched number part
        price_str = match.group(0)
        # Remove currency designations and separators
        price_str = re.sub(r'[^\d\.\,]', '', price_str)
        # Handle both . and , as decimal separators
        price_str = price_str.replace(',', '.')
        
        # Handle thousand separators (remove them if multiple dots found)
        dots = price_str.count('.')
        if dots > 1:
            # Multiple dots = thousand separators, remove all
            price_str = price_str.replace('.', '')
        
        try:
            return float(price_str) if price_str else 0.0
        except ValueError:
            pass
    
    # Fallback: if no number found, try to extract all numbers and use the largest
    numbers = re.findall(r'\d+', text)
    if numbers:
        return float(max(numbers))
    
    return 0.0
