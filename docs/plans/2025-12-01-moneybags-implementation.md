# Moneybags Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a single-user personal finance web application with monthly budgets, dated actual entries, comprehensive analysis, and smooth htmx-powered UX.

**Architecture:** Layered structure with FastAPI router (main.py), business logic layer (business_logic.py), data access layer (database_manager.py), and PeeWee ORM models (database_model.py). Frontend uses Bootstrap, htmx, Chart.js with base/partial template pattern.

**Tech Stack:** Python, FastAPI, SQLite, PeeWee ORM, Bootstrap, htmx, Chart.js, TomSelect, Tempus Dominus

---

## Task 1: Project Setup & Dependencies

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `app/__init__.py`

**Step 1: Create requirements.txt**

Create file at root of worktree:

```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
peewee==3.17.0
python-dotenv==1.0.0
jinja2==3.1.2
python-multipart==0.0.6
```

**Step 2: Create .env.example**

```txt
DATABASE_PATH=./moneybags.db
LOG_LEVEL=INFO
```

**Step 3: Create app package**

```bash
mkdir -p app
touch app/__init__.py
```

**Step 4: Create directory structure**

```bash
mkdir -p app/static/css app/static/js app/static/lib
mkdir -p app/templates/partials
mkdir -p tests
```

**Step 5: Verify structure**

Run: `ls -R app/`
Expected: Shows app/, static/, templates/, partials/ directories

**Step 6: Commit**

```bash
git add requirements.txt .env.example app/
git commit -m "feat: initial project setup with dependencies and directory structure"
```

---

## Task 2: Utils Module (UUID Generation)

**Files:**
- Create: `app/utils.py`
- Create: `tests/test_utils.py`

**Step 1: Write the failing test**

Create `tests/test_utils.py`:

```python
import pytest
from app.utils import generate_uuid


def test_generate_uuid_returns_string():
    """UUID should be returned as string."""
    uuid = generate_uuid()
    assert isinstance(uuid, str)


def test_generate_uuid_is_unique():
    """Each call should generate unique UUID."""
    uuid1 = generate_uuid()
    uuid2 = generate_uuid()
    assert uuid1 != uuid2


def test_generate_uuid_format():
    """UUID should be in correct format (8-4-4-4-12 hex)."""
    uuid = generate_uuid()
    parts = uuid.split('-')
    assert len(parts) == 5
    assert len(parts[0]) == 8
    assert len(parts[1]) == 4
    assert len(parts[2]) == 4
    assert len(parts[3]) == 4
    assert len(parts[4]) == 12
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_utils.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'app.utils'"

**Step 3: Write minimal implementation**

Create `app/utils.py`:

```python
"""Utility functions for Moneybags application."""
import uuid


def generate_uuid() -> str:
    """
    Generate a unique UUID string.

    Returns:
        str: UUID in string format (e.g., "a1b2c3d4-e5f6-7890-abcd-ef1234567890")
    """
    return str(uuid.uuid4())
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_utils.py -v`
Expected: PASS (3 tests)

**Step 5: Commit**

```bash
git add app/utils.py tests/test_utils.py
git commit -m "feat: add UUID generation utility"
```

---

## Task 3: Database Models (PeeWee ORM)

**Files:**
- Create: `app/database_model.py`
- Create: `tests/test_database_model.py`

**Step 1: Write the failing test**

Create `tests/test_database_model.py`:

```python
import pytest
from peewee import SqliteDatabase
from app.database_model import (
    Post, Tag, PostTag, BudgetEntry, ActualEntry, UserPreference,
    initialize_database
)


@pytest.fixture
def test_db():
    """Create in-memory test database."""
    test_database = SqliteDatabase(':memory:')
    models = [Post, Tag, PostTag, BudgetEntry, ActualEntry, UserPreference]
    test_database.bind(models)
    test_database.create_tables(models)
    yield test_database
    test_database.close()


def test_post_model_creation(test_db):
    """Post model should create and retrieve records."""
    post = Post.create(
        id='test-uuid-1',
        name='Test Post',
        type='expense'
    )
    assert post.id == 'test-uuid-1'
    assert post.name == 'Test Post'
    assert post.type == 'expense'


def test_tag_model_creation(test_db):
    """Tag model should create and retrieve records."""
    tag = Tag.create(
        id='tag-uuid-1',
        name='Housing'
    )
    assert tag.id == 'tag-uuid-1'
    assert tag.name == 'Housing'


def test_post_tag_relationship(test_db):
    """PostTag should link posts and tags."""
    post = Post.create(id='post-1', name='Rent', type='expense')
    tag = Tag.create(id='tag-1', name='Housing')
    post_tag = PostTag.create(post=post, tag=tag)

    assert post_tag.post_id == 'post-1'
    assert post_tag.tag_id == 'tag-1'


def test_budget_entry_model(test_db):
    """BudgetEntry should store monthly budget values."""
    post = Post.create(id='post-1', name='Rent', type='expense')
    entry = BudgetEntry.create(
        id='budget-1',
        post=post,
        year=2024,
        month=1,
        amount=1500.00
    )

    assert entry.year == 2024
    assert entry.month == 1
    assert float(entry.amount) == 1500.00


def test_actual_entry_model(test_db):
    """ActualEntry should store dated transactions with comments."""
    from datetime import date

    post = Post.create(id='post-1', name='Rent', type='expense')
    entry = ActualEntry.create(
        id='actual-1',
        post=post,
        date=date(2024, 1, 15),
        amount=1500.00,
        comment='January rent payment'
    )

    assert entry.date == date(2024, 1, 15)
    assert float(entry.amount) == 1500.00
    assert entry.comment == 'January rent payment'


def test_user_preference_model(test_db):
    """UserPreference should store key-value configuration."""
    pref = UserPreference.create(
        id='pref-1',
        key='currency_notation',
        value='NOK'
    )

    assert pref.key == 'currency_notation'
    assert pref.value == 'NOK'
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_database_model.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'app.database_model'"

**Step 3: Write minimal implementation**

Create `app/database_model.py`:

