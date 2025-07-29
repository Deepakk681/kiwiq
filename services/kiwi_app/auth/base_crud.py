from typing import Optional, List, Sequence, Type, TypeVar, Generic
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Session
from sqlalchemy.future import select
# TODO: FIXME: switch to below and remove scalars() call!
# from sqlmodel import select
from sqlalchemy.orm import selectinload
from sqlmodel import SQLModel

from kiwi_app.auth.crud_util import build_load_options

# --- Base DAO Class --- #
ModelType = TypeVar("ModelType", bound=SQLModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=SQLModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=SQLModel)

class BaseDAO(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Generic Base Data Access Object for CRUD operations.
    # TODO: FIXME: handle db commit / refresh centrally from service as part of transaction context to reduce DB round trips
    """
    def __init__(self, model: Type[ModelType]):
        self.model = model
    
    def get_by_id_sync(self, db: Session, id: uuid.UUID) -> Optional[ModelType]:
        statement = select(self.model).where(self.model.id == id)
        result = db.exec(statement)
        return result.scalars().first()

    async def get(self, db: AsyncSession, id: uuid.UUID, load_relations: Optional[List[str]] = None) -> Optional[ModelType]:
        """Get a single record by ID, optionally loading relationships."""
        statement = select(self.model).where(self.model.id == id)
        options = None
        if load_relations:
            if not isinstance(load_relations[0], str):
                # load_relations = [(self.model, r) for r in load_relations]
                # since relationships in link objects require full qualified path here from the original object like `organization_links.organization`!
                options = build_load_options(load_relations)
            else:
                options = [selectinload(getattr(self.model, rel)) for rel in load_relations if hasattr(self.model, rel)]
            if options:
                 statement = statement.options(*options)
        # Use exec instead of execute for direct Pydantic model return
        result = await db.exec(statement)
        result_scalars = result.scalars()
        
        if options is not None:
            # THis is to group multi fetch many-to-many queries, check with Gemini!
            result_scalars = result_scalars.unique()

        return result_scalars.first()

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> Sequence[ModelType]:
        """Get multiple records with pagination."""
        statement = select(self.model).offset(skip).limit(limit)
        # Use exec instead of execute for direct Pydantic model return
        result = await db.exec(statement)
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        """Create a new record."""
        # Use model_validate to handle potential nested schemas or defaults
        db_obj = self.model.model_validate(obj_in)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self, db: AsyncSession, *, db_obj: ModelType, obj_in: UpdateSchemaType
    ) -> ModelType:
        """Update an existing record."""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def delete(self, db: AsyncSession, *, db_obj: ModelType) -> bool:
        """
        Delete a record by ID.
        
        Args:
            db: Database session
            id: UUID of the record to delete
            
        Returns:
            bool: True if the record was found and deleted, False otherwise
            
        Note:
            This is similar to remove() but returns a boolean instead of the object.
            Useful when you only need to know if deletion succeeded but don't need the object.
        """
        if db_obj is not None and isinstance(db_obj, self.model):
            await db.delete(db_obj)
            await db.commit()
            return True
        return False

    async def remove(self, db: AsyncSession, *, id: uuid.UUID) -> Optional[ModelType]:
        """Delete a record by ID."""
        obj = await self.get(db, id=id)
        if obj:
            await db.delete(obj)
            await db.commit()
        return obj
