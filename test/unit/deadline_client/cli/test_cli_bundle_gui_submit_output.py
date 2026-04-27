# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""
Tests for the _print_response function used by `deadline bundle gui-submit`.
"""

import json

from click.testing import CliRunner
import click

from deadline.client.cli._groups.bundle_group import _print_response


def _invoke_print_response(**kwargs):
    """Run _print_response inside a Click context so click.echo works."""

    @click.command()
    def cmd():
        _print_response(**kwargs)

    runner = CliRunner()
    return runner.invoke(cmd)


class TestPrintResponseJson:
    def test_submitted(self):
        result = _invoke_print_response(
            output="json",
            job_bundle_dir="/bundles/my_job",
            job_history_bundle_dir="/history/my_job_2024",
            job_id="job-0123456789abcdef0123456789abcdef",
        )
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert parsed == {
            "status": "SUBMITTED",
            "jobId": "job-0123456789abcdef0123456789abcdef",
            "jobHistoryBundleDirectory": "/history/my_job_2024",
        }

    def test_canceled(self):
        result = _invoke_print_response(
            output="json",
            job_bundle_dir="/bundles/my_job",
            job_history_bundle_dir=None,
            job_id=None,
        )
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert parsed == {"status": "CANCELED"}


class TestPrintResponseVerbose:
    def test_submitted(self):
        result = _invoke_print_response(
            output="verbose",
            job_bundle_dir="/bundles/my_job",
            job_history_bundle_dir="/history/my_job_2024",
            job_id="job-0123456789abcdef0123456789abcdef",
        )
        assert result.exit_code == 0
        assert "Submitted job bundle:" in result.output
        assert "/bundles/my_job" in result.output
        assert "job-0123456789abcdef0123456789abcdef" in result.output

    def test_canceled(self):
        result = _invoke_print_response(
            output="verbose",
            job_bundle_dir="/bundles/my_job",
            job_history_bundle_dir=None,
            job_id=None,
        )
        assert result.exit_code == 0
        assert "Job submission canceled." in result.output
