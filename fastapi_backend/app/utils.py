import logging
from fastapi.routing import APIRoute

logger_info = logging.getLogger(__name__)
logger_info.setLevel(logging.INFO)
logger_error = logging.getLogger(__name__)
logger_error.setLevel(logging.ERROR)

def simple_generate_unique_route_id(route: APIRoute):
    # Handle routes without tags
    tag = route.tags[0] if route.tags else "default"
    return f"{tag}-{route.name}"



