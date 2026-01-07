import json
import logging
import logging.config
import os

from src.config import BASE_DIR


def get_logging_config() -> dict:
    with open(BASE_DIR / "logging_config.json", "r") as f:
        config = json.load(f)
    os.makedirs(BASE_DIR / "logs", exist_ok=True)
    return config


def configurate_logging() -> None:
    config = get_logging_config()
    logging.config.dictConfig(config)


def get_logger(root_logger_name: str) -> logging.Logger:
    return logging.getLogger(root_logger_name)
