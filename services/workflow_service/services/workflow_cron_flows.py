# PYTHONPATH=.:./services poetry run python /path/to/project/services/workflow_service/services/worker.py
import asyncio
import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Tuple, AsyncGenerator, Optional, List, Union, cast
# Prefect imports
from prefect import task
# from prefect.filesystems import S3, GitHub, LocalFileSystem
from prefect.cache_policies import NO_CACHE

from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import select
from db.session import get_async_session # Assuming this provides psycopg pool
from global_config.logger import get_prefect_or_regular_python_logger
from kiwi_app.auth import models as auth_models
from kiwi_app.auth import schemas as auth_schemas



# Local workflow service imports
from workflow_service.services.external_context_manager import (
    ExternalContextManager,
    get_external_context_manager_with_clients
)

# App state imports
from kiwi_app.workflow_app.app_state import (
    list_active_user_state_docnames_core,
    get_user_state,
)

# Export important functions for external use
__all__ = [
    'extract_active_entity_usernames_flow',
    'get_all_organizations_with_users',
    'get_active_entity_usernames_for_user_org_pairs',
]



@task(cache_policy=NO_CACHE)
async def extract_active_entity_usernames_flow(
    limit: Optional[int] = None,
    include_inactive_orgs: bool = False
) -> Dict[str, Any]:
    """
    Prefect flow to extract entity usernames from active app states for all user-org pairs.
    
    This flow is designed to run as a scheduled cron job to automatically collect
    all active entity usernames across all organizations and users. This data can
    be used for various purposes like scheduling content creation workflows,
    analytics, or user engagement tracking.
    
    Args:
        limit: Optional limit on number of org-user pairs to process (for testing)
        include_inactive_orgs: Whether to include inactive organizations
    
    Returns:
        Dict[str, Any]: Results including list of (org_id, user_id, entity_username) triplets
                       and processing statistics
    """
    logger = get_prefect_or_regular_python_logger(name="extract-active-entity-usernames-flow")
    
    logger.info("Starting active entity username extraction process")
    
    # Initialize external context manager
    external_context = await get_external_context_manager_with_clients()
    logger.info("External context manager initialized for entity username extraction")
    
    try:
        db_session = await get_async_session()
        
        # Task 1: Get all organizations with their users
        org_user_pairs = await get_all_organizations_with_users(
            db_session=db_session,
            limit=limit,
            include_inactive_orgs=include_inactive_orgs
        )
        
        logger.info(f"Found {len(org_user_pairs)} user-org pairs to process")
        
        # Task 2: Get entity usernames from active app states for all user-org pairs
        entity_username_triplets = await get_active_entity_usernames_for_user_org_pairs(
            external_context=external_context,
            db_session=db_session,
            org_user_pairs=org_user_pairs
        )
        
        logger.info(f"Extracted {len(entity_username_triplets)} entity username triplets")
        
        # Compile statistics
        org_count = len(set(triplet["org_id"] for triplet in entity_username_triplets))
        user_count = len(set(triplet["user_id"] for triplet in entity_username_triplets))
        unique_entity_usernames = len(set(triplet["entity_username"] for triplet in entity_username_triplets))
        
        # Group by organization for additional insights
        org_stats = {}
        for triplet in entity_username_triplets:
            org_id = triplet["org_id"]
            if org_id not in org_stats:
                org_stats[org_id] = {
                    "org_id": org_id,
                    "org_name": triplet.get("org_name", "Unknown"),
                    "users_with_active_states": set(),
                    "entity_usernames": set()
                }
            org_stats[org_id]["users_with_active_states"].add(triplet["user_id"])
            org_stats[org_id]["entity_usernames"].add(triplet["entity_username"])
        
        # Convert sets to counts for JSON serialization
        org_summary = []
        for org_id, stats in org_stats.items():
            org_summary.append({
                "org_id": org_id,
                "org_name": stats["org_name"],
                "users_with_active_states_count": len(stats["users_with_active_states"]),
                "unique_entity_usernames_count": len(stats["entity_usernames"])
            })
        
        # Create result summary
        result = {
            "status": "success",
            "executed_at": datetime.now(tz=timezone.utc).isoformat(),
            "processing_config": {
                "limit": limit,
                "include_inactive_orgs": include_inactive_orgs
            },
            "summary_statistics": {
                "total_org_user_pairs_processed": len(org_user_pairs),
                "total_entity_username_triplets": len(entity_username_triplets),
                "unique_organizations": org_count,
                "unique_users": user_count,
                "unique_entity_usernames": unique_entity_usernames
            },
            "organization_summary": org_summary,
            "entity_username_triplets": entity_username_triplets  # Full triplet data
        }
        
        logger.info(f"Entity username extraction completed successfully. Results: {json.dumps(result['summary_statistics'], indent=2)}")
        
        return result
        
    except Exception as e:
        logger.error(f"Entity username extraction flow failed: {e}", exc_info=True)
        
        # Return error information for monitoring
        error_result = {
            "status": "failed",
            "executed_at": datetime.now(tz=timezone.utc).isoformat(),
            "error_message": str(e),
            "summary_statistics": {
                "total_org_user_pairs_processed": 0,
                "total_entity_username_triplets": 0,
                "unique_organizations": 0,
                "unique_users": 0,
                "unique_entity_usernames": 0
            },
            "entity_username_triplets": []
        }
        
        # Re-raise the exception to ensure Prefect marks the flow as failed
        raise e
        
    finally:
        await db_session.close()
        # Clean up resources
        try:
            await external_context.close()
            logger.info("External context manager closed successfully")
        except Exception as close_err:
            logger.error(f"Error closing external context: {close_err}", exc_info=True)