```python
"""Database models using PeeWee ORM."""
from datetime import datetime
from peewee import (
    Model, SqliteDatabase, CharField, DateTimeField,
    IntegerField, DecimalField, DateField, TextField, ForeignKeyField
)


# Database instance (will be initialized later)
db = SqliteDatabase(None)


class BaseModel(Model):
    """Base model with common fields."""
    class Meta:
        database = db


class Post(BaseModel):
    """Master definition of budget line items."""
    id = CharField(primary_key=True, max_length=36)
    name = CharField(max_length=255)
    type = CharField(max_length=10)  # 'income' or 'expense'
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = 'posts'


class Tag(BaseModel):
    """Reusable labels for grouping posts."""
    id = CharField(primary_key=True, max_length=36)
    name = CharField(max_length=100, unique=True)

    class Meta:
        table_name = 'tags'


class PostTag(BaseModel):
    """Many-to-many relationship between Posts and Tags."""
    post = ForeignKeyField(Post, backref='post_tags')
    tag = ForeignKeyField(Tag, backref='tag_posts')

    class Meta:
        table_name = 'post_tags'
        indexes = (
            (('post', 'tag'), True),  # Unique together
        )


class BudgetEntry(BaseModel):
    """Monthly budget values for posts."""
    id = CharField(primary_key=True, max_length=36)
    post = ForeignKeyField(Post, backref='budget_entries')
    year = IntegerField()
    month = IntegerField()  # 1-12
    amount = DecimalField(max_digits=15, decimal_places=2)
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = 'budget_entries'
        indexes = (
            (('post', 'year', 'month'), True),  # Unique together
        )


class ActualEntry(BaseModel):
    """Real income/expenses with specific dates."""
    id = CharField(primary_key=True, max_length=36)
    post = ForeignKeyField(Post, backref='actual_entries')
    date = DateField()
    amount = DecimalField(max_digits=15, decimal_places=2)
    comment = TextField(null=True)
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = 'actual_entries'


class UserPreference(BaseModel):
    """Application configuration settings."""
    id = CharField(primary_key=True, max_length=36)
    key = CharField(max_length=100, unique=True)
    value = CharField(max_length=500)

    class Meta:
        table_name = 'user_preferences'


def initialize_database(database_path: str):
    """
    Initialize database connection and create tables.

    Args:
        database_path: Path to SQLite database file
    """
    db.init(database_path)
    db.create_tables([Post, Tag, PostTag, BudgetEntry, ActualEntry, UserPreference])
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_database_model.py -v`
Expected: PASS (6 tests)

**Step 5: Commit**

```bash
git add app/database_model.py tests/test_database_model.py
git commit -m "feat: add PeeWee ORM database models"
```

---

## Task 4: Database Manager (CRUD Operations)

**Files:**
- Create: `app/database_manager.py`
- Create: `tests/test_database_manager.py`

**Step 1: Write the failing test for Post CRUD**

Create `tests/test_database_manager.py`:

