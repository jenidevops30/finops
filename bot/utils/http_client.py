#!/usr/bin/env python3
"""
HTTP Client for Backend API Communication

Handles communication with the Advanced FinOps Backend API including:
- Data posting to API endpoints with authentication
- Comprehensive error handling and retry logic with circuit breaker
- Request/response logging and performance monitoring
- Circuit breaker pattern for fault tolerance
- Enhanced monitoring with correlation IDs and structured logging
- Error recovery with exponential backoff
"""

import requests
import logging
import json
import time
import hashlib
import threading
import uuid
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass, field

from .monitoring import StructuredLogger, create_correlation_context, system_monitor
from .error_recovery import with_error_recovery, global_recovery_manager

logger = logging.getLogger(__name__)
structured_logger = StructuredLogger(__name__)

# Performance monitoring logger
perf_logger = logging.getLogger(f"{__name__}.performance")

class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered

@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5  # Number of failures before opening
    recovery_timeout: int = 60  # Seconds before trying half-open
    success_threshold: int = 3  # Successes needed to close from half-open
    
@dataclass
class CircuitBreakerStats:
    """Circuit breaker statistics."""
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[float] = None
    state: CircuitBreakerState = CircuitBreakerState.CLOSED
    consecutive_successes: int = 0

@dataclass
class PerformanceMetrics:
    """Performance monitoring metrics."""
    request_count: int = 0
    total_response_time: float = 0.0
    error_count: int = 0
    success_count: int = 0
    avg_response_time: float = 0.0
    last_request_time: Optional[float] = None
    endpoint_metrics: Dict[str, Dict[str, Any]] = field(default_factory=dict)


