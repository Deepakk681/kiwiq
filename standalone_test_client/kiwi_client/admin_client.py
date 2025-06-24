"""
# poetry run python -m kiwi_client.admin_client

Admin API Test client for Admin endpoints (/auth/admin/*, etc.).

Provides admin functionality for managing users, organizations, and roles.
Requires superuser authentication.

Tests:
- List Users  
- Delete Users
- List Organizations
- Admin User Registration
- List User Organizations
- Create Roles
- And other admin operations
"""
import asyncio
import json
import httpx
import logging
import uuid
from typing import Dict, Any, Optional, List, Union, TypeVar, Tuple

# Import authenticated client and config
from kiwi_client.auth_client import AuthenticatedClient, AuthenticationError
from kiwi_client.test_config import (
    API_BASE_URL,
    CLIENT_LOG_LEVEL,
    # Admin URLs
    ADMIN_REGISTER_URL,
    ORGANIZATIONS_URL,
    ORG_DETAIL_URL,
)

# Import pydantic for validation
from pydantic import ValidationError, TypeAdapter

# Import schemas
from kiwi_client.schemas.auth_schemas import (
    UserAdminCreate,
    UserReadWithSuperuserStatus,
    UserDeleteRequest,
    OrganizationRead,
    UserReadWithOrgs,
    RoleCreate,
    RoleRead,
)

# Setup logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=CLIENT_LOG_LEVEL)

# Create TypeAdapters for validating lists of schemas
try:
    UserReadListAdapter = TypeAdapter(List[UserReadWithSuperuserStatus])
    OrganizationReadListAdapter = TypeAdapter(List[OrganizationRead])
except (AttributeError, NameError):
    logger.warning("TypeAdapter for admin schemas could not be created")
    UserReadListAdapter = None
    OrganizationReadListAdapter = None


