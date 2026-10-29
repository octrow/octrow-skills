---
type: llm
focus: trace
weight: 1
---

Core calls run off the GUI thread through one bridge (a CoreRunner with an asyncio loop thread, asyncio.to_thread, or QThreadPool) and results reach widgets only through Qt signals; QtAsyncio and qasync are not used.
