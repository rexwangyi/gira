from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.fields import EmailField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from app.models.user import User


class LoginForm(FlaskForm):
    username = StringField("ユーザー名", validators=[DataRequired()])
    password = PasswordField("パスワード", validators=[DataRequired()])
    remember_me = BooleanField("ログイン状態を保持")
    submit = SubmitField("ログイン")


class RegistrationForm(FlaskForm):
    username = StringField(
        "ユーザー名",
        validators=[
            DataRequired(),
            Length(min=3, max=64, message="ユーザー名は3文字以上64文字以下で入力してください"),
        ],
    )
    email = EmailField(
        "メールアドレス",
        validators=[
            DataRequired(),
            Email(),
            Length(max=120, message="メールアドレスは120文字以下で入力してください"),
        ],
    )
    password = PasswordField(
        "パスワード",
        validators=[DataRequired(), Length(min=8, message="パスワードは8文字以上で入力してください")],
    )
    password2 = PasswordField(
        "パスワード（確認）",
        validators=[DataRequired(), EqualTo("password", message="パスワードが一致しません")],
    )
    submit = SubmitField("登録")

    def validate_username(self, username):
        """ユーザー名の重複チェック"""
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError("このユーザー名は既に使用されています")

    def validate_email(self, email):
        """メールアドレスの重複チェック"""
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError("このメールアドレスは既に使用されています")


class ResetPasswordRequestForm(FlaskForm):
    email = EmailField("メールアドレス", validators=[DataRequired(), Email()])
    submit = SubmitField("パスワードリセット")


class ResetPasswordForm(FlaskForm):
    password = PasswordField(
        "新しいパスワード",
        validators=[DataRequired(), Length(min=8, message="パスワードは8文字以上で入力してください")],
    )
    password2 = PasswordField(
        "新しいパスワード（確認）",
        validators=[DataRequired(), EqualTo("password", message="パスワードが一致しません")],
    )
    submit = SubmitField("パスワードを変更")
