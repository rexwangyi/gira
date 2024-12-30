from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.models.project import Project
from app.models.sprint import Sprint
from app.models.story import Story
from app.extensions import db
from app import logger
from datetime import datetime

bp = Blueprint("kanban", __name__)


@bp.route("/")
@bp.route("/<int:project_id>")
@login_required
def index(project_id=None):
    """看板首页"""
    try:
        logger.info(f"User {current_user.username} accessing kanban board")

        projects = Project.query.all()
        logger.debug(f"Found {len(projects)} total projects")

        current_project = None
        active_sprint = None
        todo_stories = []
        doing_stories = []
        done_stories = []

        if project_id:
            current_project = Project.query.get_or_404(project_id)
            logger.info(
                f"Viewing kanban for project: {current_project.name} (ID: {project_id})"
            )

            active_sprint = Sprint.query.filter_by(
                project_id=current_project.id, status="active"
            ).first()

            if active_sprint:
                logger.info(
                    f"Found active sprint: {active_sprint.name} (ID: {active_sprint.id})"
                )

                todo_stories = Story.query.filter_by(
                    sprint_id=active_sprint.id, status=Story.KANBAN_TODO
                ).all()

                doing_stories = Story.query.filter_by(
                    sprint_id=active_sprint.id, status=Story.KANBAN_DOING
                ).all()

                done_stories = Story.query.filter_by(
                    sprint_id=active_sprint.id, status=Story.KANBAN_DONE
                ).all()

                # 记录每个状态的故事数量和详细信息
                logger.debug(
                    f"Stories in TODO: {len(todo_stories)} - IDs: {[s.id for s in todo_stories]}"
                )
                logger.debug(
                    f"Stories in DOING: {len(doing_stories)} - IDs: {[s.id for s in doing_stories]}"
                )
                logger.debug(
                    f"Stories in DONE: {len(done_stories)} - IDs: {[s.id for s in done_stories]}"
                )

                # 计算完成率
                total_stories = (
                    len(todo_stories) + len(doing_stories) + len(done_stories)
                )
                completion_rate = (
                    (len(done_stories) / total_stories * 100)
                    if total_stories > 0
                    else 0
                )
                logger.info(
                    f"Sprint progress - Total stories: {total_stories}, Completion rate: {completion_rate:.1f}%"
                )
            else:
                logger.info(
                    f"No active sprint found for project {current_project.name}"
                )
        else:
            logger.info("No project selected, showing project selection view")

        return render_template(
            "kanban/index.html",
            projects=projects,
            current_project=current_project,
            active_sprint=active_sprint,
            todo_stories=todo_stories,
            doing_stories=doing_stories,
            done_stories=done_stories,
        )
    except Exception as e:
        logger.error(f"Error in kanban index view: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


def _validate_story_status(new_status):
    """ストーリーのステータスを検証"""
    valid_statuses = [Story.KANBAN_TODO, Story.KANBAN_DOING, Story.KANBAN_DONE]
    if new_status not in valid_statuses:
        logger.warning(
            f"Invalid status value requested: {new_status}, "
            f"Valid values: {valid_statuses}"
        )
        return False
    return True


def _update_story_timestamps(story, old_status, new_status):
    """ストーリーのタイムスタンプを更新"""
    if new_status == Story.KANBAN_DOING and old_status == Story.KANBAN_TODO:
        story.started_at = datetime.now()
        logger.info(f"Story started at: {story.started_at}")
    elif new_status == Story.KANBAN_DONE:
        story.completed_at = datetime.now()
        logger.info(f"Story completed at: {story.completed_at}")

        if story.started_at:
            processing_time = story.completed_at - story.started_at
            logger.info(f"Story processing time: {processing_time}")
        else:
            logger.warning(f"Story {story.id} was completed without a start time")


def _log_story_update(story, sprint, new_status):
    """ストーリーの更新をログに記録"""
    logger.info(
        f"Story status update requested - Story ID: {story.id}, "
        f"Title: {story.title}, Current Status: {story.status}, "
        f"New Status: {new_status}, User: {current_user.username}"
    )

    if sprint:
        logger.debug(f"Story belongs to sprint: {sprint.name} (ID: {sprint.id})")


@bp.route("/api/stories/<int:story_id>/status", methods=["PUT"])
@login_required
def update_story_status(story_id):
    """ストーリーのステータスを更新"""
    try:
        story = Story.query.get_or_404(story_id)
        data = request.get_json()
        new_status = data.get("status")

        # スプリント情報を取得
        sprint = Sprint.query.get(story.sprint_id) if story.sprint_id else None

        # ログを記録
        _log_story_update(story, sprint, new_status)

        # ステータスを検証
        if not _validate_story_status(new_status):
            return jsonify({"status": "error", "message": "無効なステータス値です"}), 400

        try:
            # 状態変更を記録
            old_status = story.status
            story.status = new_status
            logger.debug(f"Updating story status from {old_status} to {new_status}")

            # タイムスタンプを更新
            _update_story_timestamps(story, old_status, new_status)

            db.session.commit()
            logger.info(f"Story status updated successfully - ID: {story_id}")
            return jsonify({"status": "success", "story": story.to_dict()})
        except Exception as e:
            db.session.rollback()
            logger.error(
                f"Database error while updating story status: {str(e)}", exc_info=True
            )
            return jsonify({"status": "error", "message": str(e)}), 500
    except Exception as e:
        logger.error(f"Error in update_story_status: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500
