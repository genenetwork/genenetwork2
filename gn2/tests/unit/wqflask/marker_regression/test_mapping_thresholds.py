"""Threshold normalisation for the mapping figure.

The figure is rendered twice (1x and 2x) before the interactive payload is
built, so the conversion from the raw permutation thresholds into the units
the axes are drawn in has to be derived from the raw values every time rather
than applied once per render.
"""

import unittest

from gn2.base import webqtlConfig
from gn2.wqflask.marker_regression.display_mapping_results import (
    DisplayMappingResults
)


def _results(**kwargs):
    """A DisplayMappingResults carrying only the state the threshold
    conversion looks at."""
    results = object.__new__(DisplayMappingResults)
    results.qtlresults = kwargs.get("qtlresults", [{"lrs_value": 50.0}])
    results.significant = kwargs.get("significant", 46.1)
    results.suggestive = kwargs.get("suggestive", 23.05)
    results.LRS_LOD = kwargs.get("LRS_LOD", "LOD")
    return results


class TestDisplayScaleThresholds(unittest.TestCase):
    """Thresholds reach the PNG renders and the client in the axis units."""

    def test_lrs_markers_are_converted_to_lod(self):
        significant, suggestive = _results()._display_scale_thresholds()
        self.assertAlmostEqual(significant, 10.0)
        self.assertAlmostEqual(suggestive, 5.0)

    def test_repeated_conversions_do_not_compound(self):
        """The 2x render must not divide the thresholds a second time."""
        results = _results()
        for _ in range(3):
            significant, suggestive = results._display_scale_thresholds()
        self.assertAlmostEqual(significant, 10.0)
        self.assertAlmostEqual(suggestive, 5.0)
        # The raw permutation values stay available for the next caller.
        self.assertAlmostEqual(results.significant, 46.1)
        self.assertAlmostEqual(results.suggestive, 23.05)

    def test_lrs_display_keeps_lrs_thresholds(self):
        self.assertEqual(_results(LRS_LOD="LRS")._display_scale_thresholds(),
                         (46.1, 23.05))

    def test_logp_display_converts_like_lod(self):
        significant, _suggestive = _results(
            LRS_LOD="-logP")._display_scale_thresholds()
        self.assertAlmostEqual(significant, 10.0)

    def test_lod_markers_are_converted_to_lrs(self):
        significant, suggestive = _results(
            qtlresults=[{"lod_score": 8.0}],
            significant=10.0,
            suggestive=7.0,
            LRS_LOD="LRS")._display_scale_thresholds()
        self.assertAlmostEqual(significant, 46.1)
        self.assertAlmostEqual(suggestive, 32.27)

    def test_lod_markers_keep_lod_thresholds(self):
        self.assertEqual(
            _results(qtlresults=[{"lod_score": 8.0}],
                     significant=10.0,
                     suggestive=7.0,
                     LRS_LOD="LOD")._display_scale_thresholds(),
            (10.0, 7.0))

    def test_thresholds_are_capped_like_marker_scores(self):
        self.assertEqual(
            _results(significant=5000.0,
                     suggestive=6000.0,
                     LRS_LOD="LRS")._display_scale_thresholds(),
            (webqtlConfig.MAXLRS, webqtlConfig.MAXLRS))

    def test_missing_thresholds_are_passed_through(self):
        self.assertEqual(_results(significant="",
                                  suggestive="")._display_scale_thresholds(),
                         ("", ""))
