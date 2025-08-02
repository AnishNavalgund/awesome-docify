from abc import ABC, abstractmethod
from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from langchain_core.exceptions import OutputParserException
from langchain_core.documents import Document

from app.schemas import Intent, DocumentUpdate, ContentChange
from app.config import settings
from app.utils import logger_info
from .prompts import INTENT_EXTRACTION_PROMPT, UNIFIED_CONTENT_PROMPT

# Initialize shared LLM and parsers
llm = ChatOpenAI(model=settings.LLM_MODEL, temperature=settings.LLM_TEMPERATURE, openai_api_key=settings.OPENAI_API_KEY)    
intent_parser = PydanticOutputParser(pydantic_object=Intent)
content_parser = PydanticOutputParser(pydantic_object=ContentChange)


async def extract_intent(query: str) -> Intent:
    prompt = INTENT_EXTRACTION_PROMPT.format_messages(
        query=query, format_instructions=intent_parser.get_format_instructions()
    )
    try:
        response = await llm.ainvoke(prompt)
        logger_info.info("LLM Call successful")
        return intent_parser.parse(response.content)
    except Exception as e:
        if "invalid_api_key" in str(e).lower() or "401" in str(e):
            raise ValueError(f"Invalid OpenAI API key: {e}")
        raise ValueError(f"Intent extraction failed: {e}")


class BaseIntentHandler(ABC):
    """Base class for intent handlers"""
    
    def __init__(self, llm_model):
        self.llm_model = llm_model
    
    @abstractmethod
    async def process_intent(self, intent: Intent, query: str, content_extracts: List[Document]) -> List[DocumentUpdate]:
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
    
    async def process_intent(self, intent: Intent, query: str, content_extracts: List[Document]) -> List[DocumentUpdate]:
        """Process any intent and return document updates"""
        documents_to_update = []
        
        if not content_extracts:
            return []
        
        # Combine all documents into one context for single LLM call
        combined_context = "\n\n--- DOCUMENT SEPARATOR ---\n\n".join([
            f"Document: {self._get_document_name(doc.metadata)}\nContent: {doc.page_content}"
            for doc in content_extracts
        ])
        
        try:
            formatted_prompt = UNIFIED_CONTENT_PROMPT.format_messages(
                query=query,
                keyword=intent.target,
                content=combined_context
            )
            
            response = await self.llm_model.ainvoke(formatted_prompt)
            
            # Print response for DELETE operations
            if intent.action == "delete":
                print(f"DELETE operation - LLM response: {response.content}")
            
            # Parse the response and create updates for all documents
            try:
                change_data = content_parser.parse(response.content)
                
                # Create one update per document with the same response
                for doc in content_extracts:
                    doc_name = self._get_document_name(doc.metadata)
                    documents_to_update.append(DocumentUpdate(
                        file=doc_name,
                        action=intent.action,
                        reason=f"{intent.action.capitalize()} {intent.target} based on user query",
                        section=intent.object_type or "Content",
                        original_content=change_data.original_content,
                        new_content=change_data.new_content
                    ))
                
                return documents_to_update
                        
            except OutputParserException as e:
                # Fallback if parsing fails - create updates with original content
                for doc in content_extracts:
                    doc_name = self._get_document_name(doc.metadata)
                    documents_to_update.append(DocumentUpdate(
                        file=doc_name,
                        action=intent.action,
                        reason=f"{intent.action.capitalize()} {intent.target} based on user query (fallback)",
                        section=intent.object_type or "Content",
                        original_content=doc.page_content,
                        new_content=doc.page_content,
                    ))
                return documents_to_update
                
        except Exception as e:
            print(f"Error generating changes: {e}")
            # Fallback change - create updates with original content
            for doc in content_extracts:
                doc_name = self._get_document_name(doc.metadata)
                documents_to_update.append(DocumentUpdate(
                    file=doc_name,
                    action=intent.action,
                    reason=f"Error generating changes: {str(e)}",
                    section=intent.object_type or "Content",
                    original_content=doc.page_content,
                    new_content=doc.page_content
                ))
            return documents_to_update
    

class IntentHandlerFactory:
    """Factory to create appropriate intent handlers"""
    
    @staticmethod
    def create_handler(intent: Intent, llm_model) -> BaseIntentHandler:
        """Create the unified handler for all operations"""
        return UnifiedIntentHandler(llm_model)