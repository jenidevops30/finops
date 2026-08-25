#!/usr/bin/env python3
"""
Error Recovery Mechanisms for Advanced FinOps Platform

This module provides comprehensive error recovery mechanisms including:
- Exponential backoff for AWS API failures
- Circuit breaker pattern for fault tolerance
- Retry strategies with intelligent failure classification
- Error context preservation and correlation
- Recovery state management and persistence

Requirements: 4.4 - Error recovery mechanisms for AWS API failures with exponential backoff
"""

import logging
import time
import json
import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Callable, Union, Type
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict
import random
import pickle
from pathlib import Path

from botocore.exceptions import (
    ClientError, 
    NoCredentialsError, 
    PartialCredentialsError,
    BotoCoreError,
    EndpointConnectionError,
    TokenRetrievalError,
    ProfileNotFound,
    ConnectTimeoutError,
    ReadTimeoutError
)

from .monitoring import StructuredLogger, AlertSeverity, system_monitor


class ErrorCategory(Enum):
    """Categories of errors for different recovery strategies."""
    TRANSIENT = "TRANSIENT"          # Temporary errors that should be retried
    THROTTLING = "THROTTLING"        # Rate limiting errors
    AUTHENTICATION = "AUTHENTICATION" # Auth/credential errors
    AUTHORIZATION = "AUTHORIZATION"   # Permission errors
    CLIENT_ERROR = "CLIENT_ERROR"     # Client-side errors (don't retry)
    SERVER_ERROR = "SERVER_ERROR"     # Server-side errors (retry with backoff)
    NETWORK_ERROR = "NETWORK_ERROR"   # Network connectivity issues
    TIMEOUT_ERROR = "TIMEOUT_ERROR"   # Request timeout errors
    RESOURCE_ERROR = "RESOURCE_ERROR" # Resource not found/unavailable
    UNKNOWN_ERROR = "UNKNOWN_ERROR"   # Unclassified errors


class RecoveryStrategy(Enum):
    """Recovery strategies for different error types."""
    IMMEDIATE_RETRY = "IMMEDIATE_RETRY"
    EXPONENTIAL_BACKOFF = "EXPONENTIAL_BACKOFF"
    LINEAR_BACKOFF = "LINEAR_BACKOFF"
    CIRCUIT_BREAKER = "CIRCUIT_BREAKER"
    NO_RETRY = "NO_RETRY"
    CUSTOM_STRATEGY = "CUSTOM_STRATEGY"


@dataclass
class ErrorContext:
    """Context information for error tracking and recovery."""
    error_id: str
    operation_name: str
    error_category: ErrorCategory
    error_message: str
    exception_type: str
    timestamp: float
    attempt_number: int
    correlation_id: Optional[str] = None
    aws_service: Optional[str] = None
    aws_region: Optional[str] = None
    resource_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RecoveryConfig:
    """Configuration for error recovery strategies."""
    max_retries: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    multiplier: float = 2.0
    jitter: bool = True
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: float = 60.0
    enable_persistence: bool = True
    custom_strategy: Optional[Callable] = None


@dataclass
class RecoveryState:
    """State tracking for error recovery."""
    operation_name: str
    consecutive_failures: int = 0
    last_failure_time: Optional[float] = None
    circuit_breaker_open: bool = False
    circuit_breaker_open_time: Optional[float] = None
    total_attempts: int = 0
    total_successes: int = 0
    total_failures: int = 0
    error_history: List[ErrorContext] = field(default_factory=list)


