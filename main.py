from fastapi import FastAPI
from pydantic import BaseModel
from temporalio.client import Client
from temporalio.common import WorkflowIDReusePolicy
from temporalio.service import RPCError, RPCStatusCode
from contextlib import asynccontextmanager
import uuid


#  Models
# Pydantic models are used to validate and structure the data coming in and out of the FastAPI endpoints.

class JobInput(BaseModel):
    """Represents the input for a job: a list of numbers."""
    numbers: list[int]


class JobOptions(BaseModel):
    """Represents options for the job execution."""
    fail_first_attempt: bool  # Whether the workflow should fail on first attempt


class JobPayload(BaseModel):
    """The full payload (the "package" of everything the workflow needs to run a job) for creating a job."""
    input: JobInput
    options: JobOptions


# App Initialization

# Global variable to hold the Temporal client
temporal_client: Client | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan handler: runs on startup and cleanup on shutdown.
    Connects Temporal client when app starts and closes if needed.
    """
    global temporal_client
    temporal_client = await Client.connect("localhost:7233")
    yield  # app runs here

app = FastAPI(lifespan=lifespan) # Create a FastAPI app instance

def get_client() -> Client:
    """
    Utility function to return the Temporal client.
    Raises an error if called before startup.
    """
    if temporal_client is None:
        raise RuntimeError("Temporal client not initialized")
    return temporal_client


# Routes

@app.post("/jobs")
async def start_job(payload: JobPayload):
    """
    Start a new workflow/job in Temporal.

    Args:
        payload (JobPayload): Input numbers and options for the job.

    Returns:
        dict: The job_id generated for this workflow.

    Notes:
        - Each job is given a unique ID using uuid4.
        - id_reuse_policy ensures we don't accidentally start two workflows
          with the same ID.
    """
    client = get_client()
    job_id = f"job-{uuid.uuid4()}"  # Unique job ID

    # Start the Temporal workflow
    await client.start_workflow(
        "JobWorkflow",  # The workflow name registered in Temporal
        args=[payload.input.numbers, payload.options.fail_first_attempt],
        id=job_id,
        task_queue="job-task-queue",  # Where workflow tasks are scheduled
        id_reuse_policy=WorkflowIDReusePolicy.REJECT_DUPLICATE,  # Prevent duplicate IDs
    )

    return {"job_id": job_id}


@app.get("/jobs/{job_id}")
async def get_job(job_id: str):
    client = get_client()
    handle = client.get_workflow_handle(job_id)

    try:
        desc = await handle.describe()
        status = desc.status.name

        # Query workflow for state
        query = await handle.query("get_status")
        progress = query["progress"]
        result = query["result"]
        error = query["error"]
        
        # Override progress stage if completed
        if status == "COMPLETED":
            progress["stage"] = "done"
            # Ensure result['result'] is extracted if needed, or return full dict
            if result and "result" in result:
                result = result["result"]

        return {
            "job_id": job_id,
            "status": status,
            "progress": progress,
            "result": result,
            "error": error,
        }

    except RPCError as e:
        if e.status == RPCStatusCode.FAILED_PRECONDITION:
            # Workflow might be in retry or not yet started
            return {
                "job_id": job_id,
                "status": "RUNNING",
                "progress": {"stage": "compute", "attempt": 0},
                "result": None,
                "error": None,
            }
        raise
