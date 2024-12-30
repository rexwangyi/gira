from flask import Blueprint, render_template, jsonify, request, session
from flask_login import login_required, current_user
from app.models.project import Project
from app.extensions import db
from app import logger

bp = Blueprint("project", __name__)


@bp.route("/projects")
@bp.route("/projects/<int:project_id>")
@login_required
def index(project_id=None):
    """プロジェクト一覧ページ"""
    try:
        logger.info(f"User {current_user.username} accessing projects page")

        # 現在のプロジェクトを取得（存在する場合）
        current_project = None
        if project_id:
            current_project = Project.query.get_or_404(project_id)
            session["project_id"] = project_id
            logger.info(f"Selected project: {current_project.name} (ID: {project_id})")
        elif "project_id" in session:
            current_project = Project.query.get(session["project_id"])
            if current_project:
                logger.info(
                    f"Using session project: {current_project.name} (ID: {session['project_id']})"
                )

        # ドロップダウンメニュー用に全プロジェクトを取得
        projects = Project.query.filter(Project.status != "deleted").all()
        logger.debug(f"Found {len(projects)} active projects")

        return render_template(
            "project/index.html", current_project=current_project, projects=projects
        )
    except Exception as e:
        logger.error(f"Error in project index view: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@bp.route("/api/project/list")
@login_required
def list_projects():
    """プロジェクトリストAPI"""
    try:
        # 検索パラメータを取得
        name = request.args.get("name", "")
        status = request.args.get("status", "")

        logger.info(
            f"Project list requested by {current_user.username} - filters: name='{name}', status='{status}'"
        )

        # データベース内の全プロジェクトを取得（フィルタリングなし）
        all_projects_query = Project.query
        logger.info(f"All projects SQL: {str(all_projects_query)}")
        all_projects = all_projects_query.all()
        logger.info(f"Total projects in database: {len(all_projects)}")
        for p in all_projects:
            logger.info(f"Project: ID={p.id}, Name={p.name}, Status={p.status}")

        # クエリを構築（ステータスフィルタリングは行わない）
        query = Project.query

        # 検索条件を追加
        if name:
            query = query.filter(Project.name.like(f"%{name}%"))
            logger.info(f"Query with name filter: {str(query)}")
        if status:
            query = query.filter(Project.status == status)
            logger.info(f"Query with status filter: {str(query)}")

        logger.info(f"Final SQL: {str(query)}")
        projects = query.all()
        logger.debug(f"Found {len(projects)} projects matching criteria")

        return jsonify({"projects": [project.to_dict() for project in projects]})
    except Exception as e:
        logger.error(f"Error in list_projects API: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@bp.route("/api/project/create", methods=["POST"])
@login_required
def create_project():
    """プロジェクト作成API"""
    try:
        data = request.get_json()
        logger.info(
            f"Project creation requested by {current_user.username} - name: {data.get('name', '')}"
        )

        # プロジェクトキーを生成
        last_project_query = Project.query.order_by(Project.id.desc())
        logger.info("Last project query: {}".format(str(last_project_query)))
        last_project = last_project_query.first()
        next_id = (last_project.id + 1) if last_project else 1
        key = data.get("key") or f"PRJ-{next_id:04d}"

        project = Project(
            name=data["name"],
            key=key,
            description=data.get("description", ""),
            status=data.get("status", "active"),
            owner_id=data.get("owner_id", current_user.id),
        )
        db.session.add(project)
        logger.info("Executing INSERT query for new project")
        db.session.commit()

        logger.info(
            f"Project created successfully - ID: {project.id}, Key: {project.key}, Name: {project.name}"
        )
        return jsonify({"status": "success", "project": project.to_dict()})
    except Exception as e:
        logger.error(f"Error creating project: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@bp.route("/api/project/update", methods=["POST"])
@login_required
def update_project():
    """プロジェクト更新API"""
    try:
        data = request.get_json()
        project = Project.query.get_or_404(data["id"])

        logger.info(
            f"Project update requested by {current_user.username} - ID: {project.id}, Name: {project.name}"
        )

        # 変更を記録
        changes = []
        if project.name != data["name"]:
            changes.append(f"name: {project.name} -> {data['name']}")
        if project.description != data.get("description", ""):
            changes.append("description updated")
        if project.status != data.get("status", "active"):
            changes.append(f"status: {project.status} -> {data.get('status')}")

        # プロジェクトを更新
        project.name = data["name"]
        project.description = data.get("description", "")
        project.status = data.get("status", "active")
        db.session.commit()

        logger.info(f"Project updated successfully - Changes: {', '.join(changes)}")
        return jsonify({"status": "success", "project": project.to_dict()})
    except Exception as e:
        logger.error(f"Error updating project: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@bp.route("/api/project/delete", methods=["POST"])
@login_required
def delete_project():
    """プロジェクト削除API"""
    try:
        data = request.get_json()
        project = Project.query.get_or_404(data["id"])

        logger.info(
            f"Project deletion requested by {current_user.username} - ID: {project.id}, Name: {project.name}"
        )

        # プロジェクトのステータスを変更
        old_status = project.status
        project.status = "deleted"
        db.session.commit()

        logger.info(
            f"Project marked as deleted - Status changed: {old_status} -> deleted"
        )
        return jsonify({"status": "success"})
    except Exception as e:
        logger.error(f"Error deleting project: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@bp.route("/projects/<int:project_id>")
@login_required
def detail(project_id):
    """プロジェクト詳細ページ"""
    try:
        project = Project.query.get_or_404(project_id)
        logger.info(
            f"User {current_user.username} accessing project details - ID: {project.id}, Name: {project.name}"
        )
        return render_template("project/detail.html", project=project)
    except Exception as e:
        logger.error(f"Error accessing project details: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500