class AdminClient:
    """
    Provides methods to test admin endpoints that require superuser privileges.
    
    This client wraps admin-only API endpoints for:
    - User management (list, create, delete users)
    - Organization management (list organizations)
    - Role management (create roles)
    - User organization relationships
    
    All methods require the authenticated user to have superuser privileges.
    """
    
    def __init__(self, auth_client: AuthenticatedClient):
        """
        Initializes the AdminClient.

        Args:
            auth_client (AuthenticatedClient): An authenticated client instance with superuser privileges.
        """
        self._auth_client = auth_client
        self._client: httpx.AsyncClient = auth_client.client
        logger.info("AdminClient initialized.")

    async def admin_register_user(
        self,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        is_verified: bool = True,
        is_superuser: bool = False
    ) -> Optional[UserReadWithSuperuserStatus]:
        """
        Register a new user with admin privileges.
        
        This method allows superusers to create new users with specified
        verification status and superuser privileges. Email verification
        is skipped for admin-created users.
        
        Args:
            email: Email address for the new user
            password: Password for the new user
            full_name: Optional full name for the user
            is_verified: Whether the user's email should be considered verified
            is_superuser: Whether the user should have superuser privileges
            
        Returns:
            Optional[UserReadWithSuperuserStatus]: The newly created user data or None on failure
        """
        logger.info(f"Admin registering new user: {email} (verified={is_verified}, superuser={is_superuser})")
        
        # Create user data using the UserAdminCreate schema
        user_data = UserAdminCreate(
            email=email,
            password=password,
            full_name=full_name,
            is_verified=is_verified,
            is_superuser=is_superuser
        ).model_dump()
        
        try:
            response = await self._client.post(ADMIN_REGISTER_URL, json=user_data)
            response.raise_for_status()
            response_json = response.json()
            
            # Validate the response against UserReadWithSuperuserStatus schema
            validated_user = UserReadWithSuperuserStatus.model_validate(response_json)
            logger.info(f"Successfully registered user {email} with admin privileges")
            logger.debug(f"Admin register response validated: {validated_user.model_dump_json(indent=2)}")
            return validated_user
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Error admin registering user {email}: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"Request error admin registering user {email}: {e}")
        except ValidationError as e:
            logger.error(f"Response validation error admin registering user {email}: {e}")
            logger.debug(f"Invalid response JSON: {response_json}")
        except Exception as e:
            logger.exception(f"Unexpected error admin registering user {email}")
            
        return None

    async def list_users(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> Optional[List[UserReadWithSuperuserStatus]]:
        """
        List all users in the system (admin interface).
        
        This endpoint is restricted to superusers only and provides a paginated
        list of all users with their superuser status.
        
        Args:
            skip: Number of users to skip (for pagination)
            limit: Maximum number of users to return (for pagination)
            
        Returns:
            Optional[List[UserReadWithSuperuserStatus]]: List of users or None on failure
        """
        logger.info(f"Admin listing users (skip={skip}, limit={limit})...")
        
        try:
            # The endpoint uses POST with query parameters
            params = {"skip": skip, "limit": limit}
            response = await self._client.post(f"{API_BASE_URL}/auth/admin/users", params=params)
            response.raise_for_status()
            response_json = response.json()
            
            # Validate the response list against List[UserReadWithSuperuserStatus]
            if UserReadListAdapter:
                validated_users = UserReadListAdapter.validate_python(response_json)
                logger.info(f"Successfully listed and validated {len(validated_users)} users.")
                logger.debug(f"List users response (first item): {validated_users[0].model_dump() if validated_users else 'None'}")
                return validated_users
            else:
                # Fallback if schemas weren't imported
                logger.warning("Schema validation skipped for list_users due to import failure.")
                return response_json
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Error listing users: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"Request error listing users: {e}")
        except ValidationError as e:
            logger.error(f"Response validation error listing users: {e}")
            logger.debug(f"Invalid response JSON: {response_json}")
        except Exception as e:
            logger.exception("Unexpected error listing users")
            
        return None

    async def delete_user(
        self,
        user_id: Optional[Union[str, uuid.UUID]] = None,
        email: Optional[str] = None
    ) -> bool:
        """
        Delete a user account (superuser only).
        
        This is a destructive operation that removes the user's personal data,
        organization memberships, and other associated data.
        
        Args:
            user_id: UUID of the user to delete (optional)
            email: Email of the user to delete (optional)
            
        Note: Either user_id or email must be provided.
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        if not user_id and not email:
            logger.error("Either user_id or email must be provided for user deletion")
            return False
        
        user_identifier = str(user_id) if user_id else email
        logger.info(f"Admin deleting user: {user_identifier}")
        
        # Create deletion request using the UserDeleteRequest schema
        delete_data = UserDeleteRequest(
            user_id=uuid.UUID(user_id) if user_id and isinstance(user_id, str) else user_id,
            email=email
        ).model_dump(exclude_none=True)  # Only include fields that were provided
        
        try:
            # For DELETE requests with JSON body, we use the request method
            response = await self._client.request(
                method="DELETE",
                url=f"{API_BASE_URL}/auth/admin/users",
                json=delete_data
            )
            response.raise_for_status()
            
            logger.info(f"Successfully deleted user: {user_identifier}")
            return True
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Error deleting user {user_identifier}: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"Request error deleting user {user_identifier}: {e}")
        except Exception as e:
            logger.exception(f"Unexpected error deleting user {user_identifier}")
            
        return False

    async def list_organizations(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> Optional[List[OrganizationRead]]:
        """
        List all organizations with pagination (admin interface).
        
        This endpoint provides a paginated list of all organizations in the system.
        
        Args:
            skip: Number of organizations to skip (for pagination)
            limit: Maximum number of organizations to return (for pagination)
            
        Returns:
            Optional[List[OrganizationRead]]: List of organizations or None on failure
        """
        logger.info(f"Admin listing organizations (skip={skip}, limit={limit})...")
        
        try:
            # The endpoint uses POST with query parameters
            params = {"skip": skip, "limit": limit}
            response = await self._client.post(f"{API_BASE_URL}/auth/admin/organizations", params=params)
            response.raise_for_status()
            response_json = response.json()
            
            # Validate the response list against List[OrganizationRead]
            if OrganizationReadListAdapter:
                validated_orgs = OrganizationReadListAdapter.validate_python(response_json)
                logger.info(f"Successfully listed and validated {len(validated_orgs)} organizations.")
                logger.debug(f"List organizations response (first item): {validated_orgs[0].model_dump() if validated_orgs else 'None'}")
                return validated_orgs
            else:
                # Fallback if schemas weren't imported
                logger.warning("Schema validation skipped for list_organizations due to import failure.")
                return response_json
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Error listing organizations: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"Request error listing organizations: {e}")
        except ValidationError as e:
            logger.error(f"Response validation error listing organizations: {e}")
            logger.debug(f"Invalid response JSON: {response_json}")
        except Exception as e:
            logger.exception("Unexpected error listing organizations")
            
        return None

    async def list_user_organizations(
        self,
        user_email: str
    ) -> Optional[UserReadWithOrgs]:
        """
        List all organizations a user is a member of, including their role.
        
        This is an admin endpoint that allows superusers to view any user's
        organization memberships and roles.
        
        Args:
            user_email: Email of the user to lookup
            
        Returns:
            Optional[UserReadWithOrgs]: User with organization details or None on failure
        """
        logger.info(f"Admin listing organizations for user: {user_email}")
        
        try:
            params = {"user_email": user_email}
            response = await self._client.get(f"{API_BASE_URL}/auth/admin/users/organizations", params=params)
            response.raise_for_status()
            response_json = response.json()
            
            # Validate the response against UserReadWithOrgs schema
            validated_user = UserReadWithOrgs.model_validate(response_json)
            logger.info(f"Successfully retrieved organizations for user {user_email}")
            logger.debug(f"User organizations response validated: {validated_user.model_dump_json(indent=2)}")
            return validated_user
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Error listing organizations for user {user_email}: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"Request error listing organizations for user {user_email}: {e}")
        except ValidationError as e:
            logger.error(f"Response validation error listing organizations for user {user_email}: {e}")
            logger.debug(f"Invalid response JSON: {response_json}")
        except Exception as e:
            logger.exception(f"Unexpected error listing organizations for user {user_email}")
            
        return None

    async def create_role(
        self,
        name: str,
        description: str,
        permissions: List[str]
    ) -> Optional[RoleRead]:
        """
        Create a new global role template (requires superuser).
        
        Creates a role template that can be used when assigning roles within organizations.
        Links the specified permissions by name.
        
        Args:
            name: Name of the role
            description: Description of the role
            permissions: List of permission names to associate with this role
            
        Returns:
            Optional[RoleRead]: The created role or None on failure
        """
        logger.info(f"Admin creating role: {name} with {len(permissions)} permissions")
        
        # Create role data using the RoleCreate schema
        role_data = RoleCreate(
            name=name,
            description=description,
            permissions=permissions
        ).model_dump()
        
        try:
            response = await self._client.post(f"{API_BASE_URL}/auth/admin/roles", json=role_data)
            response.raise_for_status()
            response_json = response.json()
            
            # Validate the response against RoleRead schema
            validated_role = RoleRead.model_validate(response_json)
            logger.info(f"Successfully created role: {name}")
            logger.debug(f"Create role response validated: {validated_role.model_dump_json(indent=2)}")
            return validated_role
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Error creating role {name}: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"Request error creating role {name}: {e}")
        except ValidationError as e:
            logger.error(f"Response validation error creating role {name}: {e}")
            logger.debug(f"Invalid response JSON: {response_json}")
        except Exception as e:
            logger.exception(f"Unexpected error creating role {name}")
            
        return None

    async def delete_organization(
        self,
        org_id: Union[str, uuid.UUID]
    ) -> bool:
        """
        Delete an organization and all its associated data (superuser only).
        
        This is a destructive operation that removes the organization,
        all user-organization links, and potentially other associated data.
        
        Args:
            org_id: UUID of the organization to delete
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        org_id_str = str(org_id)
        logger.info(f"Admin deleting organization: {org_id_str}")
        
        try:
            response = await self._client.delete(ORG_DETAIL_URL(org_id_str))
            response.raise_for_status()
            
            logger.info(f"Successfully deleted organization: {org_id_str}")
            return True
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Error deleting organization {org_id_str}: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"Request error deleting organization {org_id_str}: {e}")
        except Exception as e:
            logger.exception(f"Unexpected error deleting organization {org_id_str}")
            
        return False


