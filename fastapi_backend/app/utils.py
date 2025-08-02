import logging
from fastapi.routing import APIRoute

# Configure logging to output to console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Use root logger for simplicity
logger_info = logging.getLogger()
logger_error = logging.getLogger()

def simple_generate_unique_route_id(route: APIRoute):
    # Handle routes without tags
    tag = route.tags[0] if route.tags else "default"
    return f"{tag}-{route.name}"



