from pydantic import BaseModel, Field, PrivateAttr
from typing import Type

from redisdb.interface import ForeignKey


class Project(BaseModel):
    id: int
    name: str


class TestCreate:
    async def test_row_is_created(self, db):
        await db.create(Project(id=1, name="test"))
        await db.create(Project(id=2, name="test"))

        assert await db.get(Project, 1) == Project(id=1, name="test")

        assert await db.fetch_all(Project) == [
            Project(id=1, name="test"),
            Project(id=2, name="test"),
        ]


class File(BaseModel):
    id: int
    name: str
    project_id: int

    def get_foreign_key_ids(self) -> list[ForeignKey]:
        return [
            ForeignKey(model_cls=Project, model_id=self.project_id, attribute_name="project_id")
        ]

    @classmethod
    def get_foreign_key_fields(cls) -> dict[str, Type[BaseModel]]:
        return {
            "project_id": Project,
        }


class TestForeignKeys:
    async def test_something(self, db):
        await db.create(Project(id=1, name="test"))
        await db.create(File(id=3, name="test", project_id=1))
        await db.create(File(id=4, name="test", project_id=1))
        await db.create(File(id=5, name="test", project_id=2))

        assert await db.fetch_related(File, project_id=1) == [
            File(id=3, name="test", project_id=1),
            File(id=4, name="test", project_id=1),
        ]


class TestIndexes:
    async def test_it(self, db):
        await db.create(File(id=3, name="test", project_id=1))
        await db.create(File(id=4, name="test1", project_id=1))
        await db.create(File(id=5, name="test2", project_id=2))

        assert await db.fetch_by_field(File, name="test") == [
            File(id=3, name="test", project_id=1),
        ]
