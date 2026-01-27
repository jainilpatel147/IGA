# IGA Platform - Real Adoption Guide

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        IGA Platform                             │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────────────┐   │
│  │   Identity  │   │   Access    │   │   Governance        │   │
│  │  Management │   │   Requests  │   │   Evidence          │   │
│  └─────────────┘   └─────────────┘   └─────────────────────┘   │
│                                              ▲                  │
│  Roles: admin, user                          │ API              │
└──────────────────────────────────────────────┼──────────────────┘
                                               │
                    ┌──────────────────────────┼──────────────────┐
                    │         GRC Platform     │                  │
                    │   (Registered as App)    ▼                  │
                    │  ┌────────────────────────────────────┐     │
                    │  │  Entitlements (IGA-managed):       │     │
                    │  │  • Compliance Officer              │     │
                    │  │  • Auditor                         │     │
                    │  │  • Reviewer                        │     │
                    │  └────────────────────────────────────┘     │
                    │  Consumes: /grc/evidence, /grc/approvals   │
                    └─────────────────────────────────────────────┘
```

---

## IGA Roles (Simple)

| Role | Purpose |
|------|---------|
| **admin** | Full IGA management - apps, identities, connectors |
| **user** | Request access, view own access |

---

## GRC as an Application

GRC is registered as an **application** in IGA with these entitlements:

| Entitlement | Purpose |
|-------------|---------|
| **Compliance Officer** | Full GRC access, manage reviews |
| **Auditor** | Read-only evidence/reports |
| **Reviewer** | Approve access within GRC |
| **Viewer** | Basic dashboard access |

Users request access to GRC via IGA, which provisions entitlements.

---

## Login Credentials

| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | IGA Admin |
| user | user123 | Standard User |

---

## Flow: User Gets GRC Access

1. **User** logs into IGA as `user`
2. Goes to **Access Requests** → Requests `GRC Platform` + `Auditor` entitlement
3. **Admin** approves the request
4. IGA provisions the assignment → Generates `ACCESS_GRANTED` evidence
5. **GRC** reads `/grc/evidence` and knows user has auditor access

---

## GRC API Consumption

GRC consumes IGA's read-only APIs:

```bash
# Get all governance evidence
GET /grc/evidence

# Get access summary by application
GET /grc/access-summary

# Get approval records
GET /grc/approvals

# Get policy violations
GET /grc/violations

# Get control mappings
GET /grc/controls?framework=SOC2
```

---

## Quick Start

1. **Start Backend** (already running)
   ```bash
   cd backend
   venv\Scripts\python.exe -m uvicorn app.main:app --reload
   ```

2. **Start Frontend** (already running)
   ```bash
   cd frontend
   npm run dev
   ```

3. **Login** at http://localhost:5173
   - `admin` / `admin123` for full access
   - `user` / `user123` for user view

4. **Register GRC** (if not seeded)
   - Go to Applications → Register "GRC Platform"
   - Add entitlements: Compliance Officer, Auditor, Reviewer
