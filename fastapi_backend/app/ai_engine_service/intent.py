"""
Intent extraction and processing for different types of operations (modify, delete, add)
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from app.schemas import Intent, DocumentUpdate, ContentChange
from app.config import settings
from app.utils import logger_info
from .prompts import INTENT_EXTRACTION_PROMPT, UNIFIED_CONTENT_PROMPT
from langchain_core.exceptions import OutputParserException


# Initialize LLM for intent extraction
llm = ChatOpenAI(
    model="gpt-4o",  
    temperature=0.3,
    openai_api_key=settings.OPENAI_API_KEY
)

# Define the parser for Pydantic Intent
parser = PydanticOutputParser(pydantic_object=Intent)

# Define the parser for Content Change
content_change_parser = PydanticOutputParser(pydantic_object=ContentChange)


async def extract_intent(user_query: str) -> Intent:
    """
    Extract a structured Intent object from the user query using LangChain + OpenAI + Pydantic.
    """
    formatted_prompt = INTENT_EXTRACTION_PROMPT.format_messages(
        query=user_query,
        format_instructions=parser.get_format_instructions()
    )

    try:
        response = await llm.ainvoke(formatted_prompt)
        logger_info.info(f"LLM Call successful")
        return parser.parse(response.content)
    except Exception as e:
        # Check if it's an API key error
        if "invalid_api_key" in str(e).lower() or "401" in str(e):
            raise ValueError(f"OpenAI API key error: Please check your API key configuration. Error: {e}")
        else:
            raise ValueError(f"Failed to extract intent: {e}")


class BaseIntentHandler(ABC):
    """Base class for intent handlers"""
    
    def __init__(self, llm_model):
        self.llm_model = llm_model
    
    @abstractmethod
    async def process_intent(self, intent: Intent, query: str, content_extracts: List[Dict[str, Any]]) -> List[DocumentUpdate]:
        """Process the intent and return document updates"""
        pass
    
    def _get_document_name(self, change: Dict[str, Any]) -> str:
        """Extract meaningful document name from change data"""
        doc_name = None
        
        # First try title
        if change.get("title") and change["title"].strip():
            doc_name = change["title"].strip()
        # Then try URL
        elif change.get("url") and change["url"].strip():
            doc_name = change["url"].strip()
        # Then try source_url
        elif change.get("source_url") and change["source_url"].strip():
            doc_name = change["source_url"].strip()
        
        # Clean up the document name
        if doc_name and '_chunk_' in doc_name:
            doc_name = doc_name.split('_chunk_')[0]
        
        # If still no meaningful name, use a fallback
        if not doc_name or doc_name == "unknown_doc" or doc_name == "":
            doc_name = f"Document"
        
        return doc_name


class UnifiedIntentHandler(BaseIntentHandler):
    """Handler for all intent types (add, delete, modify)"""
    
    async def process_intent(self, intent: Intent, query: str, content_extracts: List[Dict[str, Any]]) -> List[DocumentUpdate]:
        """Process any intent and return document updates"""
        documents_to_update = []
        
        # Limit the number of documents to process to prevent timeout
        max_documents = 5
        content_extracts = content_extracts[:max_documents]
        
        for extract in content_extracts:
            try:
                # Create a prompt for the LLM to generate changes
                formatted_prompt = UNIFIED_CONTENT_PROMPT.format_messages(
                    query=query,
                    keyword=intent.target,
                    content=extract['content']
                )
                
                response = await self.llm_model.ainvoke(formatted_prompt)
                
                # Use LangChain's structured output parsing
                try:
                    change_data = content_change_parser.parse(response.content)
                    
                    doc_name = self._get_document_name(extract)
                    
                    documents_to_update.append(DocumentUpdate(
                        file=doc_name,
                        action=intent.action,
                        reason=f"{intent.action.capitalize()} {intent.target} based on user query",
                        section=intent.object_type or "Content",
                        original_content=change_data.original_content,
                        new_content=change_data.new_content
                    ))
                        
                except OutputParserException as e:
                    # Fallback if parsing fails
                    doc_name = self._get_document_name(extract)
                    documents_to_update.append(DocumentUpdate(
                        file=doc_name,
                        action=intent.action,
                        reason=f"{intent.action.capitalize()} {intent.target} based on user query (fallback)",
                        section=intent.object_type or "Content",
                        original_content=extract["content"],
                        new_content=extract["content"],
                    ))
                    
            except Exception as e:
                print(f"Error generating changes for document {extract.get('document_id', 'unknown')}: {e}")
                # Fallback change
                doc_name = self._get_document_name(extract)
                documents_to_update.append(DocumentUpdate(
                    file=doc_name,
                    action=intent.action,
                    reason=f"Error generating changes: {str(e)}",
                    section=intent.object_type or "Content",
                    original_content=extract["content"],
                    new_content=extract["content"]
                ))
        
        return documents_to_update


class IntentHandlerFactory:
    """Factory to create appropriate intent handlers"""
    
    @staticmethod
    def create_handler(intent: Intent, llm_model) -> BaseIntentHandler:
        """Create the unified handler for all operations"""
        return UnifiedIntentHandler(llm_model)
