"""
ETL Configuration Management

Centralized configuration using Pydantic Settings for type safety and validation.
All configuration is loaded from environment variables or .env file.
"""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from datetime import date


class ETLConfig(BaseSettings):
    """
    ETL Configuration

    All settings can be overridden via environment variables.
    Example: DATABASE_URL, API_BASE_URL, REQUESTS_PER_SECOND, etc.
    """

    # ========================================================================
    # DATABASE CONFIGURATION
    # ========================================================================

    DATABASE_URL: str = "postgresql://postgres:password@localhost:5433/govcompras"
    """PostgreSQL connection string"""

    DB_POOL_SIZE: int = 5
    """Database connection pool size"""

    DB_MAX_OVERFLOW: int = 10
    """Maximum overflow connections beyond pool size"""

    DB_POOL_RECYCLE: int = 3600
    """Recycle connections after N seconds"""

    # ========================================================================
    # API CONFIGURATION
    # ========================================================================

    API_BASE_URL: str = "https://dadosabertos.compras.gov.br"
    """Base URL for Brazilian Government Open Data API"""

    API_ENDPOINT_ARPS: str = "/modulo-arp/1_consultarARP"
    """Endpoint for fetching ARPs"""

    API_ENDPOINT_ITEMS: str = "/modulo-arp/2_consultarARPItem"
    """Endpoint for fetching ARP items"""

    API_TIMEOUT: int = 30
    """HTTP request timeout in seconds"""

    REQUESTS_PER_SECOND: float = 3.0
    """Rate limit: maximum requests per second (conservative for unknown API limits)"""

    MAX_RETRIES: int = 3
    """Maximum retry attempts for failed API requests"""

    RETRY_BACKOFF_FACTOR: float = 2.0
    """Exponential backoff factor: wait = (backoff_factor ** attempt) seconds"""

    # ========================================================================
    # ETL DATE RANGES
    # ========================================================================

    INITIAL_LOAD_START_DATE: date = date(2023, 1, 1)
    """Start date for initial data load"""

    INITIAL_LOAD_END_DATE: Optional[date] = None
    """End date for initial load (None = today)"""

    INCREMENTAL_LOOKBACK_DAYS: int = 7
    """Days to look back for incremental updates (captures late API updates)"""

    # ========================================================================
    # BATCH SIZES
    # ========================================================================

    PAGE_SIZE: int = 500
    """API pagination size (max allowed by API)"""

    BATCH_SIZE_ARPS: int = 100
    """Number of ARPs to process per database transaction"""

    BATCH_SIZE_ITEMS: int = 500
    """Number of items to insert per bulk operation"""

    # ========================================================================
    # CONCURRENCY CONTROL
    # ========================================================================

    MAX_CONCURRENT_ITEM_REQUESTS: int = 5
    """Maximum concurrent requests for fetching items (semaphore limit)"""

    MAX_CONCURRENT_DB_OPERATIONS: int = 3
    """Maximum concurrent database operations"""

    # ========================================================================
    # SCHEDULER CONFIGURATION
    # ========================================================================

    ETL_SCHEDULE_ENABLED: bool = True
    """Enable automatic ETL scheduling"""

    ETL_SCHEDULE_HOUR: int = 2
    """Hour to run daily incremental ETL (0-23, default 2 AM)"""

    ETL_SCHEDULE_MINUTE: int = 0
    """Minute to run ETL (0-59)"""

    ETL_SCHEDULE_TIMEZONE: str = "America/Sao_Paulo"
    """Timezone for scheduler (Brazilian timezone)"""

    # ========================================================================
    # LOGGING CONFIGURATION
    # ========================================================================

    LOG_LEVEL: str = "INFO"
    """Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL"""

    LOG_FILE_PATH: Optional[str] = "logs/etl.log"
    """Path to log file (None = stdout only)"""

    LOG_FORMAT: str = "json"
    """Log format: 'json' for structured logs, 'console' for human-readable"""

    LOG_MAX_BYTES: int = 10 * 1024 * 1024  # 10 MB
    """Maximum log file size before rotation"""

    LOG_BACKUP_COUNT: int = 5
    """Number of rotated log files to keep"""

    # ========================================================================
    # ETL BEHAVIOR
    # ========================================================================

    CHECKPOINT_FREQUENCY: int = 10
    """Save checkpoint every N pages processed"""

    ENABLE_SOFT_DELETE: bool = True
    """Use soft deletes (ata_excluido, item_excluido) instead of hard deletes"""

    RESUME_FAILED_EXECUTIONS: bool = True
    """Automatically resume failed executions from last checkpoint"""

    VALIDATE_DATA: bool = True
    """Enable data validation before database insertion"""

    # ========================================================================
    # MONITORING & ALERTS
    # ========================================================================

    ALERT_ON_FAILURE: bool = False
    """Send alerts when ETL fails (requires alert configuration)"""

    ALERT_EMAIL: Optional[str] = None
    """Email address for alerts"""

    ALERT_WEBHOOK_URL: Optional[str] = None
    """Webhook URL for alerts (e.g., Slack, Discord)"""

    MAX_ERROR_RATE_PERCENT: float = 5.0
    """Maximum acceptable error rate percentage before failing execution"""

    # ========================================================================
    # DEVELOPMENT & TESTING
    # ========================================================================

    DEBUG_MODE: bool = False
    """Enable debug mode (more verbose logging, smaller batches)"""

    DRY_RUN: bool = False
    """Dry run mode: fetch data but don't commit to database"""

    TEST_MODE: bool = False
    """Test mode: use smaller date ranges and limits"""

    TEST_MAX_PAGES: int = 2
    """Maximum pages to fetch in test mode"""

    # ========================================================================
    # PYDANTIC SETTINGS CONFIGURATION
    # ========================================================================

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # ========================================================================
    # COMPUTED PROPERTIES
    # ========================================================================

    @property
    def arp_endpoint_url(self) -> str:
        """Full URL for ARP endpoint"""
        return f"{self.API_BASE_URL}{self.API_ENDPOINT_ARPS}"

    @property
    def item_endpoint_url(self) -> str:
        """Full URL for item endpoint"""
        return f"{self.API_BASE_URL}{self.API_ENDPOINT_ITEMS}"

    @property
    def initial_end_date(self) -> date:
        """End date for initial load (defaults to today if not set)"""
        return self.INITIAL_LOAD_END_DATE or date.today()

    @property
    def rate_limit_delay(self) -> float:
        """Delay between requests in seconds"""
        return 1.0 / self.REQUESTS_PER_SECOND if self.REQUESTS_PER_SECOND > 0 else 0

    # ========================================================================
    # VALIDATION METHODS
    # ========================================================================

    def validate_config(self) -> None:
        """
        Validate configuration parameters

        Raises:
            ValueError: If configuration is invalid
        """
        if self.REQUESTS_PER_SECOND <= 0:
            raise ValueError("REQUESTS_PER_SECOND must be greater than 0")

        if self.PAGE_SIZE < 1 or self.PAGE_SIZE > 500:
            raise ValueError("PAGE_SIZE must be between 1 and 500")

        if self.BATCH_SIZE_ARPS < 1:
            raise ValueError("BATCH_SIZE_ARPS must be greater than 0")

        if self.MAX_CONCURRENT_ITEM_REQUESTS < 1:
            raise ValueError("MAX_CONCURRENT_ITEM_REQUESTS must be greater than 0")

        if self.ETL_SCHEDULE_HOUR < 0 or self.ETL_SCHEDULE_HOUR > 23:
            raise ValueError("ETL_SCHEDULE_HOUR must be between 0 and 23")

        if self.INCREMENTAL_LOOKBACK_DAYS < 0:
            raise ValueError("INCREMENTAL_LOOKBACK_DAYS must be non-negative")

        if self.INITIAL_LOAD_START_DATE > self.initial_end_date:
            raise ValueError("INITIAL_LOAD_START_DATE must be before end date")

    def get_summary(self) -> dict:
        """
        Get configuration summary for logging/monitoring

        Returns:
            Dictionary with key configuration parameters
        """
        return {
            "database": self.DATABASE_URL.split("@")[-1] if "@" in self.DATABASE_URL else self.DATABASE_URL,
            "api_base_url": self.API_BASE_URL,
            "rate_limit": f"{self.REQUESTS_PER_SECOND} req/s",
            "batch_size_arps": self.BATCH_SIZE_ARPS,
            "initial_date_range": f"{self.INITIAL_LOAD_START_DATE} to {self.initial_end_date}",
            "incremental_lookback": f"{self.INCREMENTAL_LOOKBACK_DAYS} days",
            "schedule": f"{self.ETL_SCHEDULE_HOUR:02d}:{self.ETL_SCHEDULE_MINUTE:02d} {self.ETL_SCHEDULE_TIMEZONE}",
            "debug_mode": self.DEBUG_MODE,
            "dry_run": self.DRY_RUN,
        }


# ============================================================================
# GLOBAL CONFIG INSTANCE
# ============================================================================

# Singleton instance of configuration
# Import this in other modules: from config import config
config = ETLConfig()

# Validate on import
config.validate_config()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_config() -> ETLConfig:
    """
    Get global configuration instance

    Returns:
        ETLConfig instance
    """
    return config


def reload_config() -> ETLConfig:
    """
    Reload configuration from environment

    Returns:
        New ETLConfig instance
    """
    global config
    config = ETLConfig()
    config.validate_config()
    return config


if __name__ == "__main__":
    # Print configuration summary when run directly
    import json

    print("=== ETL Configuration ===")
    print(json.dumps(config.get_summary(), indent=2, default=str))

    print("\n=== Computed Properties ===")
    print(f"ARP Endpoint: {config.arp_endpoint_url}")
    print(f"Item Endpoint: {config.item_endpoint_url}")
    print(f"Rate Limit Delay: {config.rate_limit_delay:.3f}s")
    print(f"Initial End Date: {config.initial_end_date}")

    print("\n=== Validation ===")
    try:
        config.validate_config()
        print("✅ Configuration is valid")
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
