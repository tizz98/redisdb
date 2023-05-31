from dataclasses import dataclass
from typing import Type

import redis.asyncio
from pydantic import BaseModel


@dataclass(frozen=True)
class ForeignKey:
    model_cls: Type[BaseModel]
    model_id: int
    attribute_name: str


class RedisDB:
    def __init__(self, client: redis.asyncio.Redis):
        self._client = client

    async def create(self, model: BaseModel):
        table_name = model.__class__.__name__
        id_key = f"{table_name}:{model.id}"
        table_key = table_name

        await self._client.set(id_key, model.json())
        await self._client.sadd(table_key, id_key)

        # Check if there are any foreign keys
        if hasattr(model, "get_foreign_key_ids"):
            foreign_key_ids = model.get_foreign_key_ids()
            # File:project_id:1 -> {File:1, File:2}
            for foreign_key in foreign_key_ids:
                foreign_table_key = f"{model.__class__.__name__}:{foreign_key.attribute_name}:{foreign_key.model_id}"
                await self._client.sadd(foreign_table_key, id_key)

    async def get(self, model_cls: Type[BaseModel], id: int):
        table_name = model_cls.__name__
        id_key = f"{table_name}:{id}"

        row = await self._client.get(id_key)
        return model_cls.parse_raw(row)

    async def fetch_all(self, model_cls: Type[BaseModel]):
        table_name = model_cls.__name__
        table_key = table_name

        id_keys = await self._client.smembers(table_key)
        rows = await self._client.mget(id_keys)  # multiple-get
        parsed_rows = [model_cls.parse_raw(row) for row in rows]
        return sorted(parsed_rows, key=lambda row: row.id)

    async def fetch_related(self, model_cls: Type[BaseModel], **kwargs):
        if not hasattr(model_cls, "get_foreign_key_fields"):
            raise ValueError("Model does not have any foreign keys")
        if len(kwargs) != 1:
            raise ValueError("Can only filter by one foreign key")

        attr_name = list(kwargs.keys())[0]
        foreign_model_id = list(kwargs.values())[0]
        foreign_table_key = f"{model_cls.__name__}:{attr_name}:{foreign_model_id}"

        id_keys = await self._client.smembers(foreign_table_key)
        rows = await self._client.mget(id_keys)
        return [model_cls.parse_raw(row) for row in rows]