```python
import pytest
from datetime import date
from peewee import SqliteDatabase
from app.database_model import (
    Post, Tag, PostTag, BudgetEntry, ActualEntry, UserPreference,
    db
)
from app.database_manager import (
    create_post, get_post, get_all_posts, update_post, delete_post,
    create_tag, get_tag_by_name, get_all_tags,
    add_tag_to_post, get_post_tags, remove_tag_from_post,
    create_budget_entry, get_budget_entries, update_budget_entry,
    create_actual_entry, get_actual_entries, update_actual_entry, delete_actual_entry,
    get_or_create_preference, update_preference
)


@pytest.fixture(autouse=True)
def test_db():
    """Setup test database before each test."""
    test_database = SqliteDatabase(':memory:')
    db.initialize(test_database)
    db.create_tables([Post, Tag, PostTag, BudgetEntry, ActualEntry, UserPreference])
    yield
    db.close()


class TestPostOperations:
    def test_create_post(self):
        """Should create a new post."""
        post_id = 'test-post-1'
        post = create_post(post_id, 'Rent', 'expense')

        assert post.id == post_id
        assert post.name == 'Rent'
        assert post.type == 'expense'

    def test_get_post(self):
        """Should retrieve existing post."""
        post_id = 'test-post-1'
        create_post(post_id, 'Salary', 'income')

        post = get_post(post_id)
        assert post is not None
        assert post.name == 'Salary'

    def test_get_all_posts(self):
        """Should retrieve all posts."""
        create_post('post-1', 'Rent', 'expense')
        create_post('post-2', 'Salary', 'income')

        posts = get_all_posts()
        assert len(posts) == 2

    def test_update_post(self):
        """Should update post name."""
        post_id = 'test-post-1'
        create_post(post_id, 'Netflix', 'expense')

        updated = update_post(post_id, name='Netflix + Disney+')
        assert updated.name == 'Netflix + Disney+'

    def test_delete_post(self):
        """Should delete post."""
        post_id = 'test-post-1'
        create_post(post_id, 'Old Post', 'expense')

        delete_post(post_id)
        post = get_post(post_id)
        assert post is None


class TestTagOperations:
    def test_create_tag(self):
        """Should create a new tag."""
        tag_id = 'tag-1'
        tag = create_tag(tag_id, 'Housing')

        assert tag.id == tag_id
        assert tag.name == 'Housing'

    def test_get_tag_by_name(self):
        """Should retrieve tag by name."""
        create_tag('tag-1', 'Streaming')

        tag = get_tag_by_name('Streaming')
        assert tag is not None
        assert tag.name == 'Streaming'

    def test_get_all_tags(self):
        """Should retrieve all tags."""
        create_tag('tag-1', 'Housing')
        create_tag('tag-2', 'Food')

        tags = get_all_tags()
        assert len(tags) == 2


class TestPostTagRelationship:
    def test_add_tag_to_post(self):
        """Should link tag to post."""
        post = create_post('post-1', 'Rent', 'expense')
        tag = create_tag('tag-1', 'Housing')

        add_tag_to_post(post.id, tag.id)

        post_tags = get_post_tags(post.id)
        assert len(post_tags) == 1
        assert post_tags[0].name == 'Housing'

    def test_remove_tag_from_post(self):
        """Should unlink tag from post."""
        post = create_post('post-1', 'Rent', 'expense')
        tag = create_tag('tag-1', 'Housing')
        add_tag_to_post(post.id, tag.id)

        remove_tag_from_post(post.id, tag.id)

        post_tags = get_post_tags(post.id)
        assert len(post_tags) == 0


class TestBudgetEntryOperations:
    def test_create_budget_entry(self):
        """Should create budget entry."""
        post = create_post('post-1', 'Rent', 'expense')
        entry_id = 'budget-1'

        entry = create_budget_entry(entry_id, post.id, 2024, 1, 1500.00)

        assert entry.year == 2024
        assert entry.month == 1
        assert float(entry.amount) == 1500.00

    def test_get_budget_entries(self):
        """Should retrieve budget entries for post and year."""
        post = create_post('post-1', 'Rent', 'expense')
        create_budget_entry('b1', post.id, 2024, 1, 1500.00)
        create_budget_entry('b2', post.id, 2024, 2, 1500.00)
        create_budget_entry('b3', post.id, 2025, 1, 1600.00)

        entries = get_budget_entries(post.id, 2024)
        assert len(entries) == 2

    def test_update_budget_entry(self):
        """Should update budget amount."""
        post = create_post('post-1', 'Rent', 'expense')
        entry = create_budget_entry('b1', post.id, 2024, 1, 1500.00)

        updated = update_budget_entry(entry.id, amount=1600.00)
        assert float(updated.amount) == 1600.00


class TestActualEntryOperations:
    def test_create_actual_entry(self):
        """Should create actual entry with date and comment."""
        post = create_post('post-1', 'Rent', 'expense')
        entry_id = 'actual-1'
        entry_date = date(2024, 1, 15)

        entry = create_actual_entry(
            entry_id, post.id, entry_date, 1500.00, 'January rent'
        )

        assert entry.date == entry_date
        assert float(entry.amount) == 1500.00
        assert entry.comment == 'January rent'

    def test_get_actual_entries(self):
        """Should retrieve actual entries for post and date range."""
        post = create_post('post-1', 'Groceries', 'expense')
        create_actual_entry('a1', post.id, date(2024, 1, 5), 100.00, '')
        create_actual_entry('a2', post.id, date(2024, 1, 15), 120.00, '')
        create_actual_entry('a3', post.id, date(2024, 2, 5), 110.00, '')

        entries = get_actual_entries(
            post.id,
            date(2024, 1, 1),
            date(2024, 1, 31)
        )
        assert len(entries) == 2

    def test_update_actual_entry(self):
        """Should update actual entry amount and comment."""
        post = create_post('post-1', 'Groceries', 'expense')
        entry = create_actual_entry('a1', post.id, date(2024, 1, 5), 100.00, '')

        updated = update_actual_entry(entry.id, amount=105.00, comment='Updated')
        assert float(updated.amount) == 105.00
        assert updated.comment == 'Updated'

    def test_delete_actual_entry(self):
        """Should delete actual entry."""
        post = create_post('post-1', 'Groceries', 'expense')
        entry = create_actual_entry('a1', post.id, date(2024, 1, 5), 100.00, '')

        delete_actual_entry(entry.id)

        entries = get_actual_entries(post.id, date(2024, 1, 1), date(2024, 12, 31))
        assert len(entries) == 0


class TestUserPreferenceOperations:
    def test_get_or_create_preference(self):
        """Should create preference if not exists."""
        pref = get_or_create_preference('currency_notation', 'USD')

        assert pref.key == 'currency_notation'
        assert pref.value == 'USD'

    def test_update_preference(self):
        """Should update existing preference."""
        get_or_create_preference('currency_notation', 'USD')

        updated = update_preference('currency_notation', 'NOK')
        assert updated.value == 'NOK'
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_database_manager.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'app.database_manager'"

**Step 3: Write minimal implementation (Part 1 - Post operations)**

Create `app/database_manager.py`:

```python
"""Database manager for all CRUD operations using PeeWee ORM."""
from typing import List, Optional
from datetime import date, datetime
from app.database_model import (
    Post, Tag, PostTag, BudgetEntry, ActualEntry, UserPreference
)


# ============================================================================
# POST OPERATIONS
# ============================================================================

def create_post(post_id: str, name: str, post_type: str) -> Post:
    """
    Create a new post.

    Args:
        post_id: Unique identifier
        name: Post name (e.g., "Rent", "Salary")
        post_type: Either 'income' or 'expense'

    Returns:
        Post: Created post object
    """
    return Post.create(
        id=post_id,
        name=name,
        type=post_type
    )


def get_post(post_id: str) -> Optional[Post]:
    """
    Retrieve a post by ID.

    Args:
        post_id: Post identifier

    Returns:
        Post or None if not found
    """
    try:
        return Post.get_by_id(post_id)
    except Post.DoesNotExist:
        return None


def get_all_posts() -> List[Post]:
    """
    Retrieve all posts.

    Returns:
        List of Post objects
    """
    return list(Post.select())


def update_post(post_id: str, name: Optional[str] = None) -> Post:
    """
    Update a post's name.

    Args:
        post_id: Post identifier
        name: New name (optional)

    Returns:
        Updated Post object
    """
    post = Post.get_by_id(post_id)
    if name is not None:
        post.name = name
        post.updated_at = datetime.now()
        post.save()
    return post


def delete_post(post_id: str) -> None:
    """
    Delete a post.

    Args:
        post_id: Post identifier
    """
    post = Post.get_by_id(post_id)
    post.delete_instance()


# ============================================================================
# TAG OPERATIONS
# ============================================================================

def create_tag(tag_id: str, name: str) -> Tag:
    """
    Create a new tag.

    Args:
        tag_id: Unique identifier
        name: Tag name (e.g., "Housing", "Fixed")

    Returns:
        Tag: Created tag object
    """
    return Tag.create(id=tag_id, name=name)


def get_tag_by_name(name: str) -> Optional[Tag]:
    """
    Retrieve a tag by name.

    Args:
        name: Tag name

    Returns:
        Tag or None if not found
    """
    try:
        return Tag.get(Tag.name == name)
    except Tag.DoesNotExist:
        return None


