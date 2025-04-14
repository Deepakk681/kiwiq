"""
# poetry run python -m kiwi_client.auth_client

Provides an authenticated HTTP client for interacting with the API.
Handles login, token storage, and setting necessary headers.
"""
import httpx
import logging
from typing import Optional, Dict, Any

# Import configuration details
from kiwi_client.test_config import (
    API_BASE_URL,
    TEST_USER_EMAIL,
    TEST_USER_PASSWORD,
    TEST_ORG_ID,
    BASE_HEADERS,
    LOGIN_URL,
    REFRESH_URL,
    USERS_ME_URL,
    CLIENT_LOG_LEVEL
)

# Setup logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=CLIENT_LOG_LEVEL)


class AuthenticationError(Exception):
    """Custom exception for authentication failures."""
    pass


class AuthenticatedClient:
    """
    Manages an authenticated httpx session for API testing.

    Handles login, stores access token, manages refresh token cookies,
    and provides an authenticated httpx.AsyncClient instance.
    """
    def __init__(
        self,
        base_url: str = API_BASE_URL,
        email: str = TEST_USER_EMAIL,
        password: str = TEST_USER_PASSWORD,
        active_org_id: str = str(TEST_ORG_ID)
    ) -> None:
        """
        Initializes the AuthenticatedClient.

        Args:
            base_url: The base URL of the API.
            email: The email for the test user.
            password: The password for the test user.
            active_org_id: The organization ID to use for the X-Active-Org header.
        """
        self._base_url = base_url
        self._email = email
        self._password = password
        self._active_org_id = active_org_id
        self._access_token: Optional[str] = None
        # Use httpx.AsyncClient with cookie handling enabled
        self._client: httpx.AsyncClient = httpx.AsyncClient(
            base_url=self._base_url,
            headers=BASE_HEADERS.copy(), # Start with base headers
            timeout=30.0 # Set a reasonable timeout
        )
        self._is_authenticated: bool = False
        logger.info("AuthenticatedClient initialized.")

    @property
    def client(self) -> httpx.AsyncClient:
        """
        Returns the authenticated httpx.AsyncClient instance.
        Ensures the client is authenticated before returning.
        """
        if not self._is_authenticated:
            raise AuthenticationError("Client is not authenticated. Call login() first.")
        return self._client

    @property
    def active_org_id(self) -> str:
        """Returns the active organization ID being used."""
        return self._active_org_id

    async def _update_auth_header(self) -> None:
        """Updates the Authorization header in the client."""
        if self._access_token:
            self._client.headers["Authorization"] = f"Bearer {self._access_token}"
            logger.debug("Authorization header updated.")
        else:
            # Should not happen if login was successful, but handle defensively
            if "Authorization" in self._client.headers:
                del self._client.headers["Authorization"]
            logger.warning("Attempted to update auth header with no access token.")

    async def _update_org_header(self) -> None:
        """Updates the X-Active-Org header in the client."""
        self._client.headers["X-Active-Org"] = self._active_org_id
        logger.debug(f"X-Active-Org header set to: {self._active_org_id}")

    async def login(self) -> None:
        """
        Logs in the user using the provided credentials and stores the access token
        and refresh token cookie.
        """
        logger.info(f"Attempting login for user: {self._email}...")
        try:
            # Use form data for login as required by OAuth2PasswordRequestForm
            login_data = {"username": self._email, "password": self._password}
            response = await self._client.post(
                LOGIN_URL, # Use absolute URL from config
                data=login_data,
                # Override content type for form data
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

            # Check response status before trying to parse JSON
            response.raise_for_status() # Raises HTTPStatusError for 4xx/5xx

            token_data = response.json()
            self._access_token = token_data.get("access_token")

            if not self._access_token:
                logger.error("Login response did not contain an access token.")
                raise AuthenticationError("Login failed: No access token received.")

            # Update headers
            await self._update_auth_header()
            await self._update_org_header() # Set org header after successful login

            self._is_authenticated = True
            logger.info(f"Login successful for user: {self._email}. Access token stored. Refresh cookie set by server.")

        except httpx.RequestError as e:
            logger.error(f"Login request failed: {e}", exc_info=True)
            raise AuthenticationError(f"Login failed: Network error connecting to {e.request.url!r}.")
        except httpx.HTTPStatusError as e:
            logger.error(f"Login failed with status {e.response.status_code}: {e.response.text}")
            self._is_authenticated = False
            detail = "Unknown authentication error."
            try:
                # Try to get more specific error detail from response
                error_details = e.response.json()
                detail = error_details.get("detail", detail)
            except Exception:
                pass # Ignore if response is not JSON or parsing fails
            raise AuthenticationError(f"Login failed: {detail} (Status: {e.response.status_code})")
        except Exception as e:
            logger.exception("An unexpected error occurred during login.")
            self._is_authenticated = False
            raise AuthenticationError(f"Login failed due to an unexpected error: {e}")

    async def refresh_token(self) -> bool:
        """
        Attempts to refresh the access token using the refresh token cookie.
        Updates the stored access token and client headers on success.

        Returns:
            True if refresh was successful, False otherwise.
        """
        logger.info("Attempting to refresh access token...")
        if not self._client.cookies.get("refresh_token"):
             logger.warning("No refresh token cookie found. Cannot refresh.")
             return False
        try:
            # The refresh endpoint expects no body, it uses the cookie
            response = await self._client.post(REFRESH_URL) # Use absolute URL
            response.raise_for_status()

            token_data = response.json()
            new_access_token = token_data.get("access_token")

            if not new_access_token:
                logger.error("Token refresh response did not contain a new access token.")
                return False

            self._access_token = new_access_token
            await self._update_auth_header() # Update header with new token
            logger.info("Access token refreshed successfully.")
            return True

        except httpx.HTTPStatusError as e:
            logger.error(f"Token refresh failed with status {e.response.status_code}: {e.response.text}")
            # If refresh fails (e.g., 401), mark as unauthenticated
            self._is_authenticated = False
            self._access_token = None
            if "Authorization" in self._client.headers:
                del self._client.headers["Authorization"]
            return False
        except httpx.RequestError as e:
            logger.error(f"Token refresh request failed: {e}", exc_info=True)
            return False
        except Exception as e:
            logger.exception("An unexpected error occurred during token refresh.")
            return False

    async def close(self) -> None:
        """Closes the underlying httpx client."""
        await self._client.aclose()
        logger.info("AuthenticatedClient closed.")

    async def __aenter__(self) -> "AuthenticatedClient":
        """Enables use as an async context manager, performing login."""
        await self.login()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Closes the client when exiting the context."""
        await self.close()


# Example Usage (for testing this module directly)
async def main():
    """Example of using the AuthenticatedClient."""
    print("Testing AuthenticatedClient...")
    auth_client = AuthenticatedClient()
    try:
        # Using context manager automatically handles login and close
        async with auth_client:
            print(f"Login successful. Using Org ID: {auth_client.active_org_id}")
            client = auth_client.client # Get the authenticated client
            print("Headers:", client.headers)

            # Example: Make an authenticated request (replace with a valid endpoint)
            try:
                # me_url = "/auth/users/me" # Relative path is okay here
                response = await client.get(USERS_ME_URL)
                response.raise_for_status()
                user_data = response.json()
                print(f"Successfully fetched /users/me: {user_data.get('email')}")
            except httpx.HTTPStatusError as e:
                print(f"Error fetching /users/me: {e.response.status_code} - {e.response.text}")
            except Exception as e:
                print(f"An error occurred: {e}")

            # Example: Test token refresh (optional, uncomment to test)
            print("Testing token refresh...")
            refreshed = await auth_client.refresh_token()
            if refreshed:
                print("Token refreshed successfully.")
                print("New Headers:", client.headers)
            else:
                print("Token refresh failed.")

    except AuthenticationError as e:
        print(f"Authentication Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        # Ensure closure if not using context manager or if login failed before entering
        if not auth_client._client.is_closed:
            await auth_client.close()

if __name__ == "__main__":
    import asyncio
    # Before running, ensure your API server is running and the credentials/org ID
    # in test_config.py are correct.
    # You might need to register the user first if they don't exist.
    asyncio.run(main())
    print("Run this script with `PYTHONPATH=. python services/kiwi_app/workflow_app/test_clients/auth_client.py`")
    print("Note: Example usage is commented out by default.") 
