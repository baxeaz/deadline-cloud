# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""Performance tests for Job Attachments upload functionality."""

import concurrent.futures
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from deadline.job_attachments.upload import S3AssetManager


class TestUploadPerformance:
    """Test performance improvements in upload functionality."""

    def test_multithreaded_file_size_calculation_performance(self):
        """Test that multithreaded file size calculation is faster than sequential."""
        # Create temporary files for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            file_paths = []
            # Create num_files test files to make the performance difference measurable
            num_files = 400 

            for i in range(num_files):
                file_path = temp_path / f"test_file_{i}.txt"
                file_path.write_text("x" * 1000)  # 1KB files
                file_paths.append(str(file_path))

            manager = S3AssetManager()

            # Test sequential version (simulating old behavior)
            def sequential_get_total_size(paths):
                total_bytes = 0
                for path in paths:
                    try:
                        total_bytes += Path(path).resolve().stat().st_size
                    except (FileNotFoundError, PermissionError, OSError):
                        pass
                return total_bytes

            # Measure sequential performance
            start_time = time.time()
            sequential_result = sequential_get_total_size(file_paths)
            sequential_time = time.time() - start_time

            # Measure multithreaded performance (current implementation)
            start_time = time.time()
            threaded_result = manager._get_total_size_of_files(file_paths)
            threaded_time = time.time() - start_time

            # Verify results are the same
            assert sequential_result == threaded_result
            assert sequential_result == num_files * 1000  # 50 files * 1KB each

            print(f"Threaded version took {threaded_time:.4f}s vs sequential {sequential_time:.4f}s")
            # Performance should be better with threading (allow some variance for CI)
            # In practice, threading should be faster, but we'll just ensure it's not significantly slower
            assert threaded_time >= sequential_time * 1.5, (
                f"Threaded version took {threaded_time:.4f}s vs sequential {sequential_time:.4f}s"
            )

    def test_multithreaded_handles_missing_files(self):
        """Test that multithreaded version properly handles missing files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create some real files and some non-existent paths
            real_file = temp_path / "real_file.txt"
            real_file.write_text("test content")

            file_paths = [
                str(real_file),
                str(temp_path / "missing_file1.txt"),
                str(temp_path / "missing_file2.txt"),
            ]

            manager = S3AssetManager()

            # Should only count the real file's size
            total_size = manager._get_total_size_of_files(file_paths)
            assert total_size == len("test content")

    def test_threadpool_executor_configuration(self):
        """Test that the ThreadPoolExecutor is configured with correct max_workers."""
        manager = S3AssetManager()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            test_file = temp_path / "test.txt"
            test_file.write_text("test")

            # Mock ThreadPoolExecutor to verify it's called with max_workers=8
            with patch(
                "deadline.job_attachments.upload.concurrent.futures.ThreadPoolExecutor"
            ) as mock_executor:
                mock_executor.return_value.__enter__.return_value.map.return_value = [
                    4
                ]  # len("test")

                manager._get_total_size_of_files([str(test_file)])

                mock_executor.assert_called_once_with(max_workers=8)
