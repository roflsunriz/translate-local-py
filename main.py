"""LLM Translation Desktop App - チャットコミュニケーション補助翻訳ツール."""

from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from src.ui.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("LLM Translator")
    app.setOrganizationName("translate-local-py")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
