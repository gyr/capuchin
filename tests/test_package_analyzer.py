"""Tests for Capuchin."""

import json
import logging
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.package_analyzer import Capuchin


@pytest.fixture
def sample_buildinfo_output() -> str:
    """Sample buildinfo output for testing."""
    return """Build bash (SLE15-SP7)

bash (Standard)
  required by:
    - bash-completion (Standard)

bash-doc (Standard)
"""


@pytest.fixture
def sample_ex_bash_included() -> str:
    """Sample ex output for bash (included in media)."""
    return """SLE-15-SP7-Full-x86_64-GM-Media1:
 └─> bash include
     is required by rpm: filesystem"""


@pytest.fixture
def sample_ex_bash_doc_not_included() -> str:
    """Sample ex output for bash-doc (not in media)."""
    return ""


@pytest.fixture
def analyzer(tmp_path: Path) -> Capuchin:
    """Create Capuchin instance for testing."""
    monkey_path = "/opt/monkey"
    return Capuchin(monkey_path=monkey_path, output_dir=tmp_path)


class TestCapuchinInit:
    """Test Capuchin initialization."""

    def test_init_with_defaults(self, tmp_path: Path) -> None:
        """Test initialization with default output directory."""
        analyzer = Capuchin(monkey_path="/opt/monkey")
        assert analyzer.monkey_path == "/opt/monkey"
        assert analyzer.output_dir == Path.cwd()

    def test_init_with_custom_output_dir(self, tmp_path: Path) -> None:
        """Test initialization with custom output directory."""
        analyzer = Capuchin(monkey_path="/opt/monkey", output_dir=tmp_path)
        assert analyzer.monkey_path == "/opt/monkey"
        assert analyzer.output_dir == tmp_path


class TestCommandExecution:
    """Test command execution methods."""

    @patch("subprocess.run")
    def test_run_buildinfo_success(
        self, mock_run: MagicMock, analyzer: Capuchin, sample_buildinfo_output: str
    ) -> None:
        """Test successful buildinfo command execution."""
        mock_run.return_value = MagicMock(stdout=sample_buildinfo_output, returncode=0)

        result = analyzer._run_buildinfo("bash")

        assert result == sample_buildinfo_output
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        cmd = args[0]
        assert cmd == ["monkey", "buildinfo", "bash"]
        assert kwargs["cwd"] == analyzer.monkey_path

    @patch("subprocess.run")
    def test_run_buildinfo_command_failure(self, mock_run: MagicMock, analyzer: Capuchin) -> None:
        """Test buildinfo command failure."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "monkey")

        with pytest.raises(RuntimeError, match="Failed to run monkey buildinfo"):
            analyzer._run_buildinfo("nonexistent")

    @patch("subprocess.run")
    def test_run_ex_success(
        self, mock_run: MagicMock, analyzer: Capuchin, sample_ex_bash_included: str
    ) -> None:
        """Test successful ex command execution (monkey ex outputs to stderr)."""
        mock_run.return_value = MagicMock(stdout="", stderr=sample_ex_bash_included, returncode=0)

        result = analyzer._run_ex("bash")

        assert result == sample_ex_bash_included
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        cmd = args[0]
        assert cmd == ["monkey", "ex", "bash"]
        assert kwargs["cwd"] == analyzer.monkey_path

    @patch("subprocess.run")
    def test_run_ex_command_failure(self, mock_run: MagicMock, analyzer: Capuchin) -> None:
        """Test ex command failure."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "monkey")

        with pytest.raises(RuntimeError, match="Failed to run monkey ex"):
            analyzer._run_ex("nonexistent")


class TestAnalyzeSourcePackage:
    """Test analyze_source_package method."""

    @patch.object(Capuchin, "_run_ex")
    @patch.object(Capuchin, "_run_buildinfo")
    def test_analyze_source_package(
        self,
        mock_buildinfo: MagicMock,
        mock_ex: MagicMock,
        analyzer: Capuchin,
        sample_buildinfo_output: str,
        sample_ex_bash_included: str,
        sample_ex_bash_doc_not_included: str,
    ) -> None:
        """Test analyzing a single source package."""
        mock_buildinfo.return_value = sample_buildinfo_output
        # Return different ex outputs for bash vs bash-doc
        mock_ex.side_effect = [sample_ex_bash_included, sample_ex_bash_doc_not_included]

        source_data = analyzer.analyze_source_package("bash")

        # Check source name
        assert source_data.source_name == "bash"

        # Check binaries dict has both packages
        assert "bash" in source_data.binaries
        assert "bash-doc" in source_data.binaries

        # Check bash binary (included in media)
        bash_data = source_data.binaries["bash"]
        assert bash_data.required_by == ["bash-completion"]
        assert bash_data.included is True
        assert "filesystem" in bash_data.required_by_rpm

        # Check bash-doc binary (not in media)
        bash_doc_data = source_data.binaries["bash-doc"]
        assert bash_doc_data.required_by == []
        assert bash_doc_data.included is False
        assert bash_doc_data.required_by_rpm == []


