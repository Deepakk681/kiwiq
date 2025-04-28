# Workflow Service DB & API Design

This document outlines the database schema, key use cases, data access patterns, service functionalities, and API routes for the KiwiQ Workflow Service.

## 1. Core Use Cases & User Journeys

*   **Workflow Creation/Management:**
    *   Users (with `WORKFLOW_CREATE` perm) create new workflow configurations within their active organization.
    *   Workflows reference Node Templates (owned by KiwiQ).
    *   Users (with `WORKFLOW_UPDATE`/`WORKFLOW_DELETE` perm) can modify or delete workflows they own.
    *   Users (with `WORKFLOW_READ` perm) can view workflows owned by their active organization.
*   **Workflow Execution:**
    *   Users (with `WORKFLOW_EXECUTE` perm) trigger a run of a specific workflow.
    *   A new `WorkflowRun` record is created.
    *   The workflow execution engine (e.g., LangGraph adapter) processes the run, potentially creating detailed logs/streams.
    *   The `WorkflowRun` status is updated (scheduled, running, paused, completed, failed, etc.).
*   **Run Monitoring & Results:**
    *   Users (with `RUN_READ` perm) can list and view the status and summary of runs associated with their active organization's workflows.
    *   Users can potentially access detailed run streams/results (link might point to NoSQL or S3).
*   **Template Management (Admin):**
    *   KiwiQ Admins manage `NodeTemplate`, shared `PromptTemplate`, and `SchemaTemplate` records.
*   **Template Usage (User):**
    *   Users can create organization-specific `PromptTemplate` and `SchemaTemplate`.
    *   Workflows reference `NodeTemplate`, `PromptTemplate`, and `SchemaTemplate` by name/version.

## 2. Database Schema Design (SQL - Postgres)

We'll use SQLModel for defining the models. The `auth.` prefix refers to tables in the auth schema (`services/kiwi_app/auth/models.py`).

**Table Prefix:** `kw_wf_` (Defined in `settings.py` as `DB_TABLE_WORKFLOW_PREFIX`)

**Enums (Defined in `constants.py`):**

*   `NodeLaunchStatus(Enum)`: `EXPERIMENTAL`, `STAGING`, `PRODUCTION`
*   `WorkflowRunStatus(Enum)`: `SCHEDULED`, `RUNNING`, `PAUSED`, `COMPLETED`, `FAILED`, `CANCELLED`, `WAITING_HITL`
*   `TemplateType(Enum)`: `NODE`, `PROMPT`, `SCHEMA`

**Models:**

1.  **`NodeTemplate`** (`kw_wf_node_template`)
    *   `id: uuid.UUID` (PK)
    *   `name: str` (Unique, Indexed) - e.g., "llm_generator", "web_search"
    *   `version: str` (Indexed) - e.g., "1.0.0", "latest" (Composite Unique Index on name, version)
    *   `description: Optional[str]`
    *   `input_schema: Dict[str, Any]` (JSONB) - JSON Schema for inputs
    *   `output_schema: Dict[str, Any]` (JSONB) - JSON Schema for outputs
    *   `config_schema: Optional[Dict[str, Any]]` (JSONB) - JSON Schema for config
    *   `launch_status: NodeLaunchStatus` (Indexed)
    *   `created_at: datetime`
    *   `updated_at: datetime`
    *   *(No owner - owned by KiwiQ)*

2.  **`Workflow`** (`kw_wf_workflow`)
    *   `id: uuid.UUID` (PK)
    *   `name: str` (Indexed)
    *   `description: Optional[str]`
    *   `owner_org_id: uuid.UUID` (FK -> `auth.Organization.id`, Indexed)
    *   `graph_config: Dict[str, Any]` (JSONB) - The core definition (nodes, edges, potentially refs to prompt/schema templates)
    *   `version_tag: Optional[str]` (Indexed) - User-defined tag like "v1.2-stable"
    *   `is_template: bool` (Default: False, Indexed) - If this can be copied by others in the org.
    *   `created_at: datetime`
    *   `updated_at: datetime`
    *   `created_by_user_id: Optional[uuid.UUID]` (FK -> `auth.User.id`, Nullable)
    *   `updated_by_user_id: Optional[uuid.UUID]` (FK -> `auth.User.id`, Nullable)
    *   **Relationships:**
        *   `owner_org: Organization` = Relationship(back_populates="workflows")
        *   `runs: List["WorkflowRun"]` = Relationship(back_populates="workflow")

