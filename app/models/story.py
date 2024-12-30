from datetime import datetime
from app import db


class Story(db.Model):
    __tablename__ = "stories"

    PRIORITY_NONE = 0
    PRIORITY_LOW = 1
    PRIORITY_MEDIUM = 2
    PRIORITY_HIGH = 3
    PRIORITY_HIGHEST = 4

    PRIORITY_CHOICES = {
        PRIORITY_NONE: {"name": "None", "color": "#6B778C", "icon": ""},
        PRIORITY_LOW: {"name": "Low", "color": "#2D8738", "icon": "↓"},
        PRIORITY_MEDIUM: {"name": "Medium", "color": "#0052CC", "icon": "="},
        PRIORITY_HIGH: {"name": "High", "color": "#CD5A19", "icon": "↑"},
        PRIORITY_HIGHEST: {"name": "Highest", "color": "#CD1F1F", "icon": "↑↑"},
    }

    # 看板状态
    KANBAN_TODO = "todo"
    KANBAN_DOING = "doing"
    KANBAN_DONE = "done"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default="todo")  # 看板状态：todo, doing, done
    story_points = db.Column(db.Integer)
    priority = db.Column(db.Integer, default=PRIORITY_NONE)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    sprint_id = db.Column(db.Integer, db.ForeignKey("sprints.id"))
    assignee_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    started_at = db.Column(db.DateTime)  # 開始日時
    completed_at = db.Column(db.DateTime)  # 完了日時

    # 关联关系
    project = db.relationship("Project", backref=db.backref("stories", lazy=True))
    sprint = db.relationship("Sprint", backref=db.backref("stories", lazy=True))
    assignee = db.relationship(
        "User", backref=db.backref("assigned_stories", lazy=True)
    )

    @property
    def priority_info(self):
        """获取优先级信息"""
        return self.PRIORITY_CHOICES.get(
            self.priority, self.PRIORITY_CHOICES[self.PRIORITY_NONE]
        )

    def to_dict(self):
        """将故事对象转换为字典格式"""
        data = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "story_points": self.story_points,
            "priority": self.priority,
            "priority_info": self.priority_info,
            "project_id": self.project_id,
            "sprint_id": self.sprint_id,
            "assignee_id": self.assignee_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
        }

        # 添加关联对象的信息
        if self.assignee:
            data["assignee"] = {
                "id": self.assignee.id,
                "username": self.assignee.username,
            }

        if self.project:
            data["project"] = {"id": self.project.id, "name": self.project.name}

        if self.sprint:
            data["sprint"] = {"id": self.sprint.id, "name": self.sprint.name}

        return data

    def __repr__(self):
        return f"<Story {self.title}>"
