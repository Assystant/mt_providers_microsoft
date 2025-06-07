from __future__ import annotations

import asyncio
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
    min_supported_version = "0.1.4"

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
    
    def _get_params(self, source_lang: str, target_lang: str) -> Dict[str, Any]:
        """Get request parameters for translation."""
        return {
            "api-version": "3.0",
            "from": source_lang,
            "to": target_lang,
        }

    def translate(
        self, text: str, source_lang: str, target_lang: str
    ) -> TranslationResponse:
        """Translate single text using Microsoft Translator."""
        # Use the batch method for a single text
        result_list = self._translate_via_microsoft([{"text": text}], source_lang, target_lang)
        return result_list[0] if result_list else self._create_response(
            translated_text="",
            source_lang=source_lang,
            target_lang=target_lang,
            char_count=len(text),
            error="No response from Microsoft Translator",
        )

    def bulk_translate(
        self, texts: List[str], source_lang: str, target_lang: str
    ) -> List[TranslationResponse]:
        return self._translate_via_microsoft(
            [{"text": text} for text in texts], source_lang, target_lang
        )

    def _translate_via_microsoft(
        self, texts: List[Dict[str, str]], source_lang: str, target_lang: str
    ) -> List[TranslationResponse]:
        """Internal method to translate a batch of texts."""
        try:

            response = requests.post(
                self.base_url,
                headers=self._get_headers(),
                params=self._get_params(source_lang, target_lang),
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
