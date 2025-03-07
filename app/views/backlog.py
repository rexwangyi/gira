from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import case  # noqa: F401
from app import db, logger
from app.models.project import Project
from app.models.story import Story
from app.models.sprint import Sprint
from app.models.user import User

bp = Blueprint("backlog", __name__)


@bp.route("/backlog")
@bp.route("/backlog/<int:project_id>")
@login_required
def index(project_id=None):
    """バックログページを表示"""
    try:
        logger.info(f"User {current_user.username} accessing backlog page")

        projects = Project.query.all()
        current_project = None
        users = User.query.filter_by(is_active=True).all()
        logger.debug(f"Found {len(users)} active users")

        if project_id:
            current_project = Project.query.get_or_404(project_id)
            logger.info(
                f"Viewing backlog for project: {current_project.name} (ID: {project_id})"
            )
        elif projects:
            current_project = projects[0]
            logger.info(
                f"No project specified, defaulting to: {current_project.name} (ID: {current_project.id})"
            )

        # 全てのスプリントを取得
        sprints = []
        backlog_stories = []
        active_sprint = None
        if current_project:
            # アクティブなスプリントを取得
            active_sprint = Sprint.query.filter_by(
                project_id=current_project.id, status="active"
            ).first()

            if active_sprint:
                logger.info(
                    f"Found active sprint: {active_sprint.name} (ID: {active_sprint.id})"
                )

            # スプリントを番号順に取得
            sprints = (
                Sprint.query.filter_by(project_id=current_project.id)
                .order_by(Sprint.name.asc())  # Sprint 1, Sprint 2, ... の順
                .all()
            )
            logger.debug(
                f"Found {len(sprints)} sprints for project {current_project.name}"
            )

            # バックログのストーリーを取得
            backlog_stories = (
                Story.query.filter_by(project_id=current_project.id, sprint_id=None)
                .order_by(Story.priority.desc())
                .all()
            )
            logger.debug(f"Found {len(backlog_stories)} stories in backlog")
        else:
            logger.info("No projects found")

        return render_template(
            "backlog/index.html",
            projects=projects,
            current_project=current_project,
            sprints=sprints,
            active_sprint=active_sprint,
            backlog_stories=backlog_stories,
            users=users,
        )
    except Exception as e:
        logger.error(f"Error in backlog index view: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@bp.route("/backlog/story/create", methods=["POST"])
@login_required
def create_story():
    """ストーリーを作成"""
    try:
        if not request.is_json:
            logger.warning(
                f"Invalid request format from user {current_user.username} - not JSON"
            )
            return (
                jsonify({"status": "error", "message": "無効なリクエスト形式です"}),
                400,
            )

        data = request.get_json()
        project_id = data.get("project_id")
        if not project_id:
            logger.warning(
                f"Story creation attempted without project ID by user {current_user.username}"
            )
            return (
                jsonify(
                    {"status": "error", "message": "プロジェクトが選択されていません"}
                ),
                400,
            )

        logger.info(
            f"Story creation requested by {current_user.username} for project ID: {project_id}"
        )

        # ログ用にプロジェクト情報を取得
        project = Project.query.get(project_id)
        if not project:
            logger.error(f"Project not found - ID: {project_id}")
            return (
                jsonify({"status": "error", "message": "プロジェクトが見つかりません"}),
                404,
            )

        story = Story(
            title=data.get("title"),
            description=data.get("description"),
            story_points=data.get("story_points", 0),
            project_id=project_id,
            assignee_id=data.get("assignee_id") if data.get("assignee_id") else None,
            priority=data.get("priority", 0),
        )

        # アサイン情報を記録
        if story.assignee_id:
            assignee = User.query.get(story.assignee_id)
            if assignee:
                logger.info(f"Story will be assigned to: {assignee.username}")

        try:
            db.session.add(story)
            db.session.commit()
            logger.info(
                f"Story created successfully - Title: {story.title}, ID: {story.id}, Project: {project.name}"
            )
            return jsonify({"status": "success", "story": story.to_dict()})
        except Exception as e:
            db.session.rollback()
            logger.error(
                f"Database error while creating story: {str(e)}", exc_info=True
            )
            return jsonify({"status": "error", "message": str(e)}), 500
    except Exception as e:
        logger.error(f"Error in create_story: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


def _update_story_from_json(story, data):
    """JSONデータからストーリーを更新"""
    story.title = data.get("title", story.title)
    story.description = data.get("description", story.description)
    story.story_points = data.get("story_points", story.story_points)
    story.assignee_id = data.get("assignee_id") if data.get("assignee_id") else None
    story.priority = data.get("priority", 0)


def _update_story_from_form(story, form):
    """フォームデータからストーリーを更新"""
    story.title = form.get("title", story.title)
    story.description = form.get("description", story.description)
    story.story_points = form.get("story_points", story.story_points, type=int)
    story.assignee_id = form.get("assignee_id", type=int)
    story.priority = form.get("priority", 0, type=int)


def _track_story_changes(story, old_values):
    """ストーリーの変更を追跡"""
    changes = []

    if story.title != old_values["title"]:
        changes.append(f"title: {old_values['title']} -> {story.title}")

    if story.description != old_values["description"]:
        changes.append("description updated")

    if story.story_points != old_values["story_points"]:
        changes.append(
            f"story points: {old_values['story_points']} -> {story.story_points}"
        )

    if story.assignee_id != old_values["assignee_id"]:
        old_assignee = (
            User.query.get(old_values["assignee_id"])
            if old_values["assignee_id"]
            else None
        )
        new_assignee = User.query.get(story.assignee_id) if story.assignee_id else None
        old_name = old_assignee.username if old_assignee else "None"
        new_name = new_assignee.username if new_assignee else "None"
        changes.append(f"assignee: {old_name} -> {new_name}")

    if story.priority != old_values["priority"]:
        changes.append(f"priority: {old_values['priority']} -> {story.priority}")

    return changes


@bp.route("/backlog/story/<int:story_id>/update", methods=["POST"])
@login_required
def update_story(story_id):
    """ストーリーを更新"""
    try:
        story = Story.query.get_or_404(story_id)
        logger.info(
            f"Story update requested by {current_user.username} - "
            f"ID: {story_id}, Title: {story.title}"
        )

        # 元の値を保存
        old_values = {
            "title": story.title,
            "description": story.description,
            "story_points": story.story_points,
            "assignee_id": story.assignee_id,
            "priority": story.priority,
        }

        # データ形式に応じて更新
        if request.is_json:
            _update_story_from_json(story, request.get_json())
        else:
            _update_story_from_form(story, request.form)

        # 変更を追跡
        changes = _track_story_changes(story, old_values)

        try:
            db.session.commit()
            logger.info(f"Story updated successfully - Changes: {', '.join(changes)}")
            return jsonify({"status": "success", "story": story.to_dict()})
        except Exception as e:
            db.session.rollback()
            logger.error(
                f"Database error while updating story: {str(e)}", exc_info=True
            )
            return jsonify({"status": "error", "message": str(e)}), 500
    except Exception as e:
        logger.error(f"Error in update_story: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.route("/backlog/story/<int:story_id>/move", methods=["POST"])
@login_required
def move_story(story_id):
    """ストーリーの移動（スプリントとバックログ間）"""
    try:
        story = Story.query.get_or_404(story_id)
        logger.info(
            f"Story move requested by {current_user.username} - ID: {story_id}, Title: {story.title}"
        )

        old_sprint_id = story.sprint_id
        sprint_id = request.form.get("sprint_id", type=int)

        # 记录移动信息
        if sprint_id:
            sprint = Sprint.query.get(sprint_id)
            if not sprint:
                logger.error(f"Target sprint not found - ID: {sprint_id}")
                return (
                    jsonify(
                        {"status": "error", "message": "スプリントが見つかりません"}
                    ),
                    404,
                )

            story.sprint_id = sprint_id
            story.status = Story.KANBAN_TODO
            logger.info(f"Moving story to sprint: {sprint.name} (ID: {sprint_id})")
        else:
            story.sprint_id = None
            logger.info("Moving story back to backlog")

        try:
            db.session.commit()

            # 记录移动结果
            if old_sprint_id:
                old_sprint = Sprint.query.get(old_sprint_id)
                from_location = (
                    f"sprint '{old_sprint.name}'"
                    if old_sprint
                    else f"sprint {old_sprint_id}"
                )
            else:
                from_location = "backlog"

            if sprint_id:
                to_location = f"sprint '{sprint.name}'"
            else:
                to_location = "backlog"

            logger.info(
                f"Story moved successfully - From: {from_location} -> To: {to_location}"
            )
            return jsonify({"status": "success"})
        except Exception as e:
            db.session.rollback()
            logger.error(f"Database error while moving story: {str(e)}", exc_info=True)
            return jsonify({"status": "error", "message": str(e)}), 500
    except Exception as e:
        logger.error(f"Error in move_story: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.route("/backlog/sprint/start", methods=["POST"])
@login_required
def start_sprint():
    """スプリントを開始"""
    try:
        sprint_id = request.form.get("sprint_id", type=int)
        if not sprint_id:
            logger.warning(
                f"Sprint start attempted without sprint ID by user {current_user.username}"
            )
            flash("スプリントが選択されていません", "error")
            return redirect(url_for("backlog.index"))

        sprint = Sprint.query.get_or_404(sprint_id)
        logger.info(
            f"Sprint start requested by {current_user.username} - ID: {sprint_id}, Name: {sprint.name}"
        )

        # 检查是否有其他活动的Sprint
        active_sprint = Sprint.query.filter_by(
            project_id=sprint.project_id, status="active"
        ).first()

        if active_sprint:
            logger.warning(
                f"Cannot start sprint - Another sprint is active: {active_sprint.name} (ID: {active_sprint.id})"
            )
            flash("他のスプリントがアクティブです", "error")
            return redirect(url_for("backlog.index"))

        # 记录Sprint状态变更
        old_status = sprint.status
        sprint.status = "active"
        sprint.start_date = datetime.now()
        # デフォルトで2週間のスプリント期間を設定
        sprint.end_date = sprint.start_date + timedelta(days=14)

        try:
            db.session.commit()
            status_msg = (
                f"Sprint started successfully - "
                f"Status changed: {old_status} -> active, "
                f"Duration: {sprint.start_date} to {sprint.end_date}"
            )
            logger.info(status_msg)
            flash("スプリントが開始されました", "success")
            return redirect(url_for("backlog.index"))
        except Exception as e:
            db.session.rollback()
            logger.error(
                f"Database error while starting sprint: {str(e)}", exc_info=True
            )
            flash("スプリントの開始に失敗しました", "error")
            return redirect(url_for("backlog.index"))
    except Exception as e:
        logger.error(f"Error in start_sprint: {str(e)}", exc_info=True)
        flash("エラーが発生しました", "error")
        return redirect(url_for("backlog.index"))


@bp.route("/backlog/sprint/create", methods=["POST"])
@login_required
def create_sprint():
    """新しいスプリントを作成"""
    try:
        project_id = request.form.get("project_id", type=int)
        if not project_id:
            logger.warning(
                f"Sprint creation attempted without project ID by user {current_user.username}"
            )
            flash("プロジェクトが選択されていません", "error")
            return redirect(url_for("backlog.index"))

        project = Project.query.get_or_404(project_id)
        logger.info(
            f"Sprint creation requested by {current_user.username} for project: {project.name} (ID: {project_id})"
        )

        # スプリント名を生成（Sprint n の形）
        sprint_number = len(project.sprints) + 1
        name = f"Sprint {sprint_number}"

        sprint = Sprint(name=name, project_id=project_id, status="planning")

        try:
            db.session.add(sprint)
            db.session.commit()
            logger.info(
                f"Sprint created successfully - Name: {sprint.name}, ID: {sprint.id}, Project: {project.name}"
            )
            flash("スプリントが作成されました", "success")
            return redirect(url_for("backlog.index", project_id=project_id))
        except Exception as e:
            db.session.rollback()
            logger.error(
                f"Database error while creating sprint: {str(e)}", exc_info=True
            )
            flash("スプリントの作成に失敗しました", "error")
            return redirect(url_for("backlog.index"))
    except Exception as e:
        logger.error(f"Error in create_sprint: {str(e)}", exc_info=True)
        flash("エラーが発生しました", "error")
        return redirect(url_for("backlog.index"))


@bp.route("/api/sprints/create", methods=["POST"])
@login_required
def create_sprint_api():
    """API経由でスプリントを作成"""
    try:
        data = request.get_json()
        name = data.get("name", "")
        goal = data.get("goal", "")
        project_id = data.get("project_id")

        logger.info(
            f"Sprint API creation requested by {current_user.username} - Name: {name}, Project ID: {project_id}"
        )

        if not name:
            logger.warning("Sprint creation attempted without name")
            return jsonify({"error": "スプリント名は必須です"}), 400
        if not project_id:
            logger.warning("Sprint creation attempted without project ID")
            return jsonify({"error": "プロジェクトIDは必須です"}), 400

        # 获取项目信息用于日志
        project = Project.query.get(project_id)
        if not project:
            logger.error(f"Project not found - ID: {project_id}")
            return jsonify({"error": "プロジェクトが見つかりません"}), 404

        # 新しい Sprint を作成
        sprint = Sprint(name=name, goal=goal, project_id=project_id, status="planning")

        try:
            db.session.add(sprint)
            db.session.commit()
            logger.info(
                f"Sprint created successfully via API - Name: {sprint.name}, ID: {sprint.id}, Project: {project.name}"
            )
            return jsonify({"status": "success", "sprint": sprint.to_dict()})
        except Exception as e:
            db.session.rollback()
            logger.error(
                "Database error while creating sprint via API: " f"{str(e)}",
                exc_info=True,
            )
            return jsonify({"error": str(e)}), 500
    except Exception as e:
        logger.error(f"Error in create_sprint_api: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@bp.route("/api/sprints/<int:sprint_id>/start", methods=["POST"])
@login_required
def start_sprint_api(sprint_id):
    """API経由でスプリントを開始"""
    try:
        sprint = Sprint.query.get_or_404(sprint_id)
        logger.info(
            f"Sprint API start requested by {current_user.username} - ID: {sprint_id}, Name: {sprint.name}"
        )

        # 检查是否已经有进行中的 Sprint
        active_sprint = Sprint.query.filter_by(
            project_id=sprint.project_id, status="active"
        ).first()

        if active_sprint and active_sprint.id != sprint.id:
            logger.warning(
                f"Cannot start sprint - Another sprint is active: {active_sprint.name} (ID: {active_sprint.id})"
            )
            return (
                jsonify({"status": "error", "error": "他のスプリントが進行中です"}),
                400,
            )

        if sprint.status != "planning":
            logger.warning(f"Cannot start sprint - Invalid status: {sprint.status}")
            return (
                jsonify({"status": "error", "error": "このスプリントは開始できません"}),
                400,
            )

        # 检查是否有编号更小的未完成 Sprint
        earlier_sprints = Sprint.query.filter(
            Sprint.project_id == sprint.project_id,
            Sprint.name < sprint.name,
            Sprint.status == "planning",
        ).first()

        if earlier_sprints:
            logger.warning(
                "Cannot start sprint - Earlier sprints are not completed: "
                f"{earlier_sprints.name}"
            )
            return (
                jsonify(
                    {"status": "error", "error": "前のスプリントが完了していません"}
                ),
                400,
            )

        # 记录Sprint状态变更
        old_status = sprint.status
        sprint.status = "active"
        sprint.start_date = datetime.now()
        sprint.end_date = sprint.start_date + timedelta(days=14)  # 默认2周

        try:
            db.session.commit()
            logger.info(
                f"Sprint started via API - Status: {old_status} -> active, "
                f"Duration: {sprint.start_date} to {sprint.end_date}"
            )
            return jsonify({"status": "success", "sprint": sprint.to_dict()})
        except Exception as e:
            db.session.rollback()
            logger.error(
                f"Database error while starting sprint via API: {str(e)}", exc_info=True
            )
            return jsonify({"error": str(e)}), 500
    except Exception as e:
        logger.error(f"Error in start_sprint_api: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@bp.route("/api/sprints/<int:sprint_id>/complete", methods=["POST"])
@login_required
def complete_sprint_api(sprint_id):
    """API経由でスプリントを完了"""
    try:
        sprint = Sprint.query.get_or_404(sprint_id)
        logger.info(
            f"Sprint completion requested by {current_user.username} - ID: {sprint_id}, Name: {sprint.name}"
        )

        if sprint.status != "active":
            logger.warning(f"Cannot complete sprint - Invalid status: {sprint.status}")
            return (
                jsonify({"status": "error", "error": "このスプリントは完了できません"}),
                400,
            )

        # 获取完成情况统计
        stories = Story.query.filter_by(sprint_id=sprint_id).all()
        total_stories = len(stories)
        completed_stories = len([s for s in stories if s.status == Story.KANBAN_DONE])
        completion_rate = (
            (completed_stories / total_stories * 100) if total_stories > 0 else 0
        )

        logger.info(
            f"Sprint completion stats - Total stories: {total_stories}, "
            f"Completed: {completed_stories}, Rate: {completion_rate:.1f}%"
        )

        # 记录Sprint状态变更
        old_status = sprint.status
        sprint.status = "completed"
        sprint.completed_at = datetime.now()

        try:
            db.session.commit()
            logger.info(
                f"Sprint completed successfully - Status changed: {old_status} -> completed, "
                f"Completion time: {sprint.completed_at}"
            )
            return jsonify(
                {
                    "status": "success",
                    "sprint": sprint.to_dict(),
                    "stats": {
                        "total_stories": total_stories,
                        "completed_stories": completed_stories,
                        "completion_rate": completion_rate,
                    },
                }
            )
        except Exception as e:
            db.session.rollback()
            logger.error(
                f"Database error while completing sprint: {str(e)}", exc_info=True
            )
            return jsonify({"error": str(e)}), 500
    except Exception as e:
        logger.error(f"Error in complete_sprint_api: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500
