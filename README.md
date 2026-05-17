# Second-Hand Product Research Agent

A powerful research assistant that scrapes, filters, and ranks second-hand product listings from multiple platforms using AI.

## Features

- **Multi-Platform Scraping**: Search DBA, Vinted, and Tradera simultaneously
- **AI-Powered Filtering**: Uses LLM to identify relevant listings based on your query
- **Intelligent Scoring**: Ranks results by relevance using AI analysis
- **Review Summarization**: Extracts and summarizes product reviews
- **Currency Conversion**: Automatic conversion between EUR, DKK, and SEK
- **Model Extraction**: Identifies product models from listing titles and descriptions
- **Flexible Configuration**: Skip any AI step for faster, simpler searches

## Platforms Supported

| Platform | Region | Status |
|----------|--------|--------|
| DBA | Denmark | ✅ Active |
| Vinted | Europe | ✅ Active |
| Tradera | Sweden | ✅ Active |

## Requirements

- Python 3.10+
- Required packages: `httpx`, `beautifulsoup4`, `rich`, `python-dotenv`, `requests`

## Installation

```bash
# Clone the repository
git clone https://github.com/pbozhok/second_hand_searcher.git
cd second_hand_searcher

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install httpx beautifulsoup4 rich python-dotenv requests
```

## API Keys

Create a `.env` file in the project root with your API keys:

```bash
# For Google Gemini (default LLM)
GOOGLE_API_KEY=your_gemini_api_key_here
# or
GEMINI_API_KEY=your_gemini_api_key_here

# For Mistral AI (alternative LLM)
MISTRAL_API_KEY=your_mistral_api_key_here

# Optional: For better review extraction via SerpAPI
SERPAPI_KEY=your_serpapi_key_here
```

> **Note**: Without SERPAPI_KEY, the agent falls back to free DuckDuckGo scraping for reviews.

## Usage

### Basic Search

```bash
# Default: uses Gemini LLM
python second_hand_research.py "iPhone 13 Pro"

# With Mistral LLM
python second_hand_research.py "Sony WH-1000XM5" --llm mistral

# Enable debug logging
python second_hand_research.py "MacBook Pro M2" --debug
```

### Advanced Options

| Option | Description | Default |
|--------|-------------|---------|
| `--llm` | LLM backend: `gemini` or `mistral` | `gemini` |
| `--currency` | Target currency: `EUR`, `DKK`, `SEK` | `EUR` |
| `--no-reviews` | Skip review extraction and summarization | Enabled |
| `--no-filter` | Skip LLM-based filtering (uses keyword matching) | Enabled |
| `--no-score` | Skip LLM-based scoring (sorts by price) | Enabled |
| `--debug` | Enable verbose debug logging | Disabled |

### Examples

```bash
# Fast search without AI processing
python second_hand_research.py "Nikon Z6" --no-filter --no-score --no-reviews

# Full AI-powered research with Mistral
python second_hand_research.py "Dyson V15" --llm mistral --currency DKK --debug

# Search in Swedish Krona
python second_hand_research.py "Samsung Galaxy S23" --currency SEK
```

## Project Structure

```
second_hand_searcher/
├── second_hand_research.py    # Main entry point
├── config.py                  # Configuration and constants
├── models.py                  # Data models (Listing, etc.)
├── output.py                  # Result formatting and display
├── ranker.py                  # LLM-based ranking logic
├── utils.py                   # Utility functions
├── agents/                    # Agent implementations
├── scrapers/                  # Platform scrapers
│   ├── base.py                # Base scraper class
│   ├── dba.py                 # DBA.dk scraper
│   ├── vinted.py              # Vinted scraper
│   └── tradera.py             # Tradera scraper
├── filters/                   # Filtering modules
│   ├── keyword_filter.py      # Keyword-based filtering
│   └── llm_filter.py          # LLM-based filtering
├── processors/                # Data processors
│   ├── description_fetcher.py # Fetches full descriptions
│   ├── price_converter.py     # Currency conversion
│   └── model_extractor.py     # Extracts product models
├── reviewers/                 # Review modules
│   ├── search.py              # Review search
│   └── summarizer.py          # Review summarization
└── tests/                     # Test suite
```

## How It Works

1. **Scraping**: Simultaneously searches all configured platforms for listings matching your query
2. **Deduplication**: Removes duplicate listings (same product across platforms)
3. **Filtering**: Uses LLM to determine which listings are relevant to your query
4. **Model Extraction**: Identifies exact product models from titles/descriptions
5. **Scoring**: LLM evaluates and scores each listing's quality and relevance
6. **Review Summarization**: Fetches and summarizes user reviews for top results
7. **Ranking**: Sorts all results by score and presents them in a formatted table

## Configuration

Edit `config.py` to customize:

```python
# Scraper settings
SCRAPER_TIMEOUT = 20          # Request timeout in seconds
MAX_RETRIES = 5               # Max retry attempts
BATCH_SIZE = 20               # LLM processing batch size
DEFAULT_MAX_RESULTS = 40      # Max results per platform

# Currency exchange rates
EXCHANGE_RATES = {
    "EUR": 1.0,
    "DKK": 7.45,
    "SEK": 11.20,
}

# Review settings
MAX_REVIEW_RESULTS = 3       # Max reviews to fetch
REVIEW_DELAY = 4.0           # Delay between review searches
```

## Output

Results are displayed in a rich terminal table with the following columns:

- **Relevant**: Whether the listing matches your query (AI-determined)
- **Title**: Listing title
- **Price**: Price in your selected currency
- **Platform**: Source platform (DBA/Vinted/Tradera)
- **Model**: Extracted product model
- **Score**: AI-generated quality score (0-100)
- **URL**: Direct link to the listing

## Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_scrapers.py

# Run with verbose output
pytest -v
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_API_KEY` or `GEMINI_API_KEY` | Yes (for Gemini) | Google Gemini API key |
| `MISTRAL_API_KEY` | Yes (for Mistral) | Mistral API key |
| `SERPAPI_KEY` | No | Optional SerpAPI key for better reviews |

## Tips

1. **Start simple**: Use `--no-filter --no-score --no-reviews` for quick tests
2. **Batch processing**: For many queries, consider adding delays between requests
3. **API limits**: Be aware of your LLM provider's rate limits
4. **Currency**: Prices are converted using approximate exchange rates

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is open source and available under the MIT License.

## Acknowledgments

- Built with [Gemini](https://ai.google.dev/) and [Mistral AI](https://mistral.ai/)
- Uses [Rich](https://github.com/Textualize/rich) for beautiful terminal output
- Scraping powered by [httpx](https://www.python-httpx.org/) and [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/)