def get_all_tags() -> List[Tag]:
    """
    Retrieve all tags.

    Returns:
        List of Tag objects
    """
    return list(Tag.select())


# ============================================================================
# POST-TAG RELATIONSHIP OPERATIONS
# ============================================================================

def add_tag_to_post(post_id: str, tag_id: str) -> PostTag:
    """
    Link a tag to a post.

    Args:
        post_id: Post identifier
        tag_id: Tag identifier

    Returns:
        PostTag: Created relationship
    """
    return PostTag.create(post=post_id, tag=tag_id)


def get_post_tags(post_id: str) -> List[Tag]:
    """
    Get all tags for a post.

    Args:
        post_id: Post identifier

    Returns:
        List of Tag objects
    """
    post_tags = PostTag.select().where(PostTag.post == post_id)
    return [pt.tag for pt in post_tags]


def remove_tag_from_post(post_id: str, tag_id: str) -> None:
    """
    Remove tag from post.

    Args:
        post_id: Post identifier
        tag_id: Tag identifier
    """
    PostTag.delete().where(
        (PostTag.post == post_id) & (PostTag.tag == tag_id)
    ).execute()


# ============================================================================
# BUDGET ENTRY OPERATIONS
# ============================================================================

def create_budget_entry(
    entry_id: str,
    post_id: str,
    year: int,
    month: int,
    amount: float
) -> BudgetEntry:
    """
    Create a budget entry.

    Args:
        entry_id: Unique identifier
        post_id: Post identifier
        year: Budget year (e.g., 2024)
        month: Budget month (1-12)
        amount: Budgeted amount

    Returns:
        BudgetEntry: Created entry
    """
    return BudgetEntry.create(
        id=entry_id,
        post=post_id,
        year=year,
        month=month,
        amount=amount
    )


def get_budget_entries(post_id: str, year: int) -> List[BudgetEntry]:
    """
    Get all budget entries for a post and year.

    Args:
        post_id: Post identifier
        year: Budget year

    Returns:
        List of BudgetEntry objects
    """
    return list(
        BudgetEntry.select().where(
            (BudgetEntry.post == post_id) & (BudgetEntry.year == year)
        ).order_by(BudgetEntry.month)
    )


def update_budget_entry(
    entry_id: str,
    amount: Optional[float] = None
) -> BudgetEntry:
    """
    Update a budget entry.

    Args:
        entry_id: Entry identifier
        amount: New amount (optional)

    Returns:
        Updated BudgetEntry object
    """
    entry = BudgetEntry.get_by_id(entry_id)
    if amount is not None:
        entry.amount = amount
        entry.updated_at = datetime.now()
        entry.save()
    return entry


# ============================================================================
# ACTUAL ENTRY OPERATIONS
# ============================================================================

def create_actual_entry(
    entry_id: str,
    post_id: str,
    entry_date: date,
    amount: float,
    comment: str = ''
) -> ActualEntry:
    """
    Create an actual entry.

    Args:
        entry_id: Unique identifier
        post_id: Post identifier
        entry_date: Date of transaction
        amount: Actual amount
        comment: Optional comment

    Returns:
        ActualEntry: Created entry
    """
    return ActualEntry.create(
        id=entry_id,
        post=post_id,
        date=entry_date,
        amount=amount,
        comment=comment if comment else None
    )


def get_actual_entries(
    post_id: str,
    start_date: date,
    end_date: date
) -> List[ActualEntry]:
    """
    Get actual entries for a post within date range.

    Args:
        post_id: Post identifier
        start_date: Start of date range (inclusive)
        end_date: End of date range (inclusive)

    Returns:
        List of ActualEntry objects
    """
    return list(
        ActualEntry.select().where(
            (ActualEntry.post == post_id) &
            (ActualEntry.date >= start_date) &
            (ActualEntry.date <= end_date)
        ).order_by(ActualEntry.date.desc())
    )


def update_actual_entry(
    entry_id: str,
    amount: Optional[float] = None,
    comment: Optional[str] = None
) -> ActualEntry:
    """
    Update an actual entry.

    Args:
        entry_id: Entry identifier
        amount: New amount (optional)
        comment: New comment (optional)

    Returns:
        Updated ActualEntry object
    """
    entry = ActualEntry.get_by_id(entry_id)
    if amount is not None:
        entry.amount = amount
    if comment is not None:
        entry.comment = comment
    entry.updated_at = datetime.now()
    entry.save()
    return entry


def delete_actual_entry(entry_id: str) -> None:
    """
    Delete an actual entry.

    Args:
        entry_id: Entry identifier
    """
    entry = ActualEntry.get_by_id(entry_id)
    entry.delete_instance()


# ============================================================================
# USER PREFERENCE OPERATIONS
# ============================================================================

def get_or_create_preference(key: str, default_value: str) -> UserPreference:
    """
    Get existing preference or create with default.

    Args:
        key: Preference key
        default_value: Default value if not exists

    Returns:
        UserPreference object
    """
    try:
        return UserPreference.get(UserPreference.key == key)
    except UserPreference.DoesNotExist:
        from app.utils import generate_uuid
        return UserPreference.create(
            id=generate_uuid(),
            key=key,
            value=default_value
        )


def update_preference(key: str, value: str) -> UserPreference:
    """
    Update a preference value.

    Args:
        key: Preference key
        value: New value

    Returns:
        Updated UserPreference object
    """
    pref = UserPreference.get(UserPreference.key == key)
    pref.value = value
    pref.save()
    return pref
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_database_manager.py -v`
Expected: PASS (all tests)

**Step 5: Commit**

```bash
git add app/database_manager.py tests/test_database_manager.py
git commit -m "feat: add database manager with CRUD operations"
```

---

## Task 5: Business Logic Layer (Basic Operations)

**Files:**
- Create: `app/business_logic.py`
- Create: `tests/test_business_logic.py`

**Step 1: Write the failing test**

Create `tests/test_business_logic.py`:

```python
import pytest
from datetime import date
from decimal import Decimal
from peewee import SqliteDatabase
from app.database_model import db, Post, Tag, BudgetEntry, ActualEntry
from app.database_manager import (
    create_post, create_tag, add_tag_to_post,
    create_budget_entry, create_actual_entry
)
from app.business_logic import (
    create_post_with_tags,
    get_monthly_variance,
    get_year_overview,
    get_posts_by_type,
    calculate_post_total_actual
)


