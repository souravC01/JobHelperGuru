# Matching source capture audit

Audit date: 2026-10-16. Scope: the original Task 1 source-transfer records. No application code, Git refs, original captures or source-checkout files were changed.

## Result

**All 40 captured source paths have verified Git content provenance.** The retained patch exactly matches the pinned base-to-source diff after CRLF/LF normalization. All 37 changed-file blob IDs match the pinned source commit; the other three paths are unchanged from the pinned base. The source branch still points to the recorded source commit.

The original manifest records SHA-256 of working-file bytes, while the previous audit compared Git blob bytes. Those are different representations. Of the 40 original hashes, 23 match exact blob bytes, four match uniform CRLF checkout bytes, and two match surviving mixed-line-ending checkout bytes with identical normalized content. The remaining 11 original working-file byte sequences are not retained in Git and cannot be independently rehashed. Their code content is authenticated by the exact captured patch and pinned blob IDs. They are not declared exact raw-hash matches.

Canonical Git SHA-256 values below supplement the original manifest; they do not replace its historical hashes. No code-content discrepancy was found. The raw-byte preservation limitation remains explicit.

## Evidence

- Source: `bccc93836303f5b2ede0faf34e4c1b8d6c6316fa` (`feat/evidence-based-resume-matching`).
- Base: `9fa7b26a4ca78c38dd977d1eff0df1f30c11b5c5`.
- Original manifest SHA-256: `5af4ce0ddf583e9119762db5192a4b7f59fcb37fb1b5769b59ad79bf34b674d0`.
- Original captured patch SHA-256: `3ab0092fdcf503f9dedf9cbb6205e268752b8aac3bd4ae430a7e68dcb00ad170`.
- Normalized captured patch SHA-256: `8d7b886d18679c7cc4393fa9320f2a26664a5f931b4f54ee97ef492c2f0ccdb3`.
- Reproduction: ignored local script `scratch/task10-source-audit.py`; machine-readable result `scratch/task10-source-audit-result.json`. It asserts complete patch equality, all changed blob IDs, three unchanged paths, immutable original records and unchanged source-checkout file hashes before/after.

## Previously reported 13 discrepancies

| Source path | Finding |
|---|---|
| `backend/config.py` | Mixed line endings confirmed from surviving checkout bytes |
| `backend/main.py` | Original working bytes unavailable; content verified by captured patch |
| `backend/models.py` | Original working bytes unavailable; content verified by captured patch |
| `backend/services/ai_engine.py` | Original working bytes unavailable; content verified by captured patch |
| `backend/services/document_parser.py` | Mixed line endings confirmed from surviving checkout bytes |
| `backend/services/heuristic_parser.py` | Original working bytes unavailable; content verified by captured patch |
| `backend/services/pinned_transport.py` | Original working bytes unavailable; content verified by captured patch |
| `backend/services/resume_files.py` | Original working bytes unavailable; content verified by captured patch |
| `backend/services/skill_matching.py` | Original working bytes unavailable; content verified by captured patch |
| `frontend/src/api/client.js` | Original working bytes unavailable; content verified by captured patch |
| `frontend/src/components/ResumeLibrary.jsx` | Original working bytes unavailable; content verified by captured patch |
| `tests/test_ai_engine.py` | Original working bytes unavailable; content verified by captured patch |
| `tests/test_pinned_transport.py` | Original working bytes unavailable; content verified by captured patch |

## Canonical content inventory

