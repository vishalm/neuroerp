"""
API Connector for NeuroERP.

This module provides a flexible API connector that enables seamless integration
with external systems and services via REST and GraphQL APIs.
"""

import logging
import time
import json
import asyncio
from typing import Dict, Any, List, Optional, Union, Callable
import aiohttp
import requests
from urllib.parse import urljoin

from ...core.config import Config

logger = logging.getLogger(__name__)

class APIConnector:
    """Connector for interacting with external APIs."""
    
    def __init__(self, api_name: str, config: Optional[Dict[str, Any]] = None):
        """Initialize the API connector.
        
        Args:
            api_name: Name of the API connection (used to load config)
            config: Optional manual configuration (overrides config file)
        """
        self.api_name = api_name
        self.config = Config()
        
        # Load configuration
        self._load_configuration(config)
        
        # Initialize session
        self._session = None
        self._async_session = None
        
        # Request metrics
        self.request_count = 0
        self.error_count = 0
        self.last_request_time = None
        
        logger.info(f"Initialized API connector for {api_name}")
    
    def _load_configuration(self, manual_config: Optional[Dict[str, Any]]):
        """Load API configuration from config or manual override.
        
        Args:
            manual_config: Optional manual configuration to override config file
        """
        # Set default configuration
        self.api_config = {
            "base_url": "",
            "auth_type": "none",  # none, basic, bearer, api_key, oauth2
            "auth_data": {},
            "headers": {"Content-Type": "application/json"},
            "timeout": 30,
            "retry_attempts": 3,
            "retry_delay": 1.0,
            "ssl_verify": True,
            "rate_limit": None
        }
        
        # Load from config file if available
        config_path = f"connectors.api.{self.api_name}"
        file_config = self.config.get(config_path, {})
        
        if file_config:
            self.api_config.update(file_config)
            logger.debug(f"Loaded configuration for API {self.api_name} from config file")
        
        # Override with manual config if provided
        if manual_config:
            self.api_config.update(manual_config)
            logger.debug(f"Applied manual configuration for API {self.api_name}")
        
        # Validate configuration
        if not self.api_config.get("base_url"):
            logger.warning(f"No base URL configured for API {self.api_name}")
    
    def _get_auth(self) -> Dict[str, Any]:
        """Get authentication data based on auth type.
        
        Returns:
            Authentication data for requests
        """
        auth_type = self.api_config.get("auth_type", "none")
        auth_data = self.api_config.get("auth_data", {})
        
        if auth_type == "none":
            return {}
        elif auth_type == "basic":
            # Basic authentication (username/password)
            username = auth_data.get("username", "")
            password = auth_data.get("password", "")
            return {"auth": (username, password)}
        elif auth_type == "bearer":
            # Bearer token authentication
            token = auth_data.get("token", "")
            return {"headers": {"Authorization": f"Bearer {token}"}}
        elif auth_type == "api_key":
            # API key authentication
            key_name = auth_data.get("key_name", "api_key")
            key_value = auth_data.get("key_value", "")
            location = auth_data.get("location", "header")
            
            if location == "header":
                return {"headers": {key_name: key_value}}
            elif location == "query":
                return {"params": {key_name: key_value}}
            else:
                logger.warning(f"Unsupported API key location: {location}")
                return {}
        elif auth_type == "oauth2":
            # OAuth2 authentication - should implement token refresh logic
            token = auth_data.get("access_token", "")
            if not token:
                token = self._refresh_oauth_token()
            
            return {"headers": {"Authorization": f"Bearer {token}"}}
        else:
            logger.warning(f"Unsupported auth type: {auth_type}")
            return {}
    
    def _refresh_oauth_token(self) -> str:
        """Refresh OAuth2 token.
        
        Returns:
            New access token
        """
        auth_data = self.api_config.get("auth_data", {})
        
        # OAuth2 token refresh logic
        token_url = auth_data.get("token_url", "")
        client_id = auth_data.get("client_id", "")
        client_secret = auth_data.get("client_secret", "")
        refresh_token = auth_data.get("refresh_token", "")
        
        if not token_url or not client_id or not client_secret or not refresh_token:
            logger.error("Missing required OAuth2 refresh parameters")
            return ""
        
        try:
            response = requests.post(
                token_url,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": client_id,
                    "client_secret": client_secret
                },
                timeout=self.api_config.get("timeout", 30)
            )
            
            response.raise_for_status()
            token_data = response.json()
            
            # Update stored tokens
            self.api_config["auth_data"]["access_token"] = token_data.get("access_token", "")
            if "refresh_token" in token_data:
                self.api_config["auth_data"]["refresh_token"] = token_data["refresh_token"]
            
            return token_data.get("access_token", "")
        except Exception as e:
            logger.error(f"Failed to refresh OAuth2 token: {e}")
            return ""
    
    def _ensure_session(self):
        """Ensure a requests session exists."""
        if self._session is None:
            self._session = requests.Session()
            
            # Apply default headers
            headers = self.api_config.get("headers", {})
            self._session.headers.update(headers)
    
    async def _ensure_async_session(self):
        """Ensure an aiohttp session exists."""
        if self._async_session is None:
            ssl_verify = self.api_config.get("ssl_verify", True)
            self._async_session = aiohttp.ClientSession(
                headers=self.api_config.get("headers", {}),
                connector=aiohttp.TCPConnector(ssl=ssl_verify)
            )
    
    def close(self):
        """Close the API connector and any open sessions."""
        if self._session:
            self._session.close()
            self._session = None
        
        if self._async_session:
            if not self._async_session.closed:
                # Create a task to close the session
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self._async_session.close())
                else:
                    loop.run_until_complete(self._async_session.close())
            self._async_session = None
        
        logger.debug(f"Closed API connector for {self.api_name}")
    
    def request(self, 
              method: str, 
              endpoint: str, 
              params: Optional[Dict[str, Any]] = None,
              data: Optional[Any] = None,
              headers: Optional[Dict[str, str]] = None,
              timeout: Optional[float] = None,
              retry_attempts: Optional[int] = None,
              ssl_verify: Optional[bool] = None) -> Dict[str, Any]:
        """Make a synchronous request to the API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            endpoint: API endpoint (will be joined with base_url)
            params: Optional query parameters
            data: Optional request body data
            headers: Optional request headers
            timeout: Optional request timeout override
            retry_attempts: Optional retry attempts override
            ssl_verify: Optional SSL verification override
            
        Returns:
            Response data (parsed JSON or raw content)
        """
        self._ensure_session()
        
        # Build request parameters
        url = urljoin(self.api_config["base_url"], endpoint)
        request_timeout = timeout if timeout is not None else self.api_config.get("timeout", 30)
        max_retries = retry_attempts if retry_attempts is not None else self.api_config.get("retry_attempts", 3)
        verify = ssl_verify if ssl_verify is not None else self.api_config.get("ssl_verify", True)
        
        # Apply authentication
        auth_params = self._get_auth()
        auth = auth_params.get("auth")
        auth_headers = auth_params.get("headers", {})
        auth_params_query = auth_params.get("params", {})
        
        # Merge headers
        merged_headers = {}
        merged_headers.update(self.api_config.get("headers", {}))
        merged_headers.update(auth_headers)
        if headers:
            merged_headers.update(headers)
        
        # Merge query parameters
        merged_params = {}
        if params:
            merged_params.update(params)
        merged_params.update(auth_params_query)
        
        # Prepare request arguments
        request_args = {
            "method": method.upper(),
            "url": url,
            "params": merged_params,
            "headers": merged_headers,
            "timeout": request_timeout,
            "verify": verify
        }
        
        # Add data if provided
        if data is not None:
            content_type = merged_headers.get("Content-Type", "").lower()
            if "application/json" in content_type and not isinstance(data, str):
                request_args["json"] = data
            else:
                request_args["data"] = data
        
        # Rate limiting
        rate_limit = self.api_config.get("rate_limit")
        if rate_limit and self.last_request_time:
            time_since_last = time.time() - self.last_request_time
            if time_since_last < rate_limit:
                wait_time = rate_limit - time_since_last
                logger.debug(f"Rate limiting: waiting {wait_time:.2f}s")
                time.sleep(wait_time)
        
        # Execute request with retries
        retries = 0
        last_exception = None
        
        while retries <= max_retries:
            try:
                # Update metrics
                self.request_count += 1
                self.last_request_time = time.time()
                
                # Make the request
                response = self._session.request(**request_args)
                
                # Check for error status codes that should trigger retry
                if 500 <= response.status_code < 600:
                    retries += 1
                    if retries <= max_retries:
                        retry_delay = self.api_config.get("retry_delay", 1.0) * (2 ** (retries - 1))  # Exponential backoff
                        logger.warning(f"Request failed with status {response.status_code}, retrying in {retry_delay:.2f}s")
                        time.sleep(retry_delay)
                        continue
                
                # Check for error status codes
                response.raise_for_status()
                
                # Parse response
                content_type = response.headers.get("Content-Type", "").lower()
                if "application/json" in content_type:
                    return response.json()
                else:
                    return {"content": response.content, "content_type": content_type}
                
            except requests.exceptions.RequestException as e:
                retries += 1
                last_exception = e
                
                if retries <= max_retries:
                    retry_delay = self.api_config.get("retry_delay", 1.0) * (2 ** (retries - 1))  # Exponential backoff
                    logger.warning(f"Request failed: {e}, retrying in {retry_delay:.2f}s")
                    time.sleep(retry_delay)
                else:
                    self.error_count += 1
                    logger.error(f"Request failed after {max_retries} retries: {e}")
                    raise
        
        # If we get here, all retries failed
        self.error_count += 1
        raise last_exception or Exception("Request failed for unknown reason")
    
    async def async_request(self,
                          method: str, 
                          endpoint: str,
                          params: Optional[Dict[str, Any]] = None,
                          data: Optional[Any] = None,
                          headers: Optional[Dict[str, str]] = None,
                          timeout: Optional[float] = None,
                          retry_attempts: Optional[int] = None,
                          ssl_verify: Optional[bool] = None) -> Dict[str, Any]:
        """Make an asynchronous request to the API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            endpoint: API endpoint (will be joined with base_url)
            params: Optional query parameters
            data: Optional request body data
            headers: Optional request headers
            timeout: Optional request timeout override
            retry_attempts: Optional retry attempts override
            ssl_verify: Optional SSL verification override
            
        Returns:
            Response data (parsed JSON or raw content)
        """
        await self._ensure_async_session()
        
        # Build request parameters
        url = urljoin(self.api_config["base_url"], endpoint)
        request_timeout = timeout if timeout is not None else self.api_config.get("timeout", 30)
        max_retries = retry_attempts if retry_attempts is not None else self.api_config.get("retry_attempts", 3)
        
        # Apply authentication
        auth_params = self._get_auth()
        auth_headers = auth_params.get("headers", {})
        auth_params_query = auth_params.get("params", {})
        
        # Merge headers
        merged_headers = {}
        merged_headers.update(self.api_config.get("headers", {}))
        merged_headers.update(auth_headers)
        if headers:
            merged_headers.update(headers)
        
        # Merge query parameters
        merged_params = {}
        if params:
            merged_params.update(params)
        merged_params.update(auth_params_query)
        
        # Handle data serialization
        request_data = data
        if data is not None and not isinstance(data, (str, bytes)):
            content_type = merged_headers.get("Content-Type", "").lower()
            if "application/json" in content_type:
                request_data = json.dumps(data)
                merged_headers["Content-Type"] = "application/json"
        
        # Rate limiting
        rate_limit = self.api_config.get("rate_limit")
        if rate_limit and self.last_request_time:
            time_since_last = time.time() - self.last_request_time
            if time_since_last < rate_limit:
                wait_time = rate_limit - time_since_last
                logger.debug(f"Rate limiting: waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
        
        # Execute request with retries
        retries = 0
        last_exception = None
        
        while retries <= max_retries:
            try:
                # Update metrics
                self.request_count += 1
                self.last_request_time = time.time()
                
                # Make the request
                async with self._async_session.request(
                    method,
                    url,
                    params=merged_params,
                    data=request_data,
                    headers=merged_headers,
                    timeout=aiohttp.ClientTimeout(total=request_timeout)
                ) as response:
                    # Check for error status codes that should trigger retry
                    if 500 <= response.status < 600:
                        retries += 1
                        if retries <= max_retries:
                            retry_delay = self.api_config.get("retry_delay", 1.0) * (2 ** (retries - 1))  # Exponential backoff
                            logger.warning(f"Request failed with status {response.status}, retrying in {retry_delay:.2f}s")
                            await asyncio.sleep(retry_delay)
                            continue
                    
                    # Check for error status codes
                    response.raise_for_status()
                    
                    # Parse response
                    content_type = response.headers.get("Content-Type", "").lower()
                    if "application/json" in content_type:
                        return await response.json()
                    else:
                        content = await response.read()
                        return {"content": content, "content_type": content_type}
                    
            except aiohttp.ClientError as e:
                retries += 1
                last_exception = e
                
                if retries <= max_retries:
                    retry_delay = self.api_config.get("retry_delay", 1.0) * (2 ** (retries - 1))  # Exponential backoff
                    logger.warning(f"Request failed: {e}, retrying in {retry_delay:.2f}s")
                    await asyncio.sleep(retry_delay)
                else:
                    self.error_count += 1
                    logger.error(f"Request failed after {max_retries} retries: {e}")
                    raise
        
        # If we get here, all retries failed
        self.error_count += 1
        raise last_exception or Exception("Request failed for unknown reason")
    
    def get(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make a GET request to the API.
        
        Args:
            endpoint: API endpoint
            **kwargs: Additional request parameters
            
        Returns:
            Response data
        """
        return self.request("GET", endpoint, **kwargs)
    
    def post(self, endpoint: str, data: Any = None, **kwargs) -> Dict[str, Any]:
        """Make a POST request to the API.
        
        Args:
            endpoint: API endpoint
            data: Request body data
            **kwargs: Additional request parameters
            
        Returns:
            Response data
        """
        return self.request("POST", endpoint, data=data, **kwargs)
    
    def put(self, endpoint: str, data: Any = None, **kwargs) -> Dict[str, Any]:
        """Make a PUT request to the API.
        
        Args:
            endpoint: API endpoint
            data: Request body data
            **kwargs: Additional request parameters
            
        Returns:
            Response data
        """
        return self.request("PUT", endpoint, data=data, **kwargs)
    
    def delete(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make a DELETE request to the API.
        
        Args:
            endpoint: API endpoint
            **kwargs: Additional request parameters
            
        Returns:
            Response data
        """
        return self.request("DELETE", endpoint, **kwargs)
    
    def patch(self, endpoint: str, data: Any = None, **kwargs) -> Dict[str, Any]:
        """Make a PATCH request to the API.
        
        Args:
            endpoint: API endpoint
            data: Request body data
            **kwargs: Additional request parameters
            
        Returns:
            Response data
        """
        return self.request("PATCH", endpoint, data=data, **kwargs)
    
    async def async_get(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make an asynchronous GET request to the API.
        
        Args:
            endpoint: API endpoint
            **kwargs: Additional request parameters
            
        Returns:
            Response data
        """
        return await self.async_request("GET", endpoint, **kwargs)
    
    async def async_post(self, endpoint: str, data: Any = None, **kwargs) -> Dict[str, Any]:
        """Make an asynchronous POST request to the API.
        
        Args:
            endpoint: API endpoint
            data: Request body data
            **kwargs: Additional request parameters
            
        Returns:
            Response data
        """
        return await self.async_request("POST", endpoint, data=data, **kwargs)
    
    async def async_put(self, endpoint: str, data: Any = None, **kwargs) -> Dict[str, Any]:
        """Make an asynchronous PUT request to the API.
        
        Args:
            endpoint: API endpoint
            data: Request body data
            **kwargs: Additional request parameters
            
        Returns:
            Response data
        """
        return await self.async_request("PUT", endpoint, data=data, **kwargs)
    
    async def async_delete(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make an asynchronous DELETE request to the API.
        
        Args:
            endpoint: API endpoint
            **kwargs: Additional request parameters
            
        Returns:
            Response data
        """
        return await self.async_request("DELETE", endpoint, **kwargs)
    
    async def async_patch(self, endpoint: str, data: Any = None, **kwargs) -> Dict[str, Any]:
        """Make an asynchronous PATCH request to the API.
        
        Args:
            endpoint: API endpoint
            data: Request body data
            **kwargs: Additional request parameters
            
        Returns:
            Response data
        """
        return await self.async_request("PATCH", endpoint, data=data, **kwargs)
    
    def graphql_query(self, query: str, variables: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """Execute a GraphQL query.
        
        Args:
            query: GraphQL query string
            variables: Optional query variables
            **kwargs: Additional request parameters
            
        Returns:
            GraphQL response data
        """
        graphql_data = {
            "query": query
        }
        
        if variables:
            graphql_data["variables"] = variables
        
        # Use the specified endpoint or default to /graphql
        endpoint = kwargs.pop("endpoint", "/graphql")
        
        # Ensure content type is set to application/json
        headers = kwargs.pop("headers", {})
        headers["Content-Type"] = "application/json"
        
        return self.post(endpoint, data=graphql_data, headers=headers, **kwargs)
    
    async def async_graphql_query(self, query: str, variables: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """Execute an asynchronous GraphQL query.
        
        Args:
            query: GraphQL query string
            variables: Optional query variables
            **kwargs: Additional request parameters
            
        Returns:
            GraphQL response data
        """
        graphql_data = {
            "query": query
        }
        
        if variables:
            graphql_data["variables"] = variables
        
        # Use the specified endpoint or default to /graphql
        endpoint = kwargs.pop("endpoint", "/graphql")
        
        # Ensure content type is set to application/json
        headers = kwargs.pop("headers", {})
        headers["Content-Type"] = "application/json"
        
        return await self.async_post(endpoint, data=graphql_data, headers=headers, **kwargs)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get connector metrics.
        
        Returns:
            Dictionary of connector metrics
        """
        return {
            "api_name": self.api_name,
            "request_count": self.request_count,
            "error_count": self.error_count,
            "success_rate": ((self.request_count - self.error_count) / self.request_count) * 100 if self.request_count > 0 else 0,
            "last_request_time": self.last_request_time
        }