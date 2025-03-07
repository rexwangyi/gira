# ユーザー管理機能 詳細設計書

## 1. 概要

ユーザー管理機能は、システム管理者がユーザーアカウントを一元管理するための機能です。ユーザーの作成、編集、削除、および一覧表示が可能で、効率的なユーザー管理を実現します。

## 2. 画面構成

### 2.1 ユーザー一覧画面

![ユーザー一覧画面](../assets/image/user-management.png)

#### 主要コンポーネント

1. ヘッダー部分

   - ページタイトル「ユーザー管理」
   - 新規ユーザー作成ボタン

2. 検索フォーム

   - キーワード検索（ユーザー名、メール、氏名）
   - ステータスフィルター（全て/有効/無効）
   - 検索ボタン

3. ユーザー一覧テーブル

   - アバター（イニシャル表示）
   - ユーザー名
   - メールアドレス
   - 氏名
   - ステータス（有効/無効）
   - 最終ログイン日時
   - 操作ボタン（編集/削除）

4. ページネーション
   - 前へ/次へボタン
   - ページ番号

### 2.2 モーダルダイアログ

1. 新規ユーザー作成モーダル

   - 入力フォーム（ユーザー情報）
   - キャンセル/作成ボタン

2. ユーザー編集モーダル

   - 入力フォーム（既存情報を表示）
   - キャンセル/更新ボタン

3. 削除確認モーダル
   - 確認メッセージ
   - キャンセル/削除ボタン

## 3. 機能詳細

### 3.1 ユーザー一覧表示機能

#### 処理概要

- ユーザー情報をページネーション付きで表示
- 検索条件に応じたフィルタリング
- ステータスによる絞り込み

#### 主要ロジック

```python
@bp.route("/users")
@login_required
def users():
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "")
    status = request.args.get("status", "")

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

    pagination = query.order_by(User.username).paginate(
        page=page,
        per_page=current_app.config["USERS_PER_PAGE"],
        error_out=False,
    )
```

### 3.2 ユーザー作成機能

#### 処理概要

- 新規ユーザーアカウントの作成
- 必須情報の入力チェック
- 重複チェック（ユーザー名、メール）

#### バリデーションルール

```python
class UserForm(FlaskForm):
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
    # ... その他のフィールド
```

### 3.3 ユーザー編集機能

#### 処理概要

- 既存ユーザー情報の更新
- パスワードの選択的更新
- アカウントの有効/無効切り替え

#### 主要ロジック

```python
@bp.route("/users/<int:user_id>/edit", methods=["POST"])
@login_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = UserForm()
    form.user_id = user_id

    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        user.is_active = form.is_active.data

        if form.password.data:
            user.set_password(form.password.data)
```

### 3.4 ユーザー削除機能

#### 処理概要

- ユーザーアカウントの削除
- 自身の削除防止
- 削除前の確認

#### セキュリティ考慮事項

- 自分自身の削除を防止
- 削除前の確認ダイアログ表示
- トランザクション管理

## 4. セキュリティ対策

### 4.1 アクセス制御

- ログインユーザーのみアクセス可能
- CSRF 対策の実装
- セッション管理

### 4.2 入力検証

- サーバーサイドでのバリデーション
- SQL インジェクション対策
- XSS 対策

### 4.3 エラー処理

- 適切なエラーメッセージ
- ログ記録
- トランザクション管理

## 5. 非機能要件

### 5.1 パフォーマンス

- ページネーションによる表示制御（10 件/ページ）
- インデックスの適切な設定
- N+1 問題の回避

### 5.2 ユーザビリティ

- レスポンシブデザイン
- 直感的な UI/UX
- フィードバックメッセージの表示

### 5.3 保守性

- モジュール化された設計
- コードの再利用性
- 適切なコメント付与

## 6. テスト項目

### 6.1 機能テスト

1. ユーザー一覧表示

   - 正常表示
   - 検索機能
   - ページネーション
   - ステータスフィルター

2. ユーザー作成

   - 正常作成
   - バリデーションチェック
   - 重複チェック

3. ユーザー編集

   - 情報更新
   - パスワード変更
   - ステータス変更

4. ユーザー削除
   - 正常削除
   - 自身の削除防止
   - 関連データの整合性

### 6.2 セキュリティテスト

- 認証・認可
- CSRF 対策
- XSS 対策
- SQL インジェクション対策

### 6.3 非機能テスト

- レスポンス時間
- ブラウザ互換性
- モバイル対応
- エラー処理
