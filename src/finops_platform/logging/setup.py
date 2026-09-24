import logging


def configure_logging(level: str = "INFO") -> None:
    """Configure conservative application logging without credential-bearing payloads."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
