# プロジェクト固有の知見

共通指針と [AGENTS.md](AGENTS.md) を読んだ後、作業前にこの文書を全文読む。元の条件・確認日・未検証事項を保ったまま、固有の実現手段と再利用する知見を集約する。

## 共通指針の具体化と適用範囲

- 対象: 共通指針の「設計と実装方針」「検証」「更新手順」「ドキュメント」と、各節に明記した共通ルール。
- 理由・範囲: Python/PyQtのデスクトップアプリなのでBunではなくrequirements.txtとPyInstallerを使う。共通の検証義務はPythonのコンパイル・単体テストと既存の検証手順で満たす。
- 代替手段・検証: 以下の実効コマンド・根拠を用い、[検証記録](verification.md) で成功・未検証を区別する。共通方針の完了条件やユーザーの明示指示は弱めない。

## READMEなどから移した開発・運用情報

## ビルド

PyInstaller の単体実行ファイルを作る場合は以下を使います。

```powershell
pyinstaller --noconfirm --clean --windowed --name translate-local-py --icon resources/icon.ico --add-data "resources;resources" main.py
```

## CI / CD

GitHub Actions で以下を実行します。

- CI: Python 3.12 / 3.13 の matrix でインポート、コンパイル、モデル選択テストを確認
- Release: `v*` タグの push で PyInstaller ビルドを実行し、成果物を GitHub Release に添付

## 依存更新の自動処理

Dependabot は対象の依存関係を毎週確認します。patch／minor 更新は PR のチェック（CI）が成功した後に自動で squash merge されます。CI の失敗ジョブは 1 回だけ再実行します。再失敗した PR は残して手動で修正します。major 更新は手動で確認します。

## 文書の役割

- [README.md](README.md): 利用開始と操作、利用者が知る必要のある制限。
- この文書: 固有の配置・ツール・実行手段・例外・再利用する調査知見。
- [verification.md](verification.md): 検証手順、実測結果、証拠、未検証事項。
- [how-to-update.md](how-to-update.md): 更新と復旧の手順。
