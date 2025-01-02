import pytest
import logging
from app import create_app, db
from app.models.project import Project
from app.models.user import User
from flask_login import login_user
from config import TestConfig

# ログの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def app():
    app = create_app(TestConfig)
    logger.info(f"テストデータベースURL: {app.config['SQLALCHEMY_DATABASE_URI']}")
    return app


@pytest.fixture(scope="function")
def _db(app):
    """各テスト関数で新しいデータベースセッションを使用"""
    with app.app_context():
        logger.info(f"テストセッションデータベースURL: {app.config['SQLALCHEMY_DATABASE_URI']}")
        db.create_all()
        yield db
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope="function")
def client(app, _db):
    return app.test_client()


@pytest.fixture(scope="function")
def test_user(app, _db):
    with app.app_context():
        user = User(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            avatar_color="#FF0000",
        )
        user.set_password("password")
        _db.session.add(user)
        _db.session.commit()
        _db.session.refresh(user)
        return user


@pytest.fixture(scope="function")
def auth_client(app, client, test_user):
    """認証クライアント"""
    with app.test_request_context():
        login_user(test_user)
        with client.session_transaction() as sess:
            sess["_user_id"] = test_user.id
            sess["_fresh"] = True
    return client


@pytest.fixture(scope="function")
def test_project(app, _db, test_user):
    """テストプロジェクトの作成"""
    with app.app_context():
        project = Project(
            name="Test Project",
            key="TEST",
            description="Test Project Description",
            owner_id=test_user.id,
            status="active",
        )
        _db.session.add(project)
        _db.session.commit()
        _db.session.refresh(project)
        return project


def test_index(app, auth_client, test_user, test_project):
    """プロジェクト一覧ページのテスト"""
    with app.app_context():
        logger.info(f"テストユーザーがプロジェクト一覧ページにアクセス - ユーザーID: {test_user.id}")
        response = auth_client.get("/projects")
        assert response.status_code == 200
        logger.info("プロジェクト一覧ページのアクセス成功")


def test_list_projects(app, auth_client, test_user, test_project):
    """プロジェクト一覧APIの基本機能テスト"""
    with app.app_context():
        logger.info(f"テストユーザーがプロジェクト一覧をリクエスト - ユーザーID: {test_user.id}")
        response = auth_client.get("/api/project/list")
        data = response.get_json()

        assert response.status_code == 200
        assert "projects" in data
        assert len(data["projects"]) == 1
        logger.info(f"{len(data['projects'])}個のプロジェクトを取得")


def test_list_projects_with_search(app, auth_client, test_user, test_project):
    """プロジェクト一覧APIの検索機能テスト"""
    with app.app_context():
        # 名前での検索テスト
        logger.info("プロジェクトを名前で検索")
        response = auth_client.get("/api/project/list?name=Test")
        data = response.get_json()
        assert len(data["projects"]) == 1
        logger.info(f"名前'Test'で{len(data['projects'])}個のプロジェクトを検索")

        # ステータスでの検索テスト
        logger.info("プロジェクトをステータスで検索")
        response = auth_client.get("/api/project/list?status=active")
        data = response.get_json()
        assert len(data["projects"]) == 1
        logger.info(f"ステータス'active'で{len(data['projects'])}個のプロジェクトを検索")

        # 複合条件での検索テスト
        logger.info("プロジェクトを複合条件で検索")
        response = auth_client.get("/api/project/list?name=Test&status=active")
        data = response.get_json()
        assert len(data["projects"]) == 1
        logger.info(f"名前'Test'とステータス'active'で{len(data['projects'])}個のプロジェクトを検索")