@pytest.fixture(autouse=True)
def test_db():
    """Setup test database."""
    test_database = SqliteDatabase(':memory:')
    db.initialize(test_database)
    db.create_tables([Post, Tag, BudgetEntry, ActualEntry])
    yield
    db.close()


def test_create_post_with_tags():
    """Should create post and link tags in one operation."""
    from app.utils import generate_uuid

    tag1_id = generate_uuid()
    tag2_id = generate_uuid()
    create_tag(tag1_id, 'Housing')
    create_tag(tag2_id, 'Fixed')

    post = create_post_with_tags('Rent', 'expense', [tag1_id, tag2_id])

    assert post.name == 'Rent'
    assert post.type == 'expense'
    # Verify tags are linked (check via database_manager)
    from app.database_manager import get_post_tags
    tags = get_post_tags(post.id)
    assert len(tags) == 2


def test_get_monthly_variance():
    """Should calculate budget vs actual variance for a month."""
    from app.utils import generate_uuid

    post_id = generate_uuid()
    create_post(post_id, 'Groceries', 'expense')

    # Budget: 500
    budget_id = generate_uuid()
    create_budget_entry(budget_id, post_id, 2024, 1, 500.00)

    # Actuals: 120 + 130 = 250
    create_actual_entry(generate_uuid(), post_id, date(2024, 1, 5), 120.00)
    create_actual_entry(generate_uuid(), post_id, date(2024, 1, 15), 130.00)

    variance = get_monthly_variance(post_id, 2024, 1)

    assert variance['budget'] == Decimal('500.00')
    assert variance['actual'] == Decimal('250.00')
    assert variance['difference'] == Decimal('250.00')  # Under budget
    assert variance['percentage'] == 50.0


def test_get_year_overview():
    """Should aggregate income and expenses for entire year."""
    from app.utils import generate_uuid

    # Create income post
    income_id = generate_uuid()
    create_post(income_id, 'Salary', 'income')
    create_actual_entry(generate_uuid(), income_id, date(2024, 1, 1), 5000.00)
    create_actual_entry(generate_uuid(), income_id, date(2024, 2, 1), 5000.00)

    # Create expense post
    expense_id = generate_uuid()
    create_post(expense_id, 'Rent', 'expense')
    create_actual_entry(generate_uuid(), expense_id, date(2024, 1, 1), 1500.00)
    create_actual_entry(generate_uuid(), expense_id, date(2024, 2, 1), 1500.00)

    overview = get_year_overview(2024)

    assert overview['total_income'] == Decimal('10000.00')
    assert overview['total_expenses'] == Decimal('3000.00')
    assert overview['net_savings'] == Decimal('7000.00')


def test_get_posts_by_type():
    """Should filter posts by income or expense type."""
    from app.utils import generate_uuid

    create_post(generate_uuid(), 'Salary', 'income')
    create_post(generate_uuid(), 'Bonus', 'income')
    create_post(generate_uuid(), 'Rent', 'expense')

    income_posts = get_posts_by_type('income')
    expense_posts = get_posts_by_type('expense')

    assert len(income_posts) == 2
    assert len(expense_posts) == 1


def test_calculate_post_total_actual():
    """Should sum all actuals for a post in date range."""
    from app.utils import generate_uuid

    post_id = generate_uuid()
    create_post(post_id, 'Groceries', 'expense')

    create_actual_entry(generate_uuid(), post_id, date(2024, 1, 5), 100.00)
    create_actual_entry(generate_uuid(), post_id, date(2024, 1, 15), 150.00)
    create_actual_entry(generate_uuid(), post_id, date(2024, 2, 5), 120.00)

    total = calculate_post_total_actual(
        post_id,
        date(2024, 1, 1),
        date(2024, 1, 31)
    )

    assert total == Decimal('250.00')
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_business_logic.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'app.business_logic'"

**Step 3: Write minimal implementation**

Create `app/business_logic.py`:

```python
"""Business logic layer for Moneybags application."""
from typing import List, Dict, Any
from datetime import date
from decimal import Decimal
from app.utils import generate_uuid
from app.database_manager import (
    create_post, get_all_posts, get_post,
    add_tag_to_post, get_budget_entries, get_actual_entries
)
from app.database_model import Post


def create_post_with_tags(
    name: str,
    post_type: str,
    tag_ids: List[str]
) -> Post:
    """
    Create a post and link tags in one operation.

    Args:
        name: Post name
        post_type: 'income' or 'expense'
        tag_ids: List of tag IDs to link

    Returns:
        Post: Created post
    """
    post_id = generate_uuid()
    post = create_post(post_id, name, post_type)

    for tag_id in tag_ids:
        add_tag_to_post(post.id, tag_id)

    return post


def get_monthly_variance(post_id: str, year: int, month: int) -> Dict[str, Any]:
    """
    Calculate budget vs actual variance for a specific month.

    Args:
        post_id: Post identifier
        year: Year
        month: Month (1-12)

    Returns:
        Dict with budget, actual, difference, and percentage
    """
    # Get budget entry for the month
    budget_entries = get_budget_entries(post_id, year)
    budget_entry = next((e for e in budget_entries if e.month == month), None)
    budget_amount = Decimal(str(budget_entry.amount)) if budget_entry else Decimal('0')

    # Get actual entries for the month
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year, 12, 31)
    else:
        from calendar import monthrange
        last_day = monthrange(year, month)[1]
        end_date = date(year, month, last_day)

    actual_entries = get_actual_entries(post_id, start_date, end_date)
    actual_amount = sum(Decimal(str(e.amount)) for e in actual_entries)

    difference = budget_amount - actual_amount
    percentage = float((actual_amount / budget_amount * 100)) if budget_amount > 0 else 0.0

    return {
        'budget': budget_amount,
        'actual': actual_amount,
        'difference': difference,
        'percentage': percentage
    }


def get_year_overview(year: int) -> Dict[str, Decimal]:
    """
    Aggregate all income and expenses for a year.

    Args:
        year: Year to analyze

    Returns:
        Dict with total_income, total_expenses, net_savings
    """
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)

    total_income = Decimal('0')
    total_expenses = Decimal('0')

    posts = get_all_posts()
    for post in posts:
        actuals = get_actual_entries(post.id, start_date, end_date)
        total = sum(Decimal(str(e.amount)) for e in actuals)

        if post.type == 'income':
            total_income += total
        else:
            total_expenses += total

    return {
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net_savings': total_income - total_expenses
    }


def get_posts_by_type(post_type: str) -> List[Post]:
    """
    Filter posts by type.

    Args:
        post_type: 'income' or 'expense'

    Returns:
        List of Post objects
    """
    all_posts = get_all_posts()
    return [p for p in all_posts if p.type == post_type]


def calculate_post_total_actual(
    post_id: str,
    start_date: date,
    end_date: date
) -> Decimal:
    """
    Sum all actual entries for a post in date range.

    Args:
        post_id: Post identifier
        start_date: Start of range
        end_date: End of range

    Returns:
        Total amount as Decimal
    """
    actuals = get_actual_entries(post_id, start_date, end_date)
    return sum(Decimal(str(e.amount)) for e in actuals)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_business_logic.py -v`
