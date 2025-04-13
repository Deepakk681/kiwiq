# PYTHONPATH=.:./services poetry run python /path/to/project/services/workflow_service/services/test_worker_job.py

import asyncio
import uuid
from typing import Dict, Any, Optional

# Assuming workflow_service and tests are importable
from workflow_service.config.constants import HITL_USER_PROMPT_KEY, HITL_USER_SCHEMA_KEY
from workflow_service.registry.nodes.llm.config import AnthropicModels, LLMModelProvider
from workflow_service.registry.registry import DBRegistry
from workflow_service.services.worker import trigger_workflow_run
from workflow_service.graph.graph import GraphSchema
# Import the function to create the graph schema
# Ensure the path is correct relative to your project structure/PYTHONPATH
from tests.unit.services.workflow_service.graph.runtime.tests.test_AI_loop import create_ai_loop_graph, human_review_handler, HumanReviewNode, AIGeneratorNode, ApprovalRouterNode, FinalProcessorNode
from workflow_service.registry.nodes.llm.tests.test_basic_llm_workflow import create_basic_llm_graph
from workflow_service.services.external_context_manager import register_node_templates, get_external_context_manager_with_clients
# --- Database and Schema Imports ---
from db.session import get_async_db_as_manager
from kiwi_app.workflow_app.crud import WorkflowDAO, WorkflowRunDAO
from kiwi_app.workflow_app.schemas import WorkflowCreate
from kiwi_app.workflow_app.constants import LaunchStatus


# async def register_test_nodes(db_registry: DBRegistry):
#     async with get_async_db_as_manager() as db:
#         await db_registry.register_node_template(db, HumanReviewNode)
#         await db_registry.register_node_template(db, AIGeneratorNode)
#         await db_registry.register_node_template(db, ApprovalRouterNode)
#         await db_registry.register_node_template(db, FinalProcessorNode)

async def deregister_test_nodes(db_registry: DBRegistry):
    async with get_async_db_as_manager() as db:
        await db_registry.deregister_node_template(db, HumanReviewNode)
        await db_registry.deregister_node_template(db, AIGeneratorNode)
        await db_registry.deregister_node_template(db, ApprovalRouterNode)
        await db_registry.deregister_node_template(db, FinalProcessorNode)


