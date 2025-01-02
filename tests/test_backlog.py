import pytest
from app import create_app, db
from app.models.project import Project
from app.models.user import User
from app.models.story import Story
from app.models.sprint import Sprint
from flask_login import login_user
from datetime import datetime, timedelta
from config import TestConfig


@pytest.fixture(scope="session")
def app():
    app = create_app(TestConfig)
    return app


@pytest.fixture(scope="function")
def _db(app):
    """各テスト関数で新しいデータベースセッションを使用"""
    with app.app_context():
        db.create_all()
        yield db
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope="function")
def client(app, _db):
    return app.test_client()


@pytest.fixture(scope="function")
def test_user(app, _db):
    """テストユーザーの作成"""
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
    """認証済みクライアント"""
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
        )
        _db.session.add(project)
        _db.session.commit()
        _db.session.refresh(project)
        return project


@pytest.fixture(scope="function")
def test_story(app, _db, test_project, test_user):
    """テストストーリーの作成"""
    with app.app_context():
        story = Story(
            title="Test Story",
            description="Test Story Description",
            project_id=test_project.id,
            status="backlog",
            story_points=5,
            priority=Story.PRIORITY_MEDIUM,
            assignee_id=test_user.id,
        )
        _db.session.add(story)
        _db.session.commit()
        _db.session.refresh(story)
        return story


@pytest.fixture(scope="function")
def test_sprint(app, _db, test_project, test_user):
    """テストスプリントの作成"""
    with app.app_context():
        sprint = Sprint(
            name="Test Sprint",
            goal="Test Sprint Goal",
            project_id=test_project.id,
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=14),
            status="planning",
        )
        _db.session.add(sprint)
        _db.session.commit()
        _db.session.refresh(sprint)
        return sprint


def test_backlog_index_without_project(app, auth_client, test_user):
    """プロジェクト未選択時のバックログページテスト"""
    with app.app_context():
        db.session.add(test_user)
        response = auth_client.get("/backlog")
        assert response.status_code == 200


def test_backlog_index_with_project(app, auth_client, test_project, test_user):
    """プロジェクト選択時のバックログページテスト"""
    with app.app_context():
        db.session.add(test_user)
        db.session.add(test_project)
        response = auth_client.get(f"/backlog/{test_project.id}")
        assert response.status_code == 200


def test_get_stories(app, auth_client, test_project, test_story, test_user):
    """ストーリー一覧取得APIテスト"""
    with app.app_context():
        db.session.add(test_user)
        db.session.add(test_project)
        db.session.add(test_story)
        response = auth_client.get(f"/backlog/{test_project.id}")
        assert response.status_code == 200


def test_delete_story(app, auth_client, test_story, test_user):
    """ストーリー削除APIテスト"""
    with app.app_context():
        db.session.add(test_user)
        db.session.add(test_story)
        response = auth_client.post(
            f"/backlog/story/{test_story.id}/move", json={"sprint_id": None}
        )
        assert response.status_code == 200

        # ストーリーが正常に削除されたことを確認
        story = Story.query.get(test_story.id)
        assert story.sprint_id is None


def test_create_sprint(app, auth_client, test_project, test_user):
    """スプリント作成APIテスト"""
    with app.app_context():
        db.session.add(test_user)
        db.session.add(test_project)

        response = auth_client.post(
            "/api/sprints/create",
            json={
                "name": "New Sprint",
                "goal": "Sprint Goal",
                "project_id": test_project.id,
            },
        )
        assert response.status_code == 200

        # スプリントが正常に作成されたことを確認
        sprint = Sprint.query.filter_by(name="New Sprint").first()
        assert sprint is not None
        assert sprint.goal == "Sprint Goal"
        assert sprint.status == "planning"
        assert sprint.project_id == test_project.id


def test_start_sprint(app, auth_client, test_sprint, test_user):
    """スプリント開始APIテスト"""
    with app.app_context():
        db.session.add(test_user)
        db.session.add(test_sprint)
        response = auth_client.post(
            f"/api/sprints/{test_sprint.id}/start",
            json={"project_id": test_sprint.project_id},
        )
        assert response.status_code == 200

        # スプリントが正常に開始されたことを確認
        sprint = Sprint.query.get(test_sprint.id)
        assert sprint.status == "active"


def test_finish_sprint(app, auth_client, test_sprint, test_user):
    """スプリント完了APIテスト"""
    with app.app_context():
        db.session.add(test_user)
        db.session.add(test_sprint)
        # まずスプリントを開始状態にする
        test_sprint.status = "active"
        test_sprint.started_at = datetime.now()
        db.session.commit()

        response = auth_client.post(
            f"/api/sprints/{test_sprint.id}/complete",
            json={"project_id": test_sprint.project_id},
        )
        assert response.status_code == 200

        # スプリントが正常に完了したことを確認
        sprint = Sprint.query.get(test_sprint.id)
        assert sprint.status == "completed"
