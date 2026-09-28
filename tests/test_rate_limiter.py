"""Tests for GlobalRateLimiter cross-process rate limiting."""
import json
import os
import sys
import tempfile
import time
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from http_client import GlobalRateLimiter


class TestGlobalRateLimiter(unittest.TestCase):

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self._lock = os.path.join(self._tmpdir, "test.lock")
        self._state = os.path.join(self._tmpdir, "test-state.json")
        self.limiter = GlobalRateLimiter(lock_path=self._lock, state_path=self._state)

    def tearDown(self):
        for f in (self._lock, self._state):
            if os.path.exists(f):
                os.remove(f)
        os.rmdir(self._tmpdir)

    def test_first_request_passes_immediately(self):
        """First request should not wait."""
        t0 = time.time()
        self.limiter.wait_for_slot()
        elapsed = time.time() - t0
        self.assertLess(elapsed, 1.0)

    def test_min_interval_enforced(self):
        """Second request should wait at least MIN_INTERVAL after the first."""
        self.limiter.MIN_INTERVAL = 0.5
        self.limiter.wait_for_slot()
        t0 = time.time()
        self.limiter.wait_for_slot()
        elapsed = time.time() - t0
        self.assertGreaterEqual(elapsed, 0.4)

    def test_window_limit_enforced(self):
        """After MAX_PER_WINDOW requests, next must wait for window to expire."""
        self.limiter.MIN_INTERVAL = 0.0
        self.limiter.MAX_PER_WINDOW = 3
        self.limiter.WINDOW_SECONDS = 2.0

        for _ in range(3):
            self.limiter.wait_for_slot()

        t0 = time.time()
        self.limiter.wait_for_slot()
        elapsed = time.time() - t0
        self.assertGreaterEqual(elapsed, 1.0)

    def test_state_persists_to_file(self):
        """State file should contain timestamps after requests."""
        self.limiter.MIN_INTERVAL = 0.0
        self.limiter.wait_for_slot()
        self.limiter.wait_for_slot()

        with open(self._state, "r") as f:
            state = json.load(f)
        self.assertEqual(len(state["timestamps"]), 2)
        self.assertGreater(state["last_request_time"], 0)

    def test_corrupt_state_file_handled(self):
        """Corrupt state file should be treated as empty."""
        with open(self._state, "w") as f:
            f.write("not json{{{")

        self.limiter.wait_for_slot()
        with open(self._state, "r") as f:
            state = json.load(f)
        self.assertEqual(len(state["timestamps"]), 1)

    def test_stale_timestamps_cleaned(self):
        """Timestamps older than window should be cleaned on next access."""
        self.limiter.MIN_INTERVAL = 0.0
        self.limiter.WINDOW_SECONDS = 1.0

        old_state = {
            "last_request_time": time.time() - 10,
            "timestamps": [time.time() - 10, time.time() - 9, time.time() - 8],
        }
        with open(self._state, "w") as f:
            json.dump(old_state, f)

        self.limiter.wait_for_slot()
        with open(self._state, "r") as f:
            state = json.load(f)
        self.assertEqual(len(state["timestamps"]), 1)

    def test_get_status(self):
        """get_status should return diagnostic info."""
        self.limiter.MIN_INTERVAL = 0.0
        self.limiter.wait_for_slot()
        status = self.limiter.get_status()
        self.assertEqual(status["requests_in_window"], 1)
        self.assertEqual(status["max_per_window"], self.limiter.MAX_PER_WINDOW)
        self.assertIsNotNone(status["last_request_age"])

    def test_concurrent_slots_serialized(self):
        """Multiple acquire_slot calls should produce sequential scheduled times."""
        self.limiter.MIN_INTERVAL = 1.0
        t1 = self.limiter._acquire_slot()
        t2 = self.limiter._acquire_slot()
        t3 = self.limiter._acquire_slot()
        self.assertGreaterEqual(t2 - t1, 1.0)
        self.assertGreaterEqual(t3 - t2, 1.0)


class TestCrossProcessSimulation(unittest.TestCase):
    """Simulate what happens when multiple processes try to use the limiter."""

    def test_hundred_queries_serialized(self):
        """100 concurrent _acquire_slot calls should produce times spanning 100*interval."""
        tmpdir = tempfile.mkdtemp()
        lock = os.path.join(tmpdir, "test.lock")
        state = os.path.join(tmpdir, "test-state.json")
        limiter = GlobalRateLimiter(lock_path=lock, state_path=state)
        limiter.MIN_INTERVAL = 3.0
        limiter.MAX_PER_WINDOW = 20
        limiter.WINDOW_SECONDS = 120.0

        slots = []
        for _ in range(100):
            slots.append(limiter._acquire_slot())

        for i in range(1, len(slots)):
            gap = slots[i] - slots[i - 1]
            self.assertGreaterEqual(gap, 3.0 - 0.01)

        total_span = slots[-1] - slots[0]
        self.assertGreaterEqual(total_span, 99 * 3.0 - 0.1)

        for f in (lock, state):
            if os.path.exists(f):
                os.remove(f)
        os.rmdir(tmpdir)

    def test_window_cap_kicks_in(self):
        """After MAX_PER_WINDOW slots, next slot should be delayed to window boundary."""
        tmpdir = tempfile.mkdtemp()
        lock = os.path.join(tmpdir, "test.lock")
        state = os.path.join(tmpdir, "test-state.json")
        limiter = GlobalRateLimiter(lock_path=lock, state_path=state)
        limiter.MIN_INTERVAL = 0.1
        limiter.MAX_PER_WINDOW = 5
        limiter.WINDOW_SECONDS = 10.0

        slots = []
        for _ in range(7):
            slots.append(limiter._acquire_slot())

        gap_6th = slots[5] - slots[0]
        self.assertGreaterEqual(gap_6th, 10.0 - 0.1)

        for f in (lock, state):
            if os.path.exists(f):
                os.remove(f)
        os.rmdir(tmpdir)


if __name__ == "__main__":
    unittest.main()
