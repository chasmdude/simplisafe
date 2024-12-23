# Hypervisor-like Service for MLOps Platform

## Overview
This is a FastAPI-based technical assessment designed to evaluate backend system design and implementation skills. The project implements a cluster management system with session-based authentication, organization management, and deployment scheduling.

## Assessment Tasks

### 1. User Authentication and Organization Management
- ✅ Implement session-based user authentication (login/logout)
- ✅ Complete user registration with password hashing
- ✅ Add organization creation with random invite codes
- ✅ Implement organization joining via invite codes

### 2. Cluster Management
- ✅ Create clusters with resource limits (CPU, RAM, GPU)
- ✅ Implement resource tracking and availability
- ✅ Add cluster listing for organization members
- ✅ Validate resource constraints

### 3. Deployment Management
- ✅ Develop a preemption-based scheduling algorithm to prioritize high-priority deployments
- ✅ Create deployment endpoints with resource requirements
- ✅ Implement basic scheduling algorithm
- ✅ Implement Priority, Preemption based scheduling algorithm 
- ✅ Add deployment status tracking
- ✅ Handle resource allocation/deallocation

### 4. Advanced Features (Optional)
- 💡 Add support for deployment dependency management (e.g., Deployment A must complete before Deployment B starts)
  - Above feature can be implemented using a DAG (Directed Acyclic Graph) for deployment dependencies.
  - Kahn's Algorithm can be used to implement the topological sorting of the DAG. 
  - Current Implementation of priority based scheduling for each cluster shall be extended to use kahn's algorithm
- ✅ Implement Basic Role-Based Access Control (RBAC)
- ✅ Add rate limiting
- ✅ Create comprehensive test coverage
- ✅ Enhance API documentation

## Project Structure
```
.
├── app
│   ├── api
│   │   └── v1
│   │       ├── endpoints
│   │       │   ├── auth.py                # Authentication endpoints
│   │       │   ├── clusters.py            # Cluster management
│   │       │   ├── deployments.py         # Deployment handling
│   │       │   └── organizations.py       # Organization management
│   │       └── api.py
│   ├── core
│   │   ├── config.py                      # Configuration settings
│   │   ├── deps.py                        # Dependencies and utilities
│   │   └── security.py                    # Security functions
│   ├── db
│   │   ├── base.py                        # Database setup
│   │   ├── base_class.py                  # Custom base class for SQLAlchemy models
│   │   └── session.py                     # Database session
│   ├── models                             # SQLAlchemy models
│   │   ├── cluster.py
│   │   ├── deployment.py
│   │   ├── organization.py
│   │   ├── organization_member.py         # Organization member model
│   │   └── user.py
│   ├── scheduler
│   │   ├── scheduler.py                   # Scheduler interface
│   │   └── preemptive_scheduler.py        # Preemptive scheduler implementation
│   ├── schemas                            # Pydantic schemas
│   │   ├── cluster.py
│   │   ├── deployment.py
│   │   ├── organization.py
│   │   └── user.py
│   └── main.py                            # Application entry point
├── tests
│   ├── conftest.py                        # Test configuration
│   ├── test_api                           # API tests
│   │   ├── test_auth.py                   # Authentication tests
│   │   ├── test_clusters.py               # Cluster management tests
│   │   ├── test_deployments.py            # Deployment management tests
│   │   └── test_organizations.py          # Organization management tests
├── project.toml                           # Poetry project file
├── README.md                              # Project documentation
└── requirements.txt                       # Python dependencies
  
```

## Authentication Flow
1. Register a new user (`POST /api/v1/auth/register`)
2. Login with credentials (`POST /api/v1/auth/login`)
   - Server sets a secure session cookie
3. Use session cookie for authenticated requests
4. Logout when finished (`POST /api/v1/auth/logout`)

## Organization Management
1. Create organization (generates invite code)
2. Share invite code with team members
3. Members join using invite code
4. Access organization resources (clusters, deployments)

## Cluster Management
1. create clusters with resource limits (CPU, RAM, GPU)
2. Clusters are created under organization of user
2. List clusters for organization members

## Deployment Management**
1. Create a deployment for any cluster by providing a Docker image path, resource requirements (CPU, RAM, GPU), and priority.
2. Resource Allocation for Deployment**: Each deployment requires a certain amount of resources (RAM, CPU, GPU).
3. Queue Deployments**: The deployment should be queued if the resources are unavailable in the cluster.
4. Preemption: Implemented a preemption-based scheduling algorithm to prioritize high-priority deployments.
5. Deployment Status Tracking: Track the status of each deployment (Queued, Running, Completed, Failed).
6. Resource Deallocation: Deallocate resources once the deployment is completed or failed.

## Getting Started

### Prerequisites
- Python 3.11+
- PostgreSQL database

### Setup Instructions

1. Create a virtual environment:
```bash
python3 -m venv .venv
```
2. Activate the virtual environment:
   - On macOS and Linux:
   ```bash
   source .venv/bin/activate
    ```
   - On Windows:
   ```bash:
   .\.venv\Scripts\activate
    ```
#### Note: If you encounter "command not found" Error, Make sure to activate the virtual environment before running following commands

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Testing
Run the test suite:
```bash
pytest --disable-warnings
```

## API Docs
Access the Updated Interactive API documentations:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Design
- The application uses FastAPI for building the RESTful API.
- SQLAlchemy is used for database management.
- Pydantic is used for data validation and serialization.
- Redis is used for deployment queue and resource tracking.
- The application uses session-based authentication.
- The application uses a preemption-based scheduling algorithm for deployment prioritization.
- The application uses Role-Based Access Control (RBAC) for user permissions.
- Since the application is a prototype, the deployment queue is managed in-memory
- ### Decisions
- The application uses a custom base class for SQLAlchemy models to avoid code duplication.
- Organization members are stored in a separate table to manage user roles and permissions.
- Scheduler is created as interface and implemented as PreemptiveScheduler for deployment prioritization.
- Deployment of only same cluster are queued and prioritized while deployments of different clusters are independent.
- Hence, the application uses a single deployment queue for each cluster achieving the decoupling and parallelism for processing deployments for clusters 


## Notes
- Focus on implementing core features first
- Use appropriate error handling throughout
- Document your design decisions
- Consider edge cases in your implementation

## Evaluation Criteria

### 1. Code Quality (40%)
- Clean, readable, and well-organized code
- Proper error handling
- Effective use of FastAPI features
- Type hints and validation

### 2. System Design (30%)
- Authentication implementation
- Resource management approach
- Scheduling algorithm design
- API structure

### 3. Functionality (20%)
- Working authentication system
- Proper resource tracking
- Successful deployment scheduling
- Error handling

### 4. Testing & Documentation (10%)
- Test coverage
- API documentation
- Code comments
- README completeness