import random
import time
import os
import sys
import json
import tempfile
from typing import Optional

import requests
from loguru import logger

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:132.0) Gecko/20100101 Firefox/132.0",
]

REQUEST_TIMEOUT = 15
INIT_TIMEOUT = 15

_STATE_DIR = tempfile.gettempdir()
_LOCK_PATH = os.path.join(_STATE_DIR, "weixin-search-skills.lock")
_STATE_PATH = os.path.join(_STATE_DIR, "weixin-search-skills-state.json")


def _lock_file(f):
    if sys.platform == "win32":
        import msvcrt
        f.seek(0)
        msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
    else:
        import fcntl
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)


def _unlock_file(f):
    if sys.platform == "win32":
        import msvcrt
        f.seek(0)
        msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
    else:
        import fcntl
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)


class GlobalRateLimiter:
    """Cross-process rate limiter using file lock + shared state file.

    Ensures all processes on this machine coordinate their requests to Sogou,
    maintaining polite request intervals.
    """

    MIN_INTERVAL = 3.0
    MAX_PER_WINDOW = 20
    WINDOW_SECONDS = 120.0

    def __init__(self, lock_path: str = _LOCK_PATH, state_path: str = _STATE_PATH) -> None:
        self._lock_path = lock_path
        self._state_path = state_path

    def _read_state(self) -> dict:
        try:
            with open(self._state_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, ValueError):
            return {"last_request_time": 0.0, "timestamps": []}

    def _write_state(self, state: dict) -> None:
        with open(self._state_path, "w", encoding="utf-8") as f:
            json.dump(state, f)

    def _acquire_slot(self) -> float:
        """Reserve a time slot under file lock. Returns the scheduled request time."""
        with open(self._lock_path, "a+b") as lock:
            _lock_file(lock)
            try:
                state = self._read_state()
                now = time.time()

                earliest = now
                if state["last_request_time"] > 0:
                    earliest = max(earliest, state["last_request_time"] + self.MIN_INTERVAL)

                cutoff = now - self.WINDOW_SECONDS
                recent = [t for t in state["timestamps"] if t > cutoff]

                if len(recent) >= self.MAX_PER_WINDOW:
                    window_wait = recent[0] + self.WINDOW_SECONDS + 0.1
                    earliest = max(earliest, window_wait)

                scheduled = earliest

                state["last_request_time"] = scheduled
                state["timestamps"] = recent + [scheduled]
                self._write_state(state)

                return scheduled
            finally:
                _unlock_file(lock)

    def wait_for_slot(self) -> None:
        """Block until it is safe to make a request. Call before each Sogou HTTP request."""
        scheduled = self._acquire_slot()
        now = time.time()
        wait = scheduled - now
        if wait > 0:
            logger.info(f"Global rate limiter: waiting {wait:.1f}s (queued behind other processes)")
            time.sleep(wait)

    def get_status(self) -> dict:
        """Return current limiter state for diagnostics."""
        state = self._read_state()
        now = time.time()
        cutoff = now - self.WINDOW_SECONDS
        recent = [t for t in state["timestamps"] if t > cutoff]
        return {
            "requests_in_window": len(recent),
            "max_per_window": self.MAX_PER_WINDOW,
            "window_seconds": self.WINDOW_SECONDS,
            "last_request_age": now - state["last_request_time"] if state["last_request_time"] > 0 else None,
        }


global_rate_limiter = GlobalRateLimiter()


def _is_antispider_response(response: requests.Response) -> bool:
    final_url = response.url.lower()
    body = response.text.lower()
    return "antispider" in final_url or "seccoderight" in body or "anti.min.css" in body


class SogouSession:
    MAX_REQUESTS_PER_SNUID = 30
    MIN_INTERVAL = 3.0
    MAX_RETRIES = 3

    def __init__(self) -> None:
        self._session: Optional[requests.Session] = None
        self._request_count: int = 0
        self._user_agent: str = ""

    def _init_session(self) -> None:
        self._session = requests.Session()
        self._user_agent = random.choice(USER_AGENTS)
        self._session.headers.update({
            "User-Agent": self._user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Pragma": "no-cache",
        })
        try:
            global_rate_limiter.wait_for_slot()
            self._session.get("https://weixin.sogou.com/", timeout=INIT_TIMEOUT)
        except requests.RequestException as e:
            logger.warning(f"Session init: failed to fetch sogou homepage: {e}")
        try:
            global_rate_limiter.wait_for_slot()
            self._session.get("https://pb.sogou.com/cl.gif?", timeout=10)
        except requests.RequestException:
            pass
        self._request_count = 0
        logger.info(f"Session initialized, UA={self._user_agent[:40]}...")

    def _ensure_session(self) -> None:
        if self._session is None or self._request_count >= self.MAX_REQUESTS_PER_SNUID:
            if self._request_count >= self.MAX_REQUESTS_PER_SNUID:
                logger.info(f"SNUID request count reached {self._request_count}, refreshing session")
            self._init_session()

    def get(self, url: str, **kwargs: object) -> requests.Response:
        self._ensure_session()
        global_rate_limiter.wait_for_slot()
        kwargs.setdefault("timeout", REQUEST_TIMEOUT)
        assert self._session is not None
        resp = self._session.get(url, **kwargs)
        self._request_count += 1
        return resp

    def get_with_retry(self, url: str, **kwargs: object) -> requests.Response:
        last_resp: Optional[requests.Response] = None
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                resp = self.get(url, **kwargs)
                if not _is_antispider_response(resp):
                    return resp
                last_resp = resp
                logger.warning(f"Antispider detected (attempt {attempt + 1}/{self.MAX_RETRIES + 1})")
                if attempt < self.MAX_RETRIES:
                    backoff = self.MIN_INTERVAL * (2 ** attempt)
                    logger.info(f"Backing off {backoff:.1f}s before retry")
                    time.sleep(backoff)
                    self._init_session()
            except requests.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt < self.MAX_RETRIES:
                    backoff = self.MIN_INTERVAL * (2 ** attempt)
                    time.sleep(backoff)
                    self._init_session()
                else:
                    raise
        assert last_resp is not None
        return last_resp

    @property
    def user_agent(self) -> str:
        return self._user_agent

    @property
    def request_count(self) -> int:
        return self._request_count


sogou_session = SogouSession()
