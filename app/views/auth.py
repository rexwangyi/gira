from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db, logger
from app.models.user import User
from app.forms.auth import LoginForm, RegistrationForm

bp = Blueprint("auth", __name__)


@bp.route("/login", methods=["GET", "POST"])
def login():
    """ユーザーログイン"""
    try:
        # 既にログインしている場合はトップページへリダイレクト
        if current_user.is_authenticated:
            logger.info(
                f"Already authenticated user {current_user.username} accessing login page"
            )
            return redirect(url_for("backlog.index"))

        # アクセス情報を記録
        if request.method == "GET":
            logger.info(f"Login page accessed from IP: {request.remote_addr}")

        form = LoginForm()
        if form.validate_on_submit():
            username = form.username.data
            logger.info(
                f"Login attempt for user: {username} from IP: {request.remote_addr}"
            )

            user = User.query.filter_by(username=username).first()

            if user is None:
                logger.warning(f"Login failed - User not found: {username}")
                flash("ユーザー名またはパスワードが正しくありません", "error")
                return redirect(url_for("auth.login"))

            if not user.check_password(form.password.data):
                logger.warning(f"Login failed - Invalid password for user: {username}")
                flash("ユーザー名またはパスワードが正しくありません", "error")
                return redirect(url_for("auth.login"))

            if not user.is_active:
                logger.warning(f"Login failed - Inactive user: {username}")
                flash("アカウントが無効です", "error")
                return redirect(url_for("auth.login"))

            # ログイン成功
            login_user(user, remember=form.remember_me.data)

            # 最終ログイン時刻を更新
            old_last_login = user.last_login
            user.update_last_login()

            logger.info(
                f"User {username} logged in successfully - Previous login: {old_last_login}"
            )

            # ログインセッション情報を記録
            logger.debug(
                f"Session info - Remember me: {form.remember_me.data}, User ID: {user.id}"
            )

            next_page = url_for("backlog.index")
            flash("ログインに成功しました", "success")
            return redirect(next_page)

        return render_template("auth/login.html", title="ログイン", form=form)
    except Exception as e:
        logger.error(f"Error in login view: {str(e)}", exc_info=True)
        flash("エラーが発生しました", "error")
        return redirect(url_for("auth.login"))


@bp.route("/logout")
@login_required
def logout():
    """ユーザーログアウト"""
    try:
        username = current_user.username
        user_id = current_user.id
        last_login = current_user.last_login

        logout_user()

        logger.info(f"User logged out - Username: {username}, ID: {user_id}")
        logger.debug(
            f"Logout details - Last login: {last_login}, Session duration: {datetime.now() - last_login}"
        )

        flash("ログアウトしました", "info")
        return redirect(url_for("auth.login"))
    except Exception as e:
        logger.error(f"Error in logout view: {str(e)}", exc_info=True)
        flash("エラーが発生しました", "error")
        return redirect(url_for("auth.login"))


@bp.route("/register", methods=["GET", "POST"])
def register():
    """ユーザー登録"""
    try:
        if current_user.is_authenticated:
            logger.info(
                f"Already authenticated user {current_user.username} accessing register page"
            )
            return redirect(url_for("backlog.index"))

        if request.method == "GET":
            logger.info(f"Register page accessed from IP: {request.remote_addr}")

        form = RegistrationForm()
        if form.validate_on_submit():
            username = form.username.data
            email = form.email.data
            logger.info(
                f"Registration attempt - Username: {username}, Email: {email}, IP: {request.remote_addr}"
            )

            # ユーザー名の重複チェック
            if User.query.filter_by(username=username).first():
                logger.warning(
                    f"Registration failed - Username already exists: {username}"
                )
                flash("このユーザー名は既に使用されています", "error")
                return redirect(url_for("auth.register"))

            # メールアドレスの重複チェック
            if User.query.filter_by(email=email).first():
                logger.warning(f"Registration failed - Email already exists: {email}")
                flash("このメールアドレスは既に使用されています", "error")
                return redirect(url_for("auth.register"))

            # 新規ユーザーを作成
            user = User(username=username, email=email, is_active=True)
            user.set_password(form.password.data)

            try:
                db.session.add(user)
                db.session.commit()
                logger.info(
                    f"User registered successfully - Username: {username}, ID: {user.id}"
                )

                # 自動ログイン
                login_user(user)
                user.update_last_login()
                logger.info(
                    f"New user {username} logged in automatically after registration"
                )

                flash("登録が完了しました", "success")
                return redirect(url_for("backlog.index"))
            except Exception as e:
                db.session.rollback()
                logger.error(
                    f"Database error while registering user: {str(e)}", exc_info=True
                )
                flash("登録に失敗しました", "error")
                return redirect(url_for("auth.register"))

        return render_template("auth/register.html", title="新規登録", form=form)
    except Exception as e:
        logger.error(f"Error in register view: {str(e)}", exc_info=True)
        flash("エラーが発生しました", "error")
        return redirect(url_for("auth.register"))
