"""Detectors for AgentLoopGuard."""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import time

from agentloopguard.utils import hash_call, simple_tokenize, tfidf_vector, cosine_similarity

@dataclass
class DetectionResult:
    detector_name: str
    confidence: float
    description: str
    pattern_details: Dict[str, Any]

class BaseDetector:
    def check(self, call_history: List[Dict[str, Any]]) -> Optional[DetectionResult]:
        raise NotImplementedError

class ExactRepeatDetector(BaseDetector):
    def __init__(self, n: int = 3):
        self.n = n
        
    def check(self, call_history: List[Dict[str, Any]]) -> Optional[DetectionResult]:
        if len(call_history) < self.n:
            return None
            
        recent_calls = call_history[-self.n:]
        
        # We need tool_name and tool_args
        first_call = recent_calls[0]
        if 'tool_name' not in first_call or 'tool_args' not in first_call:
            return None
            
        first_hash = hash_call(first_call['tool_name'], first_call['tool_args'])
        
        for call in recent_calls[1:]:
            if 'tool_name' not in call or 'tool_args' not in call:
                return None
            if hash_call(call['tool_name'], call['tool_args']) != first_hash:
                return None
                
        return DetectionResult(
            detector_name="ExactRepeatDetector",
            confidence=1.0,
            description=f"Exact same tool call repeated {self.n} times.",
            pattern_details={"tool_name": first_call['tool_name'], "repeats": self.n}
        )

class SemanticSimilarityDetector(BaseDetector):
    def __init__(self, threshold: float = 0.92, n: int = 3):
        self.threshold = threshold
        self.n = n
        
    def check(self, call_history: List[Dict[str, Any]]) -> Optional[DetectionResult]:
        if len(call_history) < self.n:
            return None
            
        recent_outputs = [call.get('output', '') for call in call_history[-self.n:] if isinstance(call.get('output'), str)]
        
        if len(recent_outputs) < self.n:
            return None
            
        # Extract vocab from all recent outputs
        vocab = set()
        tokenized_outputs = []
        for out in recent_outputs:
            tokens = simple_tokenize(out)
            vocab.update(tokens)
            tokenized_outputs.append(tokens)
            
        vocab_list = list(vocab)
        if not vocab_list:
            return None
            
        vectors = [tfidf_vector(" ".join(t), vocab_list) for t in tokenized_outputs]
        
        # Check similarity of consecutive outputs
        for i in range(len(vectors) - 1):
            sim = cosine_similarity(vectors[i], vectors[i+1])
            if sim < self.threshold:
                return None
                
        return DetectionResult(
            detector_name="SemanticSimilarityDetector",
            confidence=self.threshold,
            description=f"High semantic similarity between {self.n} consecutive outputs.",
            pattern_details={"threshold": self.threshold, "n": self.n}
        )

class CostVelocityDetector(BaseDetector):
    def __init__(self, max_usd_per_min: float = 2.0):
        self.max_usd_per_min = max_usd_per_min
        
    def check(self, call_history: List[Dict[str, Any]]) -> Optional[DetectionResult]:
        if len(call_history) < 2:
            return None
            
        # Look at last 5 mins or all history
        now = time.time()
        recent_history = [c for c in call_history if (now - c.get('timestamp', now)) < 300]
        
        if len(recent_history) < 2:
            return None
            
        total_cost = sum(c.get('cost_usd', 0.0) for c in recent_history)
        duration_sec = recent_history[-1].get('timestamp', now) - recent_history[0].get('timestamp', now - 1)
        
        if duration_sec <= 0:
            duration_sec = 1
            
        velocity = (total_cost / duration_sec) * 60
        
        if velocity > self.max_usd_per_min:
            return DetectionResult(
                detector_name="CostVelocityDetector",
                confidence=1.0,
                description=f"Cost velocity {velocity:.2f} USD/min exceeds threshold of {self.max_usd_per_min:.2f} USD/min.",
                pattern_details={"velocity_usd_per_min": velocity, "threshold": self.max_usd_per_min}
            )
        return None

class OscillationDetector(BaseDetector):
    def __init__(self, min_cycles: int = 3):
        self.min_cycles = min_cycles
        
    def check(self, call_history: List[Dict[str, Any]]) -> Optional[DetectionResult]:
        if len(call_history) < self.min_cycles * 2:
            return None
            
        hashes = []
        for call in call_history:
            if 'tool_name' in call and 'tool_args' in call:
                hashes.append(hash_call(call['tool_name'], call['tool_args']))
            else:
                hashes.append(str(id(call))) # Fallback
                
        # Check A-B-A-B
        seq = hashes[-self.min_cycles*2:]
        pattern_len = 2
        is_oscillation = True
        
        for i in range(self.min_cycles):
            for j in range(pattern_len):
                idx1 = j
                idx2 = i * pattern_len + j
                if seq[idx1] != seq[idx2]:
                    is_oscillation = False
                    break
            if not is_oscillation:
                break
                
        if is_oscillation:
            return DetectionResult(
                detector_name="OscillationDetector",
                confidence=1.0,
                description=f"Detected A-B oscillation over {self.min_cycles} cycles.",
                pattern_details={"cycle_length": 2, "cycles": self.min_cycles}
            )
            
        # Check A-B-C-A-B-C
        if len(call_history) >= self.min_cycles * 3:
            seq = hashes[-self.min_cycles*3:]
            pattern_len = 3
            is_oscillation = True
            
            for i in range(self.min_cycles):
                for j in range(pattern_len):
                    idx1 = j
                    idx2 = i * pattern_len + j
                    if seq[idx1] != seq[idx2]:
                        is_oscillation = False
                        break
                if not is_oscillation:
                    break
                    
            if is_oscillation:
                return DetectionResult(
                    detector_name="OscillationDetector",
                    confidence=1.0,
                    description=f"Detected A-B-C oscillation over {self.min_cycles} cycles.",
                    pattern_details={"cycle_length": 3, "cycles": self.min_cycles}
                )

        return None
