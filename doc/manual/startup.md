# 開発環境セットアップ手順

## 1. Chrome WebDriver のセットアップ

### 1.1 前提条件

| 項目          | 要件     | 備考               |
| ------------- | -------- | ------------------ |
| Google Chrome | 最新版   | 定期的な更新が必要 |
| Python        | 3.8 以上 | 3.11 推奨          |
| pip           | 最新版   | Python に付属      |

### 1.2 セットアップ手順

#### Windows 環境

1. Chrome WebDriver のインストール

```bash
pip install webdriver-manager
```

2. 環境変数の設定

- システムのプロパティ → 環境変数 → Path に以下を追加

```
%USERPROFILE%\AppData\Local\Programs\Python\Python3x\Scripts
```

#### Mac 環境

1. Chrome WebDriver のインストール

```bash
pip3 install webdriver-manager
```

2. 権限の設定

```bash
chmod +x ~/Library/Application\ Support/Google/Chrome/Default/chromedriver
```

#### Linux 環境

1. Chrome WebDriver のインストール

```bash
pip3 install webdriver-manager
```

2. 必要なパッケージのインストール

```bash
sudo apt-get update
sudo apt-get install -y chromium-browser
```

### 1.3 動作確認

1. Python スクリプトでの確認

```python
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

# WebDriverの初期化
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)

# テストページにアクセス
driver.get("http://127.0.0.1:5000")

# ブラウザを閉じる
driver.quit()
```

### 1.4 トラブルシューティング

| エラー内容              | 原因               | 対処方法             |
| ----------------------- | ------------------ | -------------------- |
| ChromeDriver not found  | パスが通っていない | 環境変数の設定を確認 |
| Permission denied       | 実行権限がない     | chmod +x で権限付与  |
| Chrome version mismatch | バージョンの不一致 | Chrome を更新        |

## 2. 必要な Python パッケージ

| パッケージ名      | バージョン | 用途           | インストールコマンド          |
| ----------------- | ---------- | -------------- | ----------------------------- |
| selenium          | 4.x        | ブラウザ操作   | pip install selenium          |
| webdriver-manager | 最新       | WebDriver 管理 | pip install webdriver-manager |

## 3. 開発環境の準備

### 3.1 アプリケーションサーバー

1. サーバーの起動

```bash
python app.py
```

2. 確認事項

- http://127.0.0.1:5000 にアクセス可能
- ログイン画面が表示される

### 3.2 テストデータの準備

1. データベースの初期化

```bash
python init_db.py
```

2. テストユーザーの確認

- ユーザー名: admin
- パスワード: admin123

### 3.3 テストの実行

1. 単体テスト

```bash
python -m pytest tests/unit
```

2. UI テスト

```bash
python tests/ui_test.py
```

## 4. 注意事項

1. バージョン管理

- Chrome と ChromeDriver のバージョンは一致させる
- 定期的な更新が必要

2. セキュリティ

- テスト用アカウントのパスワードは定期的に変更
- 本番環境では異なる認証情報を使用

3. パフォーマンス

- UI テストは時間がかかる場合がある
- 必要に応じてタイムアウト値を調整
