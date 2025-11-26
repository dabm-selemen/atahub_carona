"""
Async API Client for Brazilian Government Open Data

Implements rate limiting, retry logic, and async HTTP operations
for fetching ARP (Price Registration Record) data.
"""

import asyncio
import time
import random
from typing import Dict, Any, List, Optional
from datetime import date
import aiohttp
from aiohttp import ClientSession, ClientTimeout, ClientError
import structlog

from config import config

logger = structlog.get_logger(__name__)


# ============================================================================
# RATE LIMITER (Token Bucket Algorithm)
# ============================================================================

class RateLimiter:
    """
    Token Bucket Rate Limiter

    Implements token bucket algorithm for smooth rate limiting.
    Allows bursts while maintaining average rate.
    """

    def __init__(self, rate: float = 3.0):
        """
        Initialize rate limiter

        Args:
            rate: Requests per second (e.g., 3.0 = 3 req/s)
        """
        self.rate = rate
        self.tokens = rate
        self.last_refill = time.time()
        self.lock = asyncio.Lock()

    async def acquire(self):
        """
        Acquire a token (wait if necessary)

        Blocks until a token is available.
        """
        async with self.lock:
            while self.tokens < 1:
                await asyncio.sleep(0.05)  # Check every 50ms
                self._refill()

            self.tokens -= 1
            logger.debug("rate_limit_token_acquired", tokens_remaining=self.tokens)

    def _refill(self):
        """Refill tokens based on elapsed time"""
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(self.rate, self.tokens + elapsed * self.rate)
        self.last_refill = now


# ============================================================================
# RETRY EXCEPTIONS
# ============================================================================

class RetryableError(Exception):
    """Exception that should trigger retry"""
    pass


class NonRetryableError(Exception):
    """Exception that should NOT be retried"""
    pass


# ============================================================================
# ASYNC ARP API CLIENT
# ============================================================================