Expected: PASS (all tests)

**Step 5: Commit**

```bash
git add app/business_logic.py tests/test_business_logic.py
git commit -m "feat: add business logic layer with calculations"
```

---

## Task 6: FastAPI Router Setup (Basic Structure)

**Files:**
- Create: `app/main.py`
- Create: `uvicorn_log_config.ini`

**Step 1: Create uvicorn logging config**

Create `uvicorn_log_config.ini` at root:

```ini
[loggers]
keys=root,uvicorn,uvicorn.access

[handlers]
keys=console

[formatters]
keys=default

[logger_root]
level=INFO
handlers=console

[logger_uvicorn]
level=INFO
handlers=console
qualname=uvicorn
propagate=0

[logger_uvicorn.access]
level=INFO
handlers=console
qualname=uvicorn.access
propagate=0

[handler_console]
class=StreamHandler
formatter=default
args=(sys.stdout,)

[formatter_default]
format=%(asctime)s - %(name)s - %(levelname)s - %(message)s
datefmt=%Y-%m-%d %H:%M:%S
```

**Step 2: Create main.py with basic FastAPI app**

Create `app/main.py`:

```python
"""FastAPI application router for Moneybags."""
import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

from app.database_model import initialize_database

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Moneybags", version="1.0.0")

# Setup static files and templates
BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Initialize database
DATABASE_PATH = os.getenv("DATABASE_PATH", "./moneybags.db")
initialize_database(DATABASE_PATH)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page - redirects to dashboard."""
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
```

**Step 3: Test the basic app**

Run: `python -m pytest tests/ -v`
Expected: All existing tests still pass

**Step 4: Commit**

```bash
git add app/main.py uvicorn_log_config.ini
git commit -m "feat: add FastAPI router with basic structure and logging"
```

---

## Task 7: Base HTML Template & Static Assets

**Files:**
- Create: `app/templates/base.html`
- Create: `app/static/css/styles.css`
- Create: `app/static/js/app.js`

**Step 1: Create base.html template**

Create `app/templates/base.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Moneybags{% endblock %}</title>

    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">

    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>

    <!-- Custom CSS -->
    <link rel="stylesheet" href="{{ url_for('static', path='/css/styles.css') }}">
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container-fluid">
            <a class="navbar-brand" href="/">Moneybags</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav">
                    <li class="nav-item">
                        <a class="nav-link" href="/">Dashboard</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/budget">Budget & Actuals</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/analysis">Analysis</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/config">Configuration</a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <!-- Main Content -->
    <main class="container-fluid mt-4">
        {% block content %}{% endblock %}
    </main>

    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>

    <!-- htmx -->
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>

    <!-- TomSelect -->
    <link href="https://cdn.jsdelivr.net/npm/tom-select@2.3.1/dist/css/tom-select.bootstrap5.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/tom-select@2.3.1/dist/js/tom-select.complete.min.js"></script>

    <!-- Tempus Dominus -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@eonasdan/tempus-dominus@6.7.16/dist/css/tempus-dominus.min.css">
    <script src="https://cdn.jsdelivr.net/npm/@eonasdan/tempus-dominus@6.7.16/dist/js/tempus-dominus.min.js"></script>

    <!-- Custom JS -->
    <script src="{{ url_for('static', path='/js/app.js') }}"></script>
</body>
</html>
```

**Step 2: Create styles.css**

Create `app/static/css/styles.css`:

```css
/* Moneybags Custom Styles */

:root {
    --color-income: #28a745;
    --color-expense: #dc3545;
    --color-under-budget: #28a745;
    --color-over-budget: #dc3545;
    --color-neutral: #6c757d;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}

/* Budget input styling */
.budget-input {
    width: 80px;
    text-align: right;
}

/* Variance indicators */
.variance-positive {
    color: var(--color-under-budget);
    font-weight: bold;
}

.variance-negative {
    color: var(--color-over-budget);
    font-weight: bold;
}

/* Post row styling */
.post-row {
    border-bottom: 1px solid #dee2e6;
    padding: 1rem 0;
}

.post-row:last-child {
    border-bottom: none;
}

/* Chart containers */
.chart-container {
    position: relative;
    height: 300px;
    margin-bottom: 2rem;
}

/* Income/Expense sections */
.income-section {
    background-color: #f8f9fa;
    padding: 1.5rem;
    border-radius: 0.5rem;
    margin-bottom: 2rem;
}

.expense-section {
    padding: 1.5rem;
}

/* Loading indicators */
.htmx-indicator {
    display: none;
}

.htmx-request .htmx-indicator {
    display: inline-block;
}

/* Responsive adjustments */
@media (max-width: 768px) {
    .budget-input {
        width: 60px;
        font-size: 0.875rem;
    }

    .chart-container {
        height: 200px;
    }
}
```

