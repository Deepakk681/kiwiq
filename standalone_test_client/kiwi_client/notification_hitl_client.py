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
from kiwi_client.test_config import (
    NOTIFICATIONS_URL,
    NOTIFICATION_READ_URL,
    NOTIFICATIONS_READ_ALL_URL,
    NOTIFICATIONS_UNREAD_COUNT_URL,
    HITL_JOBS_URL,
    HITL_JOB_DETAIL_URL,
    HITL_JOB_CANCEL_URL,
    CLIENT_LOG_LEVEL,
)

# Import schemas and constants from the workflow app
from kiwi_client.schemas import workflow_api_schemas as wf_schemas
from kiwi_client.schemas.workflow_constants import HITLJobStatus

# Setup logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=CLIENT_LOG_LEVEL)

# Create TypeAdapters for validating lists of schemas
UserNotificationReadListAdapter = TypeAdapter(List[wf_schemas.UserNotificationRead])
HITLJobReadListAdapter = TypeAdapter(List[wf_schemas.HITLJobRead])

class NotificationTestClient:
    """
    Provides methods to test the /notifications/ endpoints defined in routes.py.
    Uses schemas from schemas.py for requests and response validation.
    """
    def __init__(self, auth_client: AuthenticatedClient):
        """
        Initializes the NotificationTestClient.

        Args:
            auth_client (AuthenticatedClient): An instance of AuthenticatedClient, assumed to be logged in.
        """
        self._auth_client: AuthenticatedClient = auth_client
        self._client: httpx.AsyncClient = auth_client.client
        logger.info("NotificationTestClient initialized.")

    async def list_notifications(self,
                                 skip: int = 0,
                                 limit: int = 10,
                                 is_read: Optional[bool] = None,
                                 get_notifications_for_all_user_orgs: bool = False
                                 ) -> Optional[List[wf_schemas.UserNotificationRead]]:
        """
        Tests listing user notifications via GET /notifications/.

        Corresponds to the `list_user_notifications` route which uses `schemas.NotificationListQuery`.

        Args:
            skip (int): Number of notifications to skip.
            limit (int): Maximum number of notifications to return.
            is_read (Optional[bool]): Filter by read status.
            get_notifications_for_all_user_orgs (bool): If True, fetches notifications for all user orgs.

        Returns:
            Optional[List[wf_schemas.UserNotificationRead]]: A list of parsed and validated notifications,
                                                            or None on failure.
        """
        logger.info(f"Attempting to list notifications (skip={skip}, limit={limit}, is_read={is_read})...")
        params: Dict[str, Any] = {
            "skip": skip,
            "limit": limit,
            "get_notifications_for_all_user_orgs": get_notifications_for_all_user_orgs
        }
        if is_read is not None:
            params["is_read"] = is_read

        try:
            # Endpoint returns 200 OK, body is List[UserNotificationRead]
            response = await self._client.get(NOTIFICATIONS_URL, params=params)
            response.raise_for_status() # Raise exception for non-2xx codes
            response_json = response.json()

            # Validate the response list against List[UserNotificationRead]
            validated_notifications = UserNotificationReadListAdapter.validate_python(response_json)
            logger.info(f"Successfully listed and validated {len(validated_notifications)} notifications.")
            logger.debug(f"List notifications response (first item): {validated_notifications[0].model_dump() if validated_notifications else 'None'}")
            return validated_notifications
        except httpx.HTTPStatusError as e:
            logger.error(f"Error listing notifications: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"Request error listing notifications: {e}")
        except ValidationError as e:
             logger.error(f"Response validation error listing notifications: {e}")
             logger.debug(f"Invalid response JSON: {response_json if 'response_json' in locals() else 'No response JSON'}")
        except Exception as e:
            logger.exception("Unexpected error during notification listing.")
        return None

    async def mark_notification_read(self, notification_id: Union[str, uuid.UUID]) -> Optional[wf_schemas.UserNotificationRead]:
        """
        Tests marking a notification as read via POST /notifications/{notification_id}/read.

        Corresponds to the `mark_notification_read` route which returns `schemas.UserNotificationRead`.

        Args:
            notification_id (Union[str, uuid.UUID]): The ID of the notification to mark as read.

        Returns:
            Optional[wf_schemas.UserNotificationRead]: The parsed and validated updated notification,
                                                      or None on failure.
        """
        notification_id_str = str(notification_id)
        logger.info(f"Attempting to mark notification {notification_id_str} as read.")
        url = NOTIFICATION_READ_URL(notification_id_str)
        try:
            # Endpoint returns 200 OK, body is UserNotificationRead schema
            response = await self._client.post(url)
            response.raise_for_status()
            response_json = response.json()

            # Validate the response against the UserNotificationRead schema
            validated_notification = wf_schemas.UserNotificationRead.model_validate(response_json)
            logger.info(f"Successfully marked notification {notification_id_str} as read (Is read: {validated_notification.is_read}).")
            return validated_notification
        except httpx.HTTPStatusError as e:
            logger.error(f"Error marking notification {notification_id_str} as read: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"Request error marking notification {notification_id_str} as read: {e}")
        except ValidationError as e:
             logger.error(f"Response validation error marking notification {notification_id_str} as read: {e}")
             logger.debug(f"Invalid response JSON: {response_json if 'response_json' in locals() else 'No response JSON'}")
        except Exception as e:
            logger.exception(f"Unexpected error marking notification {notification_id_str} as read.")
        return None

    async def mark_all_notifications_read(self) -> Optional[Dict[str, str]]:
        """
        Tests marking all notifications as read via POST /notifications/read-all.

        Corresponds to the `mark_all_notifications_read` route.

        Returns:
            Optional[Dict[str, str]]: A dictionary containing the success message, or None on failure.
                                      Example: {"message": "X notifications marked as read"}
        """
        logger.info("Attempting to mark all notifications as read.")
        try:
            # Endpoint returns 200 OK, body is a simple JSON message
            response = await self._client.post(NOTIFICATIONS_READ_ALL_URL)
            response.raise_for_status()
            response_json = response.json()
            # Basic validation for the expected message format
            if isinstance(response_json, dict) and "message" in response_json:
                logger.info(f"Successfully marked all notifications as read: {response_json['message']}")
                return response_json
            else:
                logger.error(f"Unexpected response format when marking all notifications as read: {response_json}")
                return None
        except httpx.HTTPStatusError as e:
            logger.error(f"Error marking all notifications as read: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"Request error marking all notifications as read: {e}")
        except Exception as e:
            logger.exception("Unexpected error marking all notifications as read.")
        return None

    async def get_unread_notification_count(self) -> Optional[int]:
        """
        Tests getting the count of unread notifications via GET /notifications/unread-count.

        Corresponds to the `get_unread_notification_count` route.

        Returns:
            Optional[int]: The count of unread notifications, or None on failure.
        """
        logger.info("Attempting to get unread notification count.")
        try:
            # Endpoint returns 200 OK, body is an integer
            response = await self._client.get(NOTIFICATIONS_UNREAD_COUNT_URL)
            response.raise_for_status()
            response_json = response.json()

            # Validate the response is an integer
            if isinstance(response_json, int):
                logger.info(f"Successfully retrieved unread notification count: {response_json}")
                return response_json
            else:
                 logger.error(f"Response validation error: Expected an integer, got {type(response_json)}")
                 logger.debug(f"Invalid response JSON: {response_json}")
                 return None
        except httpx.HTTPStatusError as e:
            logger.error(f"Error getting unread notification count: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"Request error getting unread notification count: {e}")
        except Exception as e:
            logger.exception("Unexpected error getting unread notification count.")
        return None


class HITLTestClient:
    """
    Provides methods to test the /hitl/ endpoints defined in routes.py.
    Uses schemas from schemas.py for requests and response validation.
    """
    def __init__(self, auth_client: AuthenticatedClient):
        """
        Initializes the HITLTestClient.

        Args:
            auth_client (AuthenticatedClient): An instance of AuthenticatedClient, assumed to be logged in.
        """
        self._auth_client: AuthenticatedClient = auth_client
        self._client: httpx.AsyncClient = auth_client.client
        logger.info("HITLTestClient initialized.")

    async def list_hitl_jobs(self,
                             skip: int = 0,
                             limit: int = 10,
                             run_id: Optional[Union[str, uuid.UUID]] = None,
                             assigned_user_id: Optional[Union[str, uuid.UUID]] = None, # Can be 'me'
                             status: Optional[HITLJobStatus] = None,
                             pending_only: bool = False,
                             exclude_cancelled: bool = True,
                             owner_org_id: Optional[Union[str, uuid.UUID]] = None # For superuser testing
                             ) -> Optional[List[wf_schemas.HITLJobRead]]:
        """
        Tests listing HITL jobs via GET /hitl/.

        Corresponds to the `list_hitl_jobs` route which uses `schemas.HITLJobListQuery`.

        Args:
            skip (int): Number of jobs to skip.
            limit (int): Maximum number of jobs to return.
            run_id (Optional[Union[str, uuid.UUID]]): Filter by workflow run ID.
            assigned_user_id (Optional[Union[str, uuid.UUID]]): Filter by assignee ('me' or UUID).
            status (Optional[HITLJobStatus]): Filter by job status.
            pending_only (bool): Shortcut to filter for PENDING status.
            exclude_cancelled (bool): If True (default), excludes CANCELLED jobs.
            owner_org_id (Optional[Union[str, uuid.UUID]]): Filter by org ID (requires superuser).

        Returns:
            Optional[List[wf_schemas.HITLJobRead]]: A list of parsed and validated HITL jobs,
                                                    or None on failure.
        """
        logger.info(f"Attempting to list HITL jobs (skip={skip}, limit={limit}, status={status}, pending_only={pending_only})...")
        # Prepare query parameters matching schemas.HITLJobListQuery
        params: Dict[str, Any] = {
            "skip": skip,
            "limit": limit,
            "pending_only": pending_only,
            "exclude_cancelled": exclude_cancelled
        }
        if run_id: params["run_id"] = str(run_id)
        if assigned_user_id: params["assigned_user_id"] = str(assigned_user_id) # Handles 'me' or UUID
        if status: params["status"] = status.value
        if owner_org_id: params["owner_org_id"] = str(owner_org_id)

        try:
            # Endpoint returns 200 OK, body is List[HITLJobRead]
            response = await self._client.get(HITL_JOBS_URL, params=params)
            response.raise_for_status() # Raise exception for non-2xx codes
            response_json = response.json()

            # Validate the response list against List[HITLJobRead]
            validated_jobs = HITLJobReadListAdapter.validate_python(response_json)
            logger.info(f"Successfully listed and validated {len(validated_jobs)} HITL jobs.")
            logger.debug(f"List HITL jobs response (first item): {validated_jobs[0].model_dump() if validated_jobs else 'None'}")
            return validated_jobs
        except httpx.HTTPStatusError as e:
            logger.error(f"Error listing HITL jobs: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"Request error listing HITL jobs: {e}")
        except ValidationError as e:
             logger.error(f"Response validation error listing HITL jobs: {e}")
             logger.debug(f"Invalid response JSON: {response_json if 'response_json' in locals() else 'No response JSON'}")
        except Exception as e:
            logger.exception("Unexpected error during HITL job listing.")
        return None

    async def get_latest_pending_hitl_job(self, run_id: Optional[Union[str, uuid.UUID]] = None) -> Optional[wf_schemas.HITLJobRead]:
        """
        Convenience function to get the most recent pending HITL job, optionally for a specific run.

        Args:
            run_id (Optional[Union[str, uuid.UUID]]): If provided, limits the search to this run.

        Returns:
            Optional[wf_schemas.HITLJobRead]: The latest pending HITL job found, or None.
        """
        logger.info(f"Attempting to get the latest pending HITL job (run_id={run_id})...")
        # Fetch the list, limiting to 1 and filtering by PENDING status.
        # The API currently doesn't guarantee ordering by creation time descending in the response,
        # but for a limit of 1, we'll likely get the most recent if one exists.
        # If ordering becomes critical, the API might need an explicit sort parameter.
        pending_jobs = await self.list_hitl_jobs(
            limit=1,
            status=HITLJobStatus.PENDING,
            run_id=run_id,
            pending_only=True # Explicitly use the shortcut filter if appropriate
        )
        if pending_jobs:
            latest_job = pending_jobs[0]
            logger.info(f"Found latest pending HITL job: {latest_job.id} for run {latest_job.requesting_run_id}")
            return latest_job
        else:
            logger.info(f"No pending HITL jobs found (run_id={run_id}).")
            return None

    async def get_hitl_job_details(self, job_id: Union[str, uuid.UUID]) -> Optional[wf_schemas.HITLJobRead]:
        """
        Tests getting the details of a specific HITL job via GET /hitl/{job_id}.

        Corresponds to the `get_hitl_job` route which returns `schemas.HITLJobRead`.

        Args:
            job_id (Union[str, uuid.UUID]): The ID of the job to retrieve details for.

        Returns:
            Optional[wf_schemas.HITLJobRead]: The parsed and validated job details, or None on failure.
        """
        job_id_str = str(job_id)
        logger.info(f"Attempting to get details for HITL job ID: {job_id_str}")
        url = HITL_JOB_DETAIL_URL(job_id_str)
        try:
            # Endpoint returns 200 OK, body is HITLJobRead schema
            response = await self._client.get(url)
            response.raise_for_status()
            response_json = response.json()

            # Validate the response against the HITLJobRead schema
            validated_job_details = wf_schemas.HITLJobRead.model_validate(response_json)
            logger.info(f"Successfully retrieved and validated details for HITL job ID: {validated_job_details.id} (Status: {validated_job_details.status})")
            logger.debug(f"Get HITL job details response validated: {validated_job_details.model_dump_json(indent=2)}")
            return validated_job_details
        except httpx.HTTPStatusError as e:
            logger.error(f"Error getting details for HITL job {job_id_str}: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"Request error getting details for HITL job {job_id_str}: {e}")
        except ValidationError as e:
             logger.error(f"Response validation error getting details for HITL job {job_id_str}: {e}")
             logger.debug(f"Invalid response JSON: {response_json if 'response_json' in locals() else 'No response JSON'}")
        except Exception as e:
            logger.exception(f"Unexpected error getting details for HITL job {job_id_str}.")
        return None

    async def cancel_hitl_job(self, job_id: Union[str, uuid.UUID]) -> Optional[wf_schemas.HITLJobRead]:
        """
        Tests cancelling a HITL job via POST /hitl/{job_id}/cancel.

        Corresponds to the `cancel_hitl_job` route which returns `schemas.HITLJobRead`.

        Args:
            job_id (Union[str, uuid.UUID]): The ID of the job to cancel.

        Returns:
            Optional[wf_schemas.HITLJobRead]: The parsed and validated updated job details (likely with CANCELLED status),
                                             or None on failure.
        """
        job_id_str = str(job_id)
        logger.info(f"Attempting to cancel HITL job ID: {job_id_str}")
        url = HITL_JOB_CANCEL_URL(job_id_str)
        try:
            # Endpoint returns 200 OK, body is HITLJobRead schema
            response = await self._client.post(url)
            response.raise_for_status()
            response_json = response.json()

            # Validate the response against the HITLJobRead schema
            validated_job = wf_schemas.HITLJobRead.model_validate(response_json)
            logger.info(f"Successfully cancelled HITL job ID: {validated_job.id} (New Status: {validated_job.status})")
            return validated_job
        except httpx.HTTPStatusError as e:
            logger.error(f"Error cancelling HITL job {job_id_str}: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"Request error cancelling HITL job {job_id_str}: {e}")
        except ValidationError as e:
             logger.error(f"Response validation error cancelling HITL job {job_id_str}: {e}")
             logger.debug(f"Invalid response JSON: {response_json if 'response_json' in locals() else 'No response JSON'}")
        except Exception as e:
            logger.exception(f"Unexpected error cancelling HITL job {job_id_str}.")
        return None

# --- Example Usage --- (Optional: for testing this module directly)
async def main():
    """Demonstrates using the NotificationTestClient and HITLTestClient."""
    print("--- Starting Notification & HITL API Test --- ")
    latest_notification_id: Optional[uuid.UUID] = None
    latest_pending_hitl_job_id: Optional[uuid.UUID] = None

    # Need an authenticated client first
    try:
        async with AuthenticatedClient() as auth_client:
            print("Authenticated.")
            # Initialize test clients
            notification_tester = NotificationTestClient(auth_client)
            hitl_tester = HITLTestClient(auth_client)

            # --- Notifications ---
            print("\n--- Testing Notifications --- ")

            # 1. Get Unread Count
            print("1. Getting unread notification count...")
            unread_count = await notification_tester.get_unread_notification_count()
            if unread_count is not None:
                print(f"   Unread count: {unread_count}")
            else:
                print("   Failed to get unread count.")

            # 2. List Notifications
            print("\n2. Listing latest notifications...")
            notifications = await notification_tester.list_notifications(limit=5)
            if notifications:
                print(f"   Found {len(notifications)} notifications.")
                # Find the first unread one to mark as read
                unread_notification = next((n for n in notifications if not n.is_read), None)
                if unread_notification:
                    latest_notification_id = unread_notification.id
                    print(f"   Found unread notification: {latest_notification_id} (Created: {unread_notification.created_at})")
                elif notifications:
                     latest_notification_id = notifications[0].id # Use the latest if all are read
                     print(f"   Using latest notification (already read): {latest_notification_id}")
            else:
                print("   No notifications found or listing failed.")

            # 3. Mark one as Read (if found)
            if latest_notification_id:
                print(f"\n3. Marking notification {latest_notification_id} as read...")
                marked_notification = await notification_tester.mark_notification_read(latest_notification_id)
                if marked_notification:
                    print(f"   Notification marked. Is read: {marked_notification.is_read}")
                    assert marked_notification.is_read is True
                else:
                    print("   Failed to mark notification as read.")

                # 3a. Get Unread Count again
                print("\n3a. Getting unread count again...")
                new_unread_count = await notification_tester.get_unread_notification_count()
                if new_unread_count is not None:
                    print(f"   New unread count: {new_unread_count}")
                    # We expect it to be less than or equal to the original count
                    if unread_count is not None:
                        assert new_unread_count <= unread_count
                else:
                    print("   Failed to get new unread count.")


            # 4. Mark All as Read
            print("\n4. Marking all notifications as read...")
            mark_all_result = await notification_tester.mark_all_notifications_read()
            if mark_all_result:
                print(f"   {mark_all_result.get('message', 'Mark all response received.')}")
            else:
                print("   Failed to mark all as read.")

            # 4a. Get Unread Count finally
            print("\n4a. Getting final unread count...")
            final_unread_count = await notification_tester.get_unread_notification_count()
            if final_unread_count is not None:
                print(f"   Final unread count: {final_unread_count}")
                assert final_unread_count == 0 # Should be zero after marking all
            else:
                print("   Failed to get final unread count.")

            # --- HITL ---
            print("\n--- Testing HITL --- ")

            # 5. List HITL Jobs (potentially pending)
            print("5. Listing latest HITL jobs (pending or otherwise)...")
            hitl_jobs = await hitl_tester.list_hitl_jobs(limit=5)
            if hitl_jobs:
                print(f"   Found {len(hitl_jobs)} recent HITL jobs.")
                for job in hitl_jobs:
                    print(f"     - Job ID: {job.id}, Status: {job.status}, Run ID: {job.requesting_run_id}")
            else:
                print("   No HITL jobs found or listing failed.")

            # 6. Get Latest Pending HITL Job
            print("\n6. Getting the latest *pending* HITL job...")
            pending_job = await hitl_tester.get_latest_pending_hitl_job()
            if pending_job:
                latest_pending_hitl_job_id = pending_job.id
                print(f"   Found pending HITL job: {latest_pending_hitl_job_id}")
                print(f"     Run ID: {pending_job.requesting_run_id}")
                # print(f"     Node ID: {pending_job.node_id}")
                print(f"     Created At: {pending_job.created_at}")
            else:
                print("   No pending HITL job found.")

            # 7. Get Details for a specific job (if found)
            if latest_pending_hitl_job_id: # Use the pending one if available
                job_to_get = latest_pending_hitl_job_id
            elif hitl_jobs: # Fallback to the most recent listed one
                 job_to_get = hitl_jobs[0].id
            else:
                job_to_get = None

            if job_to_get:
                print(f"\n7. Getting details for HITL job {job_to_get}...")
                job_details = await hitl_tester.get_hitl_job_details(job_to_get)
                if job_details:
                    print(f"   Successfully got details for job {job_details.id}")
                    print(f"     Status: {job_details.status}")
                    print(f"     Request Data Sample: {str(job_details.request_details)[:100]}...")
                    print(f"     Response Schema Sample: {str(job_details.response_schema)[:100]}...")
                else:
                    print(f"   Failed to get details for job {job_to_get}.")

            # # 8. Cancel the latest pending job (if found)
            # #    WARNING: This will actually cancel the job if run!
            # if latest_pending_hitl_job_id:
            #     print(f"\n8. Cancelling HITL job {latest_pending_hitl_job_id}...")
            #     cancelled_job = await hitl_tester.cancel_hitl_job(latest_pending_hitl_job_id)
            #     if cancelled_job:
            #          print(f"   Successfully cancelled job {cancelled_job.id}")
            #          print(f"     New Status: {cancelled_job.status}")
            #          assert cancelled_job.status == HITLJobStatus.CANCELLED
            #     else:
            #          print(f"   Failed to cancel job {latest_pending_hitl_job_id}.")
            # else:
            #     print("\n8. Skipping HITL job cancellation (no pending job found).")


    except AuthenticationError as e:
        print(f"Authentication Error: {e}")
    except ImportError as e:
         print(f"Import Error: {e}. Check PYTHONPATH and schema locations.")
    except Exception as e:
        print(f"An unexpected error occurred in the main test execution: {e}")
        logger.exception("Main test execution error:")
    finally:
        print("\n--- Notification & HITL API Test Finished --- ")

if __name__ == "__main__":
    # Ensure API server is running and config is correct
    # Run with: PYTHONPATH=. python standalone_test_client/kiwi_client/notification_hitl_client.py
    print("Attempting to run Notification & HITL test client main function...")
    asyncio.run(main())
    print("\nRun this script with `PYTHONPATH=[path_to_project_root] python standalone_test_client/kiwi_client/notification_hitl_client.py`")