3.  **`WorkflowRun`** (`kw_wf_workflow_run`)
    *   `id: uuid.UUID` (PK, Default: uuid4) - The unique Run ID
    *   `workflow_id: uuid.UUID` (FK -> `Workflow.id`, Indexed)
    *   `owner_org_id: uuid.UUID` (FK -> `auth.Organization.id`, Indexed) - Denormalized for easier querying
    *   `triggered_by_user_id: Optional[uuid.UUID]` (FK -> `auth.User.id`, Nullable, Indexed)
    *   `status: WorkflowRunStatus` (Indexed)
    *   `inputs: Optional[Dict[str, Any]]` (JSONB) - Inputs provided at runtime
    *   `outputs: Optional[Dict[str, Any]]` (JSONB) - High-level final outputs (summary)
    *   `error_message: Optional[str]`
    *   `detailed_results_ref: Optional[str]` - Link to NoSQL record ID or S3 path
    *   `thread_id: Optional[uuid.UUID]` (Indexed) - Potentially reusable langgraph thread ID
    *   `started_at: Optional[datetime]`
    *   `ended_at: Optional[datetime]`
    *   `created_at: datetime`
    *   `updated_at: datetime`
    *   **Relationships:**
        *   `workflow: Workflow` = Relationship(back_populates="runs")
        *   `owner_org: Organization` = Relationship() # No back-population needed if only FK
        *   `triggered_by: User` = Relationship() # No back-population needed

4.  **`PromptTemplate`** (`kw_wf_prompt_template`)
    *   `id: uuid.UUID` (PK)
    *   `name: str` (Indexed) - Unique within an org context + system context
    *   `version: str` (Indexed) - (Composite Unique Index on name, version, owner_org_id/is_system)
    *   `description: Optional[str]`
    *   `template_content: str` (Text) - The actual prompt template string (e.g., Jinja2)
    *   `input_variables: Optional[List[str]]` (JSONB) - List of expected input variable names
    *   `owner_org_id: Optional[uuid.UUID]` (FK -> `auth.Organization.id`, Nullable, Indexed) - Null if system template
    *   `is_system_entity: bool` (Default: False, Indexed)
    *   `created_at: datetime`
    *   `updated_at: datetime`
    *   **Relationships:**
        *   `owner_org: Optional[Organization]` = Relationship()

5.  **`SchemaTemplate`** (`kw_wf_schema_template`)
    *   `id: uuid.UUID` (PK)
    *   `name: str` (Indexed) - Unique within an org context + system context
    *   `version: str` (Indexed) - (Composite Unique Index on name, version, owner_org_id/is_system)
    *   `description: Optional[str]`
    *   `schema_definition: Dict[str, Any]` (JSONB) - The JSON schema definition
    *   `schema_type: str` (Indexed) - e.g., "json_schema", "pydantic" (can store model source later?)
    *   `owner_org_id: Optional[uuid.UUID]` (FK -> `auth.Organization.id`, Nullable, Indexed) - Null if system template
    *   `is_system_entity: bool` (Default: False, Indexed)
    *   `created_at: datetime`
    *   `updated_at: datetime`
    *   **Relationships:**
        *   `owner_org: Optional[Organization]` = Relationship()

6.  **`UserNotification`** (`kw_wf_user_notification`)
    *   `id: uuid.UUID` (PK)
    *   `user_id: uuid.UUID` (FK -> `auth.User.id`, Indexed)
    *   `org_id: uuid.UUID` (FK -> `auth.Organization.id`, Indexed) - Context for the notification
    *   `related_run_id: Optional[uuid.UUID]` (FK -> `WorkflowRun.id`, Nullable, Indexed) - Link to the relevant run
    *   `notification_type: str` (Indexed) - e.g., "RUN_COMPLETED", "RUN_FAILED", "HITL_REQUESTED", "SYSTEM_MESSAGE"
    *   `message: Dict[str, Any]` (JSONB) - Content of the notification (e.g., summary, link)
    *   `is_read: bool` (Default: False, Indexed)
    *   `created_at: datetime`
    *   `read_at: Optional[datetime]`
    *   **Relationships:**
        *   `user: User` = Relationship()
        *   `organization: Organization` = Relationship()
        *   `workflow_run: Optional[WorkflowRun]` = Relationship()