async def test_trigger_workflow_run() -> None:
    """
    Tests triggering a workflow run using the trigger_workflow_run helper.

    This test first ensures that the target Workflow object exists in the database,
    creating it if necessary using a predefined UUID and the AI loop graph schema.
    It then triggers the workflow run.
    """
    # register test nodes!
    external_context = await get_external_context_manager_with_clients()
    # NOTE: already registered in `db_node_register.py` !
    # await deregister_test_nodes(external_context.db_registry)
    # return

    # --- Define Test Parameters ---
    # Hardcoded UUIDs for testing. Replace with actual IDs from your test DB if needed.
    test_org_id: uuid.UUID = uuid.UUID("f8f9284f-c643-4672-b8a9-4fed8533a014")
    test_user_id: uuid.UUID = uuid.UUID("2b838ede-8d20-40cf-9086-ea54fe93139b")
    # Define a *fixed* Workflow ID for this test.
    # The test will create a workflow with this ID if it doesn't exist.
    test_workflow_id: uuid.UUID = uuid.UUID("a1b2c3d4-e5f6-7890-1234-567890abcdef") # Fixed ID for test workflow

    # Generate the graph schema from the test AI loop definition
    # test_graph_schema: GraphSchema = create_ai_loop_graph()
    # test_graph_schema: GraphSchema = create_ai_loop_graph()
    test_graph_schema: GraphSchema = create_basic_llm_graph(
        model_provider=LLMModelProvider.ANTHROPIC,
        model_name=AnthropicModels.CLAUDE_3_7_SONNET.value,
        output_type="text"
    )

    # Define inputs required by the AI loop graph
    test_inputs: Dict[str, Any] = {
        "user_prompt": "Generate a short creative story about a robot learning to paint."
    }

    # Optional parameters for the run trigger
    # NOTE: set these values if resuming after hitl
    test_resume_after_hitl: bool = False  # True
    test_run_id: Optional[uuid.UUID] = None  # "fb727ec4-e496-4abc-8bd5-53eaf524c2e4"  # MUST Be set to triggering run!
    # test_thread_id: Optional[uuid.UUID] = None   # Not required, autofetched when retrieving run!
    

    if test_resume_after_hitl:
        # assert test_thread_id is not None, "Thread ID must be provided if resuming after HITL"
        assert test_run_id is not None, "Run ID must be provided if resuming after HITL"
        # assert test_resume_inputs is not None, "Resume inputs must be provided if resuming after HITL"
        # logger.info(f"Resuming workflow after HITL for Run ID: {run_id}")
        # Fetch any pending HITL jobs for this run to process their responses
        async with get_async_db_as_manager() as db:
            # NOTE: this is sorted by descending created at, latest first!
            pending_hitl_jobs = await external_context.daos.hitl_job.get_pending_by_run(
                db=db, 
                requesting_run_id=test_run_id
            )
            pending_hitl_job = pending_hitl_jobs[0]
            hitl_user_prompt = pending_hitl_job.request_details
            hitl_response_schema = pending_hitl_job.response_schema
            interrupt_data = {
                HITL_USER_PROMPT_KEY: hitl_user_prompt,
                HITL_USER_SCHEMA_KEY: hitl_response_schema,
            }
            test_inputs = human_review_handler(interrupt_data)
            # if pending_hitl_jobs:
            #     # logger.info(f"Found {len(pending_hitl_jobs)} pending HITL jobs to process")
            #     for job in pending_hitl_jobs:
            #         # logger.info(f"Processing HITL job: {job.id}")
            #         # logger.info(f"Request details: {job.request_details}")
            #         # logger.info(f"Response schema: {job.response_schema}")
        # test_inputs = test_resume_inputs
    else:
        test_thread_id = uuid.uuid4() # random Langgraph thread ID

    # --- Ensure Workflow Exists in DB ---
    async with get_async_db_as_manager() as db:
        workflow_dao = WorkflowDAO()
        # Check if the workflow with the predefined ID exists
        # We use get() which is simpler than get_by_id_and_org for this check
        existing_workflow = await workflow_dao.get(db, id=test_workflow_id)

        if not existing_workflow:
            print(f"Workflow {test_workflow_id} not found. Creating...")
            # Prepare data for the new workflow
            workflow_data = WorkflowCreate(
                name="Test AI Loop Workflow (Created by Test)",
                description="Workflow created automatically for testing trigger_workflow_run.",
                # Serialize the GraphSchema object to a dictionary for storage
                graph_config=test_graph_schema.model_dump(mode='json'),
                is_template=False,
                launch_status=LaunchStatus.DEVELOPMENT
            )
            # Create the workflow using the DAO
            # Note: We are forcing the ID here by creating the model instance directly
            # This might bypass default ID generation if DAO's create doesn't handle it.
            # For testing with a fixed ID, this is often acceptable.
            # A more robust DAO might have create_with_id or update_or_create.
            new_workflow_obj = models.Workflow(
                id=test_workflow_id, # Set the fixed ID
                owner_org_id=test_org_id,
                created_by_user_id=test_user_id,
                **workflow_data.model_dump() # Get data from the schema
            )
            db.add(new_workflow_obj)
            await db.commit()
            await db.refresh(new_workflow_obj) # Refresh to load any DB defaults

            # created_workflow = await workflow_dao.create(
            #     db=db,
            #     obj_in=workflow_data,
            #     owner_org_id=test_org_id,
            #     user_id=test_user_id
            # )
            # # If create doesn't allow specifying ID, we'd need a different approach
            # # or assert that the created ID matches if we let it generate.
            # # For this test, assuming we want to use the fixed test_workflow_id.
            print(f"Workflow {test_workflow_id} created successfully.")
        else:
            print(f"Workflow {test_workflow_id} already exists. Ensuring graph config is up-to-date...")
            # Optional: Update the graph_config of the existing workflow if needed
            existing_workflow.graph_config = test_graph_schema.model_dump(mode='json')
            existing_workflow.name = "Test AI Loop Workflow (Updated by Test)" # Update name too
            db.add(existing_workflow)
            await db.commit()
            await db.refresh(existing_workflow)
            print(f"Updated existing workflow {test_workflow_id}.")
        
        # Create a new workflow run instance if this is not a resume
        # This is needed when run_id is None and we need to create a new run
        if test_run_id is not None:
            # We are probably resuming!
            assert test_resume_after_hitl, "if using an existing run_id, must set resume_after_hitl to True"
            existing_workflow_run = await external_context.daos.workflow_run.get_run_by_id_and_org(
                db=db,
                run_id=test_run_id,
                org_id=test_org_id
            )
            test_thread_id = existing_workflow_run.thread_id
            assert test_thread_id is not None, "Thread ID must be set for resuming workflow runs"
            assert existing_workflow_run is not None, "Workflow run must exist if run_id is provided"
        else:
            # We are creating a new run!
            new_workflow_run = await external_context.daos.workflow_run.create(
                db=db,
                workflow_id=test_workflow_id,
                owner_org_id=test_org_id,
                triggered_by_user_id=test_user_id,
                inputs=test_inputs,
                thread_id=test_thread_id
            )
            test_run_id = new_workflow_run.id

    # --- Trigger the Workflow Run (Now that Workflow is guaranteed to exist) ---
    print(f"\nTriggering workflow run with:")
    print(f"  Workflow ID: {test_workflow_id}")
    print(f"  Org ID: {test_org_id}")
    print(f"  User ID: {test_user_id}")
    print(f"  Run ID: {test_run_id}")
    print(f"  Inputs: {test_inputs}")

    triggered_run_id: uuid.UUID = await trigger_workflow_run(
        workflow_id=test_workflow_id,
        owner_org_id=test_org_id,
        triggered_by_user_id=test_user_id,
        inputs=test_inputs,
        run_id=test_run_id,
        thread_id=test_thread_id,
        graph_schema=test_graph_schema, # Pass the schema directly
        resume_after_hitl=test_resume_after_hitl,
    )

    print(f"\nSuccessfully triggered workflow run. Assigned Run ID: {triggered_run_id}")
    # Check if the returned run_id matches the one we provided (if any)
    if test_run_id:
        assert triggered_run_id == test_run_id, "Returned run_id should match provided run_id"

# --- Script Execution ---
if __name__ == "__main__":
    # Run the asynchronous test function
    print("Starting test workflow trigger...")
    # Need to import the actual model class for the direct creation approach
    from kiwi_app.workflow_app import models # Add this import
    asyncio.run(test_trigger_workflow_run())
    print("Test workflow trigger finished.")
