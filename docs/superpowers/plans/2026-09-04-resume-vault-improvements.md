# Resume Vault Improvements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix resume title retention bug, eliminate modal view blocking with sticky action buttons, enable inline renaming for existing vault resumes, and add a full-screen Quick View modal.

**Architecture:** Add backend parsing endpoint (`/api/resumes/parse-file`) and update endpoint (`PATCH /api/resumes/{resume_id}`), update frontend API client, refactor `ResumeLibrary.jsx` to defer database creation until explicit user save, implement responsive modal layout with fixed action footer, add inline renaming controls, and build a dedicated Quick View modal.

**Tech Stack:** FastAPI, Pydantic, Python 3.11/3.14, React 18, Vite, Tailwind CSS v4, Lucide Icons, SQLite / Neon PostgreSQL, Cloudflare R2.

---

## Global Constraints

- Zero em-dashes: visible UI text and documentation must use regular hyphens (`-`), never `—` or `–`.
- Zero data loss: user cancellation must never create residual or duplicate database records.
- Multi-tenant isolation: all resume update operations must strictly enforce `user_id` ownership.
- Responsive accessibility: modal footer action buttons must remain visible without requiring viewport scrolling.

---

### Task 1: Backend Resume Update & Parse Endpoints

**Files:**
- Modify: `backend/models.py`
- Modify: `backend/storage.py`
- Modify: `backend/main.py`
- Test: `tests/test_api.py`

**Interfaces:**
- `ResumeUpdate(BaseModel)`: `name: Optional[str] = None`, `content: Optional[str] = None`
- `StorageService.update_resume(resume_id: str, name: Optional[str] = None, content: Optional[str] = None, user_id: Optional[str] = None) -> Optional[Resume]`
- `POST /api/resumes/parse-file`: accepts `file: UploadFile`, extracts text without writing to database, returns `{"filename": str, "suggested_title": str, "text": str}`
- `PATCH /api/resumes/{resume_id}`: accepts `ResumeUpdate`, validates ownership, updates record, returns updated `Resume`

- [x] **Step 1: Write the failing tests**

In `tests/test_api.py`, add tests for `POST /api/resumes/parse-file` and `PATCH /api/resumes/{resume_id}`:
```python
def test_parse_resume_file_endpoint():
    headers = get_auth_headers()
    file_content = b"John Doe\nSoftware Engineer\nPython, React, AWS."
    files = {"file": ("test_resume.txt", file_content, "text/plain")}
    res = client.post("/api/resumes/parse-file", files=files, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["filename"] == "test_resume.txt"
    assert data["suggested_title"] == "test_resume"
    assert "Software Engineer" in data["text"]


def test_update_resume_endpoint():
    headers = get_auth_headers()
    create_res = client.post(
        "/api/resumes",
        json={"name": "Initial Title", "content": "Sample content"},
        headers=headers,
    )
    assert create_res.status_code == 200
    resume_id = create_res.json()["id"]

    patch_res = client.patch(
        f"/api/resumes/{resume_id}",
        json={"name": "Updated Custom Title"},
        headers=headers,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["name"] == "Updated Custom Title"

    # Verify updated name in list
    get_res = client.get("/api/resumes", headers=headers)
    assert get_res.status_code == 200
    updated = next(r for r in get_res.json() if r["id"] == resume_id)
    assert updated["name"] == "Updated Custom Title"
```

- [x] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_api.py::test_parse_resume_file_endpoint tests/test_api.py::test_update_resume_endpoint -v`
Expected: FAIL (endpoints return 404 or 405)

- [x] **Step 3: Add `ResumeUpdate` model in `backend/models.py`**

```python
class ResumeUpdate(BaseModel):
    name: Optional[str] = None
    content: Optional[str] = None
