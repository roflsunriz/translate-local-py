# LLM Translation Desktop App

LunaTranslator と併用するチャットコミュニケーション補助翻訳ツール。  
ローカルの llama-server（OpenAI 互換 API）を利用してテキストを翻訳し、結果をコピーしてチャットに貼り付ける運用を想定。

## 機能

- **2つの翻訳エンジン**: OpenAI 互換 API（llama-server）と Google 翻訳（非公式 API）を設定で切り替え可能
- 編集可能コンボボックスによる言語選択（プリセット＋言語コード直接入力）
- カスタマイズ可能なシステムプロンプト・ユーザーメッセージテンプレート（OpenAI 互換 API 使用時）
- AlwaysOnTop トグル（ゲーム・チャット画面の上に常時表示）
- ワンクリックで翻訳結果をクリップボードにコピー
- 翻訳結果の手動微修正に対応（訳文エリアは編集可能）

## 前提条件

- Python 3.12+
- llama-server（または OpenAI 互換 API サーバー）が起動済み

## セットアップ

```bash
# 仮想環境の作成と有効化
python -m venv .venv
.venv\Scripts\Activate.ps1   # Windows PowerShell

# 依存パッケージのインストール
pip install -r requirements.txt
```

## 起動

```bash
python main.py
```

## 設定

初回起動時に `config.json` が自動生成される。  
アプリ内の設定ダイアログ（歯車アイコン）から以下を変更可能:

### 翻訳エンジン

設定ダイアログ上部のトグルスイッチで切り替え:

| エンジン | 説明 |
|---------|------|
| OpenAI 互換 API | llama-server 等のローカル LLM サーバーを使用。プロンプトのカスタマイズ可能 |
| Google 翻訳 | Google Translate の非公式 API を使用。API キー不要 |

### API 設定（OpenAI 互換 API 選択時）

| 項目 | デフォルト値 | 説明 |
|------|-------------|------|
| API URL | `http://127.0.0.1:8080` | llama-server のエンドポイント |
| モデル名 | (空) | llama-server のデフォルトモデルを使用 |
| Temperature | 0.3 | 生成の多様性 |
| Max Tokens | 1024 | 最大生成トークン数 |
| タイムアウト | 60秒 | API リクエストタイムアウト |

### プロンプトテンプレート

設定ダイアログの「プロンプト」タブで、システムプロンプトとユーザーメッセージテンプレートを自由に編集可能。  
以下のプレースホルダーが利用可能:

- `{{source_language}}` — ソース言語コード（例: `ja`）
- `{{target_language}}` — ターゲット言語コード（例: `en`）
- `{{input_text}}` — 翻訳対象のテキスト

## ショートカットキー

| キー | 動作 |
|------|------|
| Ctrl+Enter | 翻訳実行 |

## トラブルシュート

- **接続エラー（OpenAI互換API）**: llama-server が起動しているか、API URL が正しいか確認
- **翻訳結果が空**: モデルがプロンプト形式に対応しているか確認。設定ダイアログでテンプレートを調整
- **Google翻訳が失敗する**: インターネット接続を確認。非公式 API のためレートリミットの可能性あり
- **設定リセット**: `config.json` を削除して再起動するとデフォルト設定に戻る
