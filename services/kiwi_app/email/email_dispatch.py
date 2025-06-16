"""
Email Dispatch Service

This module provides a centralized, reusable email sending service that can handle
any type of email (HTML and text) using SMTP configuration. It includes comprehensive
error handling, logging, and supports both synchronous and asynchronous operations.

Key features:
- Centralized SMTP configuration and connection management
- Support for both HTML and plain text email formats
- Comprehensive error handling and logging
- Background task support for async operations
- SSL/TLS and STARTTLS support
- Credential-based and credential-free SMTP support
- Fully asynchronous email sending using aiosmtplib

Design decisions:
- Single responsibility principle: only handles email dispatch
- Configurable SMTP settings from application settings
- Proper connection cleanup and error recovery
- Detailed logging for troubleshooting email delivery issues
- Uses aiosmtplib for true async/await support

Caveats:
- Email sending is asynchronous for better performance
- SMTP connection is established per email for simplicity
- Error handling does not include retry logic (should be handled at higher level)
"""

import aiosmtplib
import ssl
from typing import Optional, List, Union
from email.message import EmailMessage
from dataclasses import dataclass
from fastapi import BackgroundTasks
from pydantic import EmailStr

from kiwi_app.settings import settings
from kiwi_app.utils import get_kiwi_logger

email_logger = get_kiwi_logger(__name__)

@dataclass
class EmailContent:
    """
    Data structure for email content with both HTML and text versions.
    
    This class holds the email content in both formats, allowing the dispatch
    service to send multipart emails that work in all email clients.
    """
    subject: str
    html_body: str
    text_body: Optional[str] = None
    from_name: Optional[str] = None


@dataclass
class EmailRecipient:
    """
    Data structure for email recipient information.
    
    Contains recipient email address and optional name for personalization.
    """
    email: EmailStr
    name: Optional[str] = None