7.  **`HITLJob`** (`kw_wf_hitl_job`)
    *   `id: uuid.UUID` (PK)
    *   `requesting_run_id: uuid.UUID` (FK -> `WorkflowRun.id`, Indexed) - The run waiting for input
    *   `assigned_user_id: Optional[uuid.UUID]` (FK -> `auth.User.id`, Nullable, Indexed) - User assigned to respond (can be null if assigned to group/role)
    *   `org_id: uuid.UUID` (FK -> `auth.Organization.id`, Indexed) - Owning organization
    *   `status: str` (Indexed) - e.g., "PENDING", "RESPONDED", "EXPIRED", "CANCELLED" (Could be enum)
    *   `request_details: Dict[str, Any]` (JSONB) - Information sent to the user (e.g., question, context)
    *   `response_schema: Optional[Dict[str, Any]]` (JSONB) - Expected schema for the response
    *   `response_data: Optional[Dict[str, Any]]` (JSONB) - The actual response provided by the user
    *   `created_at: datetime`
    *   `responded_at: Optional[datetime]`
    *   `expires_at: Optional[datetime]`
    *   **Relationships:**
        *   `workflow_run: WorkflowRun` = Relationship()
        *   `assigned_user: Optional[User]` = Relationship()
        *   `organization: Organization` = Relationship()

*(Models for Notifications and HITL jobs are omitted for now but would follow similar principles, potentially linking to `WorkflowRun` and `User`)*

## 3. Data Storage Strategy (SQL vs. NoSQL)

*   **SQL (Postgres):** Manages core entities, relationships, ownership, status, and metadata as defined above (including `Workflow`, `WorkflowRun`, `Templates`, `UserNotification`, `HITLJob`). Suitable for structured data, transactions, and relational queries.
*   **NoSQL (MongoDB / Other):**
    *   **`WorkflowRunDetails` Collection:** Stores large, potentially unstructured or semi-structured data associated with a single `WorkflowRun`.
        *   Document ID could be `WorkflowRun.id` or stored in `WorkflowRun.detailed_results_ref`.
        *   Fields: `run_id`, `events` (array of execution events), `token_stream` (potentially large text or array), `intermediate_node_outputs` (map of node_id -> output), `full_final_output` (large JSON/text).
        *   Ideal for streaming data, large blobs, flexible schemas, and write-heavy logging during runs.

## 4. DAO Access Patterns

*   `WorkflowDAO`:
    *   `get(id)`
    *   `get_by_name(name, org_id)`
    *   `create(obj_in, owner_org_id, user_id)`
    *   `update(db_obj, obj_in, user_id)`
    *   `delete(id, owner_org_id)`
    *   `get_multi_by_org(org_id, skip, limit)`
*   `WorkflowRunDAO`:
    *   `get(id)`
    *   `create(obj_in, workflow_id, owner_org_id, user_id)`
    *   `update_status(id, status, ended_at=None, error_message=None)`
    *   `update_outputs(id, outputs, detailed_results_ref=None)`
    *   `get_multi_by_workflow(workflow_id, skip, limit, filters)`
    *   `get_multi_by_org(org_id, skip, limit, filters)`
*   `NodeTemplateDAO`:
    *   `get_by_name_version(name, version)`
    *   `get_latest_version(name)`
    *   `get_multi(launch_status=None, skip, limit)`
    *   `(Admin only) create/update/delete`
*   `PromptTemplateDAO` / `SchemaTemplateDAO`:
    *   `get_by_name_version(name, version, org_id=None)` (Checks org-specific then system)
    *   `get_multi_by_org(org_id, skip, limit)`
    *   `get_multi_system(skip, limit)`
    *   `create(obj_in, owner_org_id)`
    *   `update(db_obj, obj_in)`
    *   `delete(id, owner_org_id)`
*   `UserNotificationDAO`:
    *   `get(id)`
    *   `create(user_id, org_id, type, message, run_id=None)`
    *   `mark_as_read(id, user_id)`
    *   `mark_all_as_read(user_id, org_id)`
    *   `get_multi_by_user(user_id, org_id, is_read=None, skip, limit)`
*   `HITLJobDAO`:
    *   `get(id)`
    *   `create(run_id, org_id, details, schema=None, user_id=None, expires=None)`
    *   `update_response(id, response_data, user_id)`
    *   `update_status(id, status)`
    *   `get_pending_by_user(user_id, org_id, skip, limit)`
    *   `get_pending_by_run(run_id)`

