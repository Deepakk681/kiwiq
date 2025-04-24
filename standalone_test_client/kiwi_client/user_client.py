# -*- coding: utf-8 -*-
"""
Client for interacting with User and Organization Management endpoints in the KiwiQ API.
"""

import asyncio
import json
import httpx
import logging
import uuid
from typing import Dict, Any, Optional, List, Union

# Import pydantic for validation
from pydantic import ValidationError, TypeAdapter

# Import authenticated client and config
from kiwi_client.auth_client import AuthenticatedClient, AuthenticationError
# Import schemas from the auth app (adjust path if necessary)
from kiwi_client.schemas import auth_schemas as schemas

# Import base URL from config (assuming it's defined there)
from kiwi_client.test_config import API_BASE_URL, CLIENT_LOG_LEVEL

# Setup logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=CLIENT_LOG_LEVEL)

# --- API Endpoint Paths ---
# Define constants for the API paths relative to the base API URL
# These correspond to the routes defined in kiwi_app/auth/routers.py
USERS_ME_URL = "/auth/users/me"
USERS_ME_ORGS_URL = "/auth/users/me/organizations"
ORGANIZATIONS_URL = "/auth/organizations"
ORGANIZATION_DETAIL_URL = lambda org_id: f"{ORGANIZATIONS_URL}/{org_id}"
ORGANIZATION_USERS_URL = lambda org_id: f"{ORGANIZATION_DETAIL_URL(org_id)}/users"
USERS_URL = "/auth/users" # Admin endpoint for listing/deleting users

# --- Pydantic Type Adapters for List Validation ---
OrganizationReadListAdapter = TypeAdapter(List[schemas.OrganizationRead])
UserReadWithSuperuserStatusListAdapter = TypeAdapter(List[schemas.UserReadWithSuperuserStatus])
UserOrganizationRoleReadWithUserListAdapter = TypeAdapter(List[schemas.UserOrganizationRoleReadWithUser])


