#!/usr/bin/env python3
"""Unit tests for ai-council effort mapping, round prompts, and CLI flags."""

from __future__ import annotations

import unittest
from pathlib import Path

from dispatch_council import command_for, map_effort, prompt_for


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


class PromptForTests(unittest.TestCase):
    def test_round_one_is_independent(self) -> None:
        prompt = prompt_for("PACKET", "abc", 1, None)
        self.assertIn("PACKET", prompt)
        self.assertIn("abc", prompt)
        self.assertNotIn("JUDGE BRIEF", prompt)
        self.assertNotIn("DEFEND", prompt)

    def test_rebuttal_round_includes_brief_and_verbs(self) -> None:
        prompt = prompt_for("PACKET", "abc", 2, "BRIEF")
        self.assertIn("BEGIN JUDGE BRIEF", prompt)
        self.assertIn("BRIEF", prompt)
        self.assertIn("rebuttal round 2", prompt)
        for verb in ("DEFEND", "REVISE", "CONCEDE"):
            self.assertIn(verb, prompt)

    def test_round_one_rejects_brief(self) -> None:
        with self.assertRaises(ValueError):
            prompt_for("PACKET", "abc", 1, "BRIEF")

    def test_rebuttal_requires_brief(self) -> None:
        with self.assertRaises(ValueError):
            prompt_for("PACKET", "abc", 2, None)

    def test_round_must_be_positive(self) -> None:
        with self.assertRaises(ValueError):
            prompt_for("PACKET", "abc", 0, None)


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

    def test_pinned_model_is_passed_through(self) -> None:
        prompt = Path("/tmp/prompt.md")
        result = Path("/tmp/result.md")
        for provider in ("claude", "codex", "grok"):
            command = command_for(provider, "some-model", "high", prompt, result)
            self.assertEqual(command[command.index("--model") + 1], "some-model")


if __name__ == "__main__":
    unittest.main()