## 5. Service Functionalities (`WorkflowService`)

*   `create_workflow(db, workflow_in, org_id, user_id)`: Validates input, creates `Workflow`.
*   `get_workflow(db, workflow_id, org_id)`: Fetches workflow, ensuring ownership.
*   `list_workflows(db, org_id)`: Lists workflows for the organization.
*   `update_workflow(db, workflow_id, update_data, org_id, user_id)`: Updates workflow.
*   `delete_workflow(db, workflow_id, org_id)`: Deletes workflow.
*   `start_workflow_run(db, workflow_id, run_inputs, org_id, user_id)`:
    *   Validates workflow exists and user has execute permission.
    *   Creates `WorkflowRun` record with `SCHEDULED` status.
    *   **(Future)** Sends job to execution engine (e.g., Prefect, Celery) or directly calls adapter. Returns `WorkflowRun` object (or just ID).
*   `get_run_status(db, run_id, org_id)`: Fetches run status, ensuring ownership.
*   `list_runs(db, org_id, workflow_id=None, filters=None)`: Lists runs for the org/workflow.
*   `get_run_details(db, nosql_db, run_id, org_id)`: Fetches summary from SQL and detailed stream/results from NoSQL.
*   `update_run_status(db, run_id, status, details)`: (Likely called internally by execution engine/adapter) Updates run status, potentially outputs/errors.
*   Template management functions (CRUD for Prompt/Schema, Get for Node).
*   `create_user_notification(db, user_id, org_id, type, message, run_id=None)`: Creates a new user notification.
*   `list_user_notifications(db, user_id, org_id, is_read=None, skip=0, limit=10)`: Lists user notifications.
*   `mark_notification_read(db, notification_id, user_id)`: Marks a notification as read.
*   `create_hitl_job(db, run_id, org_id, details, schema=None, user_id=None, expires=None)`: Creates a new HITL job.
*   `respond_to_hitl_job(db, job_id, response_data, user_id)`: Submits a response to a HITL job.
*   `get_pending_hitl_jobs_for_user(db, user_id, org_id, skip=0, limit=10)`: Lists pending HITL jobs for a user.

NOTE: for a user to be able to see data of other users or orgs hes' not part of; the user should be a super user (permissions)

### Nodes Listing
- List all nodes with all schemas (by default, gives all nodes other than experimental node, optional field filter: filter by launch status)

### Workflows
- create new workflow from graph schema
- fetch workflows (complete graph schema) Optional filters: owned by org ID, launch status etc

### Workflow Runs
- fetch last runs (filters: for workflow ID, by owner ORG ID, triggered by User ID, by Run status) ; optional parameters: offset and count (for pagination)
- submit workflow run (either a workflow ID or adhoc graph schema -> adhoc graph schema creates new workflow by default first)
- check status of run (status from workflow run model and completed nodes till now from mongo DB)
- fetch current stream for run (from mongo DB)
- fetch results of run -> final output if run finished and node outputs available till now

### HITL Jobs
- submit hitl job
    - validates using expected response JSON schema and triggers the workflow run again with HITL
- get jobs [all, pending only, by run ID, owned by org ID, assigned to this user, status == not cancelled] filters; ; optional parameters: offset and count (for pagination)
- set job as cancelled

### NOtifications
- retrieva all notifications sorted by most recent [filter: read, unread, all; optional parameters: offset and count]
- mark notification read

### Template/  SChemas TODO WIP!!!
#### basic APIs below:
- Create Template
- Retrive template
- List templates

### Websockets
- consume stream / queue and send to user websocket based on user_id in event schema if connected otherwise do nothing; Its already stored in DB so can just discard it and process next in queue / stream


## 6. API Routes (`/workflows`, `/runs`, `/templates`, `/notifications`, `/hitl`)

*(Permissions checked via dependencies)*

*   **Workflows** (`/api/v1/workflows`)
    *   `POST /`: Create Workflow (`WORKFLOW_CREATE` on active org) -> `schemas.WorkflowRead`
    *   `GET /`: List Workflows for active org (`WORKFLOW_READ` on active org) -> `List[schemas.WorkflowRead]`
    *   `GET /{workflow_id}`: Get Workflow details (`WORKFLOW_READ` on owning org) -> `schemas.WorkflowRead`
    *   `PUT /{workflow_id}`: Update Workflow (`WORKFLOW_UPDATE` on owning org) -> `schemas.WorkflowRead`
    *   `DELETE /{workflow_id}`: Delete Workflow (`WORKFLOW_DELETE` on owning org) -> `status 204`
    *   `POST /{workflow_id}/runs`: Start a new Workflow Run (`WORKFLOW_EXECUTE` on owning org) -> `schemas.WorkflowRunRead`
