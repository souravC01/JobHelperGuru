import pytest
from datetime import datetime, timezone, timedelta
from backend.storage import StorageService
from backend.models import (
    ApplicationCreate,
    ApplicationUpdate,
    ApplicationStatus,
    SettingsUpdate,
)


@pytest.fixture
def storage(tmp_path):
    db_path = str(tmp_path / "test_tracker.db")
    return StorageService(db_path=db_path)


def test_transition_to_applied_sets_client_date_and_default_follow_up(storage):
    user_id = "user-tracker-1"
    # Configure 14 days default follow up
    storage.update_settings(SettingsUpdate(default_follow_up_days=14), user_id=user_id)

    app = storage.add_application(
        ApplicationCreate(
            company="Shopify",
            role="Backend Developer",
            status=ApplicationStatus.WISHLIST,
        ),
        user_id=user_id,
    )
    assert app.status == ApplicationStatus.WISHLIST
    assert not app.application_date
    assert not app.follow_up_date

    # Client transitions to Applied with local calendar date
    client_local_date = "2026-09-07"
    updated = storage.update_application(
        app.id,
        ApplicationUpdate(
            status=ApplicationStatus.APPLIED,
            application_date=client_local_date,
        ),
        user_id=user_id,
    )
    assert updated.status == ApplicationStatus.APPLIED
    assert updated.application_date == "2026-09-07"
    assert updated.follow_up_date == "2026-09-21"  # 2026-09-07 + 14 days


def test_transition_to_applied_without_client_date_uses_server_utc_fallback(storage):
    user_id = "user-tracker-2"
    # Configure 5 days default follow up
    storage.update_settings(SettingsUpdate(default_follow_up_days=5), user_id=user_id)

    app = storage.add_application(
        ApplicationCreate(
            company="Amazon",
            role="SDE II",
            status=ApplicationStatus.WISHLIST,
        ),
        user_id=user_id,
    )

    # API client transitions to Applied omitting application_date
    updated = storage.update_application(
        app.id,
        ApplicationUpdate(status=ApplicationStatus.APPLIED),
        user_id=user_id,
    )
    expected_utc_today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    expected_follow_up = (datetime.now(timezone.utc) + timedelta(days=5)).strftime("%Y-%m-%d")

    assert updated.status == ApplicationStatus.APPLIED
    assert updated.application_date == expected_utc_today
    assert updated.follow_up_date == expected_follow_up


def test_subsequent_saves_and_status_changes_do_not_overwrite_dates(storage):
    user_id = "user-tracker-3"
    storage.update_settings(SettingsUpdate(default_follow_up_days=7), user_id=user_id)

    app = storage.add_application(
        ApplicationCreate(
            company="Meta",
            role="Production Engineer",
            status=ApplicationStatus.APPLIED,
            application_date="2026-08-01",
            follow_up_date="2026-08-15",
        ),
        user_id=user_id,
    )
    assert app.application_date == "2026-08-01"
    assert app.follow_up_date == "2026-08-15"

    # Status transition to Interviewing must NOT recalculate follow_up_date or overwrite application_date
    updated = storage.update_application(
        app.id,
        ApplicationUpdate(status=ApplicationStatus.INTERVIEWING),
        user_id=user_id,
    )
    assert updated.status == ApplicationStatus.INTERVIEWING
    assert updated.application_date == "2026-08-01"
    assert updated.follow_up_date == "2026-08-15"

    # Note update must not overwrite dates
    updated2 = storage.update_application(
        app.id,
        ApplicationUpdate(notes="Recruiter screen booked"),
        user_id=user_id,
    )
    assert updated2.application_date == "2026-08-01"
    assert updated2.follow_up_date == "2026-08-15"


def test_user_can_manually_clear_follow_up_date(storage):
    user_id = "user-tracker-4"
    app = storage.add_application(
        ApplicationCreate(
            company="Apple",
            role="Hardware Engineer",
            status=ApplicationStatus.APPLIED,
            application_date="2026-09-01",
            follow_up_date="2026-09-08",
        ),
        user_id=user_id,
    )
    # Manually clear follow_up_date
    updated = storage.update_application(
        app.id,
        {"follow_up_date": ""},
        user_id=user_id,
    )
    assert updated.follow_up_date == ""

    # Subsequent update must not restore follow_up_date
    updated2 = storage.update_application(
        app.id,
        ApplicationUpdate(notes="No follow up needed"),
        user_id=user_id,
    )
    assert updated2.follow_up_date == ""
