from temporalio import activity
import asyncio

# ---------- Activity Definition ----------

@activity.defn
async def compute_sum(numbers: list[int], fail_first_attempt: bool) -> dict:
    info = activity.info()
    attempt = info.attempt

    # Heartbeat the current attempt to the workflow
    activity.heartbeat(attempt)

    # Simulate delay to make progress observable
    await asyncio.sleep(10)

    if fail_first_attempt and attempt == 1:
        raise RuntimeError("Intentional failure on first attempt")

    return {
        "result": sum(numbers),
        "attempt": attempt
    }

# Make sure attempt gets updated successfully during RUNNING stage 
