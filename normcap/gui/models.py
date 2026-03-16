"""Various Data Models."""

import logging
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any, NamedTuple

logger = logging.getLogger(__name__)


class Setting(NamedTuple):
    key: str
    flag: str
    type_: type | Callable
    value: Any
    choices: Iterable | None
    help_: str
    cli_arg: bool
    nargs: int | str | None


@dataclass
class Urls:
    """URLs used on various places."""

    releases: str
    changelog: str
    pypi: str
    github: str
    issues: str
    website: str

    @property
    def releases_atom(self) -> str:
        return f"{self.releases}.atom"

    @property
    def pypi_json(self) -> str:
        return f"{self.pypi}/json"
