import requests
import time
import sys

BASE_URL = "http://localhost:8000"

def test_screenshot_flow():
    print("\n--- Starting Job (Screenshot Flow: fail_first_attempt=True) ---")
    
    # 1. Start Job
    payload = {
        "input": {"numbers": [1, 2, 3, 4]},
        "options": {"fail_first_attempt": True}
    }
    response = requests.post(f"{BASE_URL}/jobs", json=payload)
    if response.status_code != 200:
        print(f"Failed to start: {response.text}")
        return
        
    job_id = response.json()["job_id"]
    print(f"Job started: {job_id}")

    # 2. Poll Status to observe retry
    print("\nPolling status (expecting attempt 1 -> failure -> attempt 2)...")
    for _ in range(15):
        res = requests.get(f"{BASE_URL}/jobs/{job_id}")
        data = res.json()
        
        status = data.get("status")
        progress = data.get("progress", {})
        attempt = progress.get("attempt")
        stage = progress.get("stage")
        
        print(f"Status: {status} | Stage: {stage} | Attempt: {attempt}")
        
        if status == "COMPLETED":
            print(f"\nSUCCESS: Job completed! Final Attempt: {attempt}, Result: {data['result']}")
            return
        
        time.sleep(2)

    print("\nTIMEOUT: Job did not complete in time.")

if __name__ == "__main__":
    test_screenshot_flow()
