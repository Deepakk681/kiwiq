import enum

class EnvFlag(enum.Enum):
    PROD = "prod"
    STAGING = "staging"
    DEV = "dev"
    EXPERIMENTAL = "experimental"
