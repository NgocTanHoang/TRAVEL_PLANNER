"""
Tien ich checkpoint, streaming va rate limiting cho travel plan.
"""
from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from django.db import close_old_connections

from utils.cache import cache_get, cache_set, get_redis_client
from utils.security import sanitize_sensitive_data

RUN_TTL_SECONDS = 60 * 60 * 6
RATE_LIMIT_WINDOW_SECONDS = 60 * 10
RATE_LIMIT_MAX_REQUESTS = 3

_fallback_lock = threading.Lock()


def _now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _run_key(thread_id: str) -> str:
    return f"travel_plan:run:{thread_id}"


def _safe_json(value: Any) -> Any:
    try:
        sanitized = sanitize_sensitive_data(value)
        json.dumps(sanitized, ensure_ascii=False)
        return sanitized
    except (TypeError, ValueError):
        if isinstance(value, dict):
            return {key: _safe_json(item) for key, item in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [_safe_json(item) for item in value]
        return str(value)


def release_streaming_connections() -> None:
    """Release DB connections after SSE worker/generator completes."""
    close_old_connections()


def create_thread_id(provided_thread_id: Optional[str] = None) -> str:
    if provided_thread_id:
        return str(provided_thread_id).strip()
    return f"travel-plan-{uuid.uuid4().hex}"


def get_client_ip(request) -> str:
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


def initialize_run(
    *,
    thread_id: str,
    owner_key: str,
    request_payload: Dict[str, Any],
    workflow_engine: str,
) -> Dict[str, Any]:
    existing = get_run(thread_id)
    if existing:
        return existing

    payload = {
        "thread_id": thread_id,
        "owner_key": owner_key,
        "status": "pending",
        "workflow_engine": workflow_engine,
        "request_payload": _safe_json(request_payload),
        "progress": {
            "current_step": None,
            "completed_steps": [],
        },
        "events": [],
        "next_event_id": 1,
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
        "final_response": None,
        "error": None,
    }
    cache_set(_run_key(thread_id), payload, ttl=RUN_TTL_SECONDS)
    return payload


def get_run(thread_id: str) -> Optional[Dict[str, Any]]:
    return cache_get(_run_key(thread_id))


def save_run(thread_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    payload["updated_at"] = _now_iso()
    cache_set(_run_key(thread_id), payload, ttl=RUN_TTL_SECONDS)
    return payload


def update_run(thread_id: str, **fields: Any) -> Optional[Dict[str, Any]]:
    payload = get_run(thread_id)
    if not payload:
        return None
    payload.update(_safe_json(fields))
    return save_run(thread_id, payload)


def append_event(thread_id: str, event_type: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    payload = get_run(thread_id)
    if not payload:
        return None

    event_id = int(payload.get("next_event_id", 1))
    event = {
        "id": event_id,
        "event": event_type,
        "data": _safe_json(data),
        "created_at": _now_iso(),
    }
    payload.setdefault("events", []).append(event)
    payload["next_event_id"] = event_id + 1
    return save_run(thread_id, payload)


def set_running(thread_id: str, current_step: Optional[str] = None) -> Optional[Dict[str, Any]]:
    payload = get_run(thread_id)
    if not payload:
        return None

    payload["status"] = "running"
    progress = payload.setdefault("progress", {})
    progress["current_step"] = current_step
    return save_run(thread_id, payload)


def record_progress(
    thread_id: str,
    *,
    step: str,
    message: str,
    completed_steps: Optional[List[str]] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    payload = get_run(thread_id)
    if not payload:
        return None

    progress = payload.setdefault("progress", {})
    progress["current_step"] = step
    if completed_steps is not None:
        progress["completed_steps"] = completed_steps

    event_payload = {
        "thread_id": thread_id,
        "step": step,
        "message": message,
        "completed_steps": progress.get("completed_steps", []),
        "status": payload.get("status", "running"),
    }
    if extra:
        event_payload.update(_safe_json(extra))

    save_run(thread_id, payload)
    return append_event(thread_id, "progress", event_payload)


def record_day_updates(thread_id: str, itinerary_json: Optional[Dict[str, Any]]) -> None:
    if not isinstance(itinerary_json, dict):
        return

    for day_item in itinerary_json.get("daily_itinerary", []) or []:
        if not isinstance(day_item, dict):
            continue
        append_event(
            thread_id,
            "day_ready",
            {
                "thread_id": thread_id,
                "day": day_item.get("day"),
                "date": day_item.get("date"),
                "theme": day_item.get("theme"),
                "timeline": day_item.get("timeline", []),
            },
        )


def complete_run(
    thread_id: str,
    *,
    response_data: Dict[str, Any],
    workflow_engine: str,
) -> Optional[Dict[str, Any]]:
    payload = get_run(thread_id)
    if not payload:
        return None

    payload["status"] = "completed"
    payload["workflow_engine"] = workflow_engine
    payload["final_response"] = _safe_json(response_data)
    save_run(thread_id, payload)
    return append_event(
        thread_id,
        "completed",
        {
            "thread_id": thread_id,
            "status": "success",
            "workflow_engine": workflow_engine,
            "response": response_data,
        },
    )


def fail_run(thread_id: str, message: str) -> Optional[Dict[str, Any]]:
    payload = get_run(thread_id)
    if not payload:
        return None

    payload["status"] = "failed"
    payload["error"] = message
    save_run(thread_id, payload)
    return append_event(
        thread_id,
        "error",
        {
            "thread_id": thread_id,
            "status": "error",
            "message": message,
        },
    )


def get_events_since(thread_id: str, last_event_id: int = 0) -> List[Dict[str, Any]]:
    payload = get_run(thread_id) or {}
    events = payload.get("events", [])
    return [event for event in events if int(event.get("id", 0)) > int(last_event_id)]


def _rate_limit_key(scope: str, identifier: str) -> str:
    return f"travel_plan:ratelimit:{scope}:{identifier}"


def _incr_fallback_rate_limit(key: str, window_seconds: int) -> int:
    with _fallback_lock:
        payload = cache_get(key) or {"count": 0}
        payload["count"] = int(payload.get("count", 0)) + 1
        cache_set(key, payload, ttl=window_seconds)
        return payload["count"]


def _incr_rate_limit_key(key: str, window_seconds: int) -> int:
    client = get_redis_client()
    if client:
        try:
            current = client.incr(key)
            if current == 1:
                client.expire(key, window_seconds)
            return int(current)
        except Exception:
            pass
    return _incr_fallback_rate_limit(key, window_seconds)


def check_generation_rate_limit(
    *,
    user_id: Optional[int],
    client_ip: Optional[str],
    limit: int = RATE_LIMIT_MAX_REQUESTS,
    window_seconds: int = RATE_LIMIT_WINDOW_SECONDS,
) -> Tuple[bool, Dict[str, Any]]:
    counters: Dict[str, int] = {}

    if user_id:
        user_key = _rate_limit_key("user", str(user_id))
        counters["user"] = _incr_rate_limit_key(user_key, window_seconds)

    if client_ip:
        ip_key = _rate_limit_key("ip", client_ip)
        counters["ip"] = _incr_rate_limit_key(ip_key, window_seconds)

    if not counters:
        anonymous_key = _rate_limit_key("anonymous", "global")
        counters["anonymous"] = _incr_rate_limit_key(anonymous_key, window_seconds)

    blocked = any(count > limit for count in counters.values())
    return (not blocked), {
        "limit": limit,
        "window_seconds": window_seconds,
        "counters": counters,
    }