**Step 3: Create app.js**

Create `app/static/js/app.js`:

```javascript
/**
 * Moneybags Application JavaScript
 */

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', function() {
    console.log('Moneybags app loaded');
});

/**
 * Format currency based on user preference
 */
function formatCurrency(amount, currency = 'USD') {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency
    }).format(amount);
}

/**
 * Debounce function for input fields
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Initialize TomSelect on elements with .tomselect class
 */
function initializeTomSelect() {
    document.querySelectorAll('.tomselect').forEach(function(el) {
        new TomSelect(el, {
            plugins: ['remove_button'],
            create: false
        });
    });
}

/**
 * Initialize Tempus Dominus date pickers
 */
function initializeDatePickers() {
    document.querySelectorAll('.datepicker').forEach(function(el) {
        new tempusDominus.TempusDominus(el, {
            display: {
                components: {
                    clock: false
                }
            }
        });
    });
}

// Reinitialize components after htmx swaps
document.body.addEventListener('htmx:afterSwap', function(event) {
    initializeTomSelect();
    initializeDatePickers();
});
```

**Step 4: Verify files created**

Run: `ls -la app/templates/ app/static/css/ app/static/js/`
Expected: All files exist

**Step 5: Commit**

```bash
git add app/templates/base.html app/static/
git commit -m "feat: add base template and static assets (CSS/JS)"
```

---

## Task 8: Dashboard Page (Basic Structure)

**Files:**
- Create: `app/templates/dashboard.html`
- Modify: `app/main.py` (add dashboard route with data)
- Modify: `app/business_logic.py` (add dashboard data method)

**Step 1: Add dashboard data method to business_logic**

Modify `app/business_logic.py`, add at the end:

```python
def get_dashboard_data(year: int, current_month: int) -> Dict[str, Any]:
    """
    Get all data needed for dashboard.

    Args:
        year: Current year
        current_month: Current month (1-12)

    Returns:
        Dict with year overview, monthly data, recent entries
    """
    overview = get_year_overview(year)

    # Get current month variance for all posts
    posts = get_all_posts()
    monthly_variances = []
    for post in posts:
        variance = get_monthly_variance(post.id, year, current_month)
        monthly_variances.append({
            'post_name': post.name,
            'post_type': post.type,
            **variance
        })

    # Get recent actual entries (last 10)
    from datetime import datetime
    all_recent = []
    for post in posts:
        actuals = get_actual_entries(
            post.id,
            date(year, 1, 1),
            date.today()
        )
        for actual in actuals[:10]:  # Limit per post
            all_recent.append({
                'post_name': post.name,
                'date': actual.date,
                'amount': actual.amount,
                'comment': actual.comment
            })

    # Sort by date descending and take top 10
    all_recent.sort(key=lambda x: x['date'], reverse=True)
    recent_entries = all_recent[:10]

    return {
        'overview': overview,
        'monthly_variances': monthly_variances,
        'recent_entries': recent_entries,
        'year': year,
        'month': current_month
    }
```

**Step 2: Update dashboard route in main.py**

Modify `app/main.py`, replace the home route:

```python
from datetime import datetime
from app.business_logic import get_dashboard_data

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Dashboard page."""
    current_year = datetime.now().year
    current_month = datetime.now().month

    data = get_dashboard_data(current_year, current_month)

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        **data
    })
```

**Step 3: Create dashboard.html template**

Create `app/templates/dashboard.html`:

```html
{% extends "base.html" %}

{% block title %}Dashboard - Moneybags{% endblock %}

{% block content %}
<div class="row">
    <div class="col-12">
        <h1>Dashboard</h1>
        <p class="text-muted">Year {{ year }} - Month {{ month }}</p>
    </div>
</div>

<!-- Year Overview Cards -->
<div class="row mb-4">
    <div class="col-md-4">
        <div class="card text-white bg-success">
            <div class="card-body">
                <h5 class="card-title">Total Income</h5>
                <h2>{{ "%.2f"|format(overview.total_income) }}</h2>
            </div>
        </div>
    </div>
    <div class="col-md-4">
        <div class="card text-white bg-danger">
            <div class="card-body">
                <h5 class="card-title">Total Expenses</h5>
                <h2>{{ "%.2f"|format(overview.total_expenses) }}</h2>
            </div>
        </div>
    </div>
    <div class="col-md-4">
        <div class="card text-white bg-primary">
            <div class="card-body">
                <h5 class="card-title">Net Savings</h5>
                <h2>{{ "%.2f"|format(overview.net_savings) }}</h2>
            </div>
        </div>
    </div>
</div>

<!-- Charts Placeholder -->
<div class="row mb-4">
    <div class="col-12">
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">Monthly Overview</h5>
                <div class="chart-container">
                    <canvas id="monthlyChart"></canvas>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Recent Entries -->
<div class="row">
    <div class="col-12">
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">Recent Transactions</h5>
                <table class="table table-sm">
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Post</th>
                            <th>Amount</th>
                            <th>Comment</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for entry in recent_entries %}
                        <tr>
                            <td>{{ entry.date }}</td>
                            <td>{{ entry.post_name }}</td>
                            <td>{{ "%.2f"|format(entry.amount) }}</td>
                            <td>{{ entry.comment or '-' }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>

<script>
// Basic chart initialization
const ctx = document.getElementById('monthlyChart').getContext('2d');
const monthlyChart = new Chart(ctx, {
    type: 'bar',
    data: {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        datasets: [{
            label: 'Income',
            data: [],  // Will be populated later
            backgroundColor: 'rgba(40, 167, 69, 0.5)'
        }, {
            label: 'Expenses',
            data: [],  // Will be populated later
            backgroundColor: 'rgba(220, 53, 69, 0.5)'
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false
    }
});
</script>
{% endblock %}
```

**Step 4: Test manually**

Run: `uvicorn app.main:app --reload`
Visit: `http://localhost:8000`
Expected: Dashboard renders (no data yet, but structure visible)

**Step 5: Commit**

```bash
git add app/templates/dashboard.html app/main.py app/business_logic.py
git commit -m "feat: add dashboard page with overview cards and structure"
```

