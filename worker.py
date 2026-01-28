import asyncio
from temporalio.client import Client
from temporalio.worker import Worker
from workflows import JobWorkflow  # Import your workflow class
from activities import compute_sum  # Import your activity function

# Worker Setup

async def main():
    """
    Main entry point to start a Temporal worker.

    Responsibilities:
    1. Connect to the Temporal server.
    2. Create a worker that listens on a specific task queue.
    3. Register workflows and activities that the worker can execute.
    4. Run the worker to start processing tasks.
    """

    # Connect to the Temporal server (must be running locally or remotely)
    client = await Client.connect("localhost:7233")

    # Create a Worker instance
    worker = Worker(
        client,
        task_queue="job-task-queue",  # Worker listens for tasks on this queue
        workflows=[JobWorkflow],      # Register the workflow class it can run
        activities=[compute_sum],     # Register the activity functions it can execute
    )

    # Start the worker event loop
    # This call blocks and keeps the worker running to process workflows/activities
    await worker.run()


# Script Entry Point

if __name__ == "__main__":
    # Run the async main function using asyncio
    # This starts the worker and keeps it listening for Temporal tasks
    asyncio.run(main())