| Source path | Git blob ID | SHA-256 of Git blob bytes |
|---|---|---|
| `backend/config.py` | `1fe66fbd9d20da3eda9f35fb76c74eb635ac55ac` | `8120d32629867925e0667951f348c232ea635d7a6b93af234f45136917214dfd` |
| `backend/main.py` | `5162257fc63f9464b592ccf4c011673fd9b3e5d6` | `7305493c42e4330836ffe5b7630b9323b4e6447a73c674e2192ffc3d9a742a23` |
| `backend/models.py` | `055891081d972b92bcff30970ae44d10ebdf9afa` | `8ee8fcf71f44558b161b6501b4311ab70948422f0aec0e596aab4bca459d304a` |
| `backend/services/ai_engine.py` | `a72642c0c693ca52f8a9eaa86ae48ab35f8db642` | `01b197459a4f9e406903bc64a8fcc35966ddc15267f41227a81776e1a5b19671` |
| `backend/services/document_parser.py` | `4ca5ef6175e130a4818babfb0c32e1330383e705` | `cb6014775c98a1a54bbebf13ad850de7d4b4a6feb08bc34e53ea4aa6db0c2fda` |
| `backend/services/heuristic_parser.py` | `710ee64aa61cd1abdb4776c41efde196efd3a8a8` | `56b5121735a9d2427e8f2ca318321a32f27f2bc23031e8911c68cfc28de834ed` |
| `backend/services/matching/__init__.py` | `260d04a4c47014b9874a23bbd2f096f5c95e754a` | `2acc7e77a759e39577046f70838d497de8bc477010a82cbd4dd655da1f0f9656` |
| `backend/services/matching/chunking.py` | `ffa5f7a8762fafd3b4ba9a2d6d8cbe8ca31c3e83` | `d159e88fa557db2452bdb364c975a8780fc5c4e9e9cbd1a1da119c6748943fd2` |
| `backend/services/matching/extraction.py` | `691b6cf16f54a6f937a27845c3f495c18cae49f5` | `a574705944089ab2d42d062d77dc93c7d8ae38be40f5e27670a3f515f70a40cf` |
| `backend/services/matching/models.py` | `93840c0f6c439b2e664d7d6b4d11752d0a8403a1` | `2ce2a0fef59ab78b76c9ecdc7cc1b4919ce8ba52b76a6d68d2a2bcb7a87c86f6` |
| `backend/services/matching/normalization.py` | `97d4d181c342bcf0ad7e867f5b6a336e8ec2e384` | `75ec2ed77a76720347ee5e0cefc6794b5e84685262b50337dc04b649e8a73510` |
| `backend/services/matching/pipeline.py` | `347e64acea45262daaab6dcb77f3c2813f51494f` | `1cd1a9193ca35e3052992d1f8a6a3777e03d59eaaf69d403b91c2ddd962591e5` |
| `backend/services/matching/scoring.py` | `1f80907623e93569931b6f437a527a0408f38e33` | `6c4aa84292f77b94ee726ba8fcee1204ccdefd94c3f6b43ee3d041d63beaf94d` |
| `backend/services/pinned_transport.py` | `61916fd3f233f498ef95cd369b7aa8028aa6241a` | `9b5ceb32ddb61e9a311c32eb819addc6a25e51b732b2494a2061c38ea1baeb7f` |
| `backend/services/resume_files.py` | `c8763a46422273b6d621331b44ab4d60526f23fb` | `40d3d2862fe43ed7eb53eda0cae10400caacf7f14ffe0a637ca3bbf73217e9c0` |
| `backend/services/skill_matching.py` | `73d0a83a866c4fdc94f0455703259aea2df9882d` | `214710d461b0086375f2cb08d1163016408549507f80c200bb99a70f3460b53d` |
| `backend/storage.py` | `4b153972cdf497ef7d6be9d1c8de6d4940868718` | `ca422a844d6fb42b395b41dfcebf04bf19fa8f49247dafa21ca421d8dfd37df9` |
| `docs/matching-evaluation.md` | `c54202f3ae5e53d916db509912d275eb26ca69ea` | `940093756f70a9f3755ba94be1a6679b6741ec0b18087d3d2ab46e45a55c2d1d` |
| `frontend/src/App.jsx` | `4f4f5ddf5e08404376225abed2f4de04c9579b63` | `60e51cbacc081f4a0a8cd6ba1da3afe20724b5c3f79054a48fd69298ca3fcde6` |
| `frontend/src/api/client.js` | `18133b23767005dd4fbe41af85874bb209b2444e` | `a6206e773bfac3761845bd85fe11a158c28ea4259e11e38f9cb5412f86f8a6ae` |
| `frontend/src/components/MatchEvidenceDetails.jsx` | `86ffd5c86b1e4aaa2e9ccb2490c1e33187db914a` | `45cfaf2fe0145d46548ca595e46c2e3678b337b31fcd6c15affbceacb2590b22` |
| `frontend/src/components/ResumeFitRanker.jsx` | `f510f602ee52dd009eb757e47a165640af1b479c` | `aad9b974c269b86a53e9e8a4f2918bbba259381058087dbfed97bd694648f07f` |
| `frontend/src/components/ResumeLibrary.jsx` | `02e6523e3db61c2ec19b6b7b77dddfe2b69eb01c` | `7c01d3a4d966e7ed4ab003506f9c0f2590e4c52df0a21928e491d3e983831851` |
| `frontend/src/test/MatchEvidenceDetails.test.jsx` | `6fe3b18c3bf287b78e9e764382e2dba4f9789f7c` | `4b043843f73a0ece8adc75a5d9abb2afb8973062ed031766e55c0a1dcbc64bae` |
| `frontend/src/test/ResumeFitRanker.test.jsx` | `eab012a297debb75be0a09a62ff9ec1148fdbe01` | `477bce7dc2aa3464a4cfa32ea80abab1afc9256a6abf07c5380dd4e01ceed8b6` |
| `scripts/evaluate_matching.py` | `fd3e1bfb048fbece789d271097e4ddf8e905fb17` | `9f53305b17f7019586b6e41351eb620ebafd241bcf3d86e078b817bd04a55a28` |
| `tests/test_ai_engine.py` | `14fcb4bd1e99da8342c3663722cca04b197103ef` | `1e3aa9ed4ef9bfbc06ba9208085fe04cb08640e4c6e51652fa07a25c4fb10ca5` |
| `tests/test_document_parser.py` | `e956dbd60dd00f46148f95daac431c3e3842324e` | `cdebfd82a1c6e7dc9610cf0b67f21b3ce242d9f49a7af8fccf5395e56f8b6d86` |
| `tests/test_match_api.py` | `a30f64ea25f038373c3b1d160aa74e3252a53013` | `ac0e18f78e272b665d592fa52d3a6cfd94f4d29a45466caaef6a1fe52bfed7e9` |
| `tests/test_match_benchmark.py` | `41329eb3f2e6c3a9c98ae9dbd04c32690dce6325` | `a48df8fd8f0d38ace3a3ef0d0c46f9be58c721a6101e145d8f463cc413ed2b38` |
| `tests/test_match_chunking.py` | `13a25a6900b0c59ac60ba74582829db12c76a1ed` | `c26c58e8e6accfdc18e40bfaeb90e4a40a873938b4a059f044625ffedc0c1344` |
| `tests/test_match_contracts.py` | `4098e5a0b1d781ca64563403b3fe36fcbae4de4c` | `6a7ac61f61b35d481d859e0e06d36f4428ffca8d20cf1a7f54837581e4cacbca` |
| `tests/test_match_extraction.py` | `11d763cc3201999ee4c1021b61dbbacc4c585a13` | `755970208291ad7381a1fc6113498320c4517c6697fe00a5750ea6c299691755` |
| `tests/test_match_normalization.py` | `e3ffc73e58bb6d66f8fd241b68188ee721bd624f` | `0bc396ab35dda3699d8c088d3985d611b0bfe987f673e8149a9efe91ed55de87` |
| `tests/test_match_pipeline.py` | `95ad25910ccbb7bbc8c435d9dad0a4973220b82c` | `bc2e50aa8e6dc3f6e9409bb6d78c34cc04610dbf508669e5608da05aee66a0bf` |
| `tests/test_match_ranking.py` | `32a8c6b3ab41ecdb08bef0bccc36bf6483a09ee7` | `13dd2335f5a0369baff52afdc08cd51530c51ece9832e689c487693915dfce29` |
| `tests/test_match_scoring.py` | `457d514eb41140c1d380d0c093951cde40889223` | `0021c53b4a6116078944a2ae409b0f88105fe5a3a592a7559b81d5dd10e36bba` |
| `tests/test_match_snapshots.py` | `2aa4f260a87836c136cd29c7145cbcd75753c263` | `ed8a28e24d3a5915c474dc9d358838f41ca8d781688c982101479ddaadb3232b` |
| `tests/test_matching_metadata_claims.py` | `52e4500bb81b16d759dcfa66a3ad3d62d473768e` | `08e61bfd7788f458c2c7336b11bebbbc5f7e8468f272ef454475ae8adeebe884` |
| `tests/test_pinned_transport.py` | `4e778d5af613a22b7f3e5869d2f648b4e7895b08` | `f05bd0b9a031644648598d8fee522b0eae500fb99f8e679fed34ba73dd17d233` |

## Task 10 boundary

This resolves source **content** provenance. It does not complete browser verification, unseen-document accuracy, release activation or the final Task 10 handoff. Original raw bytes for 11 files remain unavailable; future content audits should compare canonical Git blob hashes rather than historical working-copy hashes.
