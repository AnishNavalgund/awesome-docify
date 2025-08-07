"""
Prompts for the Document Update RAG Pipeline
"""

from langchain.prompts import ChatPromptTemplate

# Intent Extraction Prompt
INTENT_EXTRACTION_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Analyze the user's query and extract the intent: ADD/DELETE/MODIFY and target.",
        ),
        ("human", "{query}\n\n{format_instructions}"),
    ]
)

# Unified Content Change Generation Prompt Template
UNIFIED_CONTENT_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a precise and reliable documentation editor assistant. Based on the user's query and the given content, perform one of the following operations:

            1. **ADD** – Insert the provided information at the most contextually appropriate location within the content.
            2. **DELETE** – Remove any references to the target keyword and related lines or sections.
            3. **MODIFY** – Revise or update the relevant part of the content based on the query.

            For ADD operations: If the target doesn't exist, add it in an appropriate section. Create new sections if needed.
            - Do not hallucinate or invent content beyond what the query and keyword imply.
            - Only suggest changes that improve the documentation based on the user's request.
            - Preserve formatting and indentation wherever possible.

            Return your result strictly in JSON format with the following fields:
            - `"original_content"`: The unchanged content segment.
            - `"new_content"`: The updated version of the content after the operation.""",
        ),
        (
            "human",
            """User Query: "{query}"
                Target Keyword: "{keyword}"
                Content: {content}

            Now return only the JSON output as described above.""",
        ),
    ]
)
