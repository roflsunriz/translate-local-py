"""アニメーション付きトグルスイッチウィジェット."""

from __future__ import annotations

from PyQt6.QtCore import (
    QEasingCurve,
    QRectF,
    Qt,
    QVariantAnimation,
    pyqtSignal,
)
from PyQt6.QtGui import QColor, QMouseEvent, QPainter, QPen
from PyQt6.QtWidgets import QWidget


class ToggleSwitch(QWidget):
    """iOS / Material 風のスライダートグルスイッチ."""

    toggled = pyqtSignal(bool)

    _TRACK_W = 44
    _TRACK_H = 24
    _THUMB_RADIUS = 9
    _ANIM_MS = 150

    _COLOR_TRACK_OFF = QColor("#BDBDBD")
    _COLOR_TRACK_ON = QColor("#4CAF50")
    _COLOR_THUMB = QColor("#FFFFFF")
    _COLOR_THUMB_BORDER = QColor("#E0E0E0")

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._checked = False
        half_h = self._TRACK_H / 2.0
        self._thumb_x: float = half_h

        self._anim = QVariantAnimation(self)
        self._anim.setDuration(self._ANIM_MS)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self._anim.valueChanged.connect(self._on_anim_value)

        self.setFixedSize(self._TRACK_W, self._TRACK_H)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def isChecked(self) -> bool:  # noqa: N802
        return self._checked

    def setChecked(self, checked: bool) -> None:  # noqa: N802
        if self._checked == checked:
            return
        self._checked = checked
        self._animate()
        self.toggled.emit(checked)

    def _animate(self) -> None:
        self._anim.stop()
        half_h = self._TRACK_H / 2.0
        target = float(self._TRACK_W - half_h) if self._checked else half_h
        self._anim.setStartValue(self._thumb_x)
        self._anim.setEndValue(target)
        self._anim.start()

    def _on_anim_value(self, value: object) -> None:
        if isinstance(value, (int, float)):
            self._thumb_x = float(value)
            self.update()

    def mousePressEvent(self, event: QMouseEvent | None) -> None:  # type: ignore[override]
        self.setChecked(not self._checked)

    def paintEvent(self, event: object) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        track_color = self._COLOR_TRACK_ON if self._checked else self._COLOR_TRACK_OFF
        p.setBrush(track_color)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(
            QRectF(0, 0, self._TRACK_W, self._TRACK_H),
            self._TRACK_H / 2.0,
            self._TRACK_H / 2.0,
        )

        p.setBrush(self._COLOR_THUMB)
        p.setPen(QPen(self._COLOR_THUMB_BORDER, 0.5))
        center_y = self._TRACK_H / 2.0
        p.drawEllipse(
            QRectF(
                self._thumb_x - self._THUMB_RADIUS,
                center_y - self._THUMB_RADIUS,
                self._THUMB_RADIUS * 2,
                self._THUMB_RADIUS * 2,
            ),
        )
        p.end()