class TestAnalyzePackages:
    """Test analyze_packages method."""

    @patch.object(Capuchin, "analyze_source_package")
    def test_analyze_multiple_packages(self, mock_analyze: MagicMock, analyzer: Capuchin) -> None:
        """Test analyzing multiple source packages."""
        from src.models import BinaryPackageData, SourcePackageData

        # Mock return values for two source packages
        bash_data = SourcePackageData(
            source_name="bash",
            binaries={
                "bash": BinaryPackageData(
                    required_by=["rpm"],
                    included=True,
                    required_by_rpm=["filesystem"],
                )
            },
        )
        grep_data = SourcePackageData(
            source_name="grep",
            binaries={
                "grep": BinaryPackageData(
                    required_by=[],
                    included=False,
                    required_by_rpm=[],
                )
            },
        )
        mock_analyze.side_effect = [bash_data, grep_data]

        result = analyzer.analyze_packages(["bash", "grep"])

        # Should be keyed by source package name
        assert "bash" in result
        assert "grep" in result

        # Check bash data (SourcePackageData object)
        bash_source = result["bash"]
        assert "bash" in bash_source.binaries
        assert bash_source.binaries["bash"].included is True

        # Check grep data (SourcePackageData object)
        grep_source = result["grep"]
        assert "grep" in grep_source.binaries
        assert grep_source.binaries["grep"].included is False

    @patch("src.package_analyzer.Progress")
    @patch.object(Capuchin, "analyze_source_package")
    def test_analyze_packages_with_progress_bar(
        self, mock_analyze: MagicMock, mock_progress_class: MagicMock, analyzer: Capuchin
    ) -> None:
        """Test that progress bar is displayed during analysis."""
        from src.models import BinaryPackageData, SourcePackageData

        # Create mock progress instance
        mock_progress = MagicMock()
        mock_progress_class.return_value.__enter__.return_value = mock_progress
        mock_task_id = MagicMock()
        mock_progress.add_task.return_value = mock_task_id

        # Mock analyze_source_package
        mock_data = SourcePackageData(
            source_name="bash",
            binaries={"bash": BinaryPackageData(required_by=[], included=True, required_by_rpm=[])},
        )
        mock_analyze.return_value = mock_data

        # Analyze with progress (default)
        analyzer.analyze_packages(["bash", "grep", "coreutils"])

        # Verify Progress was created
        mock_progress_class.assert_called_once()

        # Verify task was added with total count
        mock_progress.add_task.assert_called_once_with("Analyzing packages", total=3)

        # Verify update was called for each package (3 times)
        assert mock_progress.update.call_count == 3
        mock_progress.update.assert_called_with(mock_task_id, advance=1)

    @patch("src.package_analyzer.Progress")
    @patch.object(Capuchin, "analyze_source_package")
    def test_analyze_packages_without_progress_bar(
        self, mock_analyze: MagicMock, mock_progress_class: MagicMock, analyzer: Capuchin
    ) -> None:
        """Test that progress bar is not displayed when show_progress=False."""
        from src.models import BinaryPackageData, SourcePackageData

        mock_data = SourcePackageData(
            source_name="bash",
            binaries={"bash": BinaryPackageData(required_by=[], included=True, required_by_rpm=[])},
        )
        mock_analyze.return_value = mock_data

        # Analyze without progress
        analyzer.analyze_packages(["bash", "grep"], show_progress=False)

        # Verify Progress was NOT created
        mock_progress_class.assert_not_called()

    @patch("src.package_analyzer.Progress")
    @patch.object(Capuchin, "analyze_source_package")
    def test_progress_bar_uses_count_based_columns(
        self, mock_analyze: MagicMock, mock_progress_class: MagicMock, analyzer: Capuchin
    ) -> None:
        """Test that progress bar uses count-based columns, not time remaining."""
        from rich.progress import (
            BarColumn,
            MofNCompleteColumn,
            TaskProgressColumn,
            TextColumn,
        )

        from src.models import BinaryPackageData, SourcePackageData

        mock_data = SourcePackageData(
            source_name="bash",
            binaries={"bash": BinaryPackageData(required_by=[], included=True, required_by_rpm=[])},
        )
        mock_analyze.return_value = mock_data

        analyzer.analyze_packages(["bash", "grep"], show_progress=True)

        # Verify Progress was called with specific columns (not default)
        mock_progress_class.assert_called_once()
        call_args = mock_progress_class.call_args

        # Should have exactly 4 column arguments
        assert len(call_args[0]) == 4

        # Verify column types in order
        assert isinstance(call_args[0][0], TextColumn)
        assert isinstance(call_args[0][1], BarColumn)
        assert isinstance(call_args[0][2], MofNCompleteColumn)  # "5/25" format
        assert isinstance(call_args[0][3], TaskProgressColumn)  # Percentage


