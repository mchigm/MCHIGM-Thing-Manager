"""
Unit tests for src/database/models.py

All tests use an *in-memory* SQLite database so they don't touch the user's
real `~/.mchigm_thing_manager/things.db` file.
"""
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

import src.database.models as models_mod
from src.database.models import (
    Base,
    Dependency,
    Item,
    ItemStatus,
    ItemType,
    Scenario,
    SessionLocal,
    Tag,
)


# ---------------------------------------------------------------------------
# Fixture: in-memory database
# ---------------------------------------------------------------------------
@pytest.fixture()
def db_session():
    """
    Provide a fresh SQLAlchemy session backed by an in-memory SQLite database.

    The session is rolled back after each test so tests are isolated.
    """
    mem_engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(mem_engine)
    session = Session(mem_engine)
    yield session
    session.rollback()
    session.close()
    Base.metadata.drop_all(mem_engine)


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------
class TestItemTypeEnum:
    def test_task(self):
        assert ItemType.TASK.value == "Task"

    def test_event(self):
        assert ItemType.EVENT.value == "Event"

    def test_note(self):
        assert ItemType.NOTE.value == "Note"

    def test_goal(self):
        assert ItemType.GOAL.value == "Goal"

    def test_all_members(self):
        names = {m.name for m in ItemType}
        assert names == {"TASK", "EVENT", "NOTE", "GOAL"}


class TestItemStatusEnum:
    def test_backlog(self):
        assert ItemStatus.BACKLOG.value == "Backlog"

    def test_todo(self):
        assert ItemStatus.TODO.value == "To-Do"

    def test_doing(self):
        assert ItemStatus.DOING.value == "Doing"

    def test_done(self):
        assert ItemStatus.DONE.value == "Done"


# ---------------------------------------------------------------------------
# Scenario model
# ---------------------------------------------------------------------------
class TestScenarioModel:
    def test_create_scenario(self, db_session):
        s = Scenario(name="Work", color="#ff0000")
        db_session.add(s)
        db_session.flush()
        assert s.id is not None
        assert s.name == "Work"

    def test_repr(self, db_session):
        s = Scenario(name="School", color="#0000ff")
        db_session.add(s)
        db_session.flush()
        assert "School" in repr(s)

    def test_default_color(self, db_session):
        s = Scenario(name="Personal")
        db_session.add(s)
        db_session.flush()
        assert s.color == "#5c85d6"

    def test_unique_name_constraint(self, db_session):
        db_session.add(Scenario(name="Work"))
        db_session.flush()
        db_session.add(Scenario(name="Work"))
        with pytest.raises(Exception):
            db_session.flush()


# ---------------------------------------------------------------------------
# Tag model
# ---------------------------------------------------------------------------
class TestTagModel:
    def test_create_tag(self, db_session):
        t = Tag(name="#urgent", color="#ff0000")
        db_session.add(t)
        db_session.flush()
        assert t.id is not None

    def test_repr(self, db_session):
        t = Tag(name="#cs101")
        db_session.add(t)
        db_session.flush()
        assert "#cs101" in repr(t)

    def test_default_color(self, db_session):
        t = Tag(name="#reading")
        db_session.add(t)
        db_session.flush()
        assert t.color == "#a0a0a0"

    def test_unique_name_constraint(self, db_session):
        db_session.add(Tag(name="#dup"))
        db_session.flush()
        db_session.add(Tag(name="#dup"))
        with pytest.raises(Exception):
            db_session.flush()


# ---------------------------------------------------------------------------
# Item model
# ---------------------------------------------------------------------------
class TestItemModel:
    def test_create_minimal_item(self, db_session):
        item = Item(title="My Task")
        db_session.add(item)
        db_session.flush()
        assert item.id is not None
        assert item.type == ItemType.TASK
        assert item.status == ItemStatus.TODO

    def test_repr(self, db_session):
        item = Item(title="Meeting", type=ItemType.EVENT)
        db_session.add(item)
        db_session.flush()
        r = repr(item)
        assert "Meeting" in r
        # Python 3.11+ formats str-Enum as 'ItemType.EVENT'; the value 'Event' appears in the name
        assert "EVENT" in r or "Event" in r

    def test_timestamps_set_on_create(self, db_session):
        item = Item(title="Timed")
        db_session.add(item)
        db_session.flush()
        assert item.created_at is not None
        assert item.updated_at is not None

    def test_item_with_scenario(self, db_session):
        scenario = Scenario(name="Work")
        item = Item(title="Sprint", scenario=scenario)
        db_session.add(item)
        db_session.flush()
        assert item.scenario.name == "Work"

    def test_item_with_tags(self, db_session):
        tag1 = Tag(name="#urgent")
        tag2 = Tag(name="#work")
        item = Item(title="Urgent task", tags=[tag1, tag2])
        db_session.add(item)
        db_session.flush()
        assert len(item.tags) == 2
        tag_names = {t.name for t in item.tags}
        assert "#urgent" in tag_names

    def test_item_with_time_fields(self, db_session):
        now = datetime.now(timezone.utc)
        item = Item(
            title="Event",
            type=ItemType.EVENT,
            start_time=now,
            end_time=now + timedelta(hours=2),
            deadline=now + timedelta(days=1),
        )
        db_session.add(item)
        db_session.flush()
        assert item.start_time is not None
        assert item.end_time is not None
        assert item.deadline is not None

    def test_item_nullable_time_fields(self, db_session):
        item = Item(title="No times")
        db_session.add(item)
        db_session.flush()
        assert item.start_time is None
        assert item.end_time is None
        assert item.deadline is None

    def test_item_all_types(self, db_session):
        for item_type in ItemType:
            item = Item(title=f"Test {item_type.value}", type=item_type)
            db_session.add(item)
        db_session.flush()

    def test_item_all_statuses(self, db_session):
        for status in ItemStatus:
            item = Item(title=f"Test {status.value}", status=status)
            db_session.add(item)
        db_session.flush()


