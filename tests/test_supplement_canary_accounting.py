"""Real native return-accounting control for review finding #2931, 2026-11-15."""

from scripts.adhoc.run_switchgrass_source_canary_20261115 import comparison_counts
from linkml_reference_validator.validation.supporting_text_validator import SupportingTextValidator
from tests.test_supplement_source_locator import source_case  # noqa: F401


def test_actual_results_distinguish_comparison_failure_from_selection_and_skip(request):
    """Only two of four real validation calls contain native match results."""
    _, config, locator = request.getfixturevalue("source_case")
    config.skip_prefixes = ["BIOPROJECT"]
    validator = SupportingTextValidator(config)
    results = [
        validator.validate("OAE516", "PMID:12345", source_locator=locator),
        validator.validate("OAE603", "PMID:12345", source_locator=locator),
        validator.validate("OAE516", "PMID:54321", source_locator=locator),
        validator.validate("OAE516", "BIOPROJECT:PRJNA1"),
    ]

    def observed(values):
        return [{"matched": value.match_result.found if value.match_result else None,
                 "is_valid": value.is_valid, "message": value.message} for value in values]

    assert results[0].is_valid and results[3].is_valid
    assert not results[1].is_valid and not results[2].is_valid
    counts = comparison_counts(observed(results))
    assert counts == {
        "native_validation_calls": 4, "native_comparisons": 2, "native_matches": 1,
        "native_mismatches": 1, "source_selection_failures": 1,
    }
    restored = validator.validate("OAE516", "PMID:12345", source_locator=locator)
    assert restored.is_valid
    assert comparison_counts(observed([restored])) == {
        "native_validation_calls": 1, "native_comparisons": 1, "native_matches": 1,
        "native_mismatches": 0, "source_selection_failures": 0,
    }
