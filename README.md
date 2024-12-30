# Gira - プロジェクト管理システム

![Run Tests](https://github.com/rexwangyi/gira/actions/workflows/main.yml/badge.svg)

Gira は Flask で開発されたプロジェクト管理システムです。カンバンボード、バックログ管理、スプリント管理などの機能を提供します。

![ロゴ](doc/assets/image/logo.png)

## 機能一覧

- プロジェクト管理

  - プロジェクトの作成・編集・削除
  - プロジェクト一覧表示と検索
  - プロジェクト詳細表示

- カンバンボード

  - ストーリーのステータス管理
  - ドラッグ＆ドロップでのステータス更新
  - ストーリーの詳細表示

- バックログ管理
  - ストーリーの作成・編集・削除
  - スプリントの作成・開始・完了
  - ストーリーのスプリントへの割り当て

## 技術スタック

### バックエンド

| ライブラリ       | バージョン | 用途                |
| ---------------- | ---------- | ------------------- |
| Python           | 3.8+       | 実行環境            |
| Flask            | 2.3.3      | Web フレームワーク  |
| Flask-SQLAlchemy | 3.0.5      | ORM ツール          |
| Flask-Login      | 0.6.2      | 認証管理            |
| Flask-WTF        | 1.1.1      | フォーム処理        |
| Flask-Migrate    | 4.0.4      | DB マイグレーション |
| SQLite           | 3.x        | データベース        |

### フロントエンド

| ライブラリ  | バージョン | 用途              |
| ----------- | ---------- | ----------------- |
| Bootstrap   | 5.3.0      | UI フレームワーク |
| jQuery      | 3.7.0      | DOM 操作          |
| Sortable.js | 1.15.0     | ドラッグ&ドロップ |
| Chart.js    | 4.3.0      | グラフ描画        |

### 開発ツール

| ツール     | バージョン | 用途                 |
| ---------- | ---------- | -------------------- |
| pytest     | 7.4.0      | ユニットテスト       |
| pytest-cov | 4.1.0      | カバレッジ測定       |
| black      | 23.7.0     | コードフォーマッター |
| flake8     | 6.1.0      | リンター             |

## セットアップ

1. リポジトリのクローン

```bash
git clone https://github.com/yourusername/gira.git
cd gira
```

2. 仮想環境の作成と有効化

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

4. データベースの初期化

```bash
flask db upgrade
python scripts/init_db.py
```

5. アプリケーションの起動

```bash
flask run
```

## テスト

テストの実行:

```bash
pytest
```

特定のテストファイルの実行:

```bash
pytest tests/test_project.py
pytest tests/test_kanban.py
pytest tests/test_backlog.py
```

## ドキュメント

### マニュアル

- [開発環境のセットアップ](doc/manual/startup.md)
- [プロンプトの使用方法](doc/manual/prompt_jp.md)

### 基本設計書

- [データベース設計](doc/basic-design/database.md)
- [画面設計](doc/basic-design/ui-design.md)
- [API 設計](doc/basic-design/api-spec.md)
- [インフラ構成](doc/basic-design/infrastructure.md)

### 詳細設計書

- [共通設計](doc/detail-design/common.md)
- [ログイン機能](doc/detail-design/login.md)
- [プロジェクト管理](doc/detail-design/project.md)
- [カンバンボード](doc/detail-design/kanban.md)
- [バックログ管理](doc/detail-design/backlog.md)

### テスト仕様書

- [単体テスト仕様書](doc/test-case/unit.md)
- [プロジェクト管理テスト仕様書](doc/test-case/project-test-cases.md)
- [バックログテスト仕様書](doc/test-case/backlog-test-cases.md)
- [カンバンボードテスト仕様書](doc/test-case/kanban-test-cases.md)
- [ログインテスト仕様書](doc/test-case/login-test-cases.md)
- [UI 自動化テスト仕様書](doc/test-case/ui-autotest.md)

## 動作確認済み環境

- OS: Windows 10/11, macOS, Linux
- ブラウザ: Chrome, Firefox, Safari（最新版）
- Python: 3.8 以上

## ライセンス

MIT License