def test_create_project(app, auth_client, test_user):
    """プロジェクト作成APIのテスト"""
    with app.app_context():
        logger.info(f"テストユーザーが新規プロジェクトを作成 - ユーザーID: {test_user.id}")
        response = auth_client.post(
            "/api/project/create",
            json={
                "name": "New Test Project",
                "key": "NEW-TEST",
                "description": "New Test Description",
                "owner_id": test_user.id,
            },
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"
        assert data["project"]["name"] == "New Test Project"
        logger.info(f"プロジェクト作成成功 - ID: {data['project']['id']}")

        # プロジェクトがデータベースに正しく保存されているか確認
        project = Project.query.filter_by(name="New Test Project").first()
        assert project is not None
        assert project.description == "New Test Description"
        assert project.status == "active"
        assert project.owner_id == test_user.id
        logger.info("データベース検証完了")


def test_update_project(app, auth_client, test_project):
    """プロジェクト更新APIのテスト"""
    with app.app_context():
        logger.info(f"プロジェクトの更新テスト - ID: {test_project.id}")
        response = auth_client.post(
            "/api/project/update",
            json={
                "id": test_project.id,
                "name": "Updated Project",
                "description": "Updated Description",
                "status": "archived",
            },
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"
        logger.info("プロジェクト更新成功")

        # 更新がデータベースに保存されているか確認
        updated_project = Project.query.get(test_project.id)
        assert updated_project.name == "Updated Project"
        assert updated_project.description == "Updated Description"
        assert updated_project.status == "archived"
        logger.info("データベース検証完了")


def test_delete_project(app, auth_client, test_project):
    """プロジェクト削除APIのテスト"""
    with app.app_context():
        logger.info(f"プロジェクトの削除テスト - ID: {test_project.id}")
        response = auth_client.post("/api/project/delete", json={"id": test_project.id})
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"
        logger.info("プロジェクト削除成功")

        # プロジェクトのステータスがdeletedに更新されているか確認
        deleted_project = Project.query.get(test_project.id)
        assert deleted_project.status == "deleted"
        logger.info("データベース検証完了")


def test_project_detail(app, auth_client, test_project):
    """プロジェクト詳細ページのテスト"""
    with app.app_context():
        logger.info(f"プロジェクト詳細ページへのアクセステスト - ID: {test_project.id}")
        response = auth_client.get(f"/projects/{test_project.id}")
        assert response.status_code == 200
        logger.info("プロジェクト詳細ページのアクセス成功")


def test_project_to_dict(app, _db, test_project):
    """プロジェクトのto_dictメソッドのテスト"""
    with app.app_context():
        # プロジェクトの辞書表現を取得
        project_dict = test_project.to_dict()

        # 辞書に必要なフィールドが含まれているか確認
        assert project_dict["id"] == test_project.id
        assert project_dict["name"] == "Test Project"
        assert project_dict["key"] == "TEST"
        assert project_dict["description"] == "Test Project Description"
        assert project_dict["status"] == "active"
        assert project_dict["owner_id"] == test_project.owner_id
        assert project_dict["created_at"] is not None
        assert project_dict["updated_at"] is not None


def test_project_list_api(app, auth_client, test_project, test_user):
    """プロジェクト一覧APIのテスト"""
    with app.app_context():
        # テストプロジェクトがデータベースにあることを確認
        db.session.add(test_project)
        db.session.commit()

        # テストプロジェクトがデータベースに存在することを確認
        project_in_db = Project.query.get(test_project.id)
        logger.info(f"テストプロジェクトがデータベースに存在: {project_in_db is not None}")
        if project_in_db:
            logger.info(
                f"プロジェクト詳細: ID={project_in_db.id}, 名前={project_in_db.name}, ステータス={project_in_db.status}"
            )

        # ユーザーがログインしていることを確認
        logger.info(f"現在のユーザーID: {test_user.id}")

        # プロジェクト一覧APIを呼び出し
        response = auth_client.get("/api/project/list")
        data = response.get_json()
        logger.info(f"APIレスポンス: status_code={response.status_code}, data={data}")

        # レスポンスの検証
        assert response.status_code == 200
        assert "projects" in data
        assert len(data["projects"]) == 1

        project = data["projects"][0]
        assert project["id"] == test_project.id
        assert project["name"] == "Test Project"
        assert project["key"] == "TEST"
        assert project["status"] == "active"
