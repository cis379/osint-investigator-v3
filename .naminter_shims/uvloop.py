import asyncio
def run(coro, *a, **k):
    return asyncio.run(coro)
def install(*a, **k):
    return None
def new_event_loop():
    return asyncio.new_event_loop()
