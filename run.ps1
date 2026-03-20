# pythonw.exe はコンソールを開かず GUI のみ表示する（WindowStyle 不要）
$python = "pythonw"
Start-Process -FilePath $python -ArgumentList ".\main.py"