class UserTestClient:
    """
    Provides methods to test the User and Organization Management endpoints.
    Uses schemas from kiwi_app.auth.schemas for requests and response validation.
    """

    def __init__(self, auth_client: AuthenticatedClient):
        """
        Initializes the UserTestClient.

        Args:
            auth_client (AuthenticatedClient): An instance of AuthenticatedClient, assumed to be logged in.
        """
        self._auth_client: AuthenticatedClient = auth_client
        # Use the authenticated httpx client instance
        self._client: httpx.AsyncClient = auth_client.client
        logger.info("UserTestClient initialized.")

    async def get_current_user(self) -> Optional[schemas.UserReadWithSuperuserStatus]:
        """
        Fetches the details of the currently authenticated user.
        Corresponds to the `read_users_me_endpoint` (GET /auth/users/me).

        Returns:
            Optional[schemas.UserReadWithSuperuserStatus]: The parsed and validated user details,
                                                            or None on failure.
        """
        logger.info("Attempting to get current user details (/users/me)...")
        try:
            response = await self._client.get(USERS_ME_URL)
            response.raise_for_status() # Raise exception for non-2xx codes
            response_json = response.json()

            # Validate the response against the UserReadWithSuperuserStatus schema
            validated_user = schemas.UserReadWithSuperuserStatus.model_validate(response_json)
            logger.info(f"Successfully retrieved current user: {validated_user.email}")
            logger.debug(f"Get current user response validated: {validated_user.model_dump_json(indent=2)}")
            return validated_user
        except httpx.HTTPStatusError as e:
            logger.error(f"Error getting current user: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"Request error getting current user: {e}")
        except ValidationError as e:
             logger.error(f"Response validation error getting current user: {e}")
             logger.debug(f"Invalid response JSON: {response_json if 'response_json' in locals() else 'No response JSON'}")
        except Exception as e:
            logger.exception("Unexpected error getting current user.")
        return None

    async def update_current_user(self, update_data: schemas.UserUpdate) -> Optional[schemas.UserRead]:
        """
        Updates the details of the currently authenticated user.
        Corresponds to the `update_users_me_endpoint` (PATCH /auth/users/me).

        Args:
            update_data (schemas.UserUpdate): An object containing the fields to update (e.g., full_name).

        Returns:
            Optional[schemas.UserRead]: The parsed and validated updated user details,
                                        or None on failure.
        """
        logger.info("Attempting to update current user details (/users/me)...")
        payload = update_data.model_dump(exclude_unset=True) # Only send fields that are set
        try:
            response = await self._client.patch(USERS_ME_URL, json=payload)
            response.raise_for_status() # Raise exception for non-2xx codes
            response_json = response.json()

            # Validate the response against the UserRead schema
            validated_user = schemas.UserRead.model_validate(response_json)
            logger.info(f"Successfully updated current user: {validated_user.email}")
            logger.debug(f"Update current user response validated: {validated_user.model_dump_json(indent=2)}")
            return validated_user
        except httpx.HTTPStatusError as e:
            logger.error(f"Error updating current user: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"Request error updating current user: {e}")
        except ValidationError as e:
             logger.error(f"Response validation error updating current user: {e}")
             logger.debug(f"Invalid response JSON: {response_json if 'response_json' in locals() else 'No response JSON'}")
        except Exception as e:
            logger.exception("Unexpected error updating current user.")
        return None

    async def list_my_organizations(self) -> Optional[schemas.UserReadWithOrgs]:
        """
        Fetches the organizations the current user is a member of, including their roles.
        Corresponds to the `list_my_organizations` endpoint (GET /auth/users/me/organizations).

        Returns:
            Optional[schemas.UserReadWithOrgs]: The parsed user details including organization links,
                                                 or None on failure.
        """
        logger.info("Attempting to list organizations for current user (/users/me/organizations)...")
        try:
            response = await self._client.get(USERS_ME_ORGS_URL)
            response.raise_for_status() # Raise exception for non-2xx codes
            response_json = response.json()

            # Validate the response against the UserReadWithOrgs schema
            validated_data = schemas.UserReadWithOrgs.model_validate(response_json)
            org_count = len(validated_data.organization_links)
            logger.info(f"Successfully retrieved {org_count} organizations for user: {validated_data.email}")
            logger.debug(f"List my organizations response validated: {validated_data.model_dump_json(indent=2)}")
            return validated_data
        except httpx.HTTPStatusError as e:
            logger.error(f"Error listing user organizations: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"Request error listing user organizations: {e}")
        except ValidationError as e:
             logger.error(f"Response validation error listing user organizations: {e}")
             logger.debug(f"Invalid response JSON: {response_json if 'response_json' in locals() else 'No response JSON'}")
        except Exception as e:
            logger.exception("Unexpected error listing user organizations.")
        return None

    async def create_organization(self, org_data: schemas.OrganizationCreate) -> Optional[schemas.OrganizationRead]:
        """
        Creates a new organization. The creator is automatically assigned as admin.
        Corresponds to the `create_organization_endpoint` (POST /auth/organizations).

        Args:
            org_data (schemas.OrganizationCreate): Data for the new organization (name, description).

        Returns:
            Optional[schemas.OrganizationRead]: The parsed and validated details of the created organization,
                                                or None on failure.
        """
        logger.info(f"Attempting to create organization: {org_data.name}...")
        payload = org_data.model_dump()
        try:
            # Endpoint returns 201 Created
            response = await self._client.post(ORGANIZATIONS_URL, json=payload)

            if response.status_code != 201:
                logger.error(f"Error creating organization: Status {response.status_code} - {response.text}")
                response.raise_for_status() # Raise non-201 codes

            response_json = response.json()

            # Validate the response against the OrganizationRead schema
            validated_org = schemas.OrganizationRead.model_validate(response_json)
            logger.info(f"Successfully created organization: {validated_org.name} (ID: {validated_org.id})")
            logger.debug(f"Create organization response validated: {validated_org.model_dump_json(indent=2)}")
            return validated_org
        except httpx.HTTPStatusError as e:
            # Logged above if status code wasn't 201
            logger.debug(f"HTTP Status Error Detail: {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"Request error creating organization: {e}")
        except ValidationError as e:
            logger.error(f"Response validation error creating organization: {e}")
            logger.debug(f"Invalid response JSON: {response_json if 'response_json' in locals() else 'No response JSON'}")
        except Exception as e:
            logger.exception(f"Unexpected error creating organization '{org_data.name}'.")
        return None

    async def list_organization_users(self, org_id: Union[str, uuid.UUID]) -> Optional[List[schemas.UserOrganizationRoleReadWithUser]]:
        """
        Gets all users in a specific organization with their roles.
        Requires 'org:view_members' permission in the organization.
        Corresponds to `get_organization_users_endpoint` (GET /auth/organizations/{org_id}/users).

        Args:
            org_id (Union[str, uuid.UUID]): The ID of the organization.

        Returns:
            Optional[List[schemas.UserOrganizationRoleReadWithUser]]: List of users with roles, or None on failure.
        """
        org_id_str = str(org_id)
        url = ORGANIZATION_USERS_URL(org_id_str)
        logger.info(f"Attempting to list users for organization ID: {org_id_str}...")
        try:
            response = await self._client.get(url)
            response.raise_for_status()
            response_json = response.json()

            # Validate the list response
            validated_users = UserOrganizationRoleReadWithUserListAdapter.validate_python(response_json)
            logger.info(f"Successfully listed {len(validated_users)} users for organization {org_id_str}.")
            # logger.debug(f"List organization users response validated: {validated_users}") # Can be verbose
            return validated_users
        except httpx.HTTPStatusError as e:
            logger.error(f"Error listing org users for {org_id_str}: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"Request error listing org users for {org_id_str}: {e}")
        except ValidationError as e:
             logger.error(f"Response validation error listing org users for {org_id_str}: {e}")
             logger.debug(f"Invalid response JSON: {response_json if 'response_json' in locals() else 'No response JSON'}")
        except Exception as e:
            logger.exception(f"Unexpected error listing users for organization {org_id_str}.")
        return None

    async def add_user_to_organization(self, org_id: Union[str, uuid.UUID], assignment: schemas.UserAssignRole) -> Optional[schemas.UserOrganizationRoleReadWithUser]:
        """
        Assigns a role to a user within a specific organization.
        Requires 'org:manage_members' permission in the organization.
        Corresponds to `add_user_to_organization_endpoint` (POST /auth/organizations/{org_id}/users).

        Args:
            org_id (Union[str, uuid.UUID]): The ID of the organization.
            assignment (schemas.UserAssignRole): Details of the user (email) and role (name) to assign.

        Returns:
            Optional[schemas.UserOrganizationRoleReadWithUser]: The details of the created user-org link, or None on failure.
        """
        org_id_str = str(org_id)
        url = ORGANIZATION_USERS_URL(org_id_str)
        payload = assignment.model_dump()
        logger.info(f"Attempting to add user '{assignment.user_email}' with role '{assignment.role_name}' to organization {org_id_str}...")
        try:
            # Endpoint returns 201 Created
            response = await self._client.post(url, json=payload)

            if response.status_code != 201:
                logger.error(f"Error adding user to organization: Status {response.status_code} - {response.text}")
                response.raise_for_status()

            response_json = response.json()
            # Validate the response against UserOrganizationRoleReadWithUser schema
            validated_link = schemas.UserOrganizationRoleReadWithUser.model_validate(response_json)
            logger.info(f"Successfully added user '{validated_link.user.email}' to organization '{validated_link.organization.name}' with role '{validated_link.role.name}'.")
            logger.debug(f"Add user response validated: {validated_link.model_dump_json(indent=2)}")
            return validated_link
        except httpx.HTTPStatusError as e:
            logger.debug(f"HTTP Status Error Detail: {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"Request error adding user to organization {org_id_str}: {e}")
        except ValidationError as e:
            logger.error(f"Response validation error adding user to org {org_id_str}: {e}")
            logger.debug(f"Invalid response JSON: {response_json if 'response_json' in locals() else 'No response JSON'}")
        except Exception as e:
            logger.exception(f"Unexpected error adding user to organization {org_id_str}.")
        return None

    async def remove_user_from_organization(self, org_id: Union[str, uuid.UUID], removal: schemas.UserRemoveRole) -> bool:
        """
        Removes a user from an organization.
        Requires 'org:manage_members' permission in the organization.
        Corresponds to `remove_user_from_organization_endpoint` (DELETE /auth/organizations/{org_id}/users).

        Args:
            org_id (Union[str, uuid.UUID]): The ID of the organization.
            removal (schemas.UserRemoveRole): Details of the user (email) and organization (id) to remove link for.
                                             Note: org_id in path takes precedence, but schema includes it for potential validation.

        Returns:
            bool: True if removal was successful (status 204), False otherwise.
        """
        org_id_str = str(org_id)
        url = ORGANIZATION_USERS_URL(org_id_str)
        # The DELETE request body contains the user details
        payload = removal.model_dump()
        logger.info(f"Attempting to remove user '{removal.user_email}' from organization {org_id_str}...")

        # Basic check: Ensure the org_id in the path matches the one in the payload if provided
        if removal.organization_id and uuid.UUID(org_id_str) != removal.organization_id:
             logger.error(f"Organization ID mismatch: Path '{org_id_str}' vs Body '{removal.organization_id}'. Aborting.")
             # Mimic potential API 400 Bad Request
             # raise ValueError("Organization ID in path and body mismatch.") # Or just return False
             return False

        try:
            # Endpoint returns 204 No Content on success
            response = await self._client.request("DELETE", url, json=payload) # Use request method for DELETE with body

            if response.status_code == 204:
                logger.info(f"Successfully removed user '{removal.user_email}' from organization {org_id_str}.")
                return True
            else:
                logger.error(f"Error removing user from organization {org_id_str}: Status {response.status_code} - {response.text}")
                # Attempt to raise for status to reveal more info if available
                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError as nested_e:
                    logger.debug(f"HTTP Status Error Detail: {nested_e.response.text}")
                return False
        except httpx.RequestError as e:
            logger.error(f"Request error removing user from organization {org_id_str}: {e}")
        except Exception as e:
            logger.exception(f"Unexpected error removing user from organization {org_id_str}.")
        return False

    async def delete_organization(self, org_id: Union[str, uuid.UUID]) -> bool:
        """
        Deletes an organization. Requires superuser or appropriate permissions.
        Corresponds to `delete_organization_endpoint` (DELETE /auth/organizations/{org_id}).

        Args:
            org_id (Union[str, uuid.UUID]): The ID of the organization to delete.

        Returns:
            bool: True if deletion was successful (status 204), False otherwise.
        """
        org_id_str = str(org_id)
        url = ORGANIZATION_DETAIL_URL(org_id_str)
        logger.info(f"Attempting to delete organization ID: {org_id_str}...")
        try:
            # Endpoint returns 204 No Content on success
            response = await self._client.delete(url)

            if response.status_code == 204:
                logger.info(f"Successfully deleted organization {org_id_str}.")
                return True
            else:
                logger.error(f"Error deleting organization {org_id_str}: Status {response.status_code} - {response.text}")
                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError as nested_e:
                    logger.debug(f"HTTP Status Error Detail: {nested_e.response.text}")
                return False
        except httpx.RequestError as e:
            logger.error(f"Request error deleting organization {org_id_str}: {e}")
        except Exception as e:
            logger.exception(f"Unexpected error deleting organization {org_id_str}.")
        return False

    # --- Admin Endpoints ---

    async def list_all_organizations(self, skip: int = 0, limit: int = 100) -> Optional[List[schemas.OrganizationRead]]:
        """
        Lists all organizations in the system (Admin/Superuser only).
        Corresponds to `list_organizations_endpoint` (GET /auth/organizations).

        Args:
            skip (int): Number of organizations to skip.
            limit (int): Maximum number of organizations to return.

        Returns:
            Optional[List[schemas.OrganizationRead]]: List of organizations, or None on failure.
        """
        logger.info(f"Attempting to list all organizations (skip={skip}, limit={limit})...")
        params = {"skip": skip, "limit": limit}
        try:
            response = await self._client.get(ORGANIZATIONS_URL, params=params)
            response.raise_for_status()
            response_json = response.json()

            # Validate the list response
            validated_orgs = OrganizationReadListAdapter.validate_python(response_json)
            logger.info(f"Successfully listed {len(validated_orgs)} organizations (admin).")
            return validated_orgs
        except httpx.HTTPStatusError as e:
            logger.error(f"Error listing all organizations: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"Request error listing all organizations: {e}")
        except ValidationError as e:
             logger.error(f"Response validation error listing all organizations: {e}")
             logger.debug(f"Invalid response JSON: {response_json if 'response_json' in locals() else 'No response JSON'}")
        except Exception as e:
            logger.exception("Unexpected error listing all organizations.")
        return None

    async def list_all_users(self, skip: int = 0, limit: int = 100) -> Optional[List[schemas.UserReadWithSuperuserStatus]]:
        """
        Lists all users in the system (Admin/Superuser only).
        Corresponds to `list_users_endpoint` (GET /auth/users).

        Args:
            skip (int): Number of users to skip.
            limit (int): Maximum number of users to return.

        Returns:
            Optional[List[schemas.UserReadWithSuperuserStatus]]: List of users, or None on failure.
        """
        logger.info(f"Attempting to list all users (skip={skip}, limit={limit})...")
        params = {"skip": skip, "limit": limit}
        try:
            response = await self._client.get(USERS_URL, params=params)
            response.raise_for_status()
            response_json = response.json()

            # Validate the list response
            validated_users = UserReadWithSuperuserStatusListAdapter.validate_python(response_json)
            logger.info(f"Successfully listed {len(validated_users)} users (admin).")
            return validated_users
        except httpx.HTTPStatusError as e:
            logger.error(f"Error listing all users: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"Request error listing all users: {e}")
        except ValidationError as e:
             logger.error(f"Response validation error listing all users: {e}")
             logger.debug(f"Invalid response JSON: {response_json if 'response_json' in locals() else 'No response JSON'}")
        except Exception as e:
            logger.exception("Unexpected error listing all users.")
        return None

    async def delete_user_account(self, delete_request: schemas.UserDeleteRequest) -> bool:
        """
        Deletes a user account (Admin/Superuser only).
        Corresponds to `delete_user_account_endpoint` (DELETE /auth/users).

        Args:
            delete_request (schemas.UserDeleteRequest): Details of the user to delete (email or user_id).

        Returns:
            bool: True if deletion was successful (status 204), False otherwise.
        """
        identifier = delete_request.email or str(delete_request.user_id)
        logger.info(f"Attempting to delete user account: {identifier} (admin)...")
        payload = delete_request.model_dump(exclude_unset=True)
        try:
             # Endpoint returns 204 No Content on success
            # DELETE requests can have bodies, use .request()
            response = await self._client.request("DELETE", USERS_URL, json=payload)

            if response.status_code == 204:
                logger.info(f"Successfully deleted user account {identifier} (admin).")
                return True
            else:
                logger.error(f"Error deleting user account {identifier}: Status {response.status_code} - {response.text}")
                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError as nested_e:
                    logger.debug(f"HTTP Status Error Detail: {nested_e.response.text}")
                return False
        except httpx.RequestError as e:
            logger.error(f"Request error deleting user account {identifier}: {e}")
        except Exception as e:
            logger.exception(f"Unexpected error deleting user account {identifier}.")
        return False

# --- Example Usage Placeholder ---
# You would typically import this client into another test script (like run_client.py's main)
# and use it after authenticating.
async def main():
    print("--- User/Org Client Example Usage (requires running API and auth) ---")
    # This is a placeholder demonstration. Real usage requires authentication.
    try:
        async with AuthenticatedClient() as auth_client: # Authenticate using env vars or config
            print("Authenticated successfully.")
            user_client = UserTestClient(auth_client)

            # 1. Get current user
            print("\n1. Getting current user...")
            current_user = await user_client.get_current_user()
            if current_user:
                print(f"   Current user: {current_user.email} (ID: {current_user.id})")
                user_id_for_delete = current_user.id # Save for potential delete test if needed

                # 2. Update current user's full name
                print("\n2. Updating current user's full name...")
                updated_user = await user_client.update_current_user(
                    schemas.UserUpdate(full_name=f"Test User Updated {uuid.uuid4().hex[:6]}")
                )
                if updated_user:
                    print(f"   Updated user name: {updated_user.full_name}")

                # 3. List user's organizations
                print("\n3. Listing current user's organizations...")
                user_with_orgs = await user_client.list_my_organizations()
                if user_with_orgs:
                    print(f"   User belongs to {len(user_with_orgs.organization_links)} organizations.")
                    for link in user_with_orgs.organization_links:
                        print(f"     - Org: {link.organization.name} (ID: {link.organization.id}), Role: {link.role.name}")

                # 4. Create a new organization
                print("\n4. Creating a new organization...")
                org_name = f"Test Org {uuid.uuid4().hex[:6]}"
                created_org = await user_client.create_organization(
                    schemas.OrganizationCreate(name=org_name, description="Created by test client")
                )
                org_id_to_manage = None
                if created_org:
                    print(f"   Created organization: {created_org.name} (ID: {created_org.id})")
                    org_id_to_manage = created_org.id

                    # 5. List users in the new organization (should only be the creator)
                    print(f"\n5. Listing users in organization {created_org.name}...")
                    org_users = await user_client.list_organization_users(org_id=created_org.id)
                    if org_users:
                        print(f"   Found {len(org_users)} user(s):")
                        for link in org_users:
                            print(f"     - User: {link.user.email}, Role: {link.role.name}")

                    # --- !!! Admin/Superuser actions - These might fail if the test user isn't a superuser !!! ---
                    # 6. List all organizations (Admin)
                    print("\n6. Listing all organizations (Admin)...")
                    all_orgs = await user_client.list_all_organizations(limit=5)
                    if all_orgs is not None: # Check for None in case of error
                        print(f"   Found {len(all_orgs)} organizations (limit 5).")
                    else:
                         print("   Failed to list all organizations (requires admin privileges).")

                    # 7. List all users (Admin)
                    print("\n7. Listing all users (Admin)...")
                    all_users = await user_client.list_all_users(limit=5)
                    if all_users is not None:
                         print(f"   Found {len(all_users)} users (limit 5).")
                    else:
                         print("   Failed to list all users (requires admin privileges).")
                    # --- End Admin Actions ---

                    # 8. (Optional Cleanup) Delete the created organization
                    # Be careful running delete operations in tests
                    # print(f"\n8. Deleting organization {created_org.name}...")
                    # deleted = await user_client.delete_organization(org_id=created_org.id)
                    # if deleted:
                    #     print(f"   Successfully deleted organization {created_org.id}.")
                    # else:
                    #     print(f"   Failed to delete organization {created_org.id} (permissions?).")

            else:
                 print("   Failed to get current user.")

            # 9. (Optional Cleanup - Admin) Delete a user account (e.g., the test user itself if desired)
            # USE WITH EXTREME CAUTION - DELETES THE ACCOUNT
            # if user_id_for_delete:
            #      print(f"\n9. Deleting user account {user_id_for_delete} (Admin)...")
            #      delete_req = schemas.UserDeleteRequest(user_id=user_id_for_delete)
            #      deleted_user = await user_client.delete_user_account(delete_req)
            #      if deleted_user:
            #           print(f"    Successfully deleted user {user_id_for_delete} (Admin).")
            #      else:
            #           print(f"    Failed to delete user {user_id_for_delete} (Admin).")


    except AuthenticationError as e:
        print(f"Authentication Error: {e}")
    except ImportError as e:
         print(f"Import Error: {e}. Check PYTHONPATH or schema locations.")
         print("Ensure 'kiwi_client.schemas' or 'kiwi_app.auth' is accessible.")
    except Exception as e:
        print(f"An unexpected error occurred in the main example execution: {e}")
        logger.exception("Main example execution error:")

if __name__ == "__main__":
    # To run this example:
    # 1. Ensure the KiwiQ API server is running.
    # 2. Set environment variables for authentication (e.g., TEST_USER_EMAIL, TEST_USER_PASSWORD, API_BASE_URL).
    # 3. Adjust PYTHONPATH if necessary so `kiwi_client` and potentially `kiwi_app` imports work.
    # 4. Run the script: python -m kiwi_client.user_client
    print("Attempting to run user client example...")
    # Note: Running this directly might have issues with relative imports depending on execution context.
    # It's better practice to import and use UserTestClient in a dedicated test runner script.
    asyncio.run(main()) # Uncomment to run the example directly (use with caution)
    print("\nExample run complete (or skipped). Import UserTestClient into your test suite for actual use.")
