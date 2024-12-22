from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy import create_engine
from app.api.v1.api import api_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
import psycopg2
from sqlalchemy.orm import sessionmaker


# Function to create database if it doesn't exist
def create_database_if_not_exists():
    # Connect to the PostgreSQL server using settings from config.py
    conn = psycopg2.connect(
        dbname="postgres",  # Connect to the default 'postgres' database
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        host=settings.POSTGRES_SERVER,
        port=settings.POSTGRES_PORT
    )
    conn.autocommit = True  # Enable autocommit for database creation

    try:
        # Create a cursor object
        cur = conn.cursor()

        # Check if the 'cluster_management' database exists
        cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", (settings.POSTGRES_DB,))
        exists = cur.fetchone()

        if not exists:
            # If the database does not exist, create it
            cur.execute(f"CREATE DATABASE {settings.POSTGRES_DB}")
            print(f"Database '{settings.POSTGRES_DB}' created successfully.")

        # Close the cursor and connection
        cur.close()
        conn.close()

    except Exception as e:
        print(f"Error during database creation: {e}")
        if conn:
            conn.close()

# Define the lifespan function
async def lifespan(app: FastAPI):
    # Startup logic
    create_database_if_not_exists()
    Base.metadata.create_all(bind=engine)

    # start_periodic_task()

    yield
    # Shutdown logic (if any)


# Create the FastAPI app with lifespan
app = FastAPI(
    title="Cluster Management API",
    description="""
    Technical Assessment API for managing organizations, clusters, and deployments.

    ## Features

    * **Users & Authentication** - Register, login, and manage user sessions
    * **Organizations** - Create and join organizations using invite codes
    * **Clusters** - Manage compute clusters with resource limits
    * **Deployments** - Schedule and manage deployments with priority queuing
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS and Session
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    session_cookie=settings.SESSION_COOKIE_NAME,
    max_age=settings.SESSION_MAX_AGE
)

# Include API router
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)