# translate-local-py

複数の翻訳バックエンドを切り替えて文章を翻訳するデスクトップアプリです。

## 特長

- `ローカル` `Google翻訳` `OpenRouter` `Cerebras` `Sakura` `自由入力` を切り替え可能
- OpenRouter / Cerebras / Sakura / 自由入力の API キーとモデル設定を個別保存
- 言語コードを直接入力できるコンボボックス
- システムプロンプトとユーザーメッセージテンプレートを設定画面から編集可能
- 最前面表示、透明度調整、コピー、クリアに対応
- `resources/icon.ico` をアプリのウィンドウアイコンと Windows ビルドのアイコンに使用

## 動作環境

- Python 3.12 以上
- Windows 11 / Windows 10
- `ローカル` を使う場合は、互換 API サーバーが起動済みであること

## セットアップ

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 起動

```powershell
python main.py
```

## 設定ファイル

初回起動時に `config.json` が自動生成されます。

- 通常実行時はリポジトリ直下に保存
- PyInstaller で配布した実行ファイルでは、実行ファイルと同じフォルダに保存

## ビルド

PyInstaller の単体実行ファイルを作る場合は以下を使います。

```powershell
pyinstaller --noconfirm --clean --windowed --name translate-local-py --icon resources/icon.ico --add-data "resources;resources" main.py
```

## CI / CD

GitHub Actions で以下を実行します。

- CI: Python 3.12 / 3.13 の matrix でインポートとコンパイルを確認
- Release: `v*` タグの push で PyInstaller ビルドを実行し、成果物を GitHub Release に添付

## ライセンス

MIT
