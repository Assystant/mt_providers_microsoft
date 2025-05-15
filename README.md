# Microsoft Translator Provider

Microsoft Azure Translator integration for the MT Providers framework.

## Installation

```bash
pip install mt_provider_microsoft
```

## Features
- ✅ Single and batch translations
- ✅ Async support
- ✅ Rate limiting
- ✅ Automatic retries
- ✅ Error handling
- ✅ Region support
- ✅ Response metadata with detected language

## Quick Start

```python
from mt_providers import get_provider
from mt_providers.types import TranslationConfig

# Initialize provider
config = TranslationConfig(
    api_key="your-key",
    region="your-region",  # e.g., "westus2"
    rate_limit=10  # Optional: requests per second
)

translator = get_provider("microsoft")(config)

# Single translation
result = translator.translate("Hello world", "en", "es")
print(result.translated_text)  # "¡Hola mundo!"

# Batch translation
texts = ["Hello", "World"]
results = translator.bulk_translate(texts, "en", "es")

# Async translation
async def translate():
    result = await translator.translate_async("Hello", "en", "es")
    print(result.translated_text)
```

## Configuration Options

| Option | Required | Description |
|--------|----------|-------------|
| api_key | Yes | Azure Translator subscription key |
| region | Yes | Azure region (e.g., "westus2") |
| rate_limit | No | Maximum requests per second |
| timeout | No | Request timeout in seconds |
| endpoint | No | Custom API endpoint |

## Limits
- Maximum 5000 characters per request
- Maximum 100 texts per batch request