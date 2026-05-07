import os

from postcard_mvp_flask import run_order_job_worker_loop


if __name__ == "__main__":
    poll_interval = os.getenv("ORDER_JOB_POLL_INTERVAL", "2.0")
    run_order_job_worker_loop(poll_interval=poll_interval)
