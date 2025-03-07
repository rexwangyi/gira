import os
from datetime import timedelta


class Config:
    # 基本設定
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key"

    # データベース設定
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL"
    ) or "sqlite:///" + os.path.join(
        os.path.abspath(os.path.dirname(__file__)), "instance", "gira.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = True  # 启用SQL日志记录

    # セッション設定
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=60)

    # ログ設定
    LOG_TYPE = os.environ.get("LOG_TYPE", "file")  # stream or file
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    LOG_FILE = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), "logs", "app.log"
    )
    LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
    LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S %z"  # タイムゾーン情報を含む
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5

    # ページネーション設定
    USERS_PER_PAGE = 10  # ユーザー一覧の1ページあたりの表示件数


class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(
        os.path.abspath(os.path.dirname(__file__)), "instance", "giratest.db"
    )  # 使用测试数据库
    LOGIN_DISABLED = False  # 启用登录功能
    SECRET_KEY = "test-secret-key"
