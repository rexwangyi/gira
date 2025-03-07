from flask import Blueprint, redirect, url_for, render_template
from flask_login import login_required, current_user
from app.models.project import Project
from app import logger

bp = Blueprint("main", __name__)


@bp.route("/")
@login_required
def index():
    """トップページ"""
    try:
        logger.info(f"User {current_user.username} accessing home page")
        return redirect(url_for("backlog.index"))
    except Exception as e:
        logger.error(f"Error in index view: {str(e)}", exc_info=True)
        return redirect(url_for("backlog.index"))


@bp.route("/active-sprint")
@bp.route("/active-sprint/<int:project_id>")
@login_required
def active_sprint(project_id=None):
    """アクティブスプリントページを表示（開発中）"""
    try:
        logger.info(f"User {current_user.username} accessing active sprint page")

        projects = Project.query.all()
        logger.debug(f"Found {len(projects)} total projects")

        current_project = None

        if project_id:
            current_project = Project.query.get_or_404(project_id)
            logger.info(
                f"Viewing active sprint for project: {current_project.name} (ID: {project_id})"
            )
        elif projects:
            current_project = projects[0]
            logger.info(
                f"No project specified, defaulting to: {current_project.name} (ID: {current_project.id})"
            )
        else:
            logger.info("No projects found")

        return render_template(
            "main/active_sprint.html",
            title="アクティブスプリント",
            projects=projects,
            current_project=current_project,
            active_page="active_sprint",
        )
    except Exception as e:
        logger.error(f"Error in active_sprint view: {str(e)}", exc_info=True)
        return redirect(url_for("backlog.index"))