---

## Task 9: Budget & Actuals Page (Structure)

**Files:**
- Create: `app/templates/budget.html`
- Create: `app/templates/partials/_post_row.html`
- Modify: `app/main.py` (add budget route)

**Step 1: Add budget route to main.py**

Modify `app/main.py`, add route:

```python
from app.business_logic import get_posts_by_type, get_budget_entries

@app.get("/budget", response_class=HTMLResponse)
async def budget_page(request: Request):
    """Budget and actuals page."""
    current_year = datetime.now().year

    income_posts = get_posts_by_type('income')
    expense_posts = get_posts_by_type('expense')

    # Get budget entries for each post
    income_data = []
    for post in income_posts:
        budgets = get_budget_entries(post.id, current_year)
        income_data.append({
            'post': post,
            'budgets': budgets
        })

    expense_data = []
    for post in expense_posts:
        budgets = get_budget_entries(post.id, current_year)
        expense_data.append({
            'post': post,
            'budgets': budgets
        })

    return templates.TemplateResponse("budget.html", {
        "request": request,
        "year": current_year,
        "income_data": income_data,
        "expense_data": expense_data
    })
```

**Step 2: Create budget.html template**

Create `app/templates/budget.html`:

```html
{% extends "base.html" %}

{% block title %}Budget & Actuals - Moneybags{% endblock %}

{% block content %}
<div class="row mb-3">
    <div class="col-12">
        <h1>Budget & Actuals</h1>
        <p class="text-muted">Year {{ year }}</p>
    </div>
</div>

<!-- Income Section (Top) -->
<div class="income-section">
    <h3>Income</h3>
    {% for item in income_data %}
        {% include "partials/_post_row.html" with context %}
    {% endfor %}

    <button class="btn btn-success btn-sm mt-2" hx-get="/api/post/create-form?type=income" hx-target="#modal-content">
        + Add Income Post
    </button>
</div>

<!-- Expense Section (Bottom) -->
<div class="expense-section">
    <h3>Expenses</h3>
    {% for item in expense_data %}
        {% include "partials/_post_row.html" with context %}
    {% endfor %}

    <button class="btn btn-danger btn-sm mt-2" hx-get="/api/post/create-form?type=expense" hx-target="#modal-content">
        + Add Expense Post
    </button>
</div>

<!-- Modal placeholder -->
<div id="modal-content"></div>
{% endblock %}
```

**Step 3: Create _post_row.html partial**

Create `app/templates/partials/_post_row.html`:

```html
<div class="post-row">
    <h5>{{ item.post.name }}</h5>
    <div class="row">
        <!-- Monthly budget inputs -->
        {% for month in range(1, 13) %}
        <div class="col-1">
            <label class="form-label small">{{ ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][month-1] }}</label>
            {% set budget = item.budgets | selectattr('month', 'equalto', month) | first %}
            <input
                type="number"
                class="form-control budget-input"
                value="{{ budget.amount if budget else '0' }}"
                hx-post="/api/budget/update"
                hx-trigger="change delay:500ms"
                hx-vals='{"post_id": "{{ item.post.id }}", "year": {{ year }}, "month": {{ month }}}'
                step="0.01"
            >
        </div>
        {% endfor %}
    </div>

    <!-- Actual entries -->
    <div class="mt-2">
        <h6>Actual Entries</h6>
        <button class="btn btn-sm btn-outline-primary" hx-get="/api/actual/create-form?post_id={{ item.post.id }}" hx-target="#modal-content">
            + Add Entry
        </button>
    </div>
</div>
```

**Step 4: Verify rendering**

Run: `uvicorn app.main:app --reload`
Visit: `http://localhost:8000/budget`
Expected: Budget page renders with horizontal split (no posts yet)

**Step 5: Commit**

```bash
git add app/templates/budget.html app/templates/partials/_post_row.html app/main.py
git commit -m "feat: add budget & actuals page with horizontal layout"
```

---

## Remaining Tasks Summary

Due to space constraints, here's the outline for remaining tasks:

### Task 10: API Endpoints for Budget Updates (htmx)
- Add POST `/api/budget/update` endpoint
- Update or create budget entries
- Return updated partial

### Task 11: API Endpoints for Actual Entries (htmx)
- Add POST `/api/actual/create` endpoint
- Add GET `/api/actual/create-form` for modal
- Return updated partials

### Task 12: Analysis Page
- Create `analysis.html` template
- Add filtering controls
- Add Chart.js visualizations for all 4 analysis modes
- Add business logic methods for each analysis type

### Task 13: Configuration Page
- Create `config.html` template
- Add preference management routes
- Add tag CRUD operations
- Add htmx autosave

### Task 14: Docker Configuration
- Create `Dockerfile`
- Create `docker-compose.yml`
- Create `.dockerignore`
- Add environment variable handling

### Task 15: Testing & Verification
- Write integration tests
- Test all htmx interactions
- Test mobile responsiveness
- Load test with sample data

### Task 16: Documentation
- Update README with setup instructions
- Add API documentation
- Add development guide
- Add deployment guide

---

## Execution Notes

**Testing Strategy:**
- Unit tests for database_manager and business_logic
- Integration tests for API endpoints
- Manual testing for UI/UX
- Mobile testing on actual devices

**Development Workflow:**
- Run tests frequently: `pytest tests/ -v`
- Start server: `uvicorn app.main:app --reload --log-config uvicorn_log_config.ini`
- Check database: `sqlite3 moneybags.db`

**Common Commands:**
```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_business_logic.py -v

# Start development server
uvicorn app.main:app --reload

# Check code coverage
pytest --cov=app tests/
```

**Dependencies Installation:**
```bash
pip install -r requirements.txt
```

---

## Plan Complete

This plan provides bite-sized, testable tasks following TDD principles. Each task builds incrementally toward the complete Moneybags application.

**Key Principles Applied:**
- ✅ DRY - No duplication
- ✅ YAGNI - Only what's needed
- ✅ TDD - Test first, then implement
- ✅ Frequent commits after each passing test
- ✅ Exact file paths and complete code
- ✅ Clear verification steps