# ---------------------------------------------------------------------------
# Dependency model
# ---------------------------------------------------------------------------
class TestDependencyModel:
    def test_create_dependency(self, db_session):
        parent = Item(title="Parent Task")
        child = Item(title="Child Task")
        db_session.add_all([parent, child])
        db_session.flush()

        dep = Dependency(parent_id=parent.id, child_id=child.id)
        db_session.add(dep)
        db_session.flush()
        assert dep.parent_id == parent.id
        assert dep.child_id == child.id

    def test_repr(self, db_session):
        parent = Item(title="P")
        child = Item(title="C")
        db_session.add_all([parent, child])
        db_session.flush()
        dep = Dependency(parent_id=parent.id, child_id=child.id)
        db_session.add(dep)
        db_session.flush()
        assert "→" in repr(dep) or "->" in repr(dep)

    def test_child_links_via_relationship(self, db_session):
        parent = Item(title="Parent")
        child = Item(title="Child")
        db_session.add_all([parent, child])
        db_session.flush()
        db_session.add(Dependency(parent_id=parent.id, child_id=child.id))
        db_session.flush()
        db_session.expire_all()
        loaded = db_session.get(Item, parent.id)
        assert len(loaded.child_links) == 1

    def test_parent_links_via_relationship(self, db_session):
        parent = Item(title="Par")
        child = Item(title="Chi")
        db_session.add_all([parent, child])
        db_session.flush()
        db_session.add(Dependency(parent_id=parent.id, child_id=child.id))
        db_session.flush()
        db_session.expire_all()
        loaded = db_session.get(Item, child.id)
        assert len(loaded.parent_links) == 1


# ---------------------------------------------------------------------------
# ensure_seed_data — idempotency and correctness
# ---------------------------------------------------------------------------
class TestEnsureSeedData:
    """
    We patch SessionLocal to return a session connected to an in-memory database
    so ensure_seed_data() doesn't touch the real DB.
    """

    @pytest.fixture()
    def mem_session_factory(self):
        mem_engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(mem_engine)
        sessions = []

        def factory():
            s = Session(mem_engine)
            sessions.append(s)
            return s

        yield factory, mem_engine
        for s in sessions:
            try:
                s.close()
            except Exception:
                pass
        Base.metadata.drop_all(mem_engine)

    def test_seeds_default_scenarios(self, mem_session_factory):
        factory, engine = mem_session_factory
        with patch.object(models_mod, "SessionLocal", factory):
            models_mod.ensure_seed_data()
        with Session(engine) as s:
            names = {r.name for r in s.query(Scenario).all()}
        assert "School" in names
        assert "Work" in names
        assert "Personal" in names

    def test_seeds_default_tags(self, mem_session_factory):
        factory, engine = mem_session_factory
        with patch.object(models_mod, "SessionLocal", factory):
            models_mod.ensure_seed_data()
        with Session(engine) as s:
            names = {t.name for t in s.query(Tag).all()}
        assert "#urgent" in names
        assert "#cs101" in names

    def test_seeds_sample_items(self, mem_session_factory):
        factory, engine = mem_session_factory
        with patch.object(models_mod, "SessionLocal", factory):
            models_mod.ensure_seed_data()
        with Session(engine) as s:
            count = s.query(Item).count()
        assert count > 0

    def test_seed_is_idempotent(self, mem_session_factory):
        factory, engine = mem_session_factory
        with patch.object(models_mod, "SessionLocal", factory):
            models_mod.ensure_seed_data()
            models_mod.ensure_seed_data()
        with Session(engine) as s:
            scenario_count = s.query(Scenario).count()
            tag_count = s.query(Tag).count()
            item_count = s.query(Item).count()
        # Scenarios and tags should not be duplicated
        assert scenario_count == 3
        assert tag_count == 4
        # Items seeded only once
        assert item_count == 4

    def test_sample_items_have_scenarios(self, mem_session_factory):
        factory, engine = mem_session_factory
        with patch.object(models_mod, "SessionLocal", factory):
            models_mod.ensure_seed_data()
        with Session(engine) as s:
            items = s.query(Item).all()
            for item in items:
                _ = item.scenario  # triggers relationship load
                assert item.scenario is not None
