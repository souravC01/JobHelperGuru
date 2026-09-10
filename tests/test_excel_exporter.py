import io
import openpyxl
from backend.services.excel_exporter import ExcelExporter
from backend.models import Application, ApplicationStatus

def test_generate_excel_workbook():
    exporter = ExcelExporter()
    apps = [
        Application(
            id="app-1",
            company="Google",
            role="Staff Software Engineer",
            status=ApplicationStatus.INTERVIEWING,
            location="Mountain View, CA",
            salary="$220,000 - $280,000",
            url="https://careers.google.com/jobs/1",
            required_skills=["Python", "Distributed Systems", "Kubernetes"],
            ats_keywords=["GCP", "High Throughput", "Architecture"],
            date_added="2026-09-01",
            application_date="2026-09-02",
            follow_up_date="2026-09-09",
            notes="Completed screening call with recruiter"
        ),
        Application(
            id="app-2",
            company="Netflix",
            role="Senior Backend Engineer",
            status=ApplicationStatus.APPLIED,
            location="Los Gatos, CA",
            salary="$200,000 - $250,000",
            url="https://netflix.com/jobs/2",
            required_skills=["Java", "Spring Boot", "Kafka"],
            ats_keywords=["Microservices", "Event-Driven"],
            date_added="2026-09-02",
            application_date="2026-09-02",
            follow_up_date="2026-09-10",
            notes="Applied via referral"
        )
    ]
    excel_bytes = exporter.export_workbook(apps)
    assert len(excel_bytes) > 2000
    
    # Validate with openpyxl
    wb = openpyxl.load_workbook(io.BytesIO(excel_bytes))
    assert "Applications Tracker" in wb.sheetnames
    assert "Skills & ATS Keywords" in wb.sheetnames
    
    ws1 = wb["Applications Tracker"]
    assert ws1.cell(row=1, column=2).value == "Company"
    assert ws1.cell(row=2, column=2).value == "Google"
    assert ws1.cell(row=2, column=4).value == "Interviewing"
    assert ws1.cell(row=3, column=2).value == "Netflix"
    assert ws1.cell(row=3, column=4).value == "Applied"
    
    # Check hyperlink
    cell_url = ws1.cell(row=2, column=7)
    assert cell_url.hyperlink is not None or "careers.google.com" in str(cell_url.value)

    # Validate Sheet 2
    ws2 = wb["Skills & ATS Keywords"]
    assert ws2.cell(row=1, column=1).value == "Company"
    assert ws2.cell(row=2, column=1).value == "Google"
    assert "Python" in ws2.cell(row=2, column=3).value


def test_untrusted_company_is_exported_as_text():
    payload = ExcelExporter().export_workbook([
        Application(id="test", company="=1+1", role="=SUM(A1:A10)")
    ])
    wb = openpyxl.load_workbook(io.BytesIO(payload), data_only=False)
    # Sheet 1: Applications Tracker
    ws1 = wb["Applications Tracker"]
    assert ws1["B2"].data_type == "s"
    assert ws1["B2"].value == "=1+1"
    assert ws1["C2"].data_type == "s"
    assert ws1["C2"].value == "=SUM(A1:A10)"

    # Sheet 2: Skills & ATS Keywords
    ws2 = wb["Skills & ATS Keywords"]
    assert ws2["A2"].data_type == "s"
    assert ws2["A2"].value == "=1+1"
    assert ws2["B2"].data_type == "s"
    assert ws2["B2"].value == "=SUM(A1:A10)"


def test_untrusted_formulas_across_all_fields():
    payload = ExcelExporter().export_workbook([
        Application(
            id="test-sec",
            company="=1+1",
            role="=2+2",
            location="=3+3",
            salary="=4+4",
            notes="=5+5",
            required_skills=["=6+6"],
            ats_keywords=["=7+7"],
        )
    ])
    wb = openpyxl.load_workbook(io.BytesIO(payload), data_only=False)
    ws1 = wb["Applications Tracker"]
    # Check that none of the row 2 cells have data_type 'f' (formula)
    for col_idx in range(1, 13):
        cell = ws1.cell(row=2, column=col_idx)
        assert cell.data_type != "f", f"Column {col_idx} was exported as formula cell"


def test_invalid_hyperlinks_are_not_clickable():
    payload = ExcelExporter().export_workbook([
        Application(
            id="test-url",
            company="TestCo",
            role="Engineer",
            url="javascript:alert(1)"
        ),
        Application(
            id="test-file",
            company="FileCo",
            role="Engineer",
            url="file:///etc/passwd"
        ),
        Application(
            id="test-valid",
            company="GoodCo",
            role="Engineer",
            url="https://example.com/jobs/1"
        )
    ])
    wb = openpyxl.load_workbook(io.BytesIO(payload), data_only=False)
    ws1 = wb["Applications Tracker"]
    # javascript URL -> no hyperlink
    assert ws1.cell(row=2, column=7).hyperlink is None
    # file URL -> no hyperlink
    assert ws1.cell(row=3, column=7).hyperlink is None
    # https URL -> valid hyperlink
    assert ws1.cell(row=4, column=7).hyperlink is not None


def test_empty_applications_export_works():
    payload = ExcelExporter().export_workbook([])
    wb = openpyxl.load_workbook(io.BytesIO(payload), data_only=False)
    assert "Applications Tracker" in wb.sheetnames
    assert "Skills & ATS Keywords" in wb.sheetnames
    ws1 = wb["Applications Tracker"]
    assert ws1.cell(row=1, column=2).value == "Company"
    assert ws1.max_row == 1

