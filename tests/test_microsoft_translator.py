from typing import Any

import pytest
from mt_providers.exceptions import ConfigurationError
from mt_providers.types import TranslationConfig, TranslationStatus

from mt_provider_microsoft import MicrosoftTranslator


@pytest.fixture
def translator() -> MicrosoftTranslator:
    config = TranslationConfig(api_key="test-key", region="test-region")
    return MicrosoftTranslator(config)


def test_bulk_translate(translator: MicrosoftTranslator, requests_mock: Any) -> None:
    # Mock the Microsoft Translator API response
    mock_response = [
        {
            "translations": [{"text": "¡Hola mundo!"}],
            "detectedLanguage": {"language": "en", "score": 1.0},
        },
        {
            "translations": [{"text": "¿Cómo estás?"}],
            "detectedLanguage": {"language": "en", "score": 1.0},
        },
    ]

    requests_mock.post(
        "https://api.cognitive.microsofttranslator.com/translate", json=mock_response
    )

    texts = ["Hello world", "How are you?"]
    results = translator.bulk_translate(texts, "en", "es")

    assert len(results) == 2
    assert results[0]["translated_text"] == "¡Hola mundo!"
    assert results[1]["translated_text"] == "¿Cómo estás?"
    assert all(r["status"] == TranslationStatus.SUCCESS for r in results)


def test_missing_region_raises_error() -> None:
    config = TranslationConfig(api_key="test-key")
    translator = MicrosoftTranslator(config)

    with pytest.raises(ConfigurationError):
        translator.translate("test", "en", "es")


def test_translation_with_error(
    translator: MicrosoftTranslator, requests_mock: Any
) -> None:
    requests_mock.post(
        "https://api.cognitive.microsofttranslator.com/translate", status_code=500
    )

    result = translator.translate("test", "en", "es")
    assert result.status == TranslationStatus.ERROR
    assert result.error is not None


def test_batch_translation_limits(
    translator: MicrosoftTranslator, requests_mock: Any
) -> None:
    # Test handling of batch size limits
    texts = ["text"] * 150  # Exceeds max_array_size

    mock_response = [
        {
            "translations": [{"text": f"translated_{i}"}],
            "detectedLanguage": {"language": "en", "score": 1.0},
        }
        for i in range(100)
    ]

    requests_mock.post(
        "https://api.cognitive.microsofttranslator.com/translate", json=mock_response
    )

    results = translator.bulk_translate(texts, "en", "es")
    assert len(results) == 150
