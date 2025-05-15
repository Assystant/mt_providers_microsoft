from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import requests
from mt_providers.base import BaseTranslationProvider
from mt_providers.exceptions import ConfigurationError
from mt_providers.types import TranslationConfig, TranslationResponse

logger = logging.getLogger(__name__)


class MicrosoftTranslator(BaseTranslationProvider):
    """Microsoft Translator API provider implementation."""

    name = "microsoft"
    requires_region = True
    supports_async = True
    max_chunk_size = 5000  # Microsoft's limit is 5000 characters per request
    max_array_size = 100  # Microsoft's limit is 100 texts per request
    min_supported_version = "0.1.0"

    def __init__(self, config: TranslationConfig) -> None:
        super().__init__(config)
        self.base_url = (
            config.endpoint or "https://api.cognitive.microsofttranslator.com/translate"
        )
        self._token: Optional[str] = None

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication."""
        if not self.config.region:
            raise ConfigurationError("Region is required for Microsoft Translator")

        return {
            "Ocp-Apim-Subscription-Key": self.config.api_key,
            "Ocp-Apim-Subscription-Region": self.config.region,
            "Content-Type": "application/json",
        }

    def translate(
        self, text: str, source_lang: str, target_lang: str
    ) -> TranslationResponse:
        """Translate a single text using Microsoft Translator."""
        try:
            params = {
                "api-version": "3.0",
                "from": source_lang,
                "to": target_lang,
            }

            payload = [{"text": text}]

            response = requests.post(
                self.base_url,
                headers=self._get_headers(),
                params=params,
                json=payload,
                timeout=self.config.timeout,
            )

            response.raise_for_status()
            translation_result = response.json()

            if not translation_result or not translation_result[0]["translations"]:
                raise ValueError("Empty translation response")

            translated_text = translation_result[0]["translations"][0]["text"]

            return self._create_response(
                translated_text=translated_text,
                source_lang=source_lang,
                target_lang=target_lang,
                char_count=len(text),
                metadata={
                    "detected_language": translation_result[0].get(
                        "detectedLanguage", {}
                    ),
                    "response": translation_result,
                },
            )

        except Exception as e:
            logger.error(f"Translation failed: {str(e)}")
            return self._create_response(
                translated_text="",
                source_lang=source_lang,
                target_lang=target_lang,
                char_count=len(text),
                error=str(e),
            )

    def bulk_translate(
        self, texts: List[str], source_lang: str, target_lang: str
    ) -> List[TranslationResponse]:
        """Translate multiple texts efficiently using Microsoft's batch API."""
        if not texts:
            return []

        results: List[TranslationResponse] = []
        current_batch: List[Dict[str, str]] = []
        current_batch_size = 0

        try:
            for text in texts:
                text_size = len(text)

                # Check if adding this text would exceed limits
                if (
                    len(current_batch) >= self.max_array_size
                    or current_batch_size + text_size > self.max_chunk_size
                ):
                    # Translate current batch
                    results.extend(
                        self._translate_batch(current_batch, source_lang, target_lang)
                    )
                    current_batch = []
                    current_batch_size = 0

                current_batch.append({"text": text})
                current_batch_size += text_size

            # Translate any remaining texts
            if current_batch:
                results.extend(
                    self._translate_batch(current_batch, source_lang, target_lang)
                )

            return results

        except Exception as e:
            logger.error(f"Batch translation failed: {str(e)}")
            # Return failed responses for all remaining texts
            return [
                self._create_response(
                    translated_text="",
                    source_lang=source_lang,
                    target_lang=target_lang,
                    char_count=len(text["text"]),
                    error=str(e),
                )
                for text in current_batch
            ]

    def _translate_batch(
        self, texts: List[Dict[str, str]], source_lang: str, target_lang: str
    ) -> List[TranslationResponse]:
        """Internal method to translate a batch of texts."""
        try:
            params = {
                "api-version": "3.0",
                "from": source_lang,
                "to": target_lang,
            }

            response = requests.post(
                self.base_url,
                headers=self._get_headers(),
                params=params,
                json=texts,
                timeout=self.config.timeout,
            )

            response.raise_for_status()
            translation_results = response.json()

            return [
                self._create_response(
                    translated_text=result["translations"][0]["text"],
                    source_lang=source_lang,
                    target_lang=target_lang,
                    char_count=len(texts[i]["text"]),
                    metadata={
                        "detected_language": result.get("detectedLanguage", {}),
                        "response": result,
                    },
                )
                for i, result in enumerate(translation_results)
            ]

        except Exception as e:
            logger.error(f"Batch request failed: {str(e)}")
            return [
                self._create_response(
                    translated_text="",
                    source_lang=source_lang,
                    target_lang=target_lang,
                    char_count=len(text["text"]),
                    error=str(e),
                )
                for text in texts
            ]
