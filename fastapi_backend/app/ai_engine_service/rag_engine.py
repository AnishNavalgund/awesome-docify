from app.schemas import Intent
from app.data_ingestion_service import vector_store
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from app.config import settings
from .confidence_scorer import ConfidenceScorer
from app.utils import logger_info
# Initialize confidence scorer
confidence_scorer = ConfidenceScorer(confidence_threshold=0.6)

async def run_query_pipeline(intent: Intent, original_query: str = "") -> dict:
    """
    Run the RAG pipeline to generate AI diff suggestions based on user intent.
    """
    try:
        logger_info.info(f">>>>>>> Running RAG pipeline")
        # Retrieve relevant chunks from Qdrant
        search_results = await vector_store.search(query=intent.target, limit=5)
        
        # Build context string
        context_parts = []
        for result in search_results:
            content = result.get("content", "")
            title = result.get("title", "")
            url = result.get("url", "")
            context_entry = f"Title: {title}\nURL: {url}\nContent: {content}\n"
            context_parts.append(context_entry)
        
        context = "\n---\n".join(context_parts)
        
        # Generate response with LLM
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an AI assistant that generates code/documentation updates based on user intent."),
            ("human", """
            Intent: {intent}

            Relevant Context from Documentation: {context}

            Based on the user's intent and the relevant documentation context above, please provide a specific suggestion for what changes should be made. 

            Your response should be:
            1. Clear and actionable
            2. Specific enough to implement
            3. Based on the provided context
            4. Include code examples if relevant

            Please provide your suggestion:
            """)
        ])

        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        formatted_prompt = prompt.format_messages(
            intent=intent.model_dump(),
            context=context
        )
        
        response = await llm.ainvoke(formatted_prompt)
        
        # Score the suggestion
        confidence, score_breakdown = await confidence_scorer.score_suggestion(
            suggestion=response.content,
            search_results=search_results,
            intent=intent,
            query=original_query or intent.target
        )
        
        # Check if we should use fallback
        if confidence_scorer.should_use_fallback(confidence):
            fallback_response = confidence_scorer.get_fallback_response(intent, original_query or intent.target)
            return {
                "suggested_diff": fallback_response,
                "confidence": confidence,
                "fallback_used": True,
                "score_breakdown": score_breakdown
            }
        
        return {
            "suggested_diff": response.content,
            "confidence": confidence,
            "fallback_used": False,
            "score_breakdown": score_breakdown
        }
        
    except Exception as e:
        raise ValueError(f"Failed to run RAG pipeline: {e}")