*   **Workflow Runs** (`/api/v1/runs`)
    *   `GET /`: List runs for active org (`RUN_READ` on active org, allows filtering by workflow_id) -> `List[schemas.WorkflowRunRead]`
    *   `GET /{run_id}`: Get run status and summary (`RUN_READ` on owning org) -> `schemas.WorkflowRunRead`
    *   `GET /{run_id}/details`: Get full run details (summary + NoSQL data) (`RUN_READ` on owning org) -> `schemas.WorkflowRunDetailRead` (custom schema combining SQL+NoSQL)
    *   `POST /{run_id}/cancel`: Cancel a running workflow (`WORKFLOW_EXECUTE` or specific `RUN_MANAGE` on owning org) -> `schemas.WorkflowRunRead`
    *   `POST /{run_id}/pause`: Pause a workflow (`WORKFLOW_EXECUTE` or specific `RUN_MANAGE` on owning org) -> `schemas.WorkflowRunRead`
    *   `POST /{run_id}/resume`: Resume a paused workflow (`WORKFLOW_EXECUTE` or specific `RUN_MANAGE` on owning org) -> `schemas.WorkflowRunRead`
*   **Templates** (`/api/v1/templates`)
    *   **Nodes:**
        *   `GET /nodes/`: List available Node Templates (`TEMPLATE_READ`) -> `List[schemas.NodeTemplateRead]`
        *   `GET /nodes/{name}/{version}`: Get specific Node Template (`TEMPLATE_READ`) -> `schemas.NodeTemplateRead`
    *   **Prompts:**
        *   `POST /prompts/`: Create org-specific Prompt Template (`TEMPLATE_CREATE` on active org) -> `schemas.PromptTemplateRead`
        *   `GET /prompts/`: List org + system Prompt Templates (`TEMPLATE_READ` on active org) -> `List[schemas.PromptTemplateRead]`
        *   `GET /prompts/{template_id}`: Get specific Prompt Template (`TEMPLATE_READ` on owning org / system) -> `schemas.PromptTemplateRead`
        *   `PUT /prompts/{template_id}`: Update org Prompt Template (`TEMPLATE_UPDATE` on owning org) -> `schemas.PromptTemplateRead`
        *   `DELETE /prompts/{template_id}`: Delete org Prompt Template (`TEMPLATE_DELETE` on owning org) -> `status 204`
    *   **Schemas:** (Similar CRUD as Prompts)
        *   `POST /schemas/`: Create org Schema Template (`TEMPLATE_CREATE` on active org) -> `schemas.SchemaTemplateRead`
        *   `GET /schemas/`: List org + system Schema Templates (`TEMPLATE_READ` on active org) -> `List[schemas.SchemaTemplateRead]`
        *   ... (GET by ID, PUT, DELETE)

*   **User Notifications** (`/api/v1/notifications`)
    *   `GET /`: List notifications for the current user in the active org (`USER_ACCESS`?) -> `List[schemas.UserNotificationRead]`
    *   `POST /{notification_id}/read`: Mark a specific notification as read (`USER_ACCESS`?) -> `status 200`
    *   `POST /read-all`: Mark all notifications as read for the user/org (`USER_ACCESS`?) -> `status 200`

*   **HITL Jobs** (`/api/v1/hitl`)
    *   `GET /pending`: List pending HITL jobs for the current user in the active org (`USER_ACCESS`?) -> `List[schemas.HITLJobRead]`
    *   `GET /{job_id}`: Get details of a specific HITL job (`USER_ACCESS`?) -> `schemas.HITLJobRead`
    *   `POST /{job_id}/respond`: Submit a response to a pending HITL job (`USER_ACCESS`?) -> `schemas.HITLJobRead`

*   **WebSockets** (`/ws`)
    *   `GET /ws/notifications/{user_id}`: WebSocket endpoint for real-time user notifications. Requires authentication/authorization to connect for the specific `user_id`.

## 7. Permissions (Defined in `constants.py`)

