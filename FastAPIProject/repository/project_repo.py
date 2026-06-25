from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio.session import AsyncSession

from models.knowledge_task import KnowledgeTask
from models.name_history import NameHistory
from models.naming_project import NamingProject
from schemas.name_schemas import NameIn


def build_project_title(name_info: NameIn) -> str:
    if name_info.project_title:
        return name_info.project_title.strip()[:120]

    if name_info.category == "人名" and name_info.surname:
        return f"{name_info.surname}姓起名"
    if name_info.category == "企业名":
        source = name_info.industry or name_info.other or "企业"
        return f"{source[:40]}命名"
    if name_info.category == "宠物名":
        source = name_info.other or "宠物"
        return f"{source[:40]}起名"
    return f"{name_info.category}项目"


class NamingProjectRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: int, title: str, category: str, description: str = "") -> NamingProject:
        project = NamingProject(
            user_id=user_id,
            title=title.strip()[:120],
            category=category,
            description=description or "",
        )
        self.session.add(project)
        await self.session.commit()
        await self.session.refresh(project)
        return project

    async def get_user_project(self, user_id: int, project_id: int) -> NamingProject | None:
        return await self.session.scalar(
            select(NamingProject).where(NamingProject.id == project_id, NamingProject.user_id == user_id)
        )

    async def get_or_create_for_generation(self, user_id: int, name_info: NameIn) -> NamingProject | None:
        if name_info.project_id:
            project = await self.get_user_project(user_id, name_info.project_id)
            if project:
                return project
            return None
        return await self.create(
            user_id=user_id,
            title=build_project_title(name_info),
            category=name_info.category,
            description=name_info.project_description or "",
        )

    async def find_by_thread_id(self, user_id: int, thread_id: str) -> NamingProject | None:
        return await self.session.scalar(
            select(NamingProject)
            .join(NameHistory, NameHistory.project_id == NamingProject.id)
            .where(NameHistory.user_id == user_id, NameHistory.thread_id == thread_id)
            .order_by(NameHistory.created_time.desc(), NameHistory.id.desc())
            .limit(1)
        )

    async def list_projects(
        self,
        user_id: int,
        status: str | None = "active",
        category: str | None = None,
        keyword: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[NamingProject], int]:
        conditions = [NamingProject.user_id == user_id]
        if status:
            conditions.append(NamingProject.status == status)
        if category:
            conditions.append(NamingProject.category == category)
        if keyword:
            pattern = f"%{keyword}%"
            conditions.append(or_(NamingProject.title.like(pattern), NamingProject.description.like(pattern)))

        total = await self.session.scalar(select(func.count()).select_from(NamingProject).where(*conditions))
        result = await self.session.execute(
            select(NamingProject)
            .where(*conditions)
            .order_by(NamingProject.updated_time.desc(), NamingProject.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all()), int(total or 0)

    async def stats_for_project_ids(self, project_ids: list[int]) -> dict[int, dict[str, int]]:
        if not project_ids:
            return {}
        stats = {project_id: {"history_count": 0, "favorite_count": 0, "knowledge_file_count": 0} for project_id in project_ids}

        history_rows = await self.session.execute(
            select(
                NameHistory.project_id,
                func.count(NameHistory.id),
                func.sum(case((NameHistory.is_favorite.is_(True), 1), else_=0)),
            )
            .where(NameHistory.project_id.in_(project_ids))
            .group_by(NameHistory.project_id)
        )
        for project_id, history_count, favorite_count in history_rows.all():
            stats[project_id]["history_count"] = int(history_count or 0)
            stats[project_id]["favorite_count"] = int(favorite_count or 0)

        knowledge_rows = await self.session.execute(
            select(KnowledgeTask.project_id, func.count(KnowledgeTask.id))
            .where(KnowledgeTask.project_id.in_(project_ids))
            .group_by(KnowledgeTask.project_id)
        )
        for project_id, knowledge_count in knowledge_rows.all():
            stats[project_id]["knowledge_file_count"] = int(knowledge_count or 0)

        return stats

    async def touch(self, project: NamingProject) -> NamingProject:
        project.title = project.title
        await self.session.commit()
        await self.session.refresh(project)
        return project
