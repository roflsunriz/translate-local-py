# 調査知見

- PyQtアプリのためBunではなくPythonのコンパイル・テストとPyInstallerで検証する。
- 単体実行ファイルでは `resources` を `--add-data "resources;resources"` で明示同梱する。ビルド成功とGUIの実動作は分けて確認する。