```

- [x] **Step 4: Implement `update_resume` in `backend/storage.py`**

In `StorageService`:
```python
    def update_resume(
        self,
        resume_id: str,
        name: Optional[str] = None,
        content: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Optional[Resume]:
        existing = self.get_resume(resume_id, user_id=user_id)
        if not existing:
            return None

        new_name = name.strip() if name and name.strip() else existing.name
        new_content = content if content is not None else existing.content
        now = datetime.now().isoformat()

        with self._get_cursor() as cursor:
            if user_id:
                cursor.execute(
                    self._format_sql(
                        "UPDATE resumes SET name = ?, content = ?, updated_at = ? WHERE id = ? AND user_id = ?"
                    ),
                    (new_name, new_content, now, resume_id, user_id),
                )
            else:
                cursor.execute(
                    self._format_sql(
                        "UPDATE resumes SET name = ?, content = ?, updated_at = ? WHERE id = ?"
                    ),
                    (new_name, new_content, now, resume_id),
                )

        return self.get_resume(resume_id, user_id=user_id)
```

- [x] **Step 5: Implement `POST /api/resumes/parse-file` and `PATCH /api/resumes/{resume_id}` in `backend/main.py`**

Import `ResumeUpdate` from `backend.models`.
Add:
```python
@app.post("/api/resumes/parse-file")
def parse_resume_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_RESUME_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed formats: .pdf, .docx, .doc, .txt, .rtf",
        )
    content_bytes = file.file.read(MAX_RESUME_SIZE_BYTES + 1)
    if len(content_bytes) > MAX_RESUME_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail="File exceeds maximum allowed size of 10MB.",
        )
    extracted_text = extract_text_from_file(content_bytes, file.filename)
    if not extracted_text.strip():
        raise HTTPException(status_code=400, detail="No readable text could be extracted from this document.")

    return {
        "filename": file.filename,
        "suggested_title": Path(file.filename).stem,
        "text": extracted_text,
    }