*   `WORKFLOW_CREATE`
*   `WORKFLOW_READ`
*   `WORKFLOW_UPDATE`
*   `WORKFLOW_DELETE`
*   `WORKFLOW_EXECUTE`
*   `RUN_READ`
*   `RUN_MANAGE` (Optional, for cancel/pause/resume if different from EXECUTE)
*   `TEMPLATE_READ` (Generic read for Node/Prompt/Schema)
*   `TEMPLATE_CREATE` (For org-specific Prompt/Schema)
*   `TEMPLATE_UPDATE` (For org-specific Prompt/Schema)
*   `TEMPLATE_DELETE` (For org-specific Prompt/Schema)
*   `TEMPLATE_MANAGE_SYSTEM` (Admin only, for Node Templates + system Prompt/Schema)
*   `NOTIFICATION_READ` (Implied by user login/access to org)
*   `HITL_READ` (Implied by user login/access to org)
*   `HITL_RESPOND` (Implied by user login/access to org)
*   `WEBSOCKET_CONNECT` (Implied by user login)

*(Permissions will be associated with Roles in the `auth` service setup)*

## 8. Real-time Notifications & Streaming Architecture

*   **Goal:** Provide real-time updates to the frontend about workflow run status changes, outputs, and HITL requests. Stream detailed run events (like token streams) for persistence and potential real-time display.
*   **Components:**
    *   **Workflow Execution Engine (e.g., LangGraph/Prefect Worker):** Publishes events during workflow execution.
    *   **RabbitMQ:** Message broker for decoupling publishers and consumers.
        *   **`workflow_events` Stream:** A persistent RabbitMQ Stream (configured with retention policies like `max-age` and `max-length-bytes` via `rabbitmqctl` or policies) used for all granular workflow events (token streams, intermediate results, state changes, logs). Messages contain `run_id`, `event_type`, `payload`, etc.
        *   **`user_notifications` Queue:** A standard RabbitMQ queue (likely direct exchange) for high-level notifications destined for specific users (e.g., "Run X Completed", "HITL Job Y needs attention"). Messages contain `user_id`, `org_id`, `notification_type`, `payload`.
    *   **FastAPI Backend:**
        *   **Event Consumer Service:** A background service (potentially part of the main FastAPI app or separate) responsible for consuming messages.
            *   *Consumes from `workflow_events` Stream:* Uses a RabbitMQ Streams client library (e.g., `stream-py`), tracks offsets (preferably using broker-side storage), parses messages by `run_id` and `event_type`, and persists detailed data to **MongoDB (`WorkflowRunDetails` collection)**.
            *   *Consumes from `user_notifications` Queue:* Uses a standard AMQP client (`aio-pika`), parses messages, persists the notification to the **PostgreSQL `UserNotification` table**, and attempts to push to relevant WebSocket connections.
        *   **WebSocket Manager:** Manages active WebSocket connections, mapping `user_id` to connected clients.
        *   **WebSocket Endpoint (`/ws/notifications/{user_id}`):** Allows authenticated users to establish a WebSocket connection.
*   **Flow:**
    1.  **Worker -> RabbitMQ:** Workflow engine publishes detailed events to `workflow_events` Stream and high-level user notifications to `user_notifications` Queue.
    2.  **RabbitMQ -> Consumer Service:** The consumer service reads from both the stream and the queue.
    3.  **Consumer -> Persistence:** Detailed events are written to MongoDB. User notifications are written to PostgreSQL.
    4.  **Consumer -> WebSocket Manager:** For user notifications, the consumer checks if the target `user_id` has active WebSocket connections and pushes the notification message.
    5.  **WebSocket Manager -> Client:** Sends real-time updates to connected frontend clients.
*   **Settings:**
    *   Add settings in `settings.py` for RabbitMQ stream/queue names, consumer group names, retention policies (for documentation/reference), and potentially MongoDB connection details for the event consumer.
*   **Key Considerations:**
    *   **Stream Client:** Requires a dedicated RabbitMQ Streams client library (not default `aio-pika`).
    *   **Offset Management:** Crucial for reliable stream consumption. Use broker-side offset storage.
    *   **Consumer Robustness:** Implement error handling, retries, and potentially scaling for the consumer service.
    *   **Idempotency:** Ensure database writes (Postgres/Mongo) are idempotent.
    *   **WebSocket Security:** Ensure only authenticated users can connect to their specific notification channel.
