"""
Simplified Service Object pattern.

Each service defines an ordered list of step method names. The base `Service`
class runs them in order, stopping on the first failure. Steps signal failure
by calling `self.fail(message)` which raises `ServiceError` and is caught by
the runner, preserving the error in `context.errors`.

Example:
    class CreatePostService(Service):
        steps = ["validate_params", "check_permissions", "persist", "enqueue_jobs"]

        async def validate_params(self):
            if not self.raw:
                self.fail("Post cannot be empty")

        async def check_permissions(self):
            if not self.guardian.can_create_post(self.topic):
                self.fail("Permission denied")

        async def persist(self):
            ...  # write to DB

        async def enqueue_jobs(self):
            ...  # fire Celery tasks
"""

import inspect
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


class ServiceError(Exception):
    pass


@dataclass
class ServiceContext:
    success: bool = True
    errors: list[str] = field(default_factory=list)
    result: Any = None


class Service:
    steps: list[str] = []

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.context = ServiceContext()

    def fail(self, message: str) -> None:
        raise ServiceError(message)

    async def call(self) -> ServiceContext:
        for step_name in self.steps:
            if not self.context.success:
                break
            step = getattr(self, step_name, None)
            if step is None:
                logger.warning("Service %s missing step '%s'", self.__class__.__name__, step_name)
                continue
            try:
                if inspect.iscoroutinefunction(step):
                    await step()
                else:
                    step()
            except ServiceError as exc:
                self.context.success = False
                self.context.errors.append(str(exc))
                logger.debug("%s failed at step '%s': %s", self.__class__.__name__, step_name, exc)
            except Exception as exc:
                self.context.success = False
                self.context.errors.append(f"Unexpected error in {step_name}: {exc}")
                logger.exception("Unexpected error in %s.%s", self.__class__.__name__, step_name)
        return self.context
