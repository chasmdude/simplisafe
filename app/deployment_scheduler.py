import time

import redis
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from app.core import deps
from app.models.cluster import Cluster
from app.models.deployment import DeploymentStatus
from app.schemas.deployment import DeploymentCreate
from app.models.deployment import Deployment as DeploymentModel

# Redis connection setup
redis_client = redis.StrictRedis(host="localhost", port=6379, db=0)

def deployment_scheudler():
    while True:
        task = redis_client.blpop("deployment_queue")  # Blocking pop from the queue
        if task:
            print(f"Processing task: {task[1].decode()}")
            # Simulate task processing
            time.sleep(5)  # Replace with actual task processing logic
            print(f"Task completed: {task[1].decode()}")

def process_deployment(deployment_in: DeploymentCreate):
    db: Session = deps.get_db()

    # Retrieve cluster from database
    cluster = db.query(Cluster).filter(Cluster.id == deployment_in.cluster_id).first()
    if not cluster:
        print(f"Cluster not found: {deployment_in.cluster_id}")
        return

    # Check if resources are available
    if (
            cluster.cpu_available >= deployment_in.cpu_required
            and cluster.ram_available >= deployment_in.ram_required
            and cluster.gpu_available >= deployment_in.gpu_required
    ):
        # Allocate resources and mark the deployment as running
        cluster.cpu_available -= deployment_in.cpu_required
        cluster.ram_available -= deployment_in.ram_required
        cluster.gpu_available -= deployment_in.gpu_required
        deploy_status = DeploymentStatus.RUNNING
    else:
        deploy_status = DeploymentStatus.PENDING
        # Optionally retry the deployment after some time
        sleep(10)
        return process_deployment(deployment_in)

    # Create the deployment record
    deployment = DeploymentModel(
        name=deployment_in.name,
        docker_image=deployment_in.docker_image,
        cpu_required=deployment_in.cpu_required,
        ram_required=deployment_in.ram_required,
        gpu_required=deployment_in.gpu_required,
        priority=deployment_in.priority,
        status=deploy_status,
        cluster_id=deployment_in.cluster_id,
    )
    db.add(deployment)
    db.commit()
    db.refresh(deployment)

    return deployment


import redis
import threading
import time

# Dictionary to hold separate Redis queues for each cluster
cluster_queues = {}


def background_worker(cluster_id: int):
    # Get the Redis queue for the cluster
    queue_name = f"deployment_queue_{cluster_id}"
    redis_client = redis.StrictRedis(host="localhost", port=6379, db=0)

    while True:
        task = redis_client.blpop(queue_name)  # Blocking pop from the cluster's queue
        if task:
            deployment_id = task[1].decode()
            print(f"Processing deployment {deployment_id} for cluster {cluster_id}")
            # Simulate task processing (could be resource allocation, etc.)
            time.sleep(5)  # Replace with actual task processing logic
            print(f"Deployment {deployment_id} completed for cluster {cluster_id}")


def start_cluster_worker(cluster_id: int):
    """
    Start a background worker for a specific cluster if it doesn't already exist.
    """
    if cluster_id not in cluster_queues:
        # Start the worker thread only once for each cluster
        thread = threading.Thread(target=background_worker, args=(cluster_id,))
        thread.daemon = True  # Ensure thread dies when the app shuts down
        thread.start()
        cluster_queues[cluster_id] = thread
        print(f"Started background worker for cluster {cluster_id}")


def check_for_new_clusters(db: Session):
    """
    Periodically check for new clusters and add corresponding queues if they don't exist.
    """
    # Get all clusters from the database
    clusters = db.query(Cluster).all()

    # Iterate over all clusters and ensure a queue and worker exists
    for cluster in clusters:
        # Check if queue for the cluster exists in Redis
        queue_name = f"deployment_queue_{cluster.id}"
        if not redis_client.exists(queue_name):  # If the queue doesn't exist
            # Create a queue for the new cluster
            redis_client.set(queue_name, 1)  # Just to ensure the queue is created
            print(f"Queue created for cluster {cluster.name} : {cluster.id}")

        # Start a worker if it's not running already
        start_cluster_worker(cluster.id)


# Start the background scheduler for periodic check
def start_periodic_task():
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_for_new_clusters, 'interval', seconds=30)  # Check every 30 seconds
    scheduler.start()

    print("Scheduler started for checking new clusters periodically.")