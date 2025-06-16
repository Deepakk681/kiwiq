import uuid
from typing import Optional
from datetime import datetime, timedelta, timezone # Import datetime utilities

from fastapi import BackgroundTasks
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select # Keep select for user lookup by ID

# from global_config.settings import LOG_ROOT
from kiwi_app.settings import settings

from kiwi_app.auth import models, crud, schemas
from kiwi_app.auth.utils import auth_logger
# Import JWT functions and exception
from kiwi_app.auth.security import create_access_token, decode_access_token
from kiwi_app.auth.exceptions import CredentialsException
# Import TokenData schema to check for password_reset claim
from kiwi_app.auth.schemas import TokenData

# Import the new email system
from kiwi_app.email.email_dispatch import email_dispatch, EmailContent, EmailRecipient
from kiwi_app.email.email_templates.renderer import (
    EmailRenderer, 
    AccountConfirmationEmailData, 
    PasswordResetEmailData
)


# Get loggers for different parts of a hypothetical application


# --- Email Verification Utilities --- #

# EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES = settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES # Setting used directly now
# EMAIL_FROM_ADDRESS is now handled by ConnectionConfig

# Removed generate_verification_token() as JWT creation handles uniqueness and expiry.

# def generate_verification_token() -> str:
#     """
#     Generates a secure, unique token for email verification.
#
#     Returns:
#         A unique string token.
#     """
#     return str(uuid.uuid4())

# TODO: CRITICAL: FIXME: change URLs to not redirect customers to API but the SPA and SPA can call backend for verification!

# Initialize the email renderer
email_renderer = EmailRenderer()


async def trigger_send_verification_email(
    background_tasks: BackgroundTasks, # Use FastAPI BackgroundTasks
    db: AsyncSession,
    # user_dao: crud.UserDAO, # DAO no longer needed to save token
    user: models.User,
    base_url: str
) -> Optional[str]:
    """
    Generates a JWT verification token, constructs the link,
    and adds the actual email sending to background tasks using the new template system.
    The token itself is NOT saved to the database.

    Args:
        background_tasks: FastAPI BackgroundTasks instance.
        db: The database session (kept for potential future use, but not used currently).
        user: The user object.
        base_url: Base URL for link generation.

    Returns:
        The verification JWT if generated, otherwise None.
    """
    if user.is_verified:
        auth_logger.debug(f"User {user.email} ({user.id}) is already verified. No verification email needed.")
        return None

    # Generate JWT for email verification
    try:
        # Set expiry time from settings
        expires_delta = timedelta(minutes=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES)
        # Create JWT with user ID as subject
        # No additional claims needed for verification currently
        token = create_access_token(subject=user.id, expires_delta=expires_delta)
        auth_logger.debug(f"Generated verification JWT for user {user.email} ({user.id}). Expires in {expires_delta}.")
    except Exception as e:
        # Catch potential errors during JWT creation (e.g., config issues)
        auth_logger.error(f"Error generating verification JWT for {user.email}: {e}", exc_info=True)
        return None # Cannot proceed without a token

    # Construct the verification URL with the JWT
    URL = base_url
    # URL = f"{base_url.rstrip('/')}{settings.API_V1_PREFIX}{settings.AUTH_VERIFY_EMAIL_URL}"
    verification_link = f"{URL}?token={token}"
    if settings.VERIFY_EMAIL_SPA_URL:
        verification_link = f"{settings.VERIFY_EMAIL_SPA_URL}?token={token}"

    try:
        # Create email content using the new template system
        email_data = AccountConfirmationEmailData(
            user_name=user.full_name or user.email.split('@')[0],  # Fallback to email prefix if no name
            confirmation_url=verification_link,
            expiry_hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES // 60 or 1  # Convert minutes to hours
        )
        
        # Render both HTML and text versions
        html_content = email_renderer.render_account_confirmation_email(email_data)
        text_content = email_renderer.html_to_text(html_content)
        
        # Create email content object
        email_content = EmailContent(
            subject="Verify Your Email Address for KiwiQ",
            html_body=html_content,
            text_body=text_content,
            from_name="KiwiQ Team"
        )
        
        # Create recipient object
        recipient = EmailRecipient(
            email=user.email,
            name=user.full_name
        )
        
        # Send email using the dispatch service
        success = await email_dispatch.send_email_async(
            background_tasks=background_tasks,
            recipient=recipient,
            content=email_content
        )
        
        if success:
            auth_logger.info(f"Verification email task queued for {user.email} ({user.id})")
        else:
            auth_logger.warning(f"Failed to queue verification email for {user.email}")
            
    except Exception as e:
        auth_logger.error(f"Error preparing verification email for {user.email}: {e}", exc_info=True)
        # Still return the token - useful for testing or manual verification if needed
        return token

    return token # Return the generated JWT

