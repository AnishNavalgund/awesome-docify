# API Documentation - Endpoints

### GET `/health`
Health check endpoint.

### GET `/`
Root endpoint - welcome message.

### POST `/api/v1/query`
Submit a query to the AI assistant.

### POST `/api/v1/save-change`
Save a change to a document.

### GET `/api/v1/debug/json-files`
List all available JSON document files.

### GET `/api/v1/debug/json-files/{filename}`
Get the content of a specific JSON file.

### GET `/api/v1/debug/qdrant-status`
Get the status of the Qdrant vector database.

### GET `/api/v1/collection-info`
Get information about the document collection.
