from typing import List, Dict, Any, Tuple
from app.schemas import Intent
from app.utils import logger_info, logger_error

class ConfidenceScorer:
    """
    Simple confidence scorer for RAG suggestions
    """
    
    def __init__(self, confidence_threshold: float = 0.6):
        self.confidence_threshold = confidence_threshold
    
    async def score_suggestion(
        self, 
        suggestion: str, 
        search_results: List[Dict[str, Any]], 
        intent: Intent,
        query: str
    ) -> Tuple[float, Dict[str, float]]:
        """
        Simple confidence scoring based on search results and intent coverage
        """
        
        # Base confidence from search results
        if not search_results:
            confidence = 0.1
            print(">>> No search result")
        else:
            # Calculate average similarity score
            scores = [result.get("score", 0) for result in search_results]
            print(f">>>>>>>> Scores: {scores}")
            avg_score = sum(scores) / len(scores) if scores else 0
            print(f">>>>> Avg score: {avg_score}")
            confidence = min(1.0, max(0.0, avg_score))
            print(f">>>>> Confidence similarity score: {confidence}")
        
        # Boosting confidence if suggestion mentions the target
        if intent.target.lower() in suggestion.lower():
            print(f">>>>> Target: {intent.target.lower()}")
            confidence += 0.2
        
        # Boosting confidence if suggestion mentions the action
        action_words = {
            "add": ["add", "create", "implement"],
            "remove": ["remove", "delete", "eliminate"],
            "modify": ["modify", "update", "change"]
        }
        
        action_words_list = action_words.get(intent.action, [])
        if any(word in suggestion.lower() for word in action_words_list):
            confidence += 0.1
        
        # Cap confidence at 1.0
        confidence = min(1.0, confidence)
        
        score_breakdown = {
            "base_confidence": confidence,
            "target_mentioned": intent.target.lower() in suggestion.lower(),
            "action_mentioned": any(word in suggestion.lower() for word in action_words_list),
            "search_results_count": len(search_results)
        }
        
        return confidence, score_breakdown
    
    def should_use_fallback(self, confidence: float) -> bool:
        """Determine if fallback response should be used."""
        return confidence < self.confidence_threshold
    
    def get_fallback_response(self, intent: Intent, query: str) -> str:
        print(f" >>>> Fallback!!")
        """Generate a simple fallback response."""
        return f"""I cannot find sufficient information to provide a reliable suggestion for: "{query}"
                 The requested {intent.action} operation on "{intent.target}" requires more context or the target may not exist in the current documentation.
                 Please try rephrasing your query with more specific details."""
