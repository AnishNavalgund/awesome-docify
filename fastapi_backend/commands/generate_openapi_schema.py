import json
from pathlib import Path
from app.main import app
import os

from dotenv import load_dotenv

load_dotenv()

OUTPUT_FILE = os.getenv("OPENAPI_OUTPUT_FILE", "openapi.json")


def generate_openapi_schema(output_file):
    schema = app.openapi()
    output_path = Path(output_file)

    updated_schema = remove_operation_id_tag(schema)

    output_path.write_text(json.dumps(updated_schema, indent=2))
    print(f"OpenAPI schema saved to {output_file}")


def remove_operation_id_tag(schema):
    """
    Removes the tag prefix from the operation IDs in the OpenAPI schema.

    This cleans up the OpenAPI operation IDs that are used by the frontend
    client generator to create the names of the functions. The modified
    schema is then returned.
    """
    for path_data in schema["paths"].values():
        for operation in path_data.values():
            # Skip if operation doesn't have tags or operationId
            if "tags" not in operation or "operationId" not in operation:
                continue

            tag = operation["tags"][0] if operation["tags"] else "default"
            operation_id = operation["operationId"]
            to_remove = f"{tag}-"

            # Only remove prefix if it exists
            if operation_id.startswith(to_remove):
                new_operation_id = operation_id[len(to_remove) :]
                operation["operationId"] = new_operation_id
    return schema


if __name__ == "__main__":
    generate_openapi_schema(OUTPUT_FILE)