async def verify_email_token(db: AsyncSession, token: str) -> Optional[models.User]:
    """
    Validates an email verification JWT and finds the corresponding user.
    Checks token signature, expiry, and extracts user ID from the subject ('sub') claim.

    Args:
        db: Database session, used to fetch the user by ID.
        token: The email verification JWT string.

    Returns:
        The verified user object if the token is valid and the user exists, otherwise None.
    """
    if not token:
        auth_logger.debug("Verification attempt with empty token.")
        return None

    try:
        # Decode and validate the JWT using the security utility
        # This handles signature verification and expiry check
        token_data = decode_access_token(token)
        user_id = token_data.sub # Extract user ID (UUID) from 'sub' claim

        if not user_id:
             # Should not happen if decode_access_token works correctly, but good to check
             auth_logger.error("Token decoded successfully but 'sub' claim (user_id) is missing.")
             return None

        auth_logger.debug(f"Successfully decoded verification token for user ID: {user_id}")

        # Find the user in the database by the ID from the token
        result = await db.execute(
            select(models.User).where(models.User.id == user_id)
        )
        user = result.scalars().first()

        if not user:
            # This could happen if the user was deleted after the token was issued
            auth_logger.warning(f"Verification token is valid for user ID {user_id}, but user not found in DB.")
            return None

        # Optional: Add check if user is already verified?
        # if user.is_verified:
        #     auth_logger.info(f"User {user.email} ({user_id}) is already verified. Verification via token successful but redundant.")
        #     # Return the user anyway, the endpoint handler can decide what to do

        auth_logger.info(f"Email verification successful for user {user.email} ({user_id}) via JWT.")
        return user

    except CredentialsException as e:
        # Handle specific exceptions from decode_access_token (e.g., expired, invalid signature)
        auth_logger.warning(f"Invalid or expired email verification token provided: {e.detail}")
        # Log first few chars of token for debugging without exposing full token
        auth_logger.debug(f"Token (start): {token[:10]}...")
        return None
    except Exception as e:
        # Catch unexpected database or other errors
        auth_logger.error(f"Unexpected error during email token verification: {e}", exc_info=True)
        return None 


# --- Password Reset Email Utilities --- #

# Password reset email sending is now handled by the dispatch service and templates