@app.patch("/api/resumes/{resume_id}", response_model=Resume)
def update_resume(
    resume_id: str,
    req: ResumeUpdate,
    current_user: User = Depends(get_current_user),
):
    updated = storage.update_resume(
        resume_id,
        name=req.name,
        content=req.content,
        user_id=current_user.id,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Resume not found.")
    if updated.file_key:
        updated.download_url = object_storage.generate_download_url(updated.file_key)
    return updated
```

- [x] **Step 6: Run test to verify it passes**

Run: `python -m pytest tests/test_api.py::test_parse_resume_file_endpoint tests/test_api.py::test_update_resume_endpoint -v`
Expected: PASS

- [x] **Step 7: Commit Task 1 changes**

```bash
git add backend/models.py backend/storage.py backend/main.py tests/test_api.py
git commit -m "feat(api): add resume parse-file and patch update endpoints"
```

---

### Task 2: Frontend API Client Support

**Files:**
- Modify: `frontend/src/api/client.js`

**Interfaces:**
- `parseResumeFile(file)`: posts to `/api/resumes/parse-file`, returns `{ filename, suggested_title, text }`
- `updateResume(id, { name, content })`: patches to `/api/resumes/{id}`, returns updated `Resume`

- [ ] **Step 1: Add `parseResumeFile` and `updateResume` in `frontend/src/api/client.js`**

```javascript
export async function parseResumeFile(file) {
  const formData = new FormData();
  formData.append('file', file);
  const res = await authFetch(`${API_BASE}/resumes/parse-file`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to extract text from document' }));
    throw new Error(err.detail || 'Failed to extract text from document');
  }
  return res.json();
}

export async function updateResume(id, { name, content }) {
  const res = await authFetch(`${API_BASE}/resumes/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, content }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to update resume' }));
    throw new Error(err.detail || 'Failed to update resume');
  }
  return res.json();
}
```

- [ ] **Step 2: Verify frontend compilation**

Run: `npm --prefix frontend run build`
Expected: PASS

- [ ] **Step 3: Commit Task 2 changes**

```bash
git add frontend/src/api/client.js
git commit -m "feat(api): add parseResumeFile and updateResume client functions"
```

---

### Task 3: Resume Library Add Modal Sizing & Title Preservation

**Files:**
- Modify: `frontend/src/components/ResumeLibrary.jsx`

**Interfaces:**
- Defer database creation until user clicks "Save to Vault".
- Only auto-fill title from filename if title input is empty.
- Provide sticky action footer that stays visible on all viewport heights.

- [ ] **Step 1: Refactor file processing and creation logic in `ResumeLibrary.jsx`**
  - Add state `selectedFile` (`useState(null)`).
  - When a file is dropped or selected in `handleProcessFile`:
    - Call `parseResumeFile(file)` for binary files or `file.text()` for `.txt`/`.md`.
    - If `newName.trim()` is empty, set `setNewName(data.suggested_title)`. If user already typed a title, retain `newName`!
    - Set `setNewContent(data.text)` in textarea for user review.
    - Set `setSelectedFile(file)`.
    - Do NOT call `uploadResumeFile` or `addResume` here.
  - When user submits `handleCreate`:
    - If `selectedFile` is present: call `uploadResumeFile(selectedFile, newName.trim())`.
    - If no file attached (manual text paste): call `addResume({ name: newName.trim(), content: newContent.trim() })`.
    - Reset `selectedFile`, `newName`, `newContent`, close modal, reload resumes.
  - When user clicks Cancel or closes modal:
    - Reset `selectedFile`, `newName`, `newContent`, `error`, close modal. No records saved.

- [ ] **Step 2: Update Add Modal container for responsive view**
  - Change modal container to:
    ```jsx
    <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="card-corporate bg-white border border-[#e0e0e0] w-full max-w-3xl max-h-[90vh] rounded-xl flex flex-col animate-fade-in shadow-xl text-[#000000] overflow-hidden">
        {/* Fixed Header */}
        <div className="flex items-center justify-between p-5 border-b border-[#e0e0e0] shrink-0">...</div>

        {/* Scrollable Form Body */}
        <div className="p-6 overflow-y-auto space-y-4 flex-1">...</div>

        {/* Fixed Sticky Footer */}
        <div className="p-4 border-t border-[#e0e0e0] bg-[#fcfdfe] flex items-center justify-end gap-2 shrink-0">
          <button type="button" onClick={handleCloseAddModal} className="btn-secondary-corporate text-xs py-1.5 px-4">
            Cancel
          </button>
          <button type="submit" form="add-resume-form" className="btn-primary-corporate text-xs py-1.5 px-4">
            Save to Vault
          </button>
        </div>
      </div>
    </div>
    ```

- [ ] **Step 3: Verify frontend build**

Run: `npm --prefix frontend run build`
Expected: PASS

- [ ] **Step 4: Commit Task 3 changes**

```bash
git add frontend/src/components/ResumeLibrary.jsx
git commit -m "fix(ui): preserve custom resume title and add sticky modal action buttons"
```

---

### Task 4: Resume Library Inline Renaming & Quick View Modal

**Files:**
- Modify: `frontend/src/components/ResumeLibrary.jsx`

**Interfaces:**
- Inline renaming: click pencil button, edit title input, submit on Enter or Check button, cancel on Escape or X button.
- Quick View modal: click Eye button, view complete formatted text, download file button, copy text button.

- [ ] **Step 1: Implement inline renaming on resume cards**
  - Add state: `editingId` (`useState(null)`), `editingName` (`useState('')`), `updatingId` (`useState(null)`).
  - Add handlers:
    - `handleStartEdit(resume)`: `setEditingId(resume.id)`, `setEditingName(resume.name)`.
    - `handleCancelEdit()`: `setEditingId(null)`, `setEditingName('')`.
    - `handleSaveEdit(id)`: call `updateResume(id, { name: editingName.trim() })`, update local state, exit edit mode.
  - In card header:
    - If `editingId === resume.id`: render inline `<input>` with Check (`Check`) and Cancel (`X`) buttons.
    - If not editing: render title with edit button (`Pencil` icon, size 13) right beside it.

- [ ] **Step 2: Implement Quick View modal**
  - Add state: `viewingResume` (`useState(null)`), `copied` (`useState(false)`).
  - Add Quick View button (`Eye` icon) on each card.
  - When `viewingResume` is set, render a preview modal:
    - Title, word count badge, creation date.
    - "Download Original File" button (if `viewingResume.download_url` is present).
    - "Copy Text" button with temporary checkmark feedback.
    - Full scrollable reader container (`font-mono text-xs whitespace-pre-wrap p-4 bg-[#f8fafc] border rounded-lg max-h-[60vh] overflow-y-auto`).
    - Close button.

- [ ] **Step 3: Verify complete test suite**

Run: `python -m pytest -v`
Expected: 61/61 tests pass.

- [ ] **Step 4: Verify frontend production build**

Run: `npm --prefix frontend run build`
Expected: PASS

- [ ] **Step 5: Commit Task 4 changes**

```bash
git add frontend/src/components/ResumeLibrary.jsx
git commit -m "feat(ui): add inline resume title editing and quick view modal"
```
