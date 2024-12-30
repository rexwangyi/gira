# 標準ライブラリ
import logging
import os
from logging.handlers import RotatingFileHandler

# サードパーティライブラリ
from flask import Flask, redirect, url_for
from flask_login import login_required

# ローカルアプリケーション
from app.extensions import db, login_manager, migrate
from config import Config

# ロガーの設定
logger = logging.getLogger("gira")
logger.setLevel(logging.INFO)


def create_app(test_config=None):
    app = Flask(__name__)

    if test_config is None:
        app.config.from_object(Config)
    else:
        # テスト設定が提供された場合は、それを使用
        app.config.from_object(test_config)

    # 拡張機能の初期化
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # ログハンドラーの設定
    if app.config["LOG_TYPE"] == "file":
        if not os.path.exists("logs"):
            os.mkdir("logs")
        file_handler = RotatingFileHandler(
            app.config["LOG_FILE"],
            maxBytes=app.config["LOG_MAX_BYTES"],
            backupCount=app.config["LOG_BACKUP_COUNT"],
            encoding="utf-8",
        )
        formatter = logging.Formatter(
            fmt=app.config["LOG_FORMAT"], datefmt=app.config["LOG_DATE_FORMAT"]
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(app.config["LOG_LEVEL"])
        logger.addHandler(file_handler)
    else:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(logging.Formatter(app.config["LOG_FORMAT"]))
        stream_handler.setLevel(app.config["LOG_LEVEL"])
        logger.addHandler(stream_handler)

    logger.info("GIRA application startup")

    # Blueprintの登録
    from app.views import auth, main, backlog, kanban
    from app.views import project as project_views  # 名前を変更してインポート

    # 認証関連ルートを先に登録
    app.register_blueprint(auth.bp)

    # その他のルートを登録
    app.register_blueprint(main.bp)
    app.register_blueprint(backlog.bp)
    app.register_blueprint(kanban.bp, url_prefix="/kanban")
    app.register_blueprint(project_views.bp, url_prefix="")  # 変更した名前を使用

    # ルートパスをbacklogにリダイレクト
    @app.route("/")
    @login_required
    def index():
        return redirect(url_for("backlog.index"))

    from . import commands

    app.cli.add_command(commands.init_db_command)
    app.cli.add_command(commands.create_test_data)

    return app


# 循環インポートを避けるためにモデルを最後にインポート
# noqa: F401は未使用インポートの警告を抑制
from app.models import user, project, story, sprint  # noqa: F401
