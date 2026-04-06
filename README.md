# translate-local-py

ローカルの OpenAI 互換 API サーバーまたは Google 翻訳を使って文章を翻訳するデスクトップアプリです。

## 特長

- OpenAI 互換 API と Google 翻訳を切り替え可能
- 言語コードを直接入力できるコンボボックス
- システムプロンプトとユーザーメッセージテンプレートを設定画面から編集可能
- 最前面表示、透明度調整、コピー、クリアに対応
- `resources/icon.ico` をアプリのウィンドウアイコンと Windows ビルドのアイコンに使用

## 動作環境

- Python 3.12 以上
- Windows 11 / Windows 10
- OpenAI 互換 API を使う場合は、ローカルまたはネットワーク上で API サーバーが起動済みであること

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
