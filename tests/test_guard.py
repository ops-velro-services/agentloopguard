import pytest
from agentloopguard.guard import LoopGuard
from agentloopguard.exceptions import LoopDetectedError

def test_guard_session():
    guard = LoopGuard(max_iterations=5)
    with guard.session() as sess:
        for i in range(3):
            sess.record({"tool_name": "test", "tool_args": {"i": i}})
            
        summary = sess.summary()
        assert summary["history_length"] == 3
        assert summary["budget"]["iterations"] == 3

def test_guard_detects_loop():
    guard = LoopGuard(on_alert="raise")
    with guard.session() as sess:
        with pytest.raises(LoopDetectedError) as exc:
            for i in range(4):
                sess.record({"tool_name": "test", "tool_args": {"fixed": True}, "output": "same output"})
                
        assert "ExactRepeatDetector" in str(exc.value)

def test_guard_decorator():
    guard = LoopGuard(on_alert="raise")
    
    @guard.watch(model="gpt-3.5-turbo")
    def do_work(x):
        return x
        
    with pytest.raises(LoopDetectedError):
        for _ in range(4):
            do_work(1)
