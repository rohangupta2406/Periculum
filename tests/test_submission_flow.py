"""
test_submission_flow.py
========================
Tests for the Calculate Risk Assessment button submission flow and state management
in the Streamlit application (app.py).
"""

import pytest
from streamlit.testing.v1 import AppTest


def test_initial_load_shows_form_without_assessment():
    """Before clicking Calculate Risk Assessment, no assessment should be generated."""
    at = AppTest.from_file("../app.py").run()
    assert not at.exception

    # Prompt message is shown
    info_messages = [msg.value for msg in at.info]
    assert any("Calculate Risk Assessment" in msg for msg in info_messages)

    # Executive Summary subheader should NOT be present before submission
    subheaders = [s.value for s in at.subheader]
    assert "🎯 Executive Risk Summary" not in subheaders


def test_clicking_calculate_renders_assessment():
    """Clicking Calculate Risk Assessment generates and displays the assessment dashboard."""
    at = AppTest.from_file("../app.py").run()
    assert not at.exception

    # Click the Calculate button
    at.button[0].click().run()
    assert not at.exception

    # Executive Summary subheader must be present after submission
    subheaders = [s.value for s in at.subheader]
    assert "🎯 Executive Risk Summary" in subheaders

    # Download button must be available
    download_buttons = [b.label for b in at.download_button]
    assert any("Download Assessment Report" in lbl for lbl in download_buttons)


def test_invalid_input_submission_shows_errors_and_blocks_assessment():
    """Submitting invalid inputs displays validation errors and blocks assessment generation."""
    at = AppTest.from_file("../app.py").run()
    assert not at.exception

    # Set total_tasks to 0 and completed_tasks to 5 (inconsistent)
    # Task inputs: number_input[2] is total_tasks, number_input[3] is completed_tasks
    at.number_input[2].set_value(0)
    at.number_input[3].set_value(5)

    at.button[0].click().run()
    assert not at.exception

    # Validation error must be displayed
    error_texts = [e.value for e in at.error]
    assert any("Validation Failed" in t for t in error_texts)

    # Assessment must NOT be generated
    subheaders = [s.value for s in at.subheader]
    assert "🎯 Executive Risk Summary" not in subheaders


def test_modifying_inputs_invalidates_stale_assessment():
    """Modifying an input field after calculation clears stale assessment on normal rerun."""
    at = AppTest.from_file("../app.py").run()
    at.button[0].click().run()
    assert "🎯 Executive Risk Summary" in [s.value for s in at.subheader]

    # Modify an input without clicking calculate button
    at.number_input[1].set_value(95.0).run()
    assert not at.exception

    # Assessment should not be displayed with stale data
    subheaders = [s.value for s in at.subheader]
    assert "🎯 Executive Risk Summary" not in subheaders

    # Info banner should prompt the user to recalculate
    info_messages = [msg.value for msg in at.info]
    assert any("Calculate Risk Assessment" in msg for msg in info_messages)