class TestWriteResults:
    """Test _write_results method."""

    def test_write_results_single_file(self, analyzer: Capuchin) -> None:
        """Test writing results to single packages.json file."""
        from src.models import BinaryPackageData, SourcePackageData

        # Create test data
        bash_data = SourcePackageData(
            source_name="bash",
            binaries={
                "bash": BinaryPackageData(
                    required_by=["rpm"],
                    included=True,
                    required_by_rpm=["filesystem"],
                ),
                "bash-doc": BinaryPackageData(
                    required_by=[],
                    included=False,
                    required_by_rpm=[],
                ),
            },
        )

        packages_data = {"bash": bash_data}

        analyzer._write_results(packages_data)

        # Check that packages.json was created
        output_file = analyzer.output_dir / "packages.json"
        assert output_file.exists()

        # Load and verify JSON structure
        with open(output_file) as f:
            data = json.load(f)

        # Should be keyed by source package
        assert "bash" in data

        # Should have nested binary packages
        assert "bash" in data["bash"]
        assert "bash-doc" in data["bash"]

        # Verify bash binary data
        bash_binary = data["bash"]["bash"]
        assert bash_binary["required_by"] == ["rpm"]
        assert bash_binary["included"] is True
        assert bash_binary["required_by_rpm"] == ["filesystem"]

        # Verify bash-doc binary data
        bash_doc = data["bash"]["bash-doc"]
        assert bash_doc["required_by"] == []
        assert bash_doc["included"] is False
        assert bash_doc["required_by_rpm"] == []


class TestAnalyzeAndWrite:
    """Test analyze_and_write method."""

    @patch.object(Capuchin, "_write_results")
    @patch.object(Capuchin, "analyze_packages")
    def test_analyze_and_write(
        self,
        mock_analyze: MagicMock,
        mock_write: MagicMock,
        analyzer: Capuchin,
    ) -> None:
        """Test analyze_and_write orchestration."""
        mock_packages_data = {"bash": MagicMock()}
        mock_analyze.return_value = mock_packages_data

        analyzer.analyze_and_write(["bash"])

        mock_analyze.assert_called_once_with(["bash"], show_progress=True)
        mock_write.assert_called_once_with(mock_packages_data)


class TestLogging:
    """Test logging behavior in Capuchin."""

    @patch.object(Capuchin, "_run_buildinfo")
    @patch.object(Capuchin, "_run_ex")
    def test_analyze_source_package_logs_start(
        self,
        mock_ex: MagicMock,
        mock_buildinfo: MagicMock,
        analyzer: Capuchin,
        sample_buildinfo_output: str,
        sample_ex_bash_included: str,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test that analyzing a package logs INFO message."""
        mock_buildinfo.return_value = sample_buildinfo_output
        mock_ex.return_value = sample_ex_bash_included

        with caplog.at_level(logging.INFO):
            analyzer.analyze_source_package("bash")

        assert "Analyzing source package: bash" in caplog.text

    @patch.object(Capuchin, "_run_buildinfo")
    @patch.object(Capuchin, "_run_ex")
    def test_analyze_source_package_logs_binary_count(
        self,
        mock_ex: MagicMock,
        mock_buildinfo: MagicMock,
        analyzer: Capuchin,
        sample_buildinfo_output: str,
        sample_ex_bash_included: str,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test that binary package count is logged."""
        mock_buildinfo.return_value = sample_buildinfo_output
        mock_ex.return_value = sample_ex_bash_included

        with caplog.at_level(logging.INFO):
            analyzer.analyze_source_package("bash")

        assert "Found 2 binary packages" in caplog.text

    @patch("subprocess.run")
    def test_run_buildinfo_logs_command(
        self,
        mock_run: MagicMock,
        analyzer: Capuchin,
        sample_buildinfo_output: str,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test that buildinfo command is logged at DEBUG level."""
        mock_run.return_value = MagicMock(stdout=sample_buildinfo_output, returncode=0)

        with caplog.at_level(logging.DEBUG):
            analyzer._run_buildinfo("bash")

        assert "Running: monkey buildinfo bash" in caplog.text

    @patch("subprocess.run")
    def test_run_ex_logs_command(
        self,
        mock_run: MagicMock,
        analyzer: Capuchin,
        sample_ex_bash_included: str,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test that ex command is logged at DEBUG level."""
        mock_run.return_value = MagicMock(stdout="", stderr=sample_ex_bash_included, returncode=0)

        with caplog.at_level(logging.DEBUG):
            analyzer._run_ex("bash")

        assert "Running: monkey ex bash" in caplog.text

    def test_analyze_packages_logs_total_count(
        self,
        analyzer: Capuchin,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test that total package count is logged."""
        with patch.object(analyzer, "analyze_source_package") as mock_analyze:
            mock_analyze.return_value = MagicMock()

            with caplog.at_level(logging.INFO):
                analyzer.analyze_packages(["bash", "coreutils"])

        assert "Starting analysis of 2 source packages" in caplog.text

    def test_analyze_packages_logs_completion(
        self,
        analyzer: Capuchin,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test that completion is logged with timing."""
        with patch.object(analyzer, "analyze_source_package") as mock_analyze:
            mock_analyze.return_value = MagicMock()

            with caplog.at_level(logging.INFO):
                analyzer.analyze_packages(["bash"])

        # Should log completion with elapsed time
        assert "Completed analysis" in caplog.text
        assert "elapsed" in caplog.text.lower()
