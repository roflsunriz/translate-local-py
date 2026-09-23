# 検証手順

## Dependabot 自動処理（2026-09-23）

`.github/workflows/dependabot-automation.yml` を actionlint で検査し、PR 用 workflow 名（CI）と一致することを確認する。Dependabot の patch／minor かつ全 PR チェック成功の場合だけ取り込み、major・古い SHA・再失敗は残す。

実際の Dependabot PR がまだない場合、動作経路は未検証として扱う。実 PR 発生後に自動化ジョブ、CI の再試行、マージ結果を確認する。

2026-09-23にPR #1〜#5（actions/checkout v4→v7、actions/setup-python v5→v7、softprops/action-gh-release v2→v3、PyQt6下限6.6→6.11.0、requests下限2.31→2.34.2）で全CI成功を確認し、#1〜#4を即マージ、#5はrequirements.txtの競合を両下限維持で解消して再CI成功後にマージした。mainのCI成功、`python -m compileall src main.py`、`python -m unittest discover -s tests`成功、`pip-audit -r requirements.txt`で脆弱性なしを確認した。

大量の Dependabot PR により CI 完了より分類が遅れる場合でも、分類後の `workflow_dispatch` が現在の PR 番号と head SHA を照合して再評価する。別の作成者、古い SHA、未完了の CI はマージしない。