class EmailDispatchService:
    """
    Centralized email dispatch service for sending emails via SMTP.
    
    This service handles all SMTP configuration, connection management, and
    email sending operations. It supports both HTML and text email formats,
    proper error handling, and extensive logging for troubleshooting.
    
    The service is designed to be used across the application for any type
    of email sending, making it easy to maintain consistent email configuration
    and error handling patterns.
    """
    
    def __init__(self):
        """Initialize the email dispatch service with current settings."""
        self._validate_smtp_configuration()
    
    def _validate_smtp_configuration(self) -> bool:
        """
        Validate that required SMTP settings are configured properly.
        
        This method performs comprehensive validation of SMTP settings including:
        - Required settings presence
        - Port/TLS configuration compatibility
        - Gmail-specific configuration recommendations
        
        Returns:
            True if configuration is valid, False otherwise
        """
        required_settings = [
            settings.GMAIL_SMTP_SERVER,
            settings.GMAIL_SMTP_PORT,
            settings.GMAIL_SMTP_FROM
        ]
        
        if not all(required_settings):
            email_logger.error("Critical SMTP settings missing: server, port, or from address")
            return False
        
        # Check credentials if they're required
        if settings.USE_CREDENTIALS:
            if not all([settings.GMAIL_SMTP_USERNAME, settings.GMAIL_SMTP_PASSWORD]):
                email_logger.error("USE_CREDENTIALS is True but username/password missing")
                return False
        
        # Validate TLS configuration compatibility
        if settings.MAIL_SSL_TLS and settings.MAIL_STARTTLS:
            email_logger.error(
                "Invalid TLS configuration: MAIL_SSL_TLS and MAIL_STARTTLS cannot both be True. "
                "Use MAIL_SSL_TLS=True for port 465 OR MAIL_STARTTLS=True for port 587."
            )
            return False
        
        if not settings.MAIL_SSL_TLS and not settings.MAIL_STARTTLS:
            email_logger.warning(
                "Neither MAIL_SSL_TLS nor MAIL_STARTTLS is enabled. "
                "Email transmission will not be encrypted. This is not recommended."
            )
        
        # Gmail-specific configuration validation
        if "gmail" in settings.GMAIL_SMTP_SERVER.lower():
            if settings.GMAIL_SMTP_PORT == 465 and not settings.MAIL_SSL_TLS:
                email_logger.error(
                    "Gmail port 465 requires MAIL_SSL_TLS=True. "
                    "Current configuration will fail. Set MAIL_SSL_TLS=True and MAIL_STARTTLS=False."
                )
                return False
            elif settings.GMAIL_SMTP_PORT == 587 and settings.MAIL_SSL_TLS:
                email_logger.error(
                    "Gmail port 587 requires STARTTLS, not implicit SSL/TLS. "
                    "Current configuration will fail. Set MAIL_SSL_TLS=False and MAIL_STARTTLS=True."
                )
                return False
            elif settings.GMAIL_SMTP_PORT == 587 and not settings.MAIL_STARTTLS:
                email_logger.error(
                    "Gmail port 587 requires STARTTLS. "
                    "Current configuration will fail. Set MAIL_STARTTLS=True."
                )
                return False
        
        return True
    
    def _create_email_message(
        self, 
        recipient: EmailRecipient, 
        content: EmailContent
    ) -> EmailMessage:
        """
        Create an EmailMessage object with proper headers and content.
        
        Args:
            recipient: EmailRecipient with email and optional name
            content: EmailContent with subject, HTML, and optional text body
            
        Returns:
            Configured EmailMessage ready to send
        """
        message = EmailMessage()
        
        # Set recipient
        if recipient.name:
            message["To"] = f"{recipient.name} <{recipient.email}>"
        else:
            message["To"] = recipient.email
        
        # Set sender with proper name formatting
        from_name = content.from_name or settings.MAIL_FROM_NAME or settings.GMAIL_SMTP_FROM
        message["From"] = f"{from_name} <{settings.GMAIL_SMTP_FROM}>"
        
        # Set subject
        message["Subject"] = content.subject
        
        # Set content - prioritize text first, then add HTML as alternative
        if content.text_body:
            message.set_content(content.text_body)
            if content.html_body:
                message.add_alternative(content.html_body, subtype="html")
        else:
            # If no text body provided, use HTML only (less compatible but functional)
            message.set_content(content.html_body, subtype="html")
        
        return message
    
    async def _establish_smtp_connection(self) -> aiosmtplib.SMTP:
        """
        Establish and configure SMTP connection based on settings.
        
        This method creates an async SMTP connection using aiosmtplib,
        configures SSL/TLS or STARTTLS as needed, and handles authentication.
        
        Important: SSL/TLS (implicit TLS) and STARTTLS are mutually exclusive:
        - SSL/TLS: Connection is encrypted from the start (typically port 465)
        - STARTTLS: Connection starts plain and upgrades to TLS (typically port 587)
        
        Returns:
            Configured SMTP server connection
            
        Raises:
            aiosmtplib.SMTPException: If connection cannot be established
            ssl.SSLError: If SSL/TLS configuration fails
        """
        # Create SSL context with proper certificate validation settings
        context = ssl.create_default_context()
        if not settings.VALIDATE_CERTS:
            # Disable certificate verification (not recommended for production)
            email_logger.warning(
                "Certificate validation is disabled (VALIDATE_CERTS=False). "
                "This is not recommended for production environments."
            )
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        
        email_logger.debug(
            f"Establishing SMTP connection to {settings.GMAIL_SMTP_SERVER}:{settings.GMAIL_SMTP_PORT}"
        )
        email_logger.debug(
            f"SMTP Settings - SSL/TLS: {settings.MAIL_SSL_TLS}, STARTTLS: {settings.MAIL_STARTTLS}"
        )
        
        # Detect common configuration issues
        if settings.GMAIL_SMTP_PORT == 465 and not settings.MAIL_SSL_TLS:
            email_logger.warning(
                "Port 465 typically requires SSL/TLS (MAIL_SSL_TLS=True). "
                "Current settings might cause connection issues."
            )
        elif settings.GMAIL_SMTP_PORT == 587 and settings.MAIL_SSL_TLS:
            email_logger.warning(
                "Port 587 typically uses STARTTLS (MAIL_SSL_TLS=False, MAIL_STARTTLS=True). "
                "Current settings might cause connection issues."
            )
        
        # For Gmail specifically, provide guidance
        if "gmail" in settings.GMAIL_SMTP_SERVER.lower():
            if settings.GMAIL_SMTP_PORT == 465:
                email_logger.info("Gmail port 465 requires MAIL_SSL_TLS=True")
            elif settings.GMAIL_SMTP_PORT == 587:
                email_logger.info("Gmail port 587 requires MAIL_SSL_TLS=False and MAIL_STARTTLS=True")
        
        # Choose connection type based on settings
        if settings.MAIL_SSL_TLS:
            # Use SMTP with SSL/TLS (usually port 465)
            # Connection is encrypted from the start - no STARTTLS needed
            email_logger.debug("Using SMTP with implicit TLS...")
            server = aiosmtplib.SMTP(
                hostname=settings.GMAIL_SMTP_SERVER,
                port=settings.GMAIL_SMTP_PORT,
                use_tls=True,
                tls_context=context
            )
            await server.connect()
            email_logger.debug("Connected with implicit TLS")
        else:
            # Use standard SMTP (usually port 587 or 25)
            email_logger.debug("Using standard SMTP...")
            server = aiosmtplib.SMTP(
                hostname=settings.GMAIL_SMTP_SERVER,
                port=settings.GMAIL_SMTP_PORT
            )
            await server.connect()
            
            # Only use STARTTLS if not already using implicit TLS
            if settings.MAIL_STARTTLS:
                # Secure the connection with STARTTLS
                try:
                    email_logger.debug("Initiating STARTTLS...")
                    await server.starttls(tls_context=context)
                    email_logger.debug("STARTTLS completed successfully")
                except aiosmtplib.SMTPException as e:
                    if "already using TLS" in str(e):
                        # Connection is already secured, likely auto-upgraded by server
                        email_logger.warning(
                            "STARTTLS failed: Connection already using TLS. "
                            "This might happen if the server auto-upgrades the connection. "
                            "Consider using MAIL_SSL_TLS=True for port 465 or MAIL_STARTTLS=False."
                        )
                        # Continue without error since connection is already secure
                    else:
                        # Re-raise other SMTP exceptions
                        raise
        
        # Authenticate if credentials are configured
        if settings.USE_CREDENTIALS and settings.GMAIL_SMTP_USERNAME and settings.GMAIL_SMTP_PASSWORD:
            email_logger.debug(f"Authenticating as {settings.GMAIL_SMTP_USERNAME}...")
            await server.login(settings.GMAIL_SMTP_USERNAME, settings.GMAIL_SMTP_PASSWORD)
            email_logger.debug("SMTP authentication successful")
        else:
            email_logger.debug("Skipping SMTP authentication (credentials not configured)")
        
        return server
    
    async def send_email(
        self, 
        recipient: EmailRecipient, 
        content: EmailContent
    ) -> bool:
        """
        Asynchronously send an email using SMTP.
        
        This method handles the complete email sending process including connection
        establishment, authentication, sending, and cleanup. It includes comprehensive
        error handling and logging. The method is fully asynchronous using aiosmtplib.
        
        Args:
            recipient: EmailRecipient with email address and optional name
            content: EmailContent with subject, HTML body, and optional text body
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        # Validate configuration before attempting to send
        if not self._validate_smtp_configuration():
            email_logger.warning(
                f"SMTP not configured properly, skipping email to {recipient.email}"
            )
            return False
        
        server = None
        try:
            # Create the email message
            message = self._create_email_message(recipient, content)
            
            # Establish SMTP connection
            server = await self._establish_smtp_connection()
            
            # Send the email
            email_logger.debug(f"Sending email to {recipient.email}...")
            await server.send_message(message)
            
            email_logger.info(
                f"Email successfully sent to {recipient.email} - Subject: {content.subject}"
            )
            return True
            
        except aiosmtplib.SMTPAuthenticationError as e:
            email_logger.error(
                f"SMTP Authentication failed for {settings.GMAIL_SMTP_USERNAME}: {e}",
                exc_info=True
            )
            return False
            
        except aiosmtplib.SMTPRecipientsRefused as e:
            email_logger.error(
                f"SMTP Recipients refused for {recipient.email}: {e}",
                exc_info=True
            )
            return False
            
        except aiosmtplib.SMTPSenderRefused as e:
            email_logger.error(
                f"SMTP Sender refused for {settings.GMAIL_SMTP_FROM}: {e}",
                exc_info=True
            )
            return False
            
        except aiosmtplib.SMTPDataError as e:
            email_logger.error(
                f"SMTP Data error sending to {recipient.email}: {e}",
                exc_info=True
            )
            return False
            
        except aiosmtplib.SMTPException as e:
            email_logger.error(
                f"SMTP error sending email to {recipient.email}: {e}",
                exc_info=True
            )
            return False
            
        except ssl.SSLError as e:
            # Provide specific guidance for common SSL/TLS configuration errors
            error_msg = str(e).lower()
            if "wrong version number" in error_msg:
                email_logger.error(
                    f"SSL/TLS configuration error: {e}. "
                    f"This typically means you're using the wrong TLS mode for port {settings.GMAIL_SMTP_PORT}. "
                    f"For Gmail: Use port 587 with STARTTLS (MAIL_SSL_TLS=False, MAIL_STARTTLS=True) "
                    f"OR port 465 with implicit SSL/TLS (MAIL_SSL_TLS=True, MAIL_STARTTLS=False).",
                    exc_info=True
                )
            elif "certificate verify failed" in error_msg:
                email_logger.error(
                    f"SSL certificate verification failed: {e}. "
                    f"This might be due to invalid certificates or network issues. "
                    f"You can disable certificate validation with VALIDATE_CERTS=False (not recommended for production).",
                    exc_info=True
                )
            else:
                email_logger.error(
                    f"SSL error during SMTP connection: {e}",
                    exc_info=True
                )
            return False
            
        except Exception as e:
            email_logger.error(
                f"Unexpected error sending email to {recipient.email}: {e}",
                exc_info=True
            )
            return False
            
        finally:
            # Always attempt to close the SMTP connection gracefully
            if server:
                try:
                    await server.quit()
                    email_logger.debug("SMTP connection closed successfully")
                except Exception as e:
                    email_logger.warning(
                        f"Error closing SMTP connection: {e}",
                        exc_info=True
                    )
    
    async def send_email_async(
        self,
        background_tasks: BackgroundTasks,
        recipient: EmailRecipient,
        content: EmailContent
    ) -> bool:
        """
        Add email sending to background tasks for asynchronous processing.
        
        This method adds the async email sending function to FastAPI's
        BackgroundTasks, allowing the email to be sent without blocking the
        current request. FastAPI's BackgroundTasks properly handles async functions.
        
        Args:
            background_tasks: FastAPI BackgroundTasks instance
            recipient: EmailRecipient with email address and optional name
            content: EmailContent with subject, HTML body, and optional text body
            
        Returns:
            True if the email task was successfully queued, False if configuration invalid
        """
        # Pre-validate configuration before queuing
        if not self._validate_smtp_configuration():
            email_logger.warning(
                f"SMTP not configured, skipping background email task for {recipient.email}"
            )
            return False
        
        # Add the async send function to background tasks
        background_tasks.add_task(
            self.send_email,
            recipient=recipient,
            content=content
        )
        
        email_logger.info(
            f"Email task queued for background processing - To: {recipient.email}, Subject: {content.subject}"
        )
        return True
    
    def send_bulk_emails_async(
        self,
        background_tasks: BackgroundTasks,
        recipients: List[EmailRecipient],
        content: EmailContent
    ) -> int:
        """
        Send the same email content to multiple recipients in background tasks.
        
        This method queues multiple individual email sending tasks, allowing
        for better error isolation (one failed recipient doesn't affect others)
        and potential rate limiting.
        
        Args:
            background_tasks: FastAPI BackgroundTasks instance
            recipients: List of EmailRecipient objects
            content: EmailContent to send to all recipients
            
        Returns:
            Number of email tasks successfully queued
        """
        if not self._validate_smtp_configuration():
            email_logger.warning("SMTP not configured, skipping bulk email tasks")
            return 0
        
        queued_count = 0
        for recipient in recipients:
            # Queue each email individually for better error isolation
            try:
                background_tasks.add_task(
                    self.send_email,
                    recipient=recipient,
                    content=content
                )
                queued_count += 1
                email_logger.debug(f"Queued email for {recipient.email}")
            except Exception as e:
                email_logger.error(
                    f"Failed to queue email for {recipient.email}: {e}",
                    exc_info=True
                )
        
        email_logger.info(
            f"Bulk email: {queued_count}/{len(recipients)} tasks queued - Subject: {content.subject}"
        )
        return queued_count


# Create a singleton instance for application use
email_dispatch = EmailDispatchService()
