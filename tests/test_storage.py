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
    storage.update_settings(SettingsUpdate(api_base_url="https://api.minimax.chat/v1", model_name="minimax-01"))
    settings = storage.get_settings()
    assert settings.api_base_url == "https://api.minimax.chat/v1"
    assert settings.model_name == "minimax-01"

    # Delete
    assert storage.delete_application(app.id) is True
    assert len(storage.get_applications()) == 0
    assert storage.delete_resume(r.id) is True
    assert len(storage.get_resumes()) == 0
