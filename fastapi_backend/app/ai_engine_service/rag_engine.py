import warnings
from pathlib import Path
from typing import Dict, List

from app.ai_engine_service.prompts import RAG_DOCUMENT_UPDATE_PROMPT
from app.config import settings
from app.utils import logger_error
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from qdrant_client import QdrantClient

warnings.filterwarnings("ignore")


# Singleton QdrantClient to prevent multiple instances
_qdrant_client = None


def get_qdrant_client():
    global _qdrant_client
    if _qdrant_client is None:
        _qdrant_client = QdrantClient(path=str(Path(settings.QDRANT_PATH)))
    return _qdrant_client


class DocuRAG(BaseRetriever):
    """Unified RAG system with efficient single-LLM-call approach"""

    def __init__(self):
        # Initialize parent class properly
        super().__init__()

        # Initialize components after parent initialization
        self._llm_model = ChatOpenAI(
            model=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
            openai_api_key=settings.OPENAI_API_KEY,
        )
        self._embeddings = OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL, openai_api_key=settings.OPENAI_API_KEY
        )
        self._client = get_qdrant_client()  # Use singleton
        self._collection_name = settings.QDRANT_COLLECTION_NAME

    async def _aget_relevant_documents(self, query: str) -> List[Document]:
        """Efficient vector-only retrieval with limited results"""
        search_results = self._client.search(
            collection_name=self._collection_name,
            query_vector=self._embeddings.embed_query(query),
            limit=settings.TOP_K_DOCS,  # Use the configured limit
            with_payload=True,
        )
        return [
            Document(
                page_content=result.payload.get("page_content", ""),
                metadata={
                    **result.payload.get("metadata", {}),
                    "source": result.payload.get("metadata", {}).get(
                        "title", "document.md"
                    ),
                },
            )
            for result in search_results
            if result.score >= settings.MIN_SIMILARITY_SCORE
        ]

    def _get_relevant_documents(self, query: str) -> List[Document]:
        """Synchronous version required by BaseRetriever"""
        import asyncio

        try:
            return asyncio.run(self._aget_relevant_documents(query))
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self._aget_relevant_documents(query))
            finally:
                loop.close()

    async def process_query(self, query: str) -> Dict:
        """Simple RAG approach - let the LLM provide natural responses"""
        try:
            print(f"\n PROCESSING QUERY: {query}")
            print("=" * 50)

            # Convert our ChatPromptTemplate to a regular PromptTemplate
            prompt_messages = RAG_DOCUMENT_UPDATE_PROMPT.format_messages(
                context="{context}", question="{question}"
            )

            # Extract the content from the messages
            system_content = prompt_messages[0].content
            human_content = prompt_messages[1].content

            # Combine into a single template
            combined_template = f"{system_content}\n\n{human_content}"

            print("PROMPT TEMPLATE:")
            print(f"System: {system_content}")
            print(f"Human: {human_content}")
            print("=" * 50)

            custom_prompt = PromptTemplate(
                input_variables=["context", "question"], template=combined_template
            )

            print("CREATING QA CHAIN...")

            # Create a custom QA chain with our prompt
            qa_chain = load_qa_chain(
                llm=self._llm_model, chain_type="stuff", prompt=custom_prompt
            )

            print("CREATING RETRIEVAL CHAIN...")

            # Create the retrieval chain with our custom QA chain
            chain = RetrievalQAWithSourcesChain(
                retriever=self,
                combine_documents_chain=qa_chain,
                return_source_documents=True,
            )

            print("RETRIEVING DOCUMENTS...")
            result = await chain.ainvoke({"question": query})

            print("RETRIEVAL RESULT:")
            print(f"Keys in result: {list(result.keys())}")

            source_docs = result.get("source_documents", [])
            llm_response = result.get("answer", "")

            print(f"SOURCE DOCUMENTS: {len(source_docs)} found")
            for i, doc in enumerate(source_docs[:3]):  # Show first 3 docs
                print(
                    f"  Doc {i+1}: {doc.metadata.get('title', 'Unknown')} - {len(doc.page_content)} chars"
                )

            print(f"LLM RESPONSE: {repr(llm_response)}")
            print("=" * 50)

            # Intelligent document selection - only include relevant documents
            documents_to_update = []

            if source_docs:
                # Get unique document titles to avoid duplicates
                seen_titles = set()
                print("DOCUMENT SELECTION PROCESS:")
                for i, doc in enumerate(source_docs):
                    doc_name = doc.metadata.get("title", "document.md")
                    print(f"  Processing doc {i+1}: '{doc_name}'")
                    if doc_name != "document.md" and doc_name not in seen_titles:
                        seen_titles.add(doc_name)
                        print(f"    Adding document: '{doc_name}'")
                        documents_to_update.append(
                            {
                                "file": doc_name,
                                "action": "modify",
                                "reason": "User requested update",
                                "section": "content",
                                "original_content": doc.page_content,  # Provide actual original content
                                "new_content": llm_response,
                            }
                        )
                    else:
                        print(
                            f"    Skipping document: '{doc_name}' (duplicate or invalid)"
                        )
                print(f"FINAL DOCUMENTS TO UPDATE: {len(documents_to_update)}")

            # If no documents found, create a default update
            if not documents_to_update:
                documents_to_update = [
                    {
                        "file": "document.md",
                        "action": "modify",
                        "reason": "User requested update",
                        "section": "content",
                        "original_content": "",
                        "new_content": llm_response,
                    }
                ]

            final_response = {
                "query": query,
                "keyword": "documentation",
                "analysis": f"Retrieved {len(source_docs)} relevant documents.",
                "documents_to_update": documents_to_update,
                "total_documents": len(documents_to_update),
            }

            print("FINAL RESPONSE:")
            print(f"  Query: {final_response['query']}")
            print(f"  Analysis: {final_response['analysis']}")
            print(
                f"  Documents to update: {len(final_response['documents_to_update'])}"
            )
            print("=" * 50)

            return final_response

        except Exception as e:
            print(f"ERROR: {e}")
            logger_error.error(f"Pipeline error: {e}")
            raise e


# Global instance
task = DocuRAG()


async def orchestrator(query: str) -> dict:
    return await task.process_query(query)
