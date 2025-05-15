# Microsoft Translator Provider

Microsoft Translator implementation for the MT Providers framework.

## Installation

```bash
pip install mt_provider_microsoft
```

## Configuration

```python
from mt_providers import get_provider
from mt_providers.types import TranslationConfig

config = TranslationConfig(
    api_key="your-subscription-key",
    region="your-region",  # e.g. "westus2"
    timeout=30,  # optional, defaults to 30 seconds
)

translator = get_provider("microsoft")(config)
```

## Usage

### Single Translation
```python
result = translator.translate("Hello world", "en", "es")
print(result.translated_text)  # "¡Hola mundo!"
```

### Batch Translation
```python
texts = ["Hello world", "How are you?"]
results = translator.bulk_translate(texts, "en", "es")
```

## Features
- ✅ Single text translation
- ✅ Batch translation (up to 100 texts per request)
- ✅ Automatic provider discovery
- ✅ Region support
- ✅ Error handling and retries
- ✅ Response metadata with detected language

## Limits
- Maximum 5000 characters per request
- Maximum 100 texts per batch request