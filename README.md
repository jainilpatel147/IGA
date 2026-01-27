# IGA Platform - Real Adoption Guide

## Architecture Overview

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│   Application   │◀───────▶│  IGA Platform   │───────▶│   GRC System    │
│   (Governed)    │ Access  │   (Authority)   │Evidence│   (Consumer)    │
└─────────────────┘         └─────────────────┘         └─────────────────┘
        │                           │                           │
   WRITE Access              Tracks Access               READ ONLY
   (provisioning)            (audit + evidence)          (compliance)
```

---

## User Roles

| Role | Purpose | Access |
|------|---------|--------|
| **admin** | Full platform control | All pages, manage apps & users |
| **compliance** | Governance oversight | Access reviews, evidence, compliance |
| **auditor** | Read-only audit | Audit logs, evidence (no changes) |
| **reviewer** | Approve requests | Access request queue only |
| **user** | Standard employee | My Access, request new access |

---

## Login Credentials

| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | Admin |
| compliance | comp123 | Compliance |
| auditor | audit123 | Auditor |
| reviewer | review123 | Reviewer |
| user | user123 | User |

---

## IGA → Application Flow

1. **Register Application** (Admin)
   - Add to Application Registry
   - Define entitlements with risk levels

2. **Request Access** (User)
   - User selects application + entitlement
   - Creates access request

3. **Approve Request** (Reviewer)
   - Review and approve/reject
   - Generates audit event

4. **Provision Access** (System)
   - Creates ApplicationAssignment
   - Generates `ACCESS_GRANTED` evidence
   - (Future: calls external API)

5. **Revoke Access** (Admin/Compliance)
   - Removes assignment
   - Generates `ACCESS_REVOKED` evidence

---

## GRC Integration

### Endpoints (Read-Only)

```
GET /grc/evidence         # All governance evidence
GET /grc/access-summary   # Access by application
GET /grc/approvals        # Approval records
GET /grc/violations       # Policy violations
GET /grc/controls         # Control mappings
```

### Evidence Types

- `ACCESS_GRANTED` - Access provisioned
- `ACCESS_REVOKED` - Access removed
- `APPROVAL_RECORDED` - Request decision
- `POLICY_VIOLATION` - Compliance issue

### Consuming Evidence

```python
# Example: GRC fetching evidence
import requests

response = requests.get(
    "http://localhost:8000/grc/evidence",
    headers={"Authorization": "Bearer <token>"}
)
evidence = response.json()
```

---

## Quick Start

1. **Start Backend**
   ```bash
   cd backend
   venv\Scripts\activate
   python -m uvicorn app.main:app --reload
   ```

2. **Seed Sample Data**
   ```bash
   python -m app.seed_data
   ```

3. **Start Frontend**
   ```bash
   cd frontend
   npm run dev
   ```

4. **Login** at http://localhost:5173
   - Use `admin` / `admin123` for full access
   - Try different roles to see filtered views
