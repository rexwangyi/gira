from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Email, Length, Optional, ValidationError
from app.models.user import User


class UserForm(FlaskForm):
    """ユーザー作成・編集フォーム"""

    username = StringField(
        "ユーザー名",
        validators=[
            DataRequired(message="ユーザー名は必須です"),
            Length(min=3, max=64, message="ユーザー名は3〜64文字で入力してください"),
        ],
    )
    email = StringField(
        "メールアドレス",
        validators=[
            DataRequired(message="メールアドレスは必須です"),
            Email(message="有効なメールアドレスを入力してください"),
            Length(max=120, message="メールアドレスは120文字以内で入力してください"),
        ],
    )
    password = PasswordField(
        "パスワード",
        validators=[
            Optional(),
            Length(min=6, message="パスワードは6文字以上で入力してください"),
        ],
    )
    first_name = StringField(
        "名",
        validators=[
            Optional(),
            Length(max=64, message="名は64文字以内で入力してください"),
        ],
    )
    last_name = StringField(
        "姓",
        validators=[
            Optional(),
            Length(max=64, message="姓は64文字以内で入力してください"),
        ],
    )
    is_active = BooleanField("アクティブ", default=True)

    def validate_username(self, field):
        """ユーザー名の重複チェック"""
        user = User.query.filter_by(username=field.data).first()
        if user and (not hasattr(self, "user_id") or user.id != self.user_id):
            raise ValidationError("このユーザー名は既に使用されています")

    def validate_email(self, field):
        """メールアドレスの重複チェック"""
        user = User.query.filter_by(email=field.data).first()
        if user and (not hasattr(self, "user_id") or user.id != self.user_id):
            raise ValidationError("このメールアドレスは既に使用されています")
