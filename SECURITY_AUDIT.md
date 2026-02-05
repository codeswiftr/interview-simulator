# Dependency Security Audit — interview-simulator

Date: 2026-02-05

## Scope
- Frontend (Node): `codeswiftr-com/interview-simulator/package.json`
- Backend (Python): `codeswiftr-com/interview-simulator/backend/pyproject.toml`

## Tools & Commands Run
- `npm audit --json`
- `npm outdated --json`
- `python -m pip_audit codeswiftr-com/interview-simulator/backend --locked -f json` (failed; uv.lock not recognized)
- `python -m pip_audit codeswiftr-com/interview-simulator/backend -f json` (failed; ensurepip crash)

## Findings

### 1) Security Vulnerabilities (Frontend — npm audit)
**Summary:** 3 total vulnerabilities (2 high, 1 moderate)

**a) preact — High**
- Advisory: GHSA-36hm-qxxp-pg3m (JSON VNode Injection)
- Affected range: `>=10.28.0 <10.28.2`
- Fix available: Yes
- Direct? No (transitive)

**b) react-router — High + Moderate**
- Advisory: GHSA-h5cw-625j-3rxh (CSRF issue)
- Advisory: GHSA-2w69-qvjg-hvjx (Open Redirect → XSS)
- Advisory: GHSA-8v8x-cx79-35w7 (SSR XSS in ScrollRestoration)
- Affected range: `>=7.0.0 <=7.11.0` (and `<7.12.0` for SSR XSS)
- Fix available: Yes
- Direct? No (via `react-router-dom`)

**c) react-router-dom — Moderate (via react-router)**
- Affected range: `7.0.0-pre.0 - 7.11.0`
- Fix available: Yes
- Direct? Yes

**Recommended Action:** Update `react-router-dom` to `>=7.13.0` (latest per `npm outdated`) to pull patched `react-router`.

### 2) Outdated Packages (Frontend — npm outdated)
`npm outdated --json` indicates available updates; notable:
- `lucide-react`: wanted `0.555.0` → latest `0.563.0`

Most other listed packages show `wanted == latest` (already up to date per npm). Consider updating `lucide-react` as part of routine maintenance.

### 3) Backend Vulnerability Audit (Python)
**Status:** Not completed due to tooling issues.
- `pip-audit --locked` could not detect `uv.lock`.
- `pip-audit` on project path failed due to `ensurepip` crash while creating a venv.

**Recommended Action:**
- Either convert `backend/uv.lock` to a pip-audit compatible lock (e.g., `requirements.txt` with pins), or
- Run `pip-audit` inside a working Python environment that can create venvs.

### 4) License Compliance
- **Repo root:** No top-level `LICENSE` file found.
- **Backend:** `pyproject.toml` declares `MIT` license.
- **Frontend deps:** License compliance not verified (no `node_modules` license inventory available).

**Recommended Action:**
- Add a top-level `LICENSE` file if required for distribution.
- Run a license inventory tool (e.g., `npx license-checker`) after installing dependencies.

## Summary & Risk
- **Frontend:** 3 known vulnerabilities with fixes available. Priority is upgrading `react-router-dom` to pull patched `react-router`.
- **Backend:** Vulnerability status unknown (tooling failure); requires follow-up.
- **Licensing:** Repo-level license missing; dependency license compliance unverified.

## Suggested Remediation Plan
1. Update `react-router-dom` to `>=7.13.0` and re-run `npm audit`.
2. Update `preact` transitive dependency (via primary dependency update chain) or force a resolution if needed.
3. Resolve Python audit by generating a pip-compatible lock or ensuring `pip-audit` can create a venv.
4. Add/confirm project-level LICENSE and run dependency license scan.

---

### Raw Audit Notes
- `npm audit` found: preact (high), react-router (high/moderate), react-router-dom (moderate).
- `npm outdated` shows `lucide-react` update available.
- `pip-audit` failed due to missing lock support and `ensurepip` failure.
