"""
Prompts for the Document Update RAG Pipeline
"""
from langchain.prompts import ChatPromptTemplate

# System Prompt
SYSTEM_PROMPT = """
You are an expert in documentation review and update.

Your task is to:
1. Determine whether the provided documentation content should be modified, removed, or left unchanged based on a user's update request.
2. Suggest precise and relevant edits (if any).

Only propose updates that are directly related to the user's request.

Return your output as a JSON object containing:
- "analysis": A short explanation of what needs to change (if anything).
- "documents_to_update": A list detailing the documents that need changes, with fields:
  - "file name"
  - "action" (modified / removed / unchanged / new)
  - "section" (if identifiable)
"""



# Intent Extraction Prompt
INTENT_EXTRACTION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "Extract a structured developer intent from the query below."),
    ("human", "{query}\n\n{format_instructions}")
])

# Content Change Generation Prompt Template
CONTENT_CHANGE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", """Based on the user query: "{query}"

The user wants to change the keyword "{keyword}" in the following content:

{content}

Please provide:
1. The original content (as is)
2. The suggested new content with the appropriate changes

Format your response as JSON:
{{
    "original_content": "the original content",
    "new_content": "the new content with changes"
}}""")
])

