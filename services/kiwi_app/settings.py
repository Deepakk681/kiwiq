from pydantic_settings import BaseSettings
from typing import Optional

from libs.src.global_config.settings import ENV_FILE_PATH, Settings, settings as global_settings

class Settings(Settings):
    # --- Auth Settings --- #
    SECRET_KEY: Optional[str] = None
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 10
    
    EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES: int = 1440

    DEFAULT_SUPERUSER_EMAIL: Optional[str] = None
    DEFAULT_SUPERUSER_PASSWORD: Optional[str] = None

    DB_TABLE_AUTH_PREFIX: str = "auth_"

    # --- LinkedIn Settings --- #
    LINKEDIN_CLIENT_ID: Optional[str] = None
    LINKEDIN_CLIENT_SECRET: Optional[str] = None
    LINKEDIN_REDIRECT_URI: Optional[str] = None

    # --- Gmail SMTP Settings --- #
    GMAIL_SMTP_USERNAME: Optional[str] = None # Your Gmail address (e.g., your_email@gmail.com)
    GMAIL_SMTP_PASSWORD: Optional[str] = None # Your Gmail App Password (NOT your regular password)
    GMAIL_SMTP_FROM: Optional[str] = None     # The email address emails should be sent from
    GMAIL_SMTP_PORT: int = 587                # Default SMTP TLS port
    GMAIL_SMTP_SERVER: str = "smtp.gmail.com"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = True
    MAIL_FROM_NAME: Optional[str] = "KiwiQ Verification" # Optional: Sender name

    # --- Logging Settings --- #
    LOG_LEVEL: str = "INFO"

    # --- Cookie Settings --- #
    # Add settings for cookie security (optional but recommended)
    """
    cookie_secure (True):

    When set to True, the cookie is only sent over HTTPS connections. This prevents the cookie from being transmitted over unencrypted HTTP, helping protect sensitive data from eavesdropping.

    cookie_httponly (True):

    When enabled, this setting prevents client-side JavaScript from accessing the cookie. This adds a layer of protection against cross-site scripting (XSS) attacks by ensuring that the cookie can't be read or manipulated by scripts running in the browser.

    cookie_samesite (lax):

    This setting controls when cookies are sent along with cross-site requests.

    Lax (default): Cookies are sent on top-level navigations (e.g., clicking a link) but are withheld on less safe cross-site requests (like iframes or AJAX calls), helping mitigate CSRF (Cross-Site Request Forgery) attacks.

    Strict: Cookies are only sent in a first-party context (i.e., when the site for the cookie’s domain is currently being visited).

    None: Cookies are sent with all requests, including cross-origin requests—but this requires cookie_secure to be True.
    """
    REFRESH_COOKIE_NAME: str = "refresh_token"
    REFRESH_COOKIE_SECURE: bool = global_settings.APP_ENV in ["PROD", "STAGE"] # Set to False for local HTTP development ONLY
    REFRESH_COOKIE_HTTPONLY: bool = True
    REFRESH_COOKIE_SAMESITE: str = "lax" # Or "strict"

    # NOTE: set this URL to the route to get auth token from without global prefix!
    AUTH_TOKEN_URL: str = "/auth/login/token"
    AUTH_REFRESH_URL: str = "/auth/refresh"
    AUTH_VERIFY_EMAIL_URL: str = "/auth/verify-email"
    AUTH_VERIFY_PASSWORD_RESET_TOKEN_URL: str = "/auth/verify-password-reset-token"
    # TODO: FIXME: fill these up in production to redirect correctly to the SPA to handle verification / password reset!
    VERIFY_EMAIL_SPA_URL: Optional[str] = None
    VERIFY_PASSWORD_RESET_TOKEN_SPA_URL: Optional[str] = None
    # NOTE: if API prefix var name changes, change it here: `security.py` to set `OAuth2PasswordBearer``
    # NOTE: also used in verify email url!
    API_V1_PREFIX: str = "/api/v1"

settings = Settings()
