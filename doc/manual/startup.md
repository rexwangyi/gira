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

1. データベースの初期化とテストデータの作成

```bash
# データベースの初期化のみ
flask init-db

# データベースの初期化とテストデータの作成
flask init-db --with-testdata

# テストデータのみを作成
flask create-test-data
```

2. テストユーザーの確認（テストデータを作成した場合）

- 管理者ユーザー

  - ユーザー名: admin
  - パスワード: admin123

- テストユーザー
  - ユーザー名: test
  - パスワード: test123

### 3.3 テストの実行

1. 単体テスト

```bash
python -m pytest tests/unit
```

2. UI テスト

```bash
python tests/ui_test.py
```

## 4. コードスタイルチェック

### 4.1 flake8 の設定

#### デフォルト設定での使用

flake8 は設定ファイルがなくても使用できます。デフォルトの主な設定：

| 項目         | デフォルト値 | 備考            |
| ------------ | ------------ | --------------- |
| 最大行長     | 79 文字      | PEP8 の推奨値   |
| インデント   | 4 スペース   | PEP8 の標準     |
| 複雑度上限   | なし         | 制限なし        |
| 対象ファイル | .py          | Python ファイル |

デフォルト設定での実行：

```bash
flake8 app/
```

#### カスタム設定（推奨）

プロジェクトルートの`.flake8`ファイルに以下の設定があります：

```ini
[flake8]
# 1行の最大文字数
max-line-length = 120

# 除外するディレクトリ
exclude =
    .git,
    __pycache__,
    build,
    dist,
    venv,
    migrations,
    .pytest_cache,
    .vscode,
    instance,
    htmlcov

# 無視するエラー
ignore =
    # E203: ':'の前後のスペース
    E203,
    # W503: 演算子の改行位置
    W503,
    # E402: モジュールレベルのインポート位置
    E402

# 複雑度の最大値
max-complexity = 10

# インポート順序の設定
import-order-style = google
```

### 4.2 flake8 の実行方法

1. 全体のチェック

```bash
flake8
```

2. 特定のディレクトリのチェック

```bash
flake8 app/
flake8 tests/
```

3. 特定のファイルのチェック

```bash
flake8 app/models/story.py
```

### 4.3 主なエラーコードと対処方法

| エラーコード | 説明                     | 対処方法                          |
| ------------ | ------------------------ | --------------------------------- |
| E111         | インデントエラー         | 4 スペースでインデント            |
| E201-E251    | スペースの使用ルール違反 | PEP8 に従ってスペースを調整       |
| E301-E306    | 空行の使用ルール違反     | 関数/クラス定義の前後に適切な空行 |
| F401         | 未使用のインポート       | 不要なインポートを削除            |
| F841         | 未使用の変数             | 使用しない変数を削除または使用    |

### 4.4 自動修正ツールの使用

コードスタイルの自動修正には`black`を使用します：

```bash
# 特定のファイルの修正
black app/models/story.py

# ディレクトリ内の全ファイルを修正
black app/
```

## 5. 注意事項

1. バージョン管理

- Chrome と ChromeDriver のバージョンは一致させる
- 定期的な更新が必要

2. セキュリティ

- テスト用アカウントのパスワードは定期的に変更
- 本番環境では異なる認証情報を使用

3. パフォーマンス

- UI テストは時間がかかる場合がある
- 必要に応じてタイムアウト値を調整