# --- Example Usage --- (for testing this module directly)
async def main():
    """Demonstrates using the AdminClient for admin operations."""
    print("--- Starting Admin API Test ---")
    temp_user_email: Optional[str] = None
    temp_org_id: Optional[uuid.UUID] = None
    
    try:
        async with AuthenticatedClient() as auth_client:
            print("Authenticated as admin.")
            admin_client = AdminClient(auth_client)

            # Test 1: List Users
            print("\n1. Listing Users...")
            users = await admin_client.list_users(limit=5)
            if users:
                print(f"   Found {len(users)} users.")
                for user in users[:3]:  # Show first 3
                    print(f"   - {user.email} (ID: {user.id}, Superuser: {user.is_superuser})")
            else:
                print("   Failed to list users.")

            # Test 2: List Organizations  
            print("\n2. Listing Organizations...")
            orgs = await admin_client.list_organizations(limit=5)
            if orgs:
                print(f"   Found {len(orgs)} organizations.")
                for org in orgs[:3]:  # Show first 3
                    print(f"   - {org.name} (ID: {org.id})")
                    if not temp_org_id:  # Store first org for potential testing
                        temp_org_id = org.id
            else:
                print("   Failed to list organizations.")

            # Test 3: Create a Test User
            print("\n3. Creating Test User...")
            test_email = f"test_admin_user_{uuid.uuid4().hex[:8]}@example.com"
            created_user = await admin_client.admin_register_user(
                email=test_email,
                password="TestPassword123!",
                full_name="Test Admin User",
                is_verified=True,
                is_superuser=False
            )
            if created_user:
                temp_user_email = created_user.email
                print(f"   Successfully created test user: {created_user.email}")
                print(f"   User ID: {created_user.id}, Verified: {created_user.is_verified}")
            else:
                print("   Failed to create test user.")

            # Test 4: List User Organizations (if we have a user)
            if temp_user_email:
                print(f"\n4. Listing Organizations for User: {temp_user_email}")
                user_orgs = await admin_client.list_user_organizations(temp_user_email)
                if user_orgs:
                    print(f"   User has {len(user_orgs.organization_links)} organization memberships.")
                    for link in user_orgs.organization_links:
                        print(f"   - Org: {link.organization.name if link.organization else 'Unknown'}")
                        print(f"     Role: {link.role.name if link.role else 'Unknown'}")
                else:
                    print("   Failed to list user organizations or user has no org memberships.")

            # # Test 5: Create a Role
            # print("\n5. Creating Test Role...")
            # test_role_name = f"test_role_{uuid.uuid4().hex[:8]}"
            # created_role = await admin_client.create_role(
            #     name=test_role_name,
            #     description="Test role created by admin client",
            #     permissions=["org:view_members", "org:update"]  # Use valid permission names
            # )
            # if created_role:
            #     print(f"   Successfully created role: {created_role.name}")
            #     print(f"   Role ID: {created_role.id}, Permissions: {len(created_role.permissions)}")
            # else:
            #     print("   Failed to create test role.")

            # Test 6: Delete Test User (cleanup)
            if temp_user_email and created_user:
                print(f"\n6. Deleting Test User: {temp_user_email}")
                deleted = await admin_client.delete_user(email=temp_user_email)
                if deleted:
                    print("   Successfully deleted test user.")
                    temp_user_email = None  # Clear for cleanup
                else:
                    print("   Failed to delete test user.")

            # Note: We're not testing organization deletion as it's very destructive
            # and would require careful setup to avoid deleting important data
            print("\n   Note: Organization deletion test skipped (too destructive for demo)")

    except AuthenticationError as e:
        print(f"Authentication Error: {e}")
        print("Note: Admin endpoints require superuser privileges.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        logger.exception("Main test execution error:")
    finally:
        # Cleanup any remaining test data
        if temp_user_email:
            print(f"\nAttempting cleanup: Deleting test user {temp_user_email}...")
            try:
                async with AuthenticatedClient() as cleanup_auth_client:
                    cleanup_admin = AdminClient(cleanup_auth_client)
                    await cleanup_admin.delete_user(email=temp_user_email)
                    print("   Cleanup successful.")
            except Exception as cleanup_e:
                print(f"   Cleanup failed: {cleanup_e}")

        print("--- Admin API Test Finished ---")


if __name__ == "__main__":
    # Ensure API server is running and you're authenticated as a superuser
    # Run with: PYTHONPATH=. python -m kiwi_client.admin_client
    print("Running AdminClient test...")
    asyncio.run(main())
