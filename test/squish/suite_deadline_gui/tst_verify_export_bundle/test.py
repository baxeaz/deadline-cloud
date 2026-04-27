# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# -*- coding: utf-8 -*-
# mypy: disable-error-code="attr-defined"

import os
import glob

import config
import choose_jobbundledir_helpers
import choose_jobbundledir_locators
import gui_submitter_locators
import squish
import test


def init():
    # launch Choose Job Bundle GUI Submitter based on OS platform being tested
    choose_jobbundledir_helpers.detect_platform_and_launch_jobbundle_guisubmitter()
    # verify Choose job bundle directory is open
    test.compare(
        str(
            squish.waitForObjectExists(
                choose_jobbundledir_locators.choose_job_bundle_dir
            ).windowTitle
        ),
        "Choose job bundle directory",
        "Expect Choose job bundle directory window title to be present.",
    )


def main():
    # select Simple UI - No Job Attachments job bundle (no auth needed for export)
    choose_jobbundledir_helpers.select_jobbundle(config.simple_ui_no_ja)

    # verify GUI Submitter dialogue opens
    test.compare(
        squish.waitForObjectExists(gui_submitter_locators.aws_submitter_dialogue).visible,
        True,
        "Expect AWS Deadline Cloud Submitter to be open.",
    )

    # verify export bundle button exists and is enabled
    test.compare(
        str(squish.waitForObjectExists(gui_submitter_locators.export_bundle_button).text),
        "Export bundle",
        "Expect Export bundle button to contain correct text.",
    )
    test.compare(
        squish.waitForObjectExists(gui_submitter_locators.export_bundle_button).enabled,
        True,
        "Expect Export bundle button to be enabled.",
    )

    # click export bundle button
    test.log("Clicking 'Export bundle' button.")
    squish.clickButton(squish.waitForObject(gui_submitter_locators.export_bundle_button))

    # verify success message box appears
    message_box = {"type": "QMessageBox", "unnamed": 1, "visible": 1}
    test.compare(
        squish.waitForObjectExists(message_box).visible,
        True,
        "Expect success message box to appear after export.",
    )
    message_text = str(squish.waitForObjectExists(message_box).text)
    test.verify(
        "Saved the submission as a job bundle" in message_text,
        "Expect message box to confirm bundle was saved.",
    )

    # extract the exported bundle path from the message
    # message format: "Saved the submission as a job bundle:\n<path>"
    exported_path = message_text.split("\n")[-1].strip() if "\n" in message_text else None
    test.log(f"Exported bundle path: {exported_path}")

    # dismiss the message box by clicking OK
    ok_button = {
        "text": "OK",
        "type": "QPushButton",
        "unnamed": 1,
        "visible": 1,
        "window": message_box,
    }
    squish.clickButton(squish.waitForObject(ok_button))

    # verify the exported bundle directory exists and contains a template file
    if exported_path and os.path.isdir(exported_path):
        test.passes(f"Exported bundle directory exists: {exported_path}")
        template_files = glob.glob(os.path.join(exported_path, "template.*"))
        test.verify(
            len(template_files) > 0,
            "Expect exported bundle to contain a template file.",
        )
    else:
        test.fail(f"Exported bundle directory does not exist: {exported_path}")

    # verify the submitter dialogue closed after export
    test.verify(
        not object.exists(gui_submitter_locators.aws_submitter_dialogue),
        "Expect AWS Submitter dialogue to close after export.",
    )


def cleanup():
    # if the submitter is still open, close it
    try:
        if object.exists(gui_submitter_locators.aws_submitter_dialogue):
            test.log("Closing AWS Submitter dialogue in cleanup.")
            squish.sendEvent(
                "QCloseEvent",
                squish.waitForObject(gui_submitter_locators.aws_submitter_dialogue),
            )
    except Exception:
        pass
