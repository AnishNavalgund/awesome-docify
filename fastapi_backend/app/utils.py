import logging

from fastapi.routing import APIRoute

# Configure logging to output to console
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Create and configure loggers
logger_info = logging.getLogger("info")
logger_error = logging.getLogger("error")

# Set log levels
logger_info.setLevel(logging.INFO)
logger_error.setLevel(logging.ERROR)

# Create console handlers
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)

# Add handlers to loggers
logger_info.addHandler(console_handler)
logger_error.addHandler(console_handler)


def simple_generate_unique_route_id(route: APIRoute):
    # Handle routes without tags
    tag = route.tags[0] if route.tags else "default"
    return f"{tag}-{route.name}"
