"""
Tests for retry utilities module.

Tests retry logic, exponential backoff, and error handling for API calls.

Author: Harsh
"""

import pytest
import requests
from unittest.mock import Mock, patch, call
import responses
from common.retry_utils import (
    create_retry_decorator,
    api_request_with_retry,
    safe_api_call
)


@pytest.mark.unit
class TestRetryDecorator:
    """Test retry decorator creation and configuration."""

    def test_create_retry_decorator_default_params(self):
        """Test creating retry decorator with default parameters."""
        decorator = create_retry_decorator()

        assert decorator is not None
        assert callable(decorator)

    def test_create_retry_decorator_custom_params(self):
        """Test creating retry decorator with custom parameters."""
        decorator = create_retry_decorator(
            max_attempts=5,
            min_wait=1,
            max_wait=30,
            multiplier=3
        )

        assert decorator is not None
        assert callable(decorator)

    def test_retry_decorator_on_success(self):
        """Test retry decorator succeeds on first attempt."""
        decorator = create_retry_decorator(max_attempts=3)

        @decorator
        def successful_function():
            return "success"

        result = successful_function()
        assert result == "success"

    def test_retry_decorator_retries_on_connection_error(self):
        """Test retry decorator retries on ConnectionError."""
        decorator = create_retry_decorator(max_attempts=3, min_wait=0, max_wait=0)
        call_count = {'count': 0}

        @decorator
        def failing_function():
            call_count['count'] += 1
            if call_count['count'] < 3:
                raise requests.exceptions.ConnectionError("Connection failed")
            return "success after retries"

        result = failing_function()
        assert result == "success after retries"
        assert call_count['count'] == 3

    def test_retry_decorator_gives_up_after_max_attempts(self):
        """Test retry decorator gives up after max attempts."""
        decorator = create_retry_decorator(max_attempts=3, min_wait=0, max_wait=0)
        call_count = {'count': 0}

        @decorator
        def always_failing_function():
            call_count['count'] += 1
            raise requests.exceptions.ConnectionError("Always fails")

        with pytest.raises(requests.exceptions.ConnectionError):
            always_failing_function()

        assert call_count['count'] == 3  # Tried 3 times


@pytest.mark.unit
@responses.activate
class TestAPIRequestWithRetry:
    """Test api_request_with_retry function."""

    def test_successful_post_request(self):
        """Test successful POST request on first attempt."""
        responses.add(
            responses.POST,
            'http://localhost:11434/api/generate',
            json={'response': 'test response'},
            status=200
        )

        response = api_request_with_retry(
            url='http://localhost:11434/api/generate',
            method='POST',
            json={'prompt': 'test'}
        )

        assert response.status_code == 200
        assert response.json() == {'response': 'test response'}

    def test_successful_get_request(self):
        """Test successful GET request."""
        responses.add(
            responses.GET,
            'http://localhost:11434/api/version',
            json={'version': '1.0.0'},
            status=200
        )

        response = api_request_with_retry(
            url='http://localhost:11434/api/version',
            method='GET'
        )

        assert response.status_code == 200
        assert response.json() == {'version': '1.0.0'}

    def test_raises_http_error_on_404(self):
        """Test that HTTP 404 error is raised."""
        responses.add(
            responses.POST,
            'http://localhost:11434/api/generate',
            json={'error': 'not found'},
            status=404
        )

        with pytest.raises(requests.exceptions.HTTPError):
            api_request_with_retry(
                url='http://localhost:11434/api/generate',
                method='POST',
                json={'prompt': 'test'}
            )

    def test_raises_http_error_on_500(self):
        """Test that HTTP 500 error is raised."""
        responses.add(
            responses.POST,
            'http://localhost:11434/api/generate',
            json={'error': 'server error'},
            status=500
        )

        with pytest.raises(requests.exceptions.HTTPError):
            api_request_with_retry(
                url='http://localhost:11434/api/generate',
                method='POST',
                json={'prompt': 'test'}
            )