class ErrorClassifier:
    """Classifies errors into categories for appropriate recovery strategies."""
    
    def __init__(self):
        self.logger = StructuredLogger('finops.error_classifier')
        
        # AWS error code mappings
        self.throttling_errors = {
            'Throttling', 'ThrottlingException', 'RequestLimitExceeded',
            'TooManyRequestsException', 'ProvisionedThroughputExceededException',
            'RequestThrottledException', 'SlowDown', 'BandwidthLimitExceeded'
        }
        
        self.authentication_errors = {
            'InvalidUserID.NotFound', 'AuthFailure', 'UnauthorizedOperation',
            'InvalidAccessKeyId', 'SignatureDoesNotMatch', 'TokenRefreshRequired',
            'ExpiredToken', 'InvalidToken'
        }
        
        self.authorization_errors = {
            'AccessDenied', 'Forbidden', 'UnauthorizedOperation',
            'InsufficientPrivileges', 'PermissionDenied'
        }
        
        self.client_errors = {
            'ValidationException', 'InvalidParameterValue', 'InvalidParameterCombination',
            'MissingParameter', 'InvalidRequest', 'MalformedPolicyDocument',
            'InvalidInput', 'BadRequest'
        }
        
        self.server_errors = {
            'InternalError', 'InternalFailure', 'ServiceUnavailable',
            'InternalServerError', 'ServiceException', 'ServiceFailure'
        }
        
        self.resource_errors = {
            'ResourceNotFound', 'NoSuchBucket', 'NoSuchKey', 'DBInstanceNotFound',
            'FunctionNotFound', 'InstanceNotFound', 'VolumeNotFound'
        }
        
        self.timeout_errors = {
            'RequestTimeout', 'RequestTimeoutException', 'TimeoutError'
        }
    
    def classify_error(self, exception: Exception, aws_service: Optional[str] = None) -> ErrorCategory:
        """
        Classify an error into a category for recovery strategy selection.
        
        Args:
            exception: The exception to classify
            aws_service: AWS service name for context
            
        Returns:
            Error category
        """
        error_code = None
        error_message = str(exception)
        
        # Extract AWS error code if available
        if isinstance(exception, ClientError):
            error_code = exception.response.get('Error', {}).get('Code', '')
        
        # Network and connection errors
        if isinstance(exception, (EndpointConnectionError, ConnectTimeoutError)):
            return ErrorCategory.NETWORK_ERROR
        
        # Timeout errors
        if isinstance(exception, (ReadTimeoutError,)) or error_code in self.timeout_errors:
            return ErrorCategory.TIMEOUT_ERROR
        
        # Authentication errors
        if isinstance(exception, (NoCredentialsError, PartialCredentialsError, TokenRetrievalError)):
            return ErrorCategory.AUTHENTICATION
        
        if error_code in self.authentication_errors:
            return ErrorCategory.AUTHENTICATION
        
        # Authorization errors
        if error_code in self.authorization_errors:
            return ErrorCategory.AUTHORIZATION
        
        # Throttling errors
        if error_code in self.throttling_errors:
            return ErrorCategory.THROTTLING
        
        # Client errors (don't retry)
        if error_code in self.client_errors:
            return ErrorCategory.CLIENT_ERROR
        
        # Server errors (retry with backoff)
        if error_code in self.server_errors:
            return ErrorCategory.SERVER_ERROR
        
        # Resource errors
        if error_code in self.resource_errors:
            return ErrorCategory.RESOURCE_ERROR
        
        # HTTP status code based classification for ClientError
        if isinstance(exception, ClientError):
            status_code = exception.response.get('ResponseMetadata', {}).get('HTTPStatusCode', 0)
            
            if 400 <= status_code < 500:
                if status_code == 429:  # Too Many Requests
                    return ErrorCategory.THROTTLING
                elif status_code in [401, 403]:  # Unauthorized, Forbidden
                    return ErrorCategory.AUTHORIZATION
                elif status_code == 404:  # Not Found
                    return ErrorCategory.RESOURCE_ERROR
                else:
                    return ErrorCategory.CLIENT_ERROR
            elif 500 <= status_code < 600:
                return ErrorCategory.SERVER_ERROR

        # Check for HTTP status codes in standard exception messages (e.g. from HTTP client)
        if "status 4" in error_message.lower() or "status code 4" in error_message.lower() or "status_code 4" in error_message.lower():
            return ErrorCategory.CLIENT_ERROR
        if "status 5" in error_message.lower() or "status code 5" in error_message.lower() or "status_code 5" in error_message.lower():
            return ErrorCategory.SERVER_ERROR

        
        # Transient errors (network, temporary issues)
        transient_keywords = ['timeout', 'connection', 'network', 'temporary', 'unavailable']
        if any(keyword in error_message.lower() for keyword in transient_keywords):
            return ErrorCategory.TRANSIENT
        
        # Default to unknown
        return ErrorCategory.UNKNOWN_ERROR
    
    def get_recovery_strategy(self, error_category: ErrorCategory) -> RecoveryStrategy:
        """
        Get recommended recovery strategy for an error category.
        
        Args:
            error_category: The error category
            
        Returns:
            Recommended recovery strategy
        """
        strategy_map = {
            ErrorCategory.TRANSIENT: RecoveryStrategy.EXPONENTIAL_BACKOFF,
            ErrorCategory.THROTTLING: RecoveryStrategy.EXPONENTIAL_BACKOFF,
            ErrorCategory.AUTHENTICATION: RecoveryStrategy.NO_RETRY,
            ErrorCategory.AUTHORIZATION: RecoveryStrategy.NO_RETRY,
            ErrorCategory.CLIENT_ERROR: RecoveryStrategy.NO_RETRY,
            ErrorCategory.SERVER_ERROR: RecoveryStrategy.EXPONENTIAL_BACKOFF,
            ErrorCategory.NETWORK_ERROR: RecoveryStrategy.EXPONENTIAL_BACKOFF,
            ErrorCategory.TIMEOUT_ERROR: RecoveryStrategy.LINEAR_BACKOFF,
            ErrorCategory.RESOURCE_ERROR: RecoveryStrategy.NO_RETRY,
            ErrorCategory.UNKNOWN_ERROR: RecoveryStrategy.EXPONENTIAL_BACKOFF
        }
        
        return strategy_map.get(error_category, RecoveryStrategy.NO_RETRY)


