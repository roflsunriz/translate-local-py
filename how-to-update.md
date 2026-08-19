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
