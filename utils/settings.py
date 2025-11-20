"""Centralised configuration helpers sourced from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class ProviderSettings:
    """API credentials for external LLM providers."""

    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    mistral_api_token: Optional[str] = os.getenv("MISTRAL_API_TOKEN")
    huggingface_api_token: Optional[str] = os.getenv("HF_API_TOKEN")
    openrouter_api_key: Optional[str] = os.getenv("OPENROUTER_API_KEY")
    openrouter_base_url: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    openrouter_site_url: Optional[str] = os.getenv("OPENROUTER_SITE_URL")
    openrouter_app_name: Optional[str] = os.getenv("OPENROUTER_APP_NAME")


@dataclass(frozen=True)
class ModelSettings:
    """Model choices for primary reasoning and visual agents."""

    primary_model_name: str = os.getenv("PRIMARY_MODEL_NAME", "mistral-7b")
    legacy_visual_model_name: Optional[str] = os.getenv("VISUAL_MODEL_NAME")
    visual_caption_model: str = os.getenv("VISUAL_CAPTION_MODEL") or os.getenv("VISUAL_MODEL_NAME", "blip-2")
    visual_caption_model_path: Optional[str] = os.getenv("VISUAL_CAPTION_MODEL_PATH")
    visual_ocr_engine: str = os.getenv("VISUAL_OCR_ENGINE", "PaddleOCR")
    visual_ocr_model_dir: Optional[str] = os.getenv("VISUAL_OCR_MODEL_DIR")


@dataclass(frozen=True)
class RuntimeSettings:
    """Miscellaneous runtime parameters for reproducibility."""

    data_dir: str = os.getenv("DATA_DIR", "./data")
    model_cache: str = os.getenv("MODEL_CACHE", "./models")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")


provider_settings = ProviderSettings()
model_settings = ModelSettings()
runtime_settings = RuntimeSettings()


def get_primary_model(override: Optional[str] = None) -> str:
    """Return the requested primary LLM name."""

    return override or model_settings.primary_model_name


def get_visual_model(override: Optional[str] = None) -> str:
    """Return the requested visual model name."""

    return (
        override
        or model_settings.visual_caption_model
        or model_settings.legacy_visual_model_name
        or model_settings.primary_model_name
    )


def get_visual_caption_model(override: Optional[str] = None) -> str:
    """Return the configured visual captioning model identifier."""

    return override or model_settings.visual_caption_model


def get_visual_caption_model_path() -> Optional[str]:
    """Return the on-disk path to the captioning model if specified."""

    return model_settings.visual_caption_model_path


def get_visual_ocr_engine(override: Optional[str] = None) -> str:
    """Return the OCR engine identifier."""

    return override or model_settings.visual_ocr_engine


def get_visual_ocr_model_dir() -> Optional[str]:
    """Return the OCR model directory if present."""

    return model_settings.visual_ocr_model_dir
