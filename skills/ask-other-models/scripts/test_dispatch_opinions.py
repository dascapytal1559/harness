#!/usr/bin/env python3
"""Unit tests for ask-other-models effort mapping and CLI flags."""

from __future__ import annotations

import unittest
from pathlib import Path

from dispatch_opinions import command_for, map_effort


class MapEffortTests(unittest.TestCase):
    def test_exact_match_is_identity(self) -> None:
        for provider, levels in {
            "claude": ("low", "medium", "high", "xhigh", "max"),
            "codex": ("minimal", "low", "medium", "high", "xhigh"),
            "grok": ("none", "minimal", "low", "medium", "high", "xhigh", "max"),
        }.items():
            for level in levels:
                with self.subTest(provider=provider, level=level):
                    mapping = map_effort(provider, level)
                    self.assertEqual(mapping.requested, level)
                    self.assertEqual(mapping.applied, level)
                    self.assertFalse(mapping.clamped)

    def test_claude_floors_below_low(self) -> None:
        for requested in ("none", "minimal"):
            mapping = map_effort("claude", requested)
            self.assertEqual(mapping.applied, "low")
            self.assertTrue(mapping.clamped)

    def test_codex_floors_none_and_caps_max(self) -> None:
        self.assertEqual(map_effort("codex", "none").applied, "minimal")
        self.assertEqual(map_effort("codex", "max").applied, "xhigh")
        self.assertTrue(map_effort("codex", "none").clamped)
        self.assertTrue(map_effort("codex", "max").clamped)

    def test_unknown_effort_or_provider_raises(self) -> None:
        with self.assertRaises(ValueError):
            map_effort("claude", "ultra")
        with self.assertRaises(ValueError):
            map_effort("gemini", "high")


class CommandForTests(unittest.TestCase):
    def test_each_provider_gets_its_effort_flag(self) -> None:
        prompt = Path("/tmp/prompt.md")
        result = Path("/tmp/result.md")
        claude = command_for("claude", None, "high", prompt, result)
        self.assertIn("--effort", claude)
        self.assertEqual(claude[claude.index("--effort") + 1], "high")
        codex = command_for("codex", None, "high", prompt, result)
        self.assertIn("model_reasoning_effort=high", codex)
        grok = command_for("grok", None, "high", prompt, result)
        self.assertIn("--reasoning-effort", grok)
        self.assertEqual(grok[grok.index("--reasoning-effort") + 1], "high")


if __name__ == "__main__":
    unittest.main()
