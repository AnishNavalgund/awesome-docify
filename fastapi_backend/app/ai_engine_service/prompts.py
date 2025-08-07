"""
Prompts for the Document Update RAG Pipeline
"""

from langchain.prompts import ChatPromptTemplate

# RAG Document Update Prompt - Natural responses only
RAG_DOCUMENT_UPDATE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are an intelligent documentation assistant. Analyze the context and user query to provide precise document updates.

Provide ONLY the updated content that should replace the existing documentation. Do not include "Before Update" or "After Update" sections. Just provide the final, updated content that users should see.

Focus on understanding the user's intent and providing relevant, actionable updates.""",
        ),
        (
            "human",
            """Context: {context}
Question: {question}

Provide the updated content for the documentation.""",
        ),
    ]
)