async def trigger_send_password_reset_email(
    background_tasks: BackgroundTasks,
    # db: AsyncSession, # No DB needed here
    user: models.User,
    base_url: str
) -> Optional[str]:
    """
    Generates a short-lived JWT for password reset, constructs the link,
    and adds the actual email sending to background tasks using the new template system.

    Args:
        background_tasks: FastAPI BackgroundTasks instance.
        user: The user object.
        base_url: Base URL for link generation (e.g., frontend URL).

    Returns:
        The password reset JWT if generated and email task added, otherwise None.
    """
    # Generate JWT specifically for password reset
    try:
        expires_delta = timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)
        # Add the password_reset claim
        additional_claims = {"password_reset": True}
        token = create_access_token(
            subject=user.id,
            expires_delta=expires_delta,
            additional_claims=additional_claims
        )
        auth_logger.debug(f"Generated password reset JWT for user {user.email} ({user.id}). Expires in {expires_delta}.")
    except Exception as e:
        auth_logger.error(f"Error generating password reset JWT for {user.email}: {e}", exc_info=True)
        return None

    # Construct the reset link (likely pointing to a frontend page)
    # Example: http://frontend.com/reset-password?token=JWT_HERE
    # The frontend will then use this token to call the backend /reset-password endpoint.
    # ADJUST THE BASE_URL/PATH AS NEEDED FOR YOUR FRONTEND ROUTING
    URL = base_url
    # URL = f"{base_url.rstrip('/')}{settings.API_V1_PREFIX}{settings.AUTH_VERIFY_PASSWORD_RESET_TOKEN_URL}"
    reset_link = f"{URL}?token={token}"
    if settings.VERIFY_PASSWORD_RESET_TOKEN_SPA_URL:
        reset_link = f"{settings.VERIFY_PASSWORD_RESET_TOKEN_SPA_URL}?token={token}"

    try:
        # Create email content using the new template system
        email_data = PasswordResetEmailData(
            user_name=user.full_name or user.email.split('@')[0],  # Fallback to email prefix if no name
            reset_url=reset_link,
            expiry_hours=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES // 60 or 1  # Convert minutes to hours
        )
        
        # Render both HTML and text versions
        html_content = email_renderer.render_password_reset_email(email_data)
        text_content = email_renderer.html_to_text(html_content)
        
        # Create email content object
        email_content = EmailContent(
            subject="Reset Your KiwiQ Password",
            html_body=html_content,
            text_body=text_content,
            from_name="KiwiQ Team"
        )
        
        # Create recipient object
        recipient = EmailRecipient(
            email=user.email,
            name=user.full_name
        )
        
        # Send email using the dispatch service
        success = await email_dispatch.send_email_async(
            background_tasks=background_tasks,
            recipient=recipient,
            content=email_content
        )
        
        if success:
            auth_logger.info(f"Password reset email task queued for {user.email} ({user.id})")
        else:
            auth_logger.warning(f"Failed to queue password reset email for {user.email}")
            
    except Exception as e:
        auth_logger.error(f"Error preparing password reset email for {user.email}: {e}", exc_info=True)
        # Still return the token - useful for testing or manual verification if needed
        return token

    return token

async def verify_password_reset_token(token: str) -> TokenData:
    """
    Validates a password reset JWT.
    Checks signature, expiry, and presence of 'password_reset: True' claim.

    Args:
        token: The password reset JWT string.

    Returns:
        The validated TokenData containing user ID and password_reset flag.

    Raises:
        CredentialsException: If the token is invalid, expired, malformed, or not
                              specifically for password reset.
    """
    if not token:
        raise CredentialsException(detail="Password reset token is missing.")

    try:
        # Decode and validate the JWT (handles signature, expiry)
        token_data = decode_access_token(token)

        # Crucially, check if this token was intended for password reset
        if not token_data.password_reset:
            auth_logger.warning(f"Token valid but not marked for password reset. User ID: {token_data.sub}")
            raise CredentialsException(detail="Invalid token type. Not for password reset.")

        auth_logger.info(f"Password reset token successfully verified for user ID: {token_data.sub}")
        return token_data

    except CredentialsException as e:
        # Re-raise specific exceptions from decode_access_token or our check
        auth_logger.warning(f"Invalid or expired password reset token provided: {e.detail}")
        auth_logger.debug(f"Token (start): {token[:10]}...")
        raise e # Re-raise the specific CredentialsException
    except Exception as e:
        # Catch unexpected errors
        auth_logger.error(f"Unexpected error during password reset token verification: {e}", exc_info=True)
        raise CredentialsException(detail="Could not validate password reset token due to an internal error.")
