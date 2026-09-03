import pytest
from backend.storage import StorageService
from backend.models import ApplicationCreate, ApplicationStatus


def test_multi_tenant_isolation(tmp_path):
    storage = StorageService(db_path=str(tmp_path / "test_multi_tenant.db"), force_sqlite=True)

    # 1. Create two separate users
    u1 = storage.create_user(email="alice@test.com", hashed_password="pwd", name="Alice")
    u2 = storage.create_user(email="bob@test.com", hashed_password="pwd", name="Bob")

    # 2. Alice creates an application
    app_alice = storage.add_application(
        ApplicationCreate(
            company="Alice Corp",
            role="Engineer",
            status=ApplicationStatus.WISHLIST,
        ),
        user_id=u1.id,
    )

    # 3. Bob creates an application
    app_bob = storage.add_application(
        ApplicationCreate(
            company="Bob Inc",
            role="Designer",
            status=ApplicationStatus.APPLIED,
        ),
        user_id=u2.id,
    )

    # 4. Verify isolation
    alice_apps = storage.get_applications(user_id=u1.id)
    bob_apps = storage.get_applications(user_id=u2.id)

    assert len(alice_apps) == 1
    assert alice_apps[0].company == "Alice Corp"

    assert len(bob_apps) == 1
    assert bob_apps[0].company == "Bob Inc"


def test_user_retrieval(tmp_path):
    storage = StorageService(db_path=str(tmp_path / "test_user_crud.db"), force_sqlite=True)
    user = storage.create_user(email="carol@test.com", hashed_password="pwd_hash", name="Carol")

    found_email = storage.get_user_by_email("carol@test.com")
    assert found_email is not None
    assert found_email["id"] == user.id
    assert found_email["hashed_password"] == "pwd_hash"

    found_id = storage.get_user_by_id(user.id)
    assert found_id is not None
    assert found_id.email == "carol@test.com"