@pytest.mark.unit
class TestSafeAPICall:
    """Test safe_api_call wrapper function."""

    def test_successful_api_call(self):
        """Test safe_api_call with successful function."""
        def successful_function(x, y):
            return x + y

        result = safe_api_call(successful_function, 5, 10)
        assert result == 15

    def test_api_call_with_exception_returns_fallback(self):
        """Test safe_api_call returns fallback on exception."""
        def failing_function():
            raise ValueError("Something went wrong")

        result = safe_api_call(
            failing_function,
            fallback_value="fallback"
        )
        assert result == "fallback"

    def test_api_call_with_kwargs(self):
        """Test safe_api_call with keyword arguments."""
        def function_with_kwargs(a, b=10):
            return a * b

        result = safe_api_call(function_with_kwargs, 5, b=20)
        assert result == 100

    def test_api_call_logs_exception(self, caplog):
        """Test that safe_api_call logs exceptions."""
        def failing_function():
            raise RuntimeError("Test error")

        with caplog.at_level('ERROR'):
            result = safe_api_call(
                failing_function,
                fallback_value=None
            )

        assert result is None
        assert "API call failed" in caplog.text

    def test_api_call_with_none_fallback(self):
        """Test safe_api_call with None as fallback."""
        def failing_function():
            raise Exception("Error")

        result = safe_api_call(
            failing_function,
            fallback_value=None
        )
        assert result is None

    def test_api_call_with_complex_fallback(self):
        """Test safe_api_call with complex fallback value."""
        def failing_function():
            raise Exception("Error")

        fallback = {
            'error': True,
            'message': 'Service unavailable',
            'retry_after': 60
        }

        result = safe_api_call(
            failing_function,
            fallback_value=fallback
        )

        assert result == fallback
        assert result['error'] is True


@pytest.mark.slow
@pytest.mark.integration
class TestRetryTimingBehavior:
    """Test retry timing and exponential backoff behavior (integration tests)."""

    def test_exponential_backoff_timing(self):
        """Test that exponential backoff increases wait time."""
        decorator = create_retry_decorator(
            max_attempts=3,
            min_wait=1,
            max_wait=4,
            multiplier=2
        )
        call_times = []

        @decorator
        def function_with_timing():
            import time
            call_times.append(time.time())
            if len(call_times) < 3:
                raise requests.exceptions.ConnectionError("Retry")
            return "success"

        result = function_with_timing()

        assert result == "success"
        assert len(call_times) == 3

        # Check that wait time increases (approximately)
        # First to second call: ~1 second wait
        # Second to third call: ~2 seconds wait
        if len(call_times) >= 2:
            wait1 = call_times[1] - call_times[0]
            assert wait1 >= 1.0  # At least 1 second wait

        if len(call_times) >= 3:
            wait2 = call_times[2] - call_times[1]
            assert wait2 >= 2.0  # At least 2 seconds wait


@pytest.mark.unit
class TestRetryWithDifferentExceptionTypes:
    """Test retry behavior with different exception types."""

    def test_retries_on_timeout_error(self):
        """Test retry on Timeout error."""
        decorator = create_retry_decorator(max_attempts=2, min_wait=0, max_wait=0)
        call_count = {'count': 0}

        @decorator
        def timeout_function():
            call_count['count'] += 1
            if call_count['count'] == 1:
                raise requests.exceptions.Timeout("Timeout")
            return "success"

        result = timeout_function()
        assert result == "success"
        assert call_count['count'] == 2

    def test_retries_on_request_exception(self):
        """Test retry on generic RequestException."""
        decorator = create_retry_decorator(max_attempts=2, min_wait=0, max_wait=0)
        call_count = {'count': 0}

        @decorator
        def request_error_function():
            call_count['count'] += 1
            if call_count['count'] == 1:
                raise requests.exceptions.RequestException("Request failed")
            return "success"

        result = request_error_function()
        assert result == "success"
        assert call_count['count'] == 2

    def test_does_not_retry_on_non_network_errors(self):
        """Test that non-network errors are not retried."""
        decorator = create_retry_decorator(max_attempts=3, min_wait=0, max_wait=0)
        call_count = {'count': 0}

        @decorator
        def value_error_function():
            call_count['count'] += 1
            raise ValueError("This should not retry")

        with pytest.raises(ValueError):
            value_error_function()

        # Should only be called once (no retries for ValueError)
        assert call_count['count'] == 1
