import pytest
from backend.storage import StorageService
from backend.models import ApplicationCreate, ApplicationStatus, SettingsUpdate

def test_storage_crud(tmp_path):
    db_path = str(tmp_path / "test_tracker.db")
    storage = StorageService(db_path=db_path)
    
    # Resumes
    r = storage.add_resume(name="Backend Resume", content="Python, FastAPI, Docker, SQL")
    assert r.id is not None
    assert r.name == "Backend Resume"
    assert len(storage.get_resumes()) == 1
    
    # Applications
    app_data = ApplicationCreate(
        company="Acme Corp",
        role="Senior Backend Engineer",
        status=ApplicationStatus.APPLIED,
        location="Remote",
        salary="$130k - $160k",
        url="https://example.com/job",
        required_skills=["Python", "FastAPI"],
        ats_keywords=["Microservices", "Docker"],
        notes="Applied via website",
        best_resume_id=r.id
    )
    app = storage.add_application(app_data)
    assert app.id is not None
    assert app.company == "Acme Corp"
    assert app.status == ApplicationStatus.APPLIED
    assert "Python" in app.required_skills
    
    apps = storage.get_applications()
    assert len(apps) == 1
    
    # Update
    updated = storage.update_application(app.id, {"status": ApplicationStatus.INTERVIEWING, "notes": "Got screen call"})
    assert updated is not None
    assert updated.status == ApplicationStatus.INTERVIEWING
    assert updated.notes == "Got screen call"
    
    # Settings
    storage.update_settings(SettingsUpdate(api_base_url="https://api.minimax.chat/v1", model_name="minimax-01", use_offline_mode=True))
    settings = storage.get_settings()
    assert settings.api_base_url == "https://api.minimax.chat/v1"
    assert settings.model_name == "minimax-01"
    assert settings.use_offline_mode is True

    storage.update_settings(SettingsUpdate(use_offline_mode=False))
    settings = storage.get_settings()
    assert settings.use_offline_mode is False

    # Delete
    assert storage.delete_application(app.id) is True
    assert len(storage.get_applications()) == 0
    assert storage.delete_resume(r.id) is True
    assert len(storage.get_resumes()) == 0


def test_application_deduplication(tmp_path):
    db_path = str(tmp_path / "test_tracker_dedup.db")
    storage = StorageService(db_path=db_path)

    # 1. Add first application
    app_data1 = ApplicationCreate(
        company="MindBridge",
        role="QA & Test Automation Developer",
        status=ApplicationStatus.WISHLIST,
        location="London, ON",
        salary="$120k",
        url="https://jobs.dayforcehcm.com/en-CA/mindbridge/CANDIDATEPORTAL/jobs/217",
        required_skills=["Selenium", "Playwright"],
        ats_keywords=["Test Automation"],
    )
    first_app = storage.add_application(app_data1)
    assert first_app.id is not None
    assert len(storage.get_applications()) == 1

    # 2. Add same job by same URL (e.g. user clicks Add to Pipeline again)
    app_data_same_url = ApplicationCreate(
        company="MindBridge Analytics Inc.",
        role="QA & Test Automation Developer",
        status=ApplicationStatus.WISHLIST,
        location="London, ON / Remote",
        salary="$120k - $140k",
        url="https://jobs.dayforcehcm.com/en-CA/mindbridge/CANDIDATEPORTAL/jobs/217",
        required_skills=["Selenium", "Playwright", "TypeScript"],
        ats_keywords=["Test Automation", "CI/CD"],
    )
    second_app = storage.add_application(app_data_same_url)
    assert second_app.id == first_app.id  # Same ID, updated in place!
    apps = storage.get_applications()
    assert len(apps) == 1  # No duplicate row created!
    assert "TypeScript" in second_app.required_skills

    # 3. Add same job with slightly different URL or text paste (matching company & role)
    app_data_same_company_role = ApplicationCreate(
        company="mindbridge",  # case-insensitive check
        role="qa & test automation developer",
        status=ApplicationStatus.APPLIED,
        location="Remote",
        url="https://www.linkedin.com/jobs/view/4462448668/",
        required_skills=["Python", "Playwright"],
    )
    third_app = storage.add_application(app_data_same_company_role)
    assert third_app.id == first_app.id  # Still same ID!
    assert len(storage.get_applications()) == 1
    assert third_app.status == ApplicationStatus.APPLIED


def test_deduplicate_applications_preserves_multi_tenant_isolation(tmp_path):
    db_path = str(tmp_path / "dedup_isolation_test.db")
    storage = StorageService(db_path=db_path)
    app_data = ApplicationCreate(
        company="Google",
        role="SWE",
        url="https://google.com/jobs/1",
        status=ApplicationStatus.APPLIED,
    )
    
    # User Alpha and User Beta both apply to Google SWE
    app_a = storage.add_application(app_data, user_id="user-alpha")
    app_b = storage.add_application(app_data, user_id="user-beta")
    
    # Run the table-wide deduplication cleanup
    storage.deduplicate_existing_applications()
    
    # Neither application should have been deleted because they belong to different users!
    assert storage.get_application(app_a.id) is not None
    assert storage.get_application(app_b.id) is not None
    assert len(storage.get_applications(user_id="user-alpha")) == 1
    assert len(storage.get_applications(user_id="user-beta")) == 1


