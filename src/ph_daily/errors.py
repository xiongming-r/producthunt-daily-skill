from __future__ import annotations

from enum import IntEnum


class ExitCode(IntEnum):
    SUCCESS = 0
    CONFIG_ERROR = 1
    PRODUCT_HUNT_ERROR = 2
    LLM_ERROR = 3
    OUTPUT_ERROR = 4


class PhDailyError(Exception):
    exit_code = ExitCode.CONFIG_ERROR


class ConfigError(PhDailyError):
    exit_code = ExitCode.CONFIG_ERROR


class ProductHuntError(PhDailyError):
    exit_code = ExitCode.PRODUCT_HUNT_ERROR


class LlmError(PhDailyError):
    exit_code = ExitCode.LLM_ERROR


class OutputError(PhDailyError):
    exit_code = ExitCode.OUTPUT_ERROR