class HTTPClient:
    """HTTP client for communicating with the FinOps backend API with advanced features."""
    
    def __init__(self, 
                 base_url: str = "http://localhost:5000", 
                 timeout: int = 30, 
                 max_retries: int = 3,
                 api_key: Optional[str] = None,
                 enable_circuit_breaker: bool = True,
                 circuit_breaker_config: Optional[CircuitBreakerConfig] = None,
                 enable_performance_monitoring: bool = True):
        """
        Initialize HTTP client with advanced features.
        
        Args:
            base_url: Base URL of the backend API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            api_key: Optional API key for authentication
            enable_circuit_breaker: Enable circuit breaker pattern
            circuit_breaker_config: Circuit breaker configuration
            enable_performance_monitoring: Enable performance monitoring
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self.api_key = api_key
        self.enable_circuit_breaker = enable_circuit_breaker
        self.enable_performance_monitoring = enable_performance_monitoring
        
        # Initialize circuit breaker
        self.circuit_breaker_config = circuit_breaker_config or CircuitBreakerConfig()
        self.circuit_breaker_stats = CircuitBreakerStats()
        self.circuit_breaker_lock = threading.Lock()
        
        # Initialize performance monitoring
        self.performance_metrics = PerformanceMetrics()
        self.performance_lock = threading.Lock()
        
        # Initialize session
        self.session = requests.Session()
        
        # Set default headers
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'AdvancedFinOps-Bot/1.0'
        }
        
        # Add authentication header if API key provided
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
            # Also support API key in header for different auth schemes
            headers['X-API-Key'] = self.api_key
        
        self.session.headers.update(headers)
        
        logger.info(f"HTTP client initialized for {self.base_url}")
        logger.info(f"Circuit breaker: {'enabled' if self.enable_circuit_breaker else 'disabled'}")
        logger.info(f"Performance monitoring: {'enabled' if self.enable_performance_monitoring else 'disabled'}")
        logger.info(f"Authentication: {'enabled' if self.api_key else 'disabled'}")
    
    def _update_performance_metrics(self, endpoint: str, response_time: float, success: bool):
        """Update performance metrics."""
        if not self.enable_performance_monitoring:
            return
            
        with self.performance_lock:
            # Update global metrics
            self.performance_metrics.request_count += 1
            self.performance_metrics.total_response_time += response_time
            self.performance_metrics.last_request_time = time.time()
            
            if success:
                self.performance_metrics.success_count += 1
            else:
                self.performance_metrics.error_count += 1
            
            # Calculate average response time
            if self.performance_metrics.request_count > 0:
                self.performance_metrics.avg_response_time = (
                    self.performance_metrics.total_response_time / 
                    self.performance_metrics.request_count
                )
            
            # Update endpoint-specific metrics
            if endpoint not in self.performance_metrics.endpoint_metrics:
                self.performance_metrics.endpoint_metrics[endpoint] = {
                    'request_count': 0,
                    'total_response_time': 0.0,
                    'error_count': 0,
                    'success_count': 0,
                    'avg_response_time': 0.0
                }
            
            endpoint_metrics = self.performance_metrics.endpoint_metrics[endpoint]
            endpoint_metrics['request_count'] += 1
            endpoint_metrics['total_response_time'] += response_time
            
            if success:
                endpoint_metrics['success_count'] += 1
            else:
                endpoint_metrics['error_count'] += 1
            
            # Calculate endpoint average response time
            if endpoint_metrics['request_count'] > 0:
                endpoint_metrics['avg_response_time'] = (
                    endpoint_metrics['total_response_time'] / 
                    endpoint_metrics['request_count']
                )
            
            # Log performance metrics periodically
            if self.performance_metrics.request_count % 10 == 0:
                perf_logger.info(f"Performance metrics - Total requests: {self.performance_metrics.request_count}, "
                               f"Avg response time: {self.performance_metrics.avg_response_time:.3f}s, "
                               f"Success rate: {self.performance_metrics.success_count / self.performance_metrics.request_count * 100:.1f}%")
    
    def _check_circuit_breaker(self, endpoint: str) -> bool:
        """Check if circuit breaker allows the request."""
        if not self.enable_circuit_breaker:
            return True
            
        with self.circuit_breaker_lock:
            current_time = time.time()
            
            if self.circuit_breaker_stats.state == CircuitBreakerState.OPEN:
                # Check if recovery timeout has passed
                if (self.circuit_breaker_stats.last_failure_time and 
                    current_time - self.circuit_breaker_stats.last_failure_time >= self.circuit_breaker_config.recovery_timeout):
                    self.circuit_breaker_stats.state = CircuitBreakerState.HALF_OPEN
                    self.circuit_breaker_stats.consecutive_successes = 0
                    logger.info(f"Circuit breaker transitioning to HALF_OPEN for endpoint {endpoint}")
                    return True
                else:
                    logger.warning(f"Circuit breaker OPEN - rejecting request to {endpoint}")
                    return False
            
            return True
    
    def _update_circuit_breaker(self, endpoint: str, success: bool):
        """Update circuit breaker state based on request result."""
        if not self.enable_circuit_breaker:
            return
            
        with self.circuit_breaker_lock:
            if success:
                self.circuit_breaker_stats.success_count += 1
                
                if self.circuit_breaker_stats.state == CircuitBreakerState.HALF_OPEN:
                    self.circuit_breaker_stats.consecutive_successes += 1
                    if self.circuit_breaker_stats.consecutive_successes >= self.circuit_breaker_config.success_threshold:
                        self.circuit_breaker_stats.state = CircuitBreakerState.CLOSED
                        self.circuit_breaker_stats.failure_count = 0
                        logger.info(f"Circuit breaker CLOSED for endpoint {endpoint}")
                elif self.circuit_breaker_stats.state == CircuitBreakerState.CLOSED:
                    # Reset failure count on success
                    self.circuit_breaker_stats.failure_count = max(0, self.circuit_breaker_stats.failure_count - 1)
            else:
                self.circuit_breaker_stats.failure_count += 1
                self.circuit_breaker_stats.last_failure_time = time.time()
                self.circuit_breaker_stats.consecutive_successes = 0
                
                if (self.circuit_breaker_stats.state == CircuitBreakerState.CLOSED and 
                    self.circuit_breaker_stats.failure_count >= self.circuit_breaker_config.failure_threshold):
                    self.circuit_breaker_stats.state = CircuitBreakerState.OPEN
                    logger.warning(f"Circuit breaker OPEN for endpoint {endpoint} after {self.circuit_breaker_stats.failure_count} failures")
                elif self.circuit_breaker_stats.state == CircuitBreakerState.HALF_OPEN:
                    self.circuit_breaker_stats.state = CircuitBreakerState.OPEN
                    logger.warning(f"Circuit breaker back to OPEN for endpoint {endpoint}")
    
    def _log_request(self, method: str, url: str, data: Optional[Dict] = None, params: Optional[Dict] = None):
        """Log request details."""
        # Create a sanitized version of data for logging (remove sensitive info)
        log_data = None
        if data:
            log_data = {k: v if k not in ['password', 'token', 'secret'] else '***' for k, v in data.items()}
        
        logger.debug(f"Request: {method} {url}")
        if log_data:
            logger.debug(f"Request data: {json.dumps(log_data, indent=2)}")
        if params:
            logger.debug(f"Request params: {json.dumps(params, indent=2)}")
    
    def _log_response(self, response: requests.Response, response_time: float):
        """Log response details."""
        logger.debug(f"Response: {response.status_code} in {response_time:.3f}s")
        
        # Log response headers (excluding sensitive ones) - handle mock objects gracefully
        try:
            if hasattr(response, 'headers') and response.headers:
                safe_headers = {k: v for k, v in response.headers.items() 
                               if k.lower() not in ['authorization', 'x-api-key', 'set-cookie']}
                logger.debug(f"Response headers: {json.dumps(dict(safe_headers), indent=2)}")
        except (AttributeError, TypeError):
            # Handle mock objects or other cases where headers aren't iterable
            logger.debug("Response headers: <not available>")
        
        # Log response body for non-2xx responses or if debug level is very high
        if response.status_code >= 400 or logger.isEnabledFor(logging.DEBUG):
            try:
                response_data = response.json()
                # Handle mock objects that return mock data
                if hasattr(response_data, '_mock_name'):
                    logger.debug("Response body: <mock data>")
                else:
                    logger.debug(f"Response body: {json.dumps(response_data, indent=2)}")
            except (ValueError, json.JSONDecodeError, AttributeError, TypeError):
                # Handle cases where response doesn't have json() method or it fails
                try:
                    if hasattr(response, 'text'):
                        logger.debug(f"Response body (text): {response.text[:500]}...")
                    else:
                        logger.debug("Response body: <not available>")
                except AttributeError:
                    logger.debug("Response body: <not available>")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        with self.performance_lock:
            return {
                'global_metrics': {
                    'request_count': self.performance_metrics.request_count,
                    'avg_response_time': self.performance_metrics.avg_response_time,
                    'success_count': self.performance_metrics.success_count,
                    'error_count': self.performance_metrics.error_count,
                    'success_rate': (self.performance_metrics.success_count / 
                                   max(1, self.performance_metrics.request_count) * 100),
                    'last_request_time': self.performance_metrics.last_request_time
                },
                'endpoint_metrics': dict(self.performance_metrics.endpoint_metrics),
                'circuit_breaker': {
                    'state': self.circuit_breaker_stats.state.value,
                    'failure_count': self.circuit_breaker_stats.failure_count,
                    'success_count': self.circuit_breaker_stats.success_count,
                    'last_failure_time': self.circuit_breaker_stats.last_failure_time
                }
            }
    
    def reset_performance_metrics(self):
        """Reset performance metrics."""
        with self.performance_lock:
            self.performance_metrics = PerformanceMetrics()
        logger.info("Performance metrics reset")
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic, circuit breaker, and performance monitoring.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (without base URL)
            data: Request body data
            params: Query parameters
            
        Returns:
            Response data as dictionary
            
        Raises:
            Exception: If request fails after all retries or circuit breaker is open
        """
        url = f"{self.base_url}{endpoint}"
        correlation_id = str(uuid.uuid4())
        
        # Set correlation context for structured logging
        context = create_correlation_context(
            operation_id=f"http_{method.lower()}_{endpoint.replace('/', '_')}",
            metadata={
                'method': method,
                'endpoint': endpoint,
                'url': url
            }
        )
        structured_logger.set_correlation_context(context)
        
        try:
            # Use error recovery decorator
            @with_error_recovery(
                operation_name=f"http_request_{method}_{endpoint}",
                recovery_manager=global_recovery_manager,
                correlation_id=correlation_id,
                metadata={'method': method, 'endpoint': endpoint}
            )
            def make_request_with_recovery():
                return self._execute_request(method, url, data, params, correlation_id)
            
            return make_request_with_recovery()
            
        finally:
            structured_logger.clear_correlation_context()
    
    def _sanitize_payload(self, obj: Any) -> Any:
        """Recursively replace float inf, -inf, and nan with JSON-compliant values."""
        import math
        if isinstance(obj, dict):
            return {k: self._sanitize_payload(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._sanitize_payload(x) for x in obj]
        elif isinstance(obj, float):
            if math.isinf(obj):
                return 999999.99 if obj > 0 else -999999.99
            elif math.isnan(obj):
                return 0.0
            return obj
        return obj

    def _execute_request(self, method: str, url: str, data: Optional[Dict], params: Optional[Dict], correlation_id: str) -> Dict[str, Any]:
        """Execute the actual HTTP request."""
        # Check circuit breaker
        if not self._check_circuit_breaker(url):
            raise Exception(f"Circuit breaker is OPEN for endpoint {url}")
        
        # Log request with structured logging
        structured_logger.info(f"Making {method} request", {
            'url': url,
            'has_data': data is not None,
            'has_params': params is not None,
            'correlation_id': correlation_id
        })
        
        # Sanitize data to remove any float('inf') or nan values that are not JSON compliant
        sanitized_data = self._sanitize_payload(data) if data is not None else None
        
        start_time = time.time()
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=sanitized_data,
                params=params,
                timeout=self.timeout,
                headers={'X-Correlation-ID': correlation_id}
            )
            request_time = time.time() - start_time
            
            # Log response with structured logging
            structured_logger.info(f"Request completed", {
                'status_code': response.status_code,
                'response_time_ms': request_time * 1000,
                'correlation_id': correlation_id
            })
            
            # Handle different response codes
            if response.status_code in [200, 201]:
                # Success - update metrics and circuit breaker
                self._update_performance_metrics(url, request_time, True)
                self._update_circuit_breaker(url, True)
                
                try:
                    return response.json()
                except (ValueError, json.JSONDecodeError):
                    return {'success': True, 'data': response.text}
                    
            elif response.status_code == 404:
                # Client error - don't retry, update metrics, but treat server as online/responsive
                self._update_performance_metrics(url, request_time, False)
                self._update_circuit_breaker(url, True)
                
                structured_logger.error(f"Endpoint not found", {
                    'url': url,
                    'status_code': response.status_code,
                    'correlation_id': correlation_id
                })
                raise Exception(f"API endpoint not found: {url}")
                
            elif response.status_code >= 500:
                # Server error - will be retried by error recovery
                structured_logger.warning(f"Server error", {
                    'status_code': response.status_code,
                    'correlation_id': correlation_id
                })
                raise Exception(f"Server error: {response.status_code}")
                
            else:
                # Other client errors (400, 409, etc.) - don't retry, but treat server as online/responsive
                self._update_performance_metrics(url, request_time, False)
                self._update_circuit_breaker(url, True)
                
                structured_logger.error(f"Request failed", {
                    'status_code': response.status_code,
                    'response_text': response.text[:500],
                    'correlation_id': correlation_id
                })
                raise Exception(f"API request failed with status {response.status_code}: {response.text}")
                
        except requests.exceptions.ConnectionError as e:
            structured_logger.error(f"Connection error", {
                'error': str(e),
                'correlation_id': correlation_id
            })
            raise Exception(f"Failed to connect to backend API: {str(e)}")
        
        except requests.exceptions.Timeout as e:
            structured_logger.error(f"Request timeout", {
                'timeout': self.timeout,
                'correlation_id': correlation_id
            })
            raise Exception(f"Request timeout after {self.timeout}s")
        
        except Exception as e:
            # Don't retry on 404 or other client errors
            if "endpoint not found" in str(e).lower():
                raise e
            
            structured_logger.error(f"Unexpected request error", {
                'error': str(e),
                'correlation_id': correlation_id
            })
            raise e
    
    def post_resources(self, resources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Post resource inventory data to the backend.
        
        Args:
            resources: List of resource data dictionaries
            
        Returns:
            API response
        """
        logger.info(f"Posting {len(resources)} resources to backend")
        
        results = []
        errors = []
        
        for resource in resources:
            try:
                # Add timestamp and source if not present
                if 'timestamp' not in resource:
                    resource['timestamp'] = datetime.now(timezone.utc).isoformat()
                
                result = self._make_request('POST', '/api/resources', data=resource)
                results.append(result)
                
            except Exception as e:
                logger.error(f"Failed to post resource {resource.get('resourceId', 'unknown')}: {e}")
                errors.append({
                    'resourceId': resource.get('resourceId', 'unknown'),
                    'error': str(e)
                })
        
        return {
            'success': len(errors) == 0,
            'data': {
                'posted': results,
                'errors': errors
            },
            'message': f"Posted {len(results)} resources, {len(errors)} errors",
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

    def post_data(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generic method to post data to a specific endpoint.
        
        Args:
            endpoint: API endpoint
            data: Data to post
            
        Returns:
            API response
        """
        logger.debug(f"Posting data to {endpoint}")
        return self._make_request('POST', endpoint, data=data)

    def put_data(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generic method to put data to a specific endpoint.
        
        Args:
            endpoint: API endpoint
            data: Data to put
            
        Returns:
            API response
        """
        logger.debug(f"Putting data to {endpoint}")
        return self._make_request('PUT', endpoint, data=data)
    
    def post_optimizations(self, optimizations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Post optimization recommendations to the backend.
        
        Args:
            optimizations: List of optimization recommendation dictionaries
            
        Returns:
            API response
        """
        logger.info(f"Posting {len(optimizations)} optimizations to backend")
        
        results = []
        errors = []
        
        for optimization in optimizations:
            try:
                # Add timestamp if not present
                if 'timestamp' not in optimization:
                    optimization['timestamp'] = datetime.now(timezone.utc).isoformat()
                
                result = self._make_request('POST', '/api/optimizations', data=optimization)
                results.append(result)
                
            except Exception as e:
                logger.error(f"Failed to post optimization {optimization.get('optimizationId', 'unknown')}: {e}")
                errors.append({
                    'optimizationId': optimization.get('optimizationId', 'unknown'),
                    'error': str(e)
                })
        
        return {
            'success': len(errors) == 0,
            'data': {
                'posted': results,
                'errors': errors
            },
            'message': f"Posted {len(results)} optimizations, {len(errors)} errors",
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def post_anomalies(self, anomalies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Post cost anomalies to the backend.
        
        Args:
            anomalies: List of anomaly dictionaries
            
        Returns:
            API response
        """
        logger.info(f"Posting {len(anomalies)} anomalies to backend")
        
        payload = {
            'anomalies': anomalies,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'source': 'finops-bot'
        }
        
        return self._make_request('POST', '/api/anomalies/batch', data=payload)
    
    def post_budget_forecasts(self, forecasts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Post budget forecasts to the backend.
        
        Args:
            forecasts: List of budget forecast dictionaries
            
        Returns:
            API response
        """
        logger.info(f"Posting {len(forecasts)} budget forecasts to backend")
        
        payload = {
            'forecasts': forecasts,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'source': 'finops-bot'
        }
        
        return self._make_request('POST', '/api/budgets', data=payload)
    
    def get_resources(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get resource inventory from the backend.
        
        Args:
            filters: Optional filters for the request
            
        Returns:
            API response with resources
        """
        logger.debug("Getting resources from backend")
        return self._make_request('GET', '/api/resources', params=filters)
    
    def get_optimizations(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get optimization recommendations from the backend.
        
        Args:
            filters: Optional filters for the request
            
        Returns:
            API response with optimizations
        """
        logger.debug("Getting optimizations from backend")
        return self._make_request('GET', '/api/optimizations', params=filters)
    
    def approve_optimization(self, optimization_id: str, approved: bool = True) -> Dict[str, Any]:
        """
        Approve or reject an optimization recommendation.
        
        Args:
            optimization_id: ID of the optimization to approve/reject
            approved: Whether to approve (True) or reject (False)
            
        Returns:
            API response
        """
        logger.info(f"{'Approving' if approved else 'Rejecting'} optimization {optimization_id}")
        
        payload = {
            'optimization_id': optimization_id,
            'approved': approved,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        return self._make_request('POST', '/api/optimizations/approve', data=payload)
    
    def set_authentication(self, api_key: str, auth_type: str = "bearer"):
        """
        Set or update authentication credentials.
        
        Args:
            api_key: API key or token
            auth_type: Authentication type ("bearer", "api_key", or "basic")
        """
        self.api_key = api_key
        
        # Remove existing auth headers
        headers_to_remove = ['Authorization', 'X-API-Key']
        for header in headers_to_remove:
            self.session.headers.pop(header, None)
        
        # Set new auth header based on type
        if auth_type.lower() == "bearer":
            self.session.headers['Authorization'] = f'Bearer {api_key}'
        elif auth_type.lower() == "api_key":
            self.session.headers['X-API-Key'] = api_key
        elif auth_type.lower() == "basic":
            # For basic auth, api_key should be base64 encoded username:password
            self.session.headers['Authorization'] = f'Basic {api_key}'
        
        logger.info(f"Authentication updated: {auth_type}")

    def post_savings(self, savings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Post savings data to the backend.
        
        Args:
            savings: List of savings record dictionaries
            
        Returns:
            API response
        """
        logger.info(f"Posting {len(savings)} savings records to backend")
        
        payload = {
            'savings': savings,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'source': 'finops-bot'
        }
        
        return self._make_request('POST', '/api/savings', data=payload)
    
    def post_pricing_recommendations(self, recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Post pricing recommendations to the backend.
        
        Args:
            recommendations: List of pricing recommendation dictionaries
            
        Returns:
            API response
        """
        logger.info(f"Posting {len(recommendations)} pricing recommendations to backend")
        
        payload = {
            'recommendations': recommendations,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'source': 'finops-bot'
        }
        
        return self._make_request('POST', '/api/pricing', data=payload)
    
    def get_anomalies(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get cost anomalies from the backend.
        
        Args:
            filters: Optional filters for the request
            
        Returns:
            API response with anomalies
        """
        logger.debug("Getting anomalies from backend")
        return self._make_request('GET', '/api/anomalies', params=filters)
    
    def get_budgets(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get budgets from the backend.
        
        Args:
            filters: Optional filters for the request
            
        Returns:
            API response with budgets
        """
        logger.debug("Getting budgets from backend")
        return self._make_request('GET', '/api/budgets', params=filters)
    
    def get_savings(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get savings data from the backend.
        
        Args:
            filters: Optional filters for the request
            
        Returns:
            API response with savings
        """
        logger.debug("Getting savings from backend")
        return self._make_request('GET', '/api/savings', params=filters)
    
    def validate_data_schema(self, data: Dict[str, Any], schema_type: str) -> Dict[str, Any]:
        """
        Validate data against expected schema before sending to API.
        
        Args:
            data: Data to validate
            schema_type: Type of schema to validate against
            
        Returns:
            Validation result with success status and errors
        """
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Define required fields for different data types
        schema_requirements = {
            'resource': {
                'required': ['resourceId', 'resourceType', 'region'],
                'optional': ['currentCost', 'utilizationMetrics', 'timestamp', 'accountId']
            },
            'optimization': {
                'required': ['optimizationId', 'resourceId', 'optimizationType', 'estimatedSavings'],
                'optional': ['riskLevel', 'confidenceScore', 'timestamp', 'accountId']
            },
            'anomaly': {
                'required': ['anomalyId', 'anomalyType', 'severity', 'actualCost', 'expectedCost'],
                'optional': ['region', 'rootCause', 'timestamp', 'accountId']
            },
            'budget': {
                'required': ['budgetId', 'budgetType', 'budgetAmount'],
                'optional': ['parentBudgetId', 'tags', 'timestamp', 'accountId']
            }
        }
        
        if schema_type not in schema_requirements:
            validation_result['warnings'].append(f"Unknown schema type: {schema_type}")
            return validation_result
        
        schema = schema_requirements[schema_type]
        
        # Check required fields
        for field in schema['required']:
            if field not in data or data[field] is None:
                validation_result['valid'] = False
                validation_result['errors'].append(f"Missing required field: {field}")
        
        # Check data types for common fields
        if 'timestamp' in data and data['timestamp']:
            try:
                from datetime import datetime
                if isinstance(data['timestamp'], str):
                    datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
            except ValueError:
                validation_result['warnings'].append("Invalid timestamp format")
        
        # Validate numeric fields
        numeric_fields = ['currentCost', 'estimatedSavings', 'actualCost', 'expectedCost', 'budgetAmount']
        for field in numeric_fields:
            if field in data and data[field] is not None:
                try:
                    float(data[field])
                except (ValueError, TypeError):
                    validation_result['valid'] = False
                    validation_result['errors'].append(f"Invalid numeric value for {field}: {data[field]}")
        
        # Validate enum fields
        if 'riskLevel' in data and data['riskLevel'] not in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']:
            validation_result['warnings'].append(f"Unknown risk level: {data['riskLevel']}")
        
        if 'severity' in data and data['severity'] not in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']:
            validation_result['warnings'].append(f"Unknown severity: {data['severity']}")
        
        return validation_result
    
    def health_check(self) -> bool:
        """
        Check if the backend API is healthy and reachable.
        Also reports circuit breaker status.
        
        Returns:
            True if backend is healthy, False otherwise
        """
        try:
            # Try to make a simple GET request to a health endpoint
            # If no health endpoint exists, try the base API
            try:
                response = self._make_request('GET', '/health')
            except Exception as e:
                if "endpoint not found" in str(e).lower():
                    # Fallback to checking resources endpoint
                    response = self._make_request('GET', '/api/resources')
                else:
                    raise e
                    
            is_healthy = response.get('success', False) or response.get('status') == 'ok'
            
            if is_healthy:
                logger.info("Backend health check passed")
                # Log circuit breaker status
                with self.circuit_breaker_lock:
                    logger.info(f"Circuit breaker state: {self.circuit_breaker_stats.state.value}")
            
            return is_healthy
            
        except Exception as e:
            logger.error(f"Backend health check failed: {e}")
            return False