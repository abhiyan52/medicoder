import logging
import sys

import structlog


def setup_logging(is_dev_mode: bool = True):
    """
    Configure standard library logging and structlog.
    """
    # 1. Configure standard logging to route to structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )

    # 2. Decide on the renderer (Console view for dev, JSON for prod)
    if is_dev_mode:
        renderer = structlog.dev.ConsoleRenderer(colors=True)
    else:
        renderer = structlog.processors.JSONRenderer()

    # 3. Configure structlog processors
    structlog.configure(
        processors=[
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            renderer,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


# Run the setup once when the module is imported
setup_logging()

# Export a configured logger instance to be used across the app
logger = structlog.get_logger()