@task(cache_policy=NO_CACHE)
async def get_all_organizations_with_users(
    db_session: AsyncSession,
    limit: Optional[int] = None,
    include_inactive_orgs: bool = False
) -> List[auth_schemas.UserOrganizationRoleReadWithUser]:
    """
    Get all organizations with their users using an optimized query.
    
    This function performs a single optimized query to fetch all organizations
    and their associated users with roles, avoiding N+1 query problems.
    
    Args:
        db_session: Database session
        limit: Optional limit on number of user-org pairs to process
        include_inactive_orgs: Whether to include inactive organizations
        
    Returns:
        List of UserOrganizationRoleReadWithUser schema objects containing
        complete user, organization, and role information
    """
    logger = get_prefect_or_regular_python_logger(name="get-all-organizations-with-users")
    
    try:
        # Build optimized query to get all org-user relationships in one query
        query = select(
            auth_models.Organization.id.label("org_id"),
            auth_models.Organization.name.label("org_name"),
            auth_models.Organization.is_active.label("org_is_active"),
            auth_models.User.id.label("user_id"),
            auth_models.User.email.label("user_email"),
            auth_models.User.full_name.label("user_full_name"),
            auth_models.User.is_active.label("user_is_active"),
            auth_models.User.is_verified.label("user_is_verified"),
            auth_models.Role.name.label("role_name")
        ).select_from(
            auth_models.Organization
        ).join(
            auth_models.UserOrganizationRole,
            auth_models.Organization.id == auth_models.UserOrganizationRole.organization_id
        ).join(
            auth_models.User,
            auth_models.UserOrganizationRole.user_id == auth_models.User.id
        ).join(
            auth_models.Role,
            auth_models.UserOrganizationRole.role_id == auth_models.Role.id
        )
        
        # Add filters
        if not include_inactive_orgs:
            query = query.where(auth_models.Organization.is_active == True)
            query = query.where(auth_models.User.is_active == True)
            # query = query.where(auth_models.Role.name != "client")
        
        # Add ordering for consistent results
        query = query.order_by(
            auth_models.Organization.created_at.desc(),
            auth_models.User.created_at.desc()
        )
        
        # Add limit if specified
        if limit:
            query = query.limit(limit)
        
        logger.info(f"Executing optimized query to get org-user pairs (limit={limit})")
        
        # Execute query
        result = await db_session.exec(query)
        raw_rows = result.fetchall()
        
        logger.info(f"Query returned {len(raw_rows)} org-user relationships")
        
        # Convert raw rows to schema objects
        org_user_pairs = []
        
        for row in raw_rows:
            try:
                # Create schema objects from raw row data
                user_schema = auth_schemas.UserRead(
                    id=row.user_id,
                    email=row.user_email,
                    full_name=row.user_full_name,
                    is_active=row.user_is_active,
                    is_verified=row.user_is_verified,
                    linkedin_id=None,  # Not selected in query
                    created_at=datetime.now(timezone.utc),  # Placeholder
                    updated_at=datetime.now(timezone.utc)   # Placeholder
                )
                
                org_schema = auth_schemas.OrganizationRead(
                    id=row.org_id,
                    name=row.org_name,
                    description=None,  # Not selected in query
                    primary_billing_email=None,  # Not selected in query
                    is_active=row.org_is_active,
                    created_at=datetime.now(timezone.utc),  # Placeholder
                    updated_at=datetime.now(timezone.utc)   # Placeholder
                )
                
                role_schema = auth_schemas.RoleRead(
                    id=uuid.uuid4(),  # Placeholder UUID
                    name=row.role_name,
                    description=None,  # Not selected in query
                    is_system_role=False,  # Default
                    created_at=datetime.now(timezone.utc),  # Placeholder
                    updated_at=datetime.now(timezone.utc)   # Placeholder
                )
                
                user_org_role_schema = auth_schemas.UserOrganizationRoleReadWithUser(
                    user=user_schema,
                    organization=org_schema,
                    role=role_schema,
                    created_at=datetime.now(timezone.utc)  # Placeholder
                )
                
                org_user_pairs.append(user_org_role_schema)
                
            except Exception as schema_err:
                logger.warning(f"Could not convert row to schema object: {schema_err}")
                continue
        
        # Log statistics
        unique_orgs = len(set(str(pair.organization.id) for pair in org_user_pairs))
        unique_users = len(set(str(pair.user.id) for pair in org_user_pairs))
        
        logger.info(
            f"Processed {len(org_user_pairs)} org-user pairs across "
            f"{unique_orgs} organizations and {unique_users} users"
        )
        
        return org_user_pairs
        
    except Exception as e:
        logger.error(f"Error getting organizations with users: {e}", exc_info=True)
        raise


