"""Utility functions for AgentLoopGuard."""
import hashlib
import json
import math
from typing import Any, Dict, List, Optional

def hash_call(tool_name: str, args: Dict[str, Any]) -> str:
    """Deterministic hash of a tool call."""
    call_repr = json.dumps({"name": tool_name, "args": args}, sort_keys=True)
    return hashlib.sha256(call_repr.encode("utf-8")).hexdigest()

def simple_tokenize(text: str) -> List[str]:
    """Basic whitespace tokenizer."""
    if not text:
        return []
    return [word.lower().strip(".,!?()[]{}\"'") for word in text.split() if word.strip()]

def tfidf_vector(text: str, vocabulary: List[str]) -> List[float]:
    """Simple TF-IDF vectorization without external deps."""
    tokens = simple_tokenize(text)
    if not tokens or not vocabulary:
        return [0.0] * len(vocabulary)
    
    # TF
    tf: Dict[str, float] = {}
    total_tokens = len(tokens)
    for token in tokens:
        tf[token] = tf.get(token, 0) + 1 / total_tokens
        
    # IDF (simplified - assumes doc frequency is 1 for words present, 2 for vocabulary)
    # This is a hacky way to do it for single comparisons without a full corpus
    vec = []
    for word in vocabulary:
        val = tf.get(word, 0.0)
        # simplistic idf weight for demonstration
        vec.append(val * 1.5) 
    return vec

def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Simple cosine similarity."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot_product / (norm_a * norm_b)

PRICING_TABLE = {
    "gpt-4o": {"input": 5.0, "output": 15.0},
    "gpt-4o-mini": {"input": 0.150, "output": 0.600},
    "gpt-4-turbo": {"input": 10.0, "output": 30.0},
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    "claude-3.5-sonnet": {"input": 3.0, "output": 15.0},
    "claude-3-haiku": {"input": 0.25, "output": 1.25},
    "claude-3-opus": {"input": 15.0, "output": 75.0},
    "gemini-1.5-pro": {"input": 3.5, "output": 10.5},
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
    "gemini-2.0-flash": {"input": 0.10, "output": 0.40},
}

def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate cost in USD for a given model and token usage."""
    model_lower = model.lower()
    for key, rates in PRICING_TABLE.items():
        if key in model_lower:
            cost_in = (input_tokens / 1_000_000) * rates["input"]
            cost_out = (output_tokens / 1_000_000) * rates["output"]
            return cost_in + cost_out
    return 0.0