class AsyncARPAPIClient:
    """
    Async client for Brazilian Government ARP API

    Features:
    - Rate limiting (token bucket)
    - Exponential backoff retry
    - Connection pooling
    - Timeout handling
    """

    def __init__(self):
        """Initialize API client"""
        self.base_url = config.API_BASE_URL
        self.rate_limiter = RateLimiter(rate=config.REQUESTS_PER_SECOND)
        self.session: Optional[ClientSession] = None

        logger.info(
            "api_client_initialized",
            base_url=self.base_url,
            rate_limit=f"{config.REQUESTS_PER_SECOND} req/s"
        )

    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    async def start(self):
        """Start HTTP session"""
        if self.session is None:
            timeout = ClientTimeout(total=config.API_TIMEOUT)
            connector = aiohttp.TCPConnector(limit=100, limit_per_host=10)

            self.session = ClientSession(
                timeout=timeout,
                connector=connector,
                headers={"User-Agent": "AtaHub-Carona-ETL/1.0"}
            )

            logger.info("http_session_started")

    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("http_session_closed")

    async def _request_with_retry(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic

        Args:
            method: HTTP method (GET, POST, etc)
            url: Request URL
            params: Query parameters
            **kwargs: Additional arguments for aiohttp

        Returns:
            JSON response as dictionary

        Raises:
            NonRetryableError: For non-retryable errors
            RetryableError: After max retries exhausted
        """
        if not self.session:
            await self.start()

        for attempt in range(config.MAX_RETRIES):
            try:
                # Acquire rate limit token
                await self.rate_limiter.acquire()

                # Make request
                start_time = time.time()
                async with self.session.request(method, url, params=params, **kwargs) as response:
                    duration_ms = (time.time() - start_time) * 1000

                    # Log request
                    logger.debug(
                        "api_request",
                        method=method,
                        url=url,
                        status=response.status,
                        duration_ms=f"{duration_ms:.0f}",
                        attempt=attempt + 1
                    )

                    # Handle rate limiting (429)
                    if response.status == 429:
                        retry_after = int(response.headers.get("Retry-After", 5))
                        logger.warning(
                            "api_rate_limited",
                            retry_after=retry_after,
                            attempt=attempt + 1
                        )

                        if attempt < config.MAX_RETRIES - 1:
                            await asyncio.sleep(retry_after)
                            continue
                        raise RetryableError(f"Rate limited after {config.MAX_RETRIES} attempts")

                    # Handle server errors (5xx) - retryable
                    if 500 <= response.status < 600:
                        logger.warning(
                            "api_server_error",
                            status=response.status,
                            attempt=attempt + 1
                        )

                        if attempt < config.MAX_RETRIES - 1:
                            wait = self._calculate_backoff(attempt)
                            await asyncio.sleep(wait)
                            continue
                        raise RetryableError(f"Server error {response.status} after {config.MAX_RETRIES} attempts")

                    # Handle client errors (4xx) - mostly non-retryable
                    if 400 <= response.status < 500:
                        error_text = await response.text()
                        logger.error(
                            "api_client_error",
                            status=response.status,
                            error=error_text[:200]
                        )
                        raise NonRetryableError(f"Client error {response.status}: {error_text[:200]}")

                    # Success - parse JSON
                    response.raise_for_status()
                    data = await response.json()

                    return data

            except (ClientError, asyncio.TimeoutError) as e:
                logger.warning(
                    "api_connection_error",
                    error=str(e),
                    attempt=attempt + 1
                )

                if attempt < config.MAX_RETRIES - 1:
                    wait = self._calculate_backoff(attempt)
                    await asyncio.sleep(wait)
                    continue
                raise RetryableError(f"Connection error after {config.MAX_RETRIES} attempts: {e}")

            except Exception as e:
                logger.error("api_unexpected_error", error=str(e), attempt=attempt + 1)
                raise NonRetryableError(f"Unexpected error: {e}")

        raise RetryableError(f"Max retries ({config.MAX_RETRIES}) exhausted")

    def _calculate_backoff(self, attempt: int) -> float:
        """
        Calculate exponential backoff wait time with jitter

        Args:
            attempt: Attempt number (0-indexed)

        Returns:
            Wait time in seconds
        """
        base_wait = config.RETRY_BACKOFF_FACTOR ** attempt
        jitter = random.uniform(0.5, 1.5)  # ±50% jitter
        wait = base_wait * jitter

        logger.debug("backoff_calculated", attempt=attempt, wait_seconds=f"{wait:.2f}")
        return wait

    # ========================================================================
    # ARP API METHODS
    # ========================================================================

    async def fetch_arps_page(
        self,
        date_start: date,
        date_end: date,
        page: int = 1
    ) -> Dict[str, Any]:
        """
        Fetch a page of ARPs from API

        Args:
            date_start: Start date for vigencia filter (YYYY-MM-DD)
            date_end: End date for vigencia filter (YYYY-MM-DD)
            page: Page number (1-indexed)

        Returns:
            API response with 'resultado', 'totalRegistros', 'totalPaginas', 'paginasRestantes'

        Example response:
            {
                "resultado": [...],
                "totalRegistros": 140865,
                "totalPaginas": 282,
                "paginasRestantes": 281
            }
        """
        params = {
            "dataVigenciaInicialMin": date_start.strftime("%Y-%m-%d"),
            "dataVigenciaInicialMax": date_end.strftime("%Y-%m-%d"),
            "pagina": page,
            "tamanhoPagina": config.PAGE_SIZE
        }

        url = f"{self.base_url}{config.API_ENDPOINT_ARPS}"

        logger.info(
            "fetching_arps_page",
            date_range=f"{date_start} to {date_end}",
            page=page
        )

        response = await self._request_with_retry("GET", url, params=params)

        result_count = len(response.get("resultado", []))
        logger.info(
            "arps_page_fetched",
            page=page,
            results=result_count,
            total_records=response.get("totalRegistros"),
            total_pages=response.get("totalPaginas")
        )

        return response

    async def fetch_arp_items(
        self,
        numero_compra: str,
        codigo_unidade_gerenciadora: str,
        data_vigencia_inicial: date,
        page: int = 1
    ) -> Dict[str, Any]:
        """
        Fetch items for a specific ARP

        Args:
            numero_compra: Purchase number (numeroCompra from ARP)
            codigo_unidade_gerenciadora: UASG code
            data_vigencia_inicial: Start validity date
            page: Page number (1-indexed)

        Returns:
            API response with 'resultado', pagination info

        Note: This endpoint also supports pagination!
        """
        params = {
            "numeroCompra": numero_compra,
            "codigoUnidadeGerenciadora": codigo_unidade_gerenciadora,
            "dataVigenciaInicialMin": data_vigencia_inicial.strftime("%Y-%m-%d"),
            "dataVigenciaInicialMax": data_vigencia_inicial.strftime("%Y-%m-%d"),
            "pagina": page,
            "tamanhoPagina": config.PAGE_SIZE
        }

        url = f"{self.base_url}{config.API_ENDPOINT_ITEMS}"

        logger.debug(
            "fetching_arp_items",
            numero_compra=numero_compra,
            uasg=codigo_unidade_gerenciadora,
            page=page
        )

        response = await self._request_with_retry("GET", url, params=params)

        result_count = len(response.get("resultado", []))
        logger.debug(
            "arp_items_fetched",
            numero_compra=numero_compra,
            results=result_count
        )

        return response

    async def fetch_all_arp_items(
        self,
        numero_compra: str,
        codigo_unidade_gerenciadora: str,
        data_vigencia_inicial: date
    ) -> List[Dict[str, Any]]:
        """
        Fetch ALL items for an ARP (handling pagination)

        Args:
            numero_compra: Purchase number
            codigo_unidade_gerenciadora: UASG code
            data_vigencia_inicial: Start validity date

        Returns:
            List of all items across all pages
        """
        all_items = []
        page = 1

        while True:
            response = await self.fetch_arp_items(
                numero_compra,
                codigo_unidade_gerenciadora,
                data_vigencia_inicial,
                page
            )

            items = response.get("resultado", [])
            if not items:
                break

            all_items.extend(items)

            # Check if more pages
            total_pages = response.get("totalPaginas", 1)
            if page >= total_pages:
                break

            page += 1

        logger.info(
            "all_arp_items_fetched",
            numero_compra=numero_compra,
            total_items=len(all_items)
        )

        return all_items


# ============================================================================
# CONCURRENT FETCHING HELPERS
# ============================================================================

async def fetch_items_for_arps_concurrent(
    client: AsyncARPAPIClient,
    arps: List[Dict[str, Any]],
    max_concurrent: int = 5
) -> List[Dict[str, Any]]:
    """
    Fetch items for multiple ARPs concurrently

    Args:
        client: API client instance
        arps: List of ARP dictionaries
        max_concurrent: Maximum concurrent requests (semaphore limit)

    Returns:
        List of tuples: (arp, items_or_error)
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    async def fetch_with_limit(arp: Dict[str, Any]):
        async with semaphore:
            try:
                items = await client.fetch_all_arp_items(
                    numero_compra=arp.get("numeroCompra"),
                    codigo_unidade_gerenciadora=arp.get("codigoUnidadeGerenciadora"),
                    data_vigencia_inicial=date.fromisoformat(arp.get("dataVigenciaInicial"))
                )
                return (arp, items)
            except Exception as e:
                logger.error(
                    "concurrent_fetch_error",
                    arp=arp.get("numeroControlePncpAta"),
                    error=str(e)
                )
                return (arp, e)

    tasks = [fetch_with_limit(arp) for arp in arps]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    return results


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    # Test API client
    async def test():
        logger.info("Testing API client...")

        async with AsyncARPAPIClient() as client:
            # Test 1: Fetch one page of ARPs
            response = await client.fetch_arps_page(
                date_start=date(2024, 1, 1),
                date_end=date(2024, 1, 31),
                page=1
            )

            print(f"\n✅ ARPs fetched: {len(response.get('resultado', []))}")
            print(f"   Total records: {response.get('totalRegistros')}")
            print(f"   Total pages: {response.get('totalPaginas')}")

            # Test 2: Fetch items for first ARP (if any)
            arps = response.get("resultado", [])
            if arps:
                first_arp = arps[0]
                items = await client.fetch_all_arp_items(
                    numero_compra=first_arp.get("numeroCompra"),
                    codigo_unidade_gerenciadora=first_arp.get("codigoUnidadeGerenciadora"),
                    data_vigencia_inicial=date.fromisoformat(first_arp.get("dataVigenciaInicial"))
                )

                print(f"\n✅ Items fetched for ARP {first_arp.get('numeroAtaRegistroPreco')}: {len(items)}")

    asyncio.run(test())
