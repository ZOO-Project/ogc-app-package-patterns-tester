"""Tests for data models."""

from ogc_patterns_tester.models import (
    ExecutionResult,
    JobInfo,
    JobStatus,
    PatternConfig,
    PatternType,
    ProcessInfo,
    ServerConfig,
)


class TestJobStatus:
    """Test JobStatus enum."""

    def test_job_status_values(self):
        """Test JobStatus enum values."""
        assert JobStatus.RUNNING.value == "running"
        assert JobStatus.SUCCESSFUL.value == "successful"
        assert JobStatus.FAILED.value == "failed"
        assert JobStatus.DISMISSED.value == "dismissed"
        assert JobStatus.ACCEPTED.value == "accepted"
        assert JobStatus.UNKNOWN.value == "unknown"


class TestPatternType:
    """Test PatternType enum."""

    def test_pattern_type_from_pattern_id(self):
        """Test pattern type determination from pattern ID."""
        assert PatternType.from_pattern_id("pattern-1") == PatternType.BASIC_PROCESSING
        assert PatternType.from_pattern_id("pattern-4") == PatternType.SCATTER_GATHER
        assert (
            PatternType.from_pattern_id("pattern-5") == PatternType.CONDITIONAL_WORKFLOW
        )
        assert PatternType.from_pattern_id("pattern-6") == PatternType.NESTED_WORKFLOW

    def test_pattern_type_unknown_pattern(self):
        """Test pattern type for unknown pattern ID."""
        # Should handle unknown patterns gracefully
        try:
            result = PatternType.from_pattern_id("unknown-pattern")
            # If it doesn't raise an exception, it should return a sensible default
            assert result in PatternType
        except (KeyError, ValueError):
            # It's acceptable to raise an exception for unknown patterns
            pass


class TestServerConfig:
    """Test ServerConfig dataclass."""

    def test_server_config_basic(self):
        """Test basic ServerConfig creation."""
        config = ServerConfig(
            base_url="https://example.com/ogc-api",
            username="testuser",
            password="testpass",
            timeout=60,
        )

        assert config.base_url == "https://example.com/ogc-api"
        assert config.username == "testuser"
        assert config.password == "testpass"
        assert config.timeout == 60

    def test_server_config_legacy_auth_token(self):
        """Test ServerConfig with legacy auth_token mapping."""
        config = ServerConfig(
            base_url="https://example.com/ogc-api", auth_token="legacy-token-123"
        )

        # Legacy auth_token should be mapped to api_key
        assert config.auth_token == "legacy-token-123"
        assert config.api_key == "legacy-token-123"

    def test_server_config_api_key_precedence(self):
        """Test that api_key takes precedence over auth_token."""
        config = ServerConfig(
            base_url="https://example.com/ogc-api",
            auth_token="legacy-token",
            api_key="new-api-key",
        )

        # api_key should not be overwritten by auth_token
        assert config.auth_token == "legacy-token"
        assert config.api_key == "new-api-key"

    def test_server_config_defaults(self):
        """Test ServerConfig default values."""
        config = ServerConfig(base_url="https://example.com/ogc-api")

        assert config.auth_token is None
        assert config.username is None
        assert config.password is None
        assert config.api_key is None
        assert config.timeout == 300


class TestPatternConfig:
    """Test PatternConfig dataclass."""

    def test_pattern_config_creation(self):
        """Test PatternConfig creation."""
        config = PatternConfig(
            pattern_id="test-pattern-1",
            cwl_url="https://example.com/test.cwl",
            parameters={"input": "test_value"},
            pattern_type=PatternType.BASIC_PROCESSING,
        )

        assert config.pattern_id == "test-pattern-1"
        assert config.cwl_url == "https://example.com/test.cwl"
        assert config.parameters == {"input": "test_value"}
        assert config.pattern_type == PatternType.BASIC_PROCESSING


class TestProcessInfo:
    """Test ProcessInfo dataclass."""

    def test_process_info_creation(self):
        """Test ProcessInfo creation."""
        info = ProcessInfo(
            process_id="test-process", title="Test Process", deployed=True
        )

        assert info.process_id == "test-process"
        assert info.title == "Test Process"
        assert info.deployed is True


class TestJobInfo:
    """Test JobInfo dataclass."""

    def test_job_info_creation(self):
        """Test JobInfo creation."""
        info = JobInfo(
            job_id="job-123",
            process_id="process-456",
            status=JobStatus.RUNNING,
            progress=50,
            message="Processing...",
            outputs={"result": "partial"},
        )

        assert info.job_id == "job-123"
        assert info.process_id == "process-456"
        assert info.status == JobStatus.RUNNING
        assert info.progress == 50
        assert info.message == "Processing..."
        assert info.outputs == {"result": "partial"}


class TestExecutionResult:
    """Test ExecutionResult dataclass."""

    def test_execution_result_success(self):
        """Test ExecutionResult for successful execution."""
        result = ExecutionResult(
            pattern_id="pattern-1",
            success=True,
            job_id="job-123",
            execution_time=120.5,
            message=None,
            outputs={"result": "success"},
        )

        assert result.pattern_id == "pattern-1"
        assert result.success is True
        assert result.job_id == "job-123"
        assert result.execution_time == 120.5
        assert result.message is None
        assert result.outputs == {"result": "success"}

    def test_execution_result_failure(self):
        """Test ExecutionResult for failed execution."""
        result = ExecutionResult(
            pattern_id="pattern-2",
            success=False,
            job_id=None,
            execution_time=0,
            message="Process deployment failed",
            outputs=None,
        )

        assert result.pattern_id == "pattern-2"
        assert result.success is False
        assert result.job_id is None
        assert result.execution_time == 0
        assert result.message == "Process deployment failed"
        assert result.outputs is None
