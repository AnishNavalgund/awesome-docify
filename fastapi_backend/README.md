# Awesome Docify Backend

## File Structure
```bash
app/
├── main.py                 # FastAPI application entry point
├── docker                  # Docker configuration
├── start.sh                # Start script
├── config.py               # Configuration management
├── database.py             # Database connection and utilities
├── models.py               # SQLAlchemy ORM models
├── schemas.py              # Pydantic data models
├── utils.py                # Utility functions
├── tests/                  # Tests
├── testScripts/            # Test scripts for local testing while dev
├── watcher.py              # Watcher for file changes
├── commands/               # To generate openAPI schema
├── routes/                 # API route handlers
│   ├── query.py            # Query and save processing endpoints
│   └── debug.py            # Debug endpoints
├── ai_engine_service/      # AI and RAG functionality
│   ├── rag_engine.py       # Rag with hybrid retrieval
│   ├── intent.py           # Intent detection and analysis
│   └── prompts.py          # AI prompt templates
└── data_ingestion_service/ # Document processing
    └── ingest.py           # Document ingestion logic
```

## Tech Stack

- **FastAPI**: Web framework
- **SQLAlchemy**: Database operations
- **asyncpg**: Async PostgreSQL driver
- **Pydantic**: Data validation and structured data
- **OpenAI**: LLM and embedding model
- **Qdrant**: Vector database
- **LangChain**: RAG framework integration


## Startup Process

1. **Database Initialization**: Creates tables and clears existing data to start fresh
2. **Document Ingestion**: Loads JSON files from configured directory
3. **Chunking**: Splits documents into searchable chunks
4. **Vector Storage**: Stores embeddings in Qdrant
5. **PostgreSQL Storage**: Saves documents and chunks to database
6. **API Validation**: Verifies OpenAI API connectivity

Then the app is ready to be used.

## Query Processing Flow

1. **Query**: User provides a query to the AI assistant.
2. **Intent Extraction**: Determines user intent (ADD/DELETE/MODIFY)
3. **Hybrid Retrieval**: Combines keyword-based and semantic search
4. **Content Generation**: AI-powered document update suggestions
5. **Save Changes**: Save the changes to the documents
