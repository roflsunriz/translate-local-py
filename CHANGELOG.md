# 変更履歴

このプロジェクトの主な変更はこのファイルに記録します。

書式は [Keep a Changelog](https://keepachangelog.com/ja/1.1.0/) に基づきます。

## [Unreleased]

### Fixed

- CI と Dependabot の分類の実行順が前後しても更新を取りこぼさないよう、同じ PR 番号と head SHA を再照合する経路を追加した。

### Changed

- 依存更新を安全に省力化するため、Dependabot の patch／minor PR を既存 CI の全チェック成功後に自動取り込みし、失敗ジョブを一度再実行する設定を追加した。
- GitHub Actionsの保守性を保つため、actions/checkoutをv4からv7へ、actions/setup-pythonをv5からv7へ、softprops/action-gh-releaseをv2からv3へ更新した。
- セキュリティ修正と互換性維持のため、requestsの下限を2.31から2.34.2へ、PyQt6の下限を6.6から6.11.0へ引き上げた。

## [1.0.7] - 2026-08-19

### Changed

- CerebrasとSakuraの提供モデル変更へ自動追従できるように、固定候補配列を廃止し、認証付きモデル一覧から音声・埋め込みを除外した有効モデルを選ぶよう変更した。
- 作業開始時の共通指針見落としを防ぐため、調査やコマンド実行より前に `COMMON-AGENTS.md` を先頭から末尾まで読み、EOFを確認する必須ゲートを追加した。
