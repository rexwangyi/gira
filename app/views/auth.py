from datetime import datetime
from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    jsonify,
    current_app,
)
from flask_login import login_user, logout_user, login_required, current_user
from app import db, logger
from app.models.user import User
from app.forms.auth import LoginForm, RegistrationForm, UserForm
import random

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


@bp.route("/users")
@login_required
def users():
    """ユーザー一覧ページ"""
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "")
    status = request.args.get("status", "")

    # クエリの構築
    query = User.query
    if search:
        query = query.filter(
            (User.username.ilike(f"%{search}%"))
            | (User.email.ilike(f"%{search}%"))
            | (User.first_name.ilike(f"%{search}%"))
            | (User.last_name.ilike(f"%{search}%"))
        )
    if status == "active":
        query = query.filter_by(is_active=True)
    elif status == "inactive":
        query = query.filter_by(is_active=False)

    # ページネーション
    pagination = query.order_by(User.username).paginate(
        page=page,
        per_page=current_app.config["USERS_PER_PAGE"],
        error_out=False,
    )

    return render_template(
        "auth/users.html",
        users=pagination.items,
        pagination=pagination,
        form=UserForm(),
    )


@bp.route("/api/users/<int:user_id>")
@login_required
def get_user(user_id):
    """ユーザー情報のAPI"""
    user = User.query.get_or_404(user_id)
    return jsonify(
        {
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_active": user.is_active,
        }
    )


@bp.route("/users/create", methods=["POST"])
@login_required
def create_user():
    """ユーザーの新規作成"""
    form = UserForm()
    if form.validate_on_submit():
        # ランダムなアバター色を生成
        colors = ["#0052CC", "#00875A", "#FF5630", "#6554C0", "#FFAB00", "#FF7452"]
        avatar_color = random.choice(colors)

        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            avatar_color=avatar_color,
            is_active=form.is_active.data,
        )
        user.set_password(form.password.data)

        try:
            db.session.add(user)
            db.session.commit()
            flash("ユーザーを作成しました。", "success")
        except Exception as e:
            db.session.rollback()
            flash("ユーザーの作成に失敗しました。", "error")
            current_app.logger.error(f"Failed to create user: {str(e)}")

    return redirect(url_for("auth.users"))


@bp.route("/users/<int:user_id>/edit", methods=["POST"])
@login_required
def edit_user(user_id):
    """ユーザーの編集"""
    user = User.query.get_or_404(user_id)
    form = UserForm()
    form.user_id = user_id  # バリデーション用にuser_idを設定

    if form.validate_on_submit():
        try:
            user.username = form.username.data
            user.email = form.email.data
            user.first_name = form.first_name.data
            user.last_name = form.last_name.data
            user.is_active = form.is_active.data

            if form.password.data:
                user.set_password(form.password.data)

            db.session.commit()
            flash("ユーザー情報を更新しました。", "success")
        except Exception as e:
            db.session.rollback()
            flash("ユーザー情報の更新に失敗しました。", "error")
            current_app.logger.error(f"Failed to update user: {str(e)}")

    return redirect(url_for("auth.users"))


@bp.route("/users/<int:user_id>/delete", methods=["POST"])
@login_required
def delete_user(user_id):
    """ユーザーの削除"""
    if current_user.id == user_id:
        flash("自分自身は削除できません。", "error")
        return redirect(url_for("auth.users"))

    user = User.query.get_or_404(user_id)
    try:
        db.session.delete(user)
        db.session.commit()
        flash("ユーザーを削除しました。", "success")
    except Exception as e:
        db.session.rollback()
        flash("ユーザーの削除に失敗しました。", "error")
        current_app.logger.error(f"Failed to delete user: {str(e)}")

    return redirect(url_for("auth.users"))
