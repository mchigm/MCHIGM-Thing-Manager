"""
SQLAlchemy models for the MCHIGM Thing Manager.

Unified Item Model — everything (task, event, note, goal) is an Item.
"""
import enum
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session, relationship

# ---------------------------------------------------------------------------
# Database setup
# ---------------------------------------------------------------------------
_DB_DIR = Path.home() / ".mchigm_thing_manager"
_DB_DIR.mkdir(parents=True, exist_ok=True)
_DB_PATH = _DB_DIR / "things.db"

engine = create_engine(f"sqlite:///{_DB_PATH}", echo=False)


def SessionLocal() -> Session:
    """Return a new SQLAlchemy session."""
    return Session(engine)


# ---------------------------------------------------------------------------
# Declarative base
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------
class ItemType(str, enum.Enum):
    TASK = "Task"
    EVENT = "Event"
    NOTE = "Note"
    GOAL = "Goal"


class ItemStatus(str, enum.Enum):
    BACKLOG = "Backlog"
    TODO = "To-Do"
    DOING = "Doing"
    DONE = "Done"


# ---------------------------------------------------------------------------
# Association table: Item ↔ Tag  (many-to-many)
# ---------------------------------------------------------------------------
class ItemTag(Base):
    __tablename__ = "item_tags"

    item_id = Column(Integer, ForeignKey("items.id", ondelete="CASCADE"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class Scenario(Base):
    """High-level workspace (e.g. School, Work, Personal)."""

    __tablename__ = "scenarios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    color = Column(String(20), default="#5c85d6")

    items = relationship("Item", back_populates="scenario", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Scenario id={self.id} name={self.name!r}>"


class Tag(Base):
    """Granular, cross-scenario label (e.g. #urgent, #cs101)."""

    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    color = Column(String(20), default="#a0a0a0")

    items = relationship("Item", secondary="item_tags", back_populates="tags")

    def __repr__(self) -> str:
        return f"<Tag id={self.id} name={self.name!r}>"


class Item(Base):
    """
    The core unified entity.

    Everything — a quick thought, a 2-hour meeting, a massive project — is an
    Item.  Type, Status, Time attributes, and relationships determine how it is
    displayed across the four pages.
    """

    __tablename__ = "items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, default="")

    # Classification
    type = Column(Enum(ItemType), default=ItemType.TASK, nullable=False)
    status = Column(Enum(ItemStatus), default=ItemStatus.TODO, nullable=False)

    # Timing
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    deadline = Column(DateTime, nullable=True)

    # Workspace
    scenario_id = Column(Integer, ForeignKey("scenarios.id", ondelete="SET NULL"), nullable=True)
    scenario = relationship("Scenario", back_populates="items")

    # Tags
    tags = relationship("Tag", secondary="item_tags", back_populates="items")

    # Parent/child dependencies (self-referential via Dependency table)
    child_links = relationship(
        "Dependency",
        foreign_keys="Dependency.parent_id",
        back_populates="parent",
        cascade="all, delete-orphan",
    )
    parent_links = relationship(
        "Dependency",
        foreign_keys="Dependency.child_id",
        back_populates="child",
        cascade="all, delete-orphan",
    )

    # Timestamps (UTC-aware)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Item id={self.id} title={self.title!r} type={self.type} status={self.status}>"


class Dependency(Base):
    """
    Directed dependency edge between two Items.

    parent → child means *child* depends on *parent* being completed first.
    """

    __tablename__ = "dependencies"

    parent_id = Column(Integer, ForeignKey("items.id", ondelete="CASCADE"), primary_key=True)
    child_id = Column(Integer, ForeignKey("items.id", ondelete="CASCADE"), primary_key=True)

    parent = relationship("Item", foreign_keys=[parent_id], back_populates="child_links")
    child = relationship("Item", foreign_keys=[child_id], back_populates="parent_links")

    def __repr__(self) -> str:
        return f"<Dependency parent={self.parent_id} → child={self.child_id}>"


# ---------------------------------------------------------------------------
# Seed helpers (demo data for early phases)
# ---------------------------------------------------------------------------
def ensure_seed_data() -> None:
    """
    Populate default scenarios, tags, and a handful of Items for Phase 1 demos.

    The seed is idempotent per table:
    - ensure default scenarios exist,
    - ensure default tags exist,
    - seed sample items only when the Item table is empty.
    """
    with SessionLocal() as session:
        # Seed default scenarios: insert only missing ones.
        default_scenarios = {
            "School": "#5c85d6",
            "Work": "#d6855c",
            "Personal": "#5cd685",
        }
        existing_scenarios = session.query(Scenario).all()
        existing_scenario_names = {s.name for s in existing_scenarios}
        new_scenarios = [
            Scenario(name=name, color=color)
            for name, color in default_scenarios.items()
            if name not in existing_scenario_names
        ]
        if new_scenarios:
            session.add_all(new_scenarios)
            session.commit()
        scenarios_by_name = {s.name: s for s in session.query(Scenario).all()}

        # Seed default tags: insert only missing ones.
        default_tags = {
            "#urgent": "#d65c5c",
            "#cs101": "#5c85d6",
            "#frontend": "#5cd6c8",
            "#reading": "#c8c85c",
        }
        existing_tags = session.query(Tag).all()
        existing_tag_names = {t.name for t in existing_tags}
        new_tags = [
            Tag(name=name, color=color)
            for name, color in default_tags.items()
            if name not in existing_tag_names
        ]
        if new_tags:
            session.add_all(new_tags)
            session.commit()
        tags_by_name = {t.name: t for t in session.query(Tag).all()}

        # Seed sample items only if none exist yet
        if session.query(Item.id).limit(1).first() is None:
            now = datetime.now(timezone.utc)
            sample_items = [
                Item(
                    title="Prep CS 101 research outline",
                    description="Skim papers and collect sources.",
                    type=ItemType.NOTE,
                    status=ItemStatus.BACKLOG,
                    deadline=now + timedelta(days=4),
                    scenario=scenarios_by_name["School"],
                    tags=[tags_by_name["#cs101"], tags_by_name["#reading"]],
                ),
                Item(
                    title="Design sprint kickoff",
                    description="Align on roadmap milestones.",
                    type=ItemType.EVENT,
                    status=ItemStatus.TODO,
                    start_time=now + timedelta(days=1, hours=2),
                    end_time=now + timedelta(days=1, hours=4),
                    scenario=scenarios_by_name["Work"],
                    tags=[tags_by_name["#frontend"]],
                ),
                Item(
                    title="Implement calendar drag-and-drop stub",
                    type=ItemType.TASK,
                    status=ItemStatus.DOING,
                    scenario=scenarios_by_name["Work"],
                    tags=[tags_by_name["#frontend"], tags_by_name["#urgent"]],
                ),
                Item(
                    title="Read 30 minutes",
                    type=ItemType.GOAL,
                    status=ItemStatus.DONE,
                    scenario=scenarios_by_name["Personal"],
                    tags=[tags_by_name["#reading"]],
                ),
            ]
            session.add_all(sample_items)
            session.commit()


# ---------------------------------------------------------------------------
# Create all tables on import
# ---------------------------------------------------------------------------
Base.metadata.create_all(engine)
