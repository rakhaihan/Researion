from app.core.redis import get_redis_settings
from app.workers.research_worker import run_research_job, shutdown, startup


class WorkerSettings:
    functions = [run_research_job]
    redis_settings = get_redis_settings()
    on_startup = startup
    on_shutdown = shutdown
    max_jobs = 5
    job_timeout = 900