class RecoveryManager:
    """Manages error recovery state and strategies."""
    
    def __init__(self, config: Optional[RecoveryConfig] = None, state_file: Optional[str] = None):
        self.config = config or RecoveryConfig()
        self.state_file = state_file or "recovery_state.pkl"
        self.logger = StructuredLogger('finops.recovery_manager')
        self.classifier = ErrorClassifier()
        
        # Recovery state tracking
        self.recovery_states: Dict[str, RecoveryState] = {}
        self.lock = threading.Lock()
        
        # Load persisted state if available
        if self.config.enable_persistence:
            self._load_state()
    
    def _load_state(self):
        """Load recovery state from disk."""
        try:
            if Path(self.state_file).exists():
                with open(self.state_file, 'rb') as f:
                    self.recovery_states = pickle.load(f)
                self.logger.info(f"Loaded recovery state for {len(self.recovery_states)} operations")
        except Exception as e:
            self.logger.warning(f"Failed to load recovery state: {str(e)}")
    
    def _save_state(self):
        """Save recovery state to disk."""
        if not self.config.enable_persistence:
            return
        
        try:
            with open(self.state_file, 'wb') as f:
                pickle.dump(self.recovery_states, f)
        except Exception as e:
            self.logger.warning(f"Failed to save recovery state: {str(e)}")
    
    def _get_or_create_state(self, operation_name: str) -> RecoveryState:
        """Get or create recovery state for an operation."""
        with self.lock:
            if operation_name not in self.recovery_states:
                self.recovery_states[operation_name] = RecoveryState(operation_name=operation_name)
            return self.recovery_states[operation_name]
    
    def _calculate_delay(self, attempt: int, strategy: RecoveryStrategy, error_category: ErrorCategory) -> float:
        """Calculate delay for retry attempt."""
        if strategy == RecoveryStrategy.IMMEDIATE_RETRY:
            return 0.0
        
        elif strategy == RecoveryStrategy.EXPONENTIAL_BACKOFF:
            delay = min(
                self.config.initial_delay * (self.config.multiplier ** attempt),
                self.config.max_delay
            )
            
            # Add extra delay for throttling errors
            if error_category == ErrorCategory.THROTTLING:
                delay *= 2
            
        elif strategy == RecoveryStrategy.LINEAR_BACKOFF:
            delay = min(
                self.config.initial_delay * (attempt + 1),
                self.config.max_delay
            )
        
        else:
            delay = self.config.initial_delay
        
        # Add jitter to prevent thundering herd
        if self.config.jitter and delay > 0:
            jitter_range = delay * 0.1
            delay += random.uniform(-jitter_range, jitter_range)
        
        return max(0, delay)
    
    def _should_open_circuit_breaker(self, state: RecoveryState) -> bool:
        """Determine if circuit breaker should be opened."""
        return (state.consecutive_failures >= self.config.circuit_breaker_threshold and
                not state.circuit_breaker_open)
    
    def _should_close_circuit_breaker(self, state: RecoveryState) -> bool:
        """Determine if circuit breaker should be closed."""
        if not state.circuit_breaker_open:
            return False
        
        if state.circuit_breaker_open_time is None:
            return False
        
        return (time.time() - state.circuit_breaker_open_time) >= self.config.circuit_breaker_timeout
    
    def record_error(self, 
                    operation_name: str,
                    exception: Exception,
                    attempt_number: int,
                    correlation_id: Optional[str] = None,
                    aws_service: Optional[str] = None,
                    aws_region: Optional[str] = None,
                    resource_id: Optional[str] = None,
                    metadata: Optional[Dict[str, Any]] = None) -> ErrorContext:
        """
        Record an error occurrence for recovery tracking.
        
        Args:
            operation_name: Name of the operation that failed
            exception: The exception that occurred
            attempt_number: Current attempt number
            correlation_id: Correlation ID for tracking
            aws_service: AWS service name
            aws_region: AWS region
            resource_id: Resource identifier
            metadata: Additional metadata
            
        Returns:
            Error context object
        """
        error_category = self.classifier.classify_error(exception, aws_service)
        
        error_context = ErrorContext(
            error_id=f"{operation_name}_{int(time.time())}_{attempt_number}",
            operation_name=operation_name,
            error_category=error_category,
            error_message=str(exception),
            exception_type=type(exception).__name__,
            timestamp=time.time(),
            attempt_number=attempt_number,
            correlation_id=correlation_id,
            aws_service=aws_service,
            aws_region=aws_region,
            resource_id=resource_id,
            metadata=metadata or {}
        )
        
        # Update recovery state
        state = self._get_or_create_state(operation_name)
        with self.lock:
            if error_category != ErrorCategory.CLIENT_ERROR:
                state.consecutive_failures += 1
            state.last_failure_time = time.time()
            state.total_attempts += 1
            state.total_failures += 1
            state.error_history.append(error_context)
            
            # Keep only recent error history
            if len(state.error_history) > 100:
                state.error_history = state.error_history[-100:]
            
            # Check circuit breaker
            if self._should_open_circuit_breaker(state):
                state.circuit_breaker_open = True
                state.circuit_breaker_open_time = time.time()
                
                # Create alert for circuit breaker opening
                system_monitor.alert_manager.create_alert(
                    severity=AlertSeverity.ERROR,
                    title=f"Circuit Breaker Opened: {operation_name}",
                    message=f"Circuit breaker opened for {operation_name} after {state.consecutive_failures} consecutive failures",
                    source="error_recovery",
                    correlation_id=correlation_id,
                    metadata={
                        'operation_name': operation_name,
                        'consecutive_failures': state.consecutive_failures,
                        'error_category': error_category.value
                    }
                )
        
        # Save state
        self._save_state()
        
        # Log error with structured logging
        self.logger.error(f"Operation failed: {operation_name}", {
            'error_id': error_context.error_id,
            'error_category': error_category.value,
            'exception_type': error_context.exception_type,
            'attempt_number': attempt_number,
            'consecutive_failures': state.consecutive_failures,
            'aws_service': aws_service,
            'aws_region': aws_region,
            'resource_id': resource_id
        })
        
        return error_context
    
    def record_success(self, operation_name: str, correlation_id: Optional[str] = None):
        """
        Record a successful operation for recovery tracking.
        
        Args:
            operation_name: Name of the operation that succeeded
            correlation_id: Correlation ID for tracking
        """
        state = self._get_or_create_state(operation_name)
        
        with self.lock:
            state.consecutive_failures = 0
            state.total_attempts += 1
            state.total_successes += 1
            
            # Close circuit breaker if it was open
            if state.circuit_breaker_open:
                state.circuit_breaker_open = False
                state.circuit_breaker_open_time = None
                
                # Create alert for circuit breaker closing
                system_monitor.alert_manager.create_alert(
                    severity=AlertSeverity.INFO,
                    title=f"Circuit Breaker Closed: {operation_name}",
                    message=f"Circuit breaker closed for {operation_name} after successful operation",
                    source="error_recovery",
                    correlation_id=correlation_id,
                    metadata={'operation_name': operation_name}
                )
        
        # Save state
        self._save_state()
        
        self.logger.info(f"Operation succeeded: {operation_name}", {
            'total_successes': state.total_successes,
            'success_rate': state.total_successes / max(1, state.total_attempts)
        })
    
    def should_retry(self, operation_name: str, error_context: ErrorContext) -> bool:
        """
        Determine if an operation should be retried.
        
        Args:
            operation_name: Name of the operation
            error_context: Error context from the failure
            
        Returns:
            True if operation should be retried
        """
        state = self._get_or_create_state(operation_name)
        
        # Check circuit breaker
        if state.circuit_breaker_open:
            if not self._should_close_circuit_breaker(state):
                self.logger.warning(f"Circuit breaker open for {operation_name}, not retrying")
                return False
        
        # Check max retries
        if error_context.attempt_number >= self.config.max_retries:
            self.logger.warning(f"Max retries exceeded for {operation_name}")
            return False
        
        # Check recovery strategy
        strategy = self.classifier.get_recovery_strategy(error_context.error_category)
        
        if strategy == RecoveryStrategy.NO_RETRY:
            self.logger.info(f"No retry strategy for {error_context.error_category.value}")
            return False
        
        return True
    
    def get_retry_delay(self, operation_name: str, error_context: ErrorContext) -> float:
        """
        Get delay before retry attempt.
        
        Args:
            operation_name: Name of the operation
            error_context: Error context from the failure
            
        Returns:
            Delay in seconds
        """
        strategy = self.classifier.get_recovery_strategy(error_context.error_category)
        return self._calculate_delay(error_context.attempt_number, strategy, error_context.error_category)
    
    def get_recovery_stats(self, operation_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get recovery statistics.
        
        Args:
            operation_name: Specific operation name, or None for all operations
            
        Returns:
            Recovery statistics
        """
        with self.lock:
            if operation_name:
                if operation_name not in self.recovery_states:
                    return {}
                
                state = self.recovery_states[operation_name]
                return {
                    'operation_name': operation_name,
                    'total_attempts': state.total_attempts,
                    'total_successes': state.total_successes,
                    'total_failures': state.total_failures,
                    'success_rate': state.total_successes / max(1, state.total_attempts),
                    'consecutive_failures': state.consecutive_failures,
                    'circuit_breaker_open': state.circuit_breaker_open,
                    'last_failure_time': state.last_failure_time,
                    'recent_errors': [
                        {
                            'error_category': err.error_category.value,
                            'error_message': err.error_message,
                            'timestamp': err.timestamp,
                            'attempt_number': err.attempt_number
                        }
                        for err in state.error_history[-10:]  # Last 10 errors
                    ]
                }
            else:
                # Return summary for all operations
                total_attempts = sum(state.total_attempts for state in self.recovery_states.values())
                total_successes = sum(state.total_successes for state in self.recovery_states.values())
                total_failures = sum(state.total_failures for state in self.recovery_states.values())
                
                return {
                    'total_operations': len(self.recovery_states),
                    'total_attempts': total_attempts,
                    'total_successes': total_successes,
                    'total_failures': total_failures,
                    'overall_success_rate': total_successes / max(1, total_attempts),
                    'operations_with_circuit_breaker_open': sum(
                        1 for state in self.recovery_states.values() if state.circuit_breaker_open
                    ),
                    'operations': {
                        name: {
                            'success_rate': state.total_successes / max(1, state.total_attempts),
                            'consecutive_failures': state.consecutive_failures,
                            'circuit_breaker_open': state.circuit_breaker_open
                        }
                        for name, state in self.recovery_states.items()
                    }
                }


def with_error_recovery(operation_name: str, 
                       recovery_manager: Optional[RecoveryManager] = None,
                       correlation_id: Optional[str] = None,
                       aws_service: Optional[str] = None,
                       aws_region: Optional[str] = None,
                       resource_id: Optional[str] = None,
                       metadata: Optional[Dict[str, Any]] = None):
    """
    Decorator to add error recovery to a function.
    
    Args:
        operation_name: Name of the operation for tracking
        recovery_manager: Recovery manager instance (creates default if None)
        correlation_id: Correlation ID for tracking
        aws_service: AWS service name
        aws_region: AWS region
        resource_id: Resource identifier
        metadata: Additional metadata
    """
    if recovery_manager is None:
        recovery_manager = RecoveryManager()
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            attempt = 0
            
            while True:
                attempt += 1
                start_time = time.time()
                
                try:
                    result = func(*args, **kwargs)
                    
                    # Record success
                    recovery_manager.record_success(operation_name, correlation_id)
                    
                    # Record performance metric
                    duration_ms = (time.time() - start_time) * 1000
                    system_monitor.record_operation_metric(operation_name, duration_ms, True)
                    
                    return result
                    
                except Exception as e:
                    # Record error
                    error_context = recovery_manager.record_error(
                        operation_name=operation_name,
                        exception=e,
                        attempt_number=attempt,
                        correlation_id=correlation_id,
                        aws_service=aws_service,
                        aws_region=aws_region,
                        resource_id=resource_id,
                        metadata=metadata
                    )
                    
                    # Record performance metric
                    duration_ms = (time.time() - start_time) * 1000
                    system_monitor.record_operation_metric(operation_name, duration_ms, False)
                    
                    # Check if we should retry
                    if not recovery_manager.should_retry(operation_name, error_context):
                        raise e
                    
                    # Wait before retry
                    delay = recovery_manager.get_retry_delay(operation_name, error_context)
                    if delay > 0:
                        time.sleep(delay)
        
        return wrapper
    return decorator


# Global recovery manager instance
global_recovery_manager = RecoveryManager()