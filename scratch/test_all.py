"""Full integration test for Manu — tests every module main.py uses."""
import sys
import logging

sys.path.insert(0, ".")
logging.basicConfig(level=logging.WARNING)

import config

results = []

def test(name, fn):
    try:
        result = fn()
        results.append((name, "PASS", result))
        print(f"  PASS  {name}: {result}")
    except Exception as e:
        results.append((name, "FAIL", str(e)))
        print(f"  FAIL  {name}: {e}")

print("=== Module Instantiation ===\n")

from modules.memory.store import MemoryStore
memory = MemoryStore(config.DB_PATH)
test("MemoryStore", lambda: "OK")

from engines.tts_engine import TTSEngine
tts = TTSEngine()
test("TTSEngine", lambda: "OK")

from engines.stt_engine import STTEngine
stt = STTEngine()
test("STTEngine", lambda: "OK")

from modules.emotional.state_manager import EmotionalStateManager
emotional = EmotionalStateManager(tts)
test("EmotionalStateManager", lambda: "OK")

from engines.llm_engine import LLMEngine
llm = LLMEngine(memory)
test("LLMEngine", lambda: "OK")

from modules.security.auth import AuthManager
auth = AuthManager(tts, memory)
test("AuthManager", lambda: "OK")

from modules.commands.dispatcher import CommandDispatcher
dispatcher = CommandDispatcher(tts=tts, memory=memory, llm=llm, emotional=emotional)
test("CommandDispatcher", lambda: "OK")

from modules.events.monitor import EventMonitor
monitor = EventMonitor(emotional, tts, memory)
test("EventMonitor", lambda: "OK")

print("\n=== Command Tests ===\n")

test("time",     lambda: dispatcher.process("what time is it"))
test("date",     lambda: dispatcher.process("what date is it"))
test("joke",     lambda: dispatcher.process("tell me a joke"))
test("battery",  lambda: dispatcher.process("check battery"))
test("identity", lambda: dispatcher.process("who are you"))
test("thanks",   lambda: dispatcher.process("thank you manu"))
test("sysinfo",  lambda: dispatcher.process("system info"))
test("lock",     lambda: dispatcher.process("enter sleep mode"))

print("\n=== Memory Tests ===\n")

test("log",      lambda: (memory.log_interaction("test input", "test response"), "logged")[1])
test("recall",   lambda: memory.get_recent(1))
test("setting",  lambda: (memory.set_setting("test_key", "test_val"), memory.get_setting("test_key"))[1])
test("context",  lambda: memory.build_llm_context(2)[:80])

print("\n=== Emotion Tests ===\n")

test("mood_low",  lambda: (emotional.update_mood_on_event("battery_low", 15), f"{emotional.current_mood} {emotional.get_mood_emoji()}")[1])
test("mood_full", lambda: (emotional.update_mood_on_event("battery_full", 100), f"{emotional.current_mood} {emotional.get_mood_emoji()}")[1])
test("prefix",    lambda: emotional.get_contextual_prefix())
test("tts_params",lambda: emotional.get_tts_params())

print("\n=== Security Tests ===\n")

test("no_auth", lambda: auth.verify_password("anything"))  # config has a hash set

print("\n" + "=" * 50)
passed = sum(1 for _, s, _ in results if s == "PASS")
failed = sum(1 for _, s, _ in results if s == "FAIL")
print(f"Results: {passed} passed, {failed} failed out of {len(results)}")

if failed:
    print("\nFailed tests:")
    for name, status, detail in results:
        if status == "FAIL":
            print(f"  - {name}: {detail}")
