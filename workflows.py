from temporalio import workflow
from temporalio.common import RetryPolicy
from datetime import timedelta
from activities import compute_sum  # Import the activity that does the actual computation


# Workflow Definition

@workflow.defn
class JobWorkflow:
    def __init__(self):
        self.progress = {"stage": "init", "attempt": 0}
        self.result = None
        self.error = None

    @workflow.run
    async def run(self, numbers: list[int], fail_first_attempt: bool):
        self.progress["stage"] = "compute"
        self.progress["attempt"] = 1  # Assume first attempt starts

        try:
            self.result = await workflow.execute_activity(
                compute_sum,
                args=[numbers, fail_first_attempt],
                start_to_close_timeout=timedelta(seconds=20),
                heartbeat_timeout=timedelta(seconds=15),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=1),
                    maximum_attempts=3
                ),
            )
            self.progress["attempt"] = self.result["attempt"]
            return self.result
        except Exception as e:
            self.error = str(e)
            raise

    @workflow.query
    def get_status(self):
        return {
            "progress": self.progress,
            "result": self.result,
            "error": self.error
        }
