"""
Service-laag voor applicatie- en gebruikersstate.

Doel: UI-componenten ontkoppelen van directe file/processor calls.
"""

from __future__ import annotations

from typing import Any

from data import processor


class AppStateService:
    """Thin service rond processor-functies voor user/system state."""

    def load_system_variables(self) -> dict[str, Any]:
        return processor.load_system_variables()

    def load_user_variables(self) -> dict[str, Any]:
        return processor.load_user_variables()

    def save_user_variables(self, user_vars: dict[str, Any]) -> None:
        processor.save_user_variables(user_vars)

    def get_work_mode(self, username: str | None = None) -> str:
        user_vars = self.load_user_variables()
        return processor.get_work_mode(user_vars, username=username)

    def set_work_mode(self, mode: str, username: str | None = None) -> str:
        user_vars = self.load_user_variables()
        mode_norm = processor.set_work_mode(user_vars, mode, username=username)
        self.save_user_variables(user_vars)
        return mode_norm

    def get_selected_aircraft(self, username: str | None = None, work_mode: str | None = None) -> list[str]:
        user_vars = self.load_user_variables()
        return processor.get_selected_aircraft(user_vars, username=username, work_mode=work_mode)

    def set_selected_aircraft(self, selected: list[str], username: str | None = None, work_mode: str | None = None) -> None:
        user_vars = self.load_user_variables()
        processor.set_selected_aircraft(
            user_vars, selected, username=username, work_mode=work_mode
        )
        self.save_user_variables(user_vars)

    def save_selection_and_mode(
        self,
        selected: list[str],
        mode: str,
        username: str | None = None,
    ) -> None:
        user_vars = self.load_user_variables()
        mode_norm = processor.set_work_mode(user_vars, mode, username=username)
        processor.set_selected_aircraft(
            user_vars, selected, username=username, work_mode=mode_norm
        )
        self.save_user_variables(user_vars)

    def get_hide_completed(self, username: str | None = None) -> bool:
        user_vars = self.load_user_variables()
        return processor.get_hide_completed(user_vars, username=username)

    def set_hide_completed(self, hide: bool, username: str | None = None) -> None:
        user_vars = self.load_user_variables()
        processor.set_hide_completed(user_vars, hide, username=username)
        self.save_user_variables(user_vars)

    def last_meta(self) -> float:
        return processor.last_meta()