@task(cache_policy=NO_CACHE)
async def get_active_entity_usernames_for_user_org_pairs(
    external_context: ExternalContextManager,
    db_session: AsyncSession,
    org_user_pairs: List[auth_schemas.UserOrganizationRoleReadWithUser]
) -> List[Dict[str, Any]]:
    """
    Get entity usernames from active app states for all user-org pairs.
    
    This function processes each user-org pair to find their active app states
    and extracts the entity_username field using the get_user_state function
    from app_state.py, creating the final triplets directly.
    
    Args:
        external_context: ExternalContextManager for accessing services
        db_session: Database session
        org_user_pairs: List of UserOrganizationRoleReadWithUser schema objects
        
    Returns:
        List of dictionaries containing entity username triplets:
        [
            {
                "org_id": str,
                "org_name": str,
                "user_id": str,
                "user_email": str,
                "user_full_name": str,
                "entity_username": str,
                "docname": str,
                "linkedin_profile_url": str (optional)
            },
            ...
        ]
    """
    logger = get_prefect_or_regular_python_logger(name="get-active-entity-usernames-for-user-org-pairs")
    
    entity_username_triplets = []
    
    try:
        # Process each user-org pair to find active app states
        for i, pair in enumerate(org_user_pairs):
            try:
                org_id = pair.organization.id
                user_id = pair.user.id
                
                # Create a User model object for compatibility with existing functions
                user_obj = auth_schemas.UserReadWithSuperuserStatus(
                    id=user_id,
                    email=pair.user.email,
                    full_name=pair.user.full_name,
                    is_active=pair.user.is_active,
                    is_verified=pair.user.is_verified,
                    is_superuser=False,  # superuser priviledges not required here!
                    linkedin_id=pair.user.linkedin_id,
                    created_at=pair.user.created_at,
                    updated_at=pair.user.updated_at
                )
                
                # Get active app state document names for this user-org pair
                active_docnames_response = await list_active_user_state_docnames_core(
                    active_org_id=org_id,
                    current_user=user_obj,
                    service=external_context.customer_data_service,
                    logger=logger,
                    on_behalf_of_user_id=None
                )
                
                # For each active document, get the entity_username using the app_state function
                for docname in active_docnames_response.active_docnames:
                    try:
                        # Use the get_user_state function to get just the entity_username field
                        user_state_response = await get_user_state(
                            docname=docname,
                            paths_to_get_str="entity_username,linkedin_profile_url",  # Get both entity_username and linkedin_profile_url
                            active_org_id=org_id,
                            current_user=user_obj,
                            service=external_context.customer_data_service,
                            logger=logger,
                            on_behalf_of_user_id=None
                        )
                        
                        # Extract entity_username from the response
                        entity_username = user_state_response.retrieved_states.get("entity_username")
                        linkedin_profile_url = user_state_response.retrieved_states.get("linkedin_profile_url")
                        
                        if entity_username:
                            # Create the final entity username triplet directly
                            triplet = {
                                "org_id": str(pair.organization.id),
                                "org_name": pair.organization.name,
                                "user_id": str(pair.user.id),
                                "user_email": pair.user.email,
                                "user_full_name": pair.user.full_name,
                                "entity_username": entity_username,
                                "docname": docname,
                                "user": user_obj,
                            }
                            
                            # Add optional linkedin_profile_url if available
                            if linkedin_profile_url:
                                triplet["linkedin_profile_url"] = linkedin_profile_url
                            
                            entity_username_triplets.append(triplet)
                            
                            logger.debug(f"Extracted entity username '{entity_username}' for user {pair.user.email} in org {pair.organization.name}")
                        else:
                            logger.warning(f"No entity_username found in app state for user {pair.user.email} (docname: {docname})")
                            
                    except Exception as doc_err:
                        logger.warning(f"Could not retrieve entity_username from app state document {docname} for user {pair.user.email}: {doc_err}")
                        continue
                        
            except Exception as pair_err:
                logger.warning(f"Error processing user-org pair {i+1}: {pair_err}")
                continue
        
        logger.info(f"Extracted {len(entity_username_triplets)} entity username triplets")
        
        return entity_username_triplets
        
    except Exception as e:
        logger.error(f"Error getting entity usernames for user-org pairs: {e}", exc_info=True)
        raise

async def main():
    res = await extract_active_entity_usernames_flow()
    print(json.dumps(res, indent=2))
    import ipdb; ipdb.set_trace()

if __name__ == "__main__":
    asyncio.run(main())
