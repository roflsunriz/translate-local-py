# 更新手順

## 前提

- Python 3.12以上
- 作業前に `git status --short --branch` で既存差分を確認する

## 更新と検証

```powershell
python -m pip install -r requirements.txt --upgrade
python -m compileall src main.py
python -m unittest discover -s tests
```

CerebrasとSakuraのモデル更新では、認証付き `GET /v1/models` の `data[]` に `id` と `created` が含まれることを確認します。音声・埋め込みモデルが先頭でもチャットモデルを選べること、一覧順を反転しても選択が変わらないこと、保存済みモデルが一覧から消えた場合に有効モデルへ切り替わることをテストします。APIキーやAuthorizationヘッダーの値をログ・例外・テスト成果物へ出力しません。

## ロールバック

更新前のGitコミットへ戻し、依存関係を再インストールします。設定ファイルは保持されるため、旧版でモデル名が無効になった場合は設定画面で利用可能なモデル名を手動指定します。

## リリース

mainのテスト、依存関係監査、Windows onefileビルドが成功し、作業ツリーがクリーンであることを確認してから、次のパッチバージョンのタグを作成してpushします。

```powershell
git push origin main
git tag vX.Y.Z
git push origin vX.Y.Z
```

タグpushでReleaseワークフローが `dist/translate-local-py.exe` を生成し、同名のGitHub Releaseへ添付します。ワークフロー完了後にReleaseが公開済みで、exeが1件添付され、タグとmainの対象コミットが一致することを確認します。公開済みタグを付け替えず、修正が必要な場合は新しいパッチバージョンで再リリースします。

## Dependabot PR の更新

前提は `.github/dependabot.yml` と PR 用 CI（CI）です。更新 PR の head SHA と `gh pr checks <PR番号>` の結果を確認してください。patch／minor は全チェック成功後に自動取り込みされます。初回 CI 失敗は failed jobs のみを 1 回再実行し、再失敗した PR は残して手動で修正します。

設定を変えたときは `actionlint .github/workflows/dependabot-automation.yml` と実際の PR の Actions 結果を確認します。問題があれば呼び出し先の共通 workflow SHA を直前の検証済み値へ戻すコミットを push します。取り込まれた依存更新に問題があれば通常の revert コミットで復旧します。

CI 完了より Dependabot の分類が遅れる場合は、`callback_workflow_file` が指す呼び出し側 workflow を `workflow_dispatch` し、同じ PR 番号・head SHA・全チェックを再確認する。呼び出し側のファイル名を変える際はこの入力も一緒に更新する。
