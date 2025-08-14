from core.tools.microtool import microtool
import asyncio


@microtool("async_echo", description="Asynchronously echo a message", tags=["async"])
async def async_echo(msg: str, delay: float = 0.0) -> dict:
    await asyncio.sleep(delay)
    return {"echo": msg}

