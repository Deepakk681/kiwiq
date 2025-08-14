### User App Resume Metadata – Frontend Integration Guide

This guide explains how to integrate the User App Resume Metadata service from the frontend. It is written for frontend engineers who do not have access to backend code and need a clear, self-contained reference for endpoints, headers, request/response shapes, constraints, and practical usage patterns. It also covers how this feature relates to Assets.

This functionality lives under the workflow service and is mounted at the API prefix `/api/v1`.
Path roots from code:
- API prefix is defined in `services/kiwi_app/settings.py` as `API_V1_PREFIX = "/api/v1"` and applied in `services/kiwi_app/main.py` via `app.include_router(..., prefix=settings.API_V1_PREFIX)`.
- Route bases are declared in `services/kiwi_app/workflow_app/routes.py`:
  - `user_app_resume_router = APIRouter(prefix="/user-app-resume")`
  - `asset_router = APIRouter(prefix="/assets")`

### Quick TL;DR

- **Base URL (User Resume)**: `/api/v1/user-app-resume`
- **Base URL (Assets)**: `/api/v1/assets`
- **Auth**: Bearer token in `Authorization: Bearer <token>`
- **Org context (required)**: `X-Active-Org: <org-uuid>` header
- **Core identifiers (choose at least one)**: `workflow_name` | `asset_id` | `entity_tag` | `frontend_stage`
- **Data fields (provide at least one)**: `run_id` | `app_metadata`
- **CRUD**:
  - Create: `POST /` → returns the record
  - Get: `GET /{metadata_id}` → returns the record
  - Update (partial): `PATCH /{metadata_id}` → returns updated record
  - Delete: `DELETE /{metadata_id}` → 204 No Content
  - List (filtered): `GET /?query...` → returns an array

### Endpoint summary table (global overview)

| No. | Category | Method & Path | What it does | Auth/Perm | Required headers | Request body | Response |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [1](#1-create-metadata) | User Resume (Write) | [POST `/api/v1/user-app-resume/`](#1-create-metadata) | Create a resume record for the current user within the active org. Includes flexible `app_metadata` and optional `run_id`. | `Authorization: Bearer` + `ORG_DATA_WRITE` | `X-Active-Org` | `UserAppResumeMetadataCreate` | `200` `UserAppResumeMetadataRead` | 
| [2](#2-get-by-id) | User Resume (Read) | [GET `/api/v1/user-app-resume/{metadata_id}`](#2-get-by-id) | Fetch a single record by ID. Must belong to the caller unless superuser. | `Authorization: Bearer` + `ORG_DATA_READ` | `X-Active-Org` | N/A | `200` `UserAppResumeMetadataRead` |
| [3](#3-update-partial) | User Resume (Write) | [PATCH `/api/v1/user-app-resume/{metadata_id}`](#3-update-partial) | Partial update; backend enforces identifier/data constraints after merge. | `Authorization: Bearer` + `ORG_DATA_WRITE` | `X-Active-Org` | `UserAppResumeMetadataUpdate` | `200` `UserAppResumeMetadataRead` |
| [4](#4-delete) | User Resume (Write) | [DELETE `/api/v1/user-app-resume/{metadata_id}`](#4-delete) | Delete a record (e.g., when draft is published). | `Authorization: Bearer` + `ORG_DATA_WRITE` | `X-Active-Org` | N/A | `204 No Content` |
| [5](#5-list-filterable) | User Resume (Read) | [GET `/api/v1/user-app-resume/`](#5-list-filterable) | List records with filters (`workflow_name`, `asset_id`, `entity_tag`, `frontend_stage`, `run_id`). Superusers can target `org_id`/`user_id`. | `Authorization: Bearer` + `ORG_DATA_READ` | `X-Active-Org` | Query params | `200` `UserAppResumeMetadataRead[]` |
| [6](#6-assets-types-list) | Assets (Read) | [GET `/api/v1/assets/types`](#6-assets-types-list) | List supported asset types and their app_data schemas. Use to build UI forms. | `Authorization: Bearer` (verified user) | — | N/A | `200` `AssetTypeInfo[]` |
| [7](#7-assets-type-info) | Assets (Read) | [GET `/api/v1/assets/types/{asset_type}`](#7-assets-type-info) | Fetch schema/info for a specific asset type. | `Authorization: Bearer` (verified user) | — | N/A | `200` `AssetTypeInfo` |
| [8](#8-create-asset) | Assets (Write) | [POST `/api/v1/assets/`](#8-create-asset) | Create an asset (e.g., `blog_url`, `linkedin_profile`) optionally with `app_data`. | `Authorization: Bearer` + `ORG_DATA_WRITE` | `X-Active-Org` | `AssetCreate` | `200` `AssetRead` |
| [9](#9-get-asset) | Assets (Read) | [GET `/api/v1/assets/{asset_id}`](#9-get-asset) | Get a single asset. | `Authorization: Bearer` + `ORG_DATA_READ` | `X-Active-Org` | Query (`app_data_fields` optional) | `200` `AssetRead` |
| [10](#10-update-asset) | Assets (Write) | [PATCH `/api/v1/assets/{asset_id}`](#10-update-asset) | Update basic asset fields or full `app_data`. | `Authorization: Bearer` + `ORG_DATA_WRITE` | `X-Active-Org` | `AssetUpdate` | `200` `AssetRead` |
| [11](#11-update-asset-app-data) | Assets (Write) | [PATCH `/api/v1/assets/{asset_id}/app-data`](#11-update-asset-app-data) | Targeted app_data update with operation (`add_or_update`, `delete`, `replace`). | `Authorization: Bearer` + `ORG_DATA_WRITE` | `X-Active-Org` | `AssetAppDataUpdate` | `200` `AssetRead` |
| [12](#12-increment-asset-app-data) | Assets (Write) | [PATCH `/api/v1/assets/{asset_id}/app-data/increment`](#12-increment-asset-app-data) | Atomic increment of numeric app_data field. | `Authorization: Bearer` + `ORG_DATA_WRITE` | `X-Active-Org` | `AssetAppDataIncrement` | `200` `AssetRead` |
| [13](#13-deactivate-asset) | Assets (Write) | [POST `/api/v1/assets/{asset_id}/deactivate`](#13-deactivate-asset) | Soft-deactivate an asset. | `Authorization: Bearer` + `ORG_DATA_WRITE` | `X-Active-Org` | N/A | `200` `AssetRead` |
| [14](#14-list-managed-assets) | Assets (Read) | [GET `/api/v1/assets/managed`](#14-list-managed-assets) | List assets managed by the current user (optionally across orgs). | `Authorization: Bearer` + `ORG_DATA_READ` | `X-Active-Org` | Query | `200` `AssetRead[]` |
| [15](#15-list-all-org-assets) | Assets (Read) | [GET `/api/v1/assets/org/all`](#15-list-all-org-assets) | List all assets for the active org (requires write perm). | `Authorization: Bearer` + `ORG_DATA_WRITE` | `X-Active-Org` | Query | `200` `AssetRead[]` |
| [16](#16-list-accessible-assets) | Assets (Read) | [GET `/api/v1/assets/`](#16-list-accessible-assets) | List accessible assets for the user in the active org. | `Authorization: Bearer` + `ORG_DATA_READ` | `X-Active-Org` | Query | `200` `AssetRead[]` |

Quick links:
- User Resume: [1) Create `/api/v1/user-app-resume/`](#1-create-metadata) • [2) Get `/api/v1/user-app-resume/{metadata_id}`](#2-get-by-id) • [3) Update `/api/v1/user-app-resume/{metadata_id}`](#3-update-partial) • [4) Delete `/api/v1/user-app-resume/{metadata_id}`](#4-delete) • [5) List `/api/v1/user-app-resume/`](#5-list-filterable)
- Assets: [6) `/api/v1/assets/types`](#6-assets-types-list) • [7) `/api/v1/assets/types/{asset_type}`](#7-assets-type-info) • [8) `/api/v1/assets/`](#8-create-asset) • [9) `/api/v1/assets/{asset_id}`](#9-get-asset) • [10) `/api/v1/assets/{asset_id}`](#10-update-asset) • [11) `/api/v1/assets/{asset_id}/app-data`](#11-update-asset-app-data) • [12) `/api/v1/assets/{asset_id}/app-data/increment`](#12-increment-asset-app-data) • [13) `/api/v1/assets/{asset_id}/deactivate`](#13-deactivate-asset) • [14) `/api/v1/assets/managed`](#14-list-managed-assets) • [15) `/api/v1/assets/org/all`](#15-list-all-org-assets) • [16) `/api/v1/assets/`](#16-list-accessible-assets)

### Why this exists (philosophy)

User App Resume Metadata stores lightweight durable state so your app can resume a workflow or UI flow where the user left off. Think of it as a small, indexed bookmark pointing to a workflow run (`run_id`) and UI state (`app_metadata`). It intentionally keeps the schema minimal and flexible so feature teams can evolve the UI without heavy backend migrations.

Key principles:

- **Minimal but structured**: You must supply at least one identifier and one data field (details below). Beyond that, `app_metadata` is free-form JSON.
- **Organization scoped**: Requests require an organization context using `X-Active-Org`.
- **Safe partial updates**: Updates are partial; backend ensures final state still respects constraints. Concurrent updates are protected via distributed locks when available.
- **First-class relation to Assets**: You can link records to an `asset_id` for content-centric resumes (e.g., resume work on a specific blog URL or LinkedIn profile).

### Common headers and auth

- `Authorization: Bearer <token>`
- `X-Active-Org: <org-uuid>`

If the header is missing or invalid, the server returns `400`. Your token must grant appropriate permissions:

- Read endpoints require `ORG_DATA_READ`.
- Write endpoints require `ORG_DATA_WRITE`.

Superusers may pass special fields as noted below.

### Schemas

Record payload fields (create/update) use the following shapes. Types shown for clarity; everything except constraints is straightforward JSON.

```json
// UserAppResumeMetadataCreate (request body for POST /)
{
  "workflow_name": "string | null",
  "asset_id": "uuid | null",
  "entity_tag": "string | null",
  "frontend_stage": "string | null",
  "run_id": "uuid | null",
  "app_metadata": { "any": "json" } | null,

  // Superuser-only optional targeting
  "org_id": "uuid | null",
  "on_behalf_of_user_id": "uuid | null"
}
```

Constraints for create:
- Provide at least one identifier: one of `workflow_name`, `asset_id`, `entity_tag`, `frontend_stage`.
- Provide at least one data field: one of `run_id`, `app_metadata`.

```json
// UserAppResumeMetadataUpdate (request body for PATCH /{id}) – all fields optional
{
  "workflow_name": "string | null",
  "asset_id": "uuid | null",
  "entity_tag": "string | null",
  "frontend_stage": "string | null",
  "run_id": "uuid | null",
  "app_metadata": { "any": "json" } | null
}
```

Constraints for update:
- Partial updates are allowed, but the resulting record must still satisfy the same creation constraints. If not, the backend returns `400`.

```json
// UserAppResumeMetadataRead (response shape)
{
  "id": "uuid",
  "org_id": "uuid",
  "user_id": "uuid",
  "workflow_name": "string | null",
  "asset_id": "uuid | null",
  "entity_tag": "string | null",
  "frontend_stage": "string | null",
  "run_id": "uuid | null",
  "app_metadata": { "any": "json" } | null,
  "created_at": "ISO8601 datetime",
  "updated_at": "ISO8601 datetime"
}
```

```json
// List query (as URL query params)
{
  "workflow_name": "string | null",
  "asset_id": "uuid | null",
  "entity_tag": "string | null",
  "frontend_stage": "string | null",
  "run_id": "uuid | null",
  "user_id": "uuid | superuser only",
  "org_id": "uuid | superuser only",
  "skip": 0,
  "limit": 100
}
```

### User App Resume Endpoints (with TL;DR and examples)

All endpoints below show full routes with `/api/v1` prefix.

### Endpoint summary table

| No. | Category | Method & Path | What it does | Auth/Perm | Required headers | Request body | Response |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Write | POST `/` | Create a resume record for the current user within the active org. Includes flexible `app_metadata` and optional `run_id`. | `Authorization: Bearer` + `ORG_DATA_WRITE` | `X-Active-Org` | `UserAppResumeMetadataCreate` | `200` `UserAppResumeMetadataRead` | 
| 2 | Read | GET `/{metadata_id}` | Fetch a single record by ID. Must belong to the caller unless superuser; returns the stored identifiers and data. | `Authorization: Bearer` + `ORG_DATA_READ` | `X-Active-Org` | N/A | `200` `UserAppResumeMetadataRead` |
| 3 | Write | PATCH `/{metadata_id}` | Partial update of a record; backend enforces identifier/data constraints post-merge. Safe for iterative UI saves. | `Authorization: Bearer` + `ORG_DATA_WRITE` | `X-Active-Org` | `UserAppResumeMetadataUpdate` | `200` `UserAppResumeMetadataRead` |
| 4 | Write | DELETE `/{metadata_id}` | Delete a record (e.g., when draft is published or discarded). No body required. | `Authorization: Bearer` + `ORG_DATA_WRITE` | `X-Active-Org` | N/A | `204 No Content` |
| 5 | Read | GET `/` | List records with filters (`workflow_name`, `asset_id`, `entity_tag`, `frontend_stage`, `run_id`). Superusers can target `org_id`/`user_id`. | `Authorization: Bearer` + `ORG_DATA_READ` | `X-Active-Org` | Query params | `200` `UserAppResumeMetadataRead[]` |

Quick links: [1) Create](#1-create-metadata) • [2) Get by ID](#2-get-by-id) • [3) Update](#3-update-partial) • [4) Delete](#4-delete) • [5) List](#5-list-filterable)

#### 1) Create metadata

 - Method: `POST /api/v1/user-app-resume/`
- TL;DR: Create a resume record for the current user in the active org.
- Permissions: `ORG_DATA_WRITE`
- Superuser options: can set `org_id` and `on_behalf_of_user_id` in the body.

Example request:
```bash
curl -X POST \
  "$API_BASE/api/v1/user-app-resume/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Active-Org: $ORG_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_name": "content_studio",
    "entity_tag": "draft-42",
    "run_id": "7a6c2d9a-63e1-47b3-b3f1-2b7b3c5a7b2c",
    "app_metadata": {"step": "writing", "draftTitle": "SEO plan"}
  }'
```

Response: `200` with `UserAppResumeMetadataRead` body.

Common errors:
- `400` if required constraints are not met or `X-Active-Org` invalid/missing.
- `403` if lacking `ORG_DATA_WRITE`.

Use cases:
- Start a flow: as soon as a user begins an operation, create a record with early `app_metadata`.
- Attach to an asset: include `asset_id` so you can resume per specific content.

#### 2) Get by ID

 - Method: `GET /api/v1/user-app-resume/{metadata_id}`
- TL;DR: Fetch a single record by ID (must belong to the current user unless superuser).
- Permissions: `ORG_DATA_READ`

Example:
```bash
curl -X GET \
  "$API_BASE/api/v1/user-app-resume/$METADATA_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Active-Org: $ORG_ID"
```

Response: `200` with `UserAppResumeMetadataRead`.

Errors: `404` if not found; `403` if access denied.

#### 3) Update (partial)

 - Method: `PATCH /api/v1/user-app-resume/{metadata_id}`
- TL;DR: Partial update; backend ensures final state still satisfies constraints.
- Permissions: `ORG_DATA_WRITE`

Example:
```bash
curl -X PATCH \
  "$API_BASE/api/v1/user-app-resume/$METADATA_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Active-Org: $ORG_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "app_metadata": {"step": "review", "notes": "needs examples"}
  }'
```

Response: `200` with updated `UserAppResumeMetadataRead`.

Concurrency note: updates are protected with a distributed lock when available; prefer small, idempotent updates.

#### 4) Delete

 - Method: `DELETE /api/v1/user-app-resume/{metadata_id}`
- TL;DR: Delete a record.
- Permissions: `ORG_DATA_WRITE`

Example:
```bash
curl -X DELETE \
  "$API_BASE/api/v1/user-app-resume/$METADATA_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Active-Org: $ORG_ID"
```

Response: `204 No Content`.

Errors: `404` if not found; `403` if access denied.

#### 5) List (filterable)

 - Method: `GET /api/v1/user-app-resume/`
- TL;DR: Query by identifiers to fetch relevant records for the current user in the active org.
- Permissions: `ORG_DATA_READ`
- Superuser: can additionally pass `org_id` and `user_id` as query params to target others.

Example (by workflow and tag):
```bash
curl -G \
  "$API_BASE/api/v1/user-app-resume/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Active-Org: $ORG_ID" \
  --data-urlencode "workflow_name=content_studio" \
  --data-urlencode "entity_tag=draft-42" \
  --data-urlencode "skip=0" \
  --data-urlencode "limit=20"
```

Response: `200` with `UserAppResumeMetadataRead[]`.

### Assets Endpoints (with TL;DR and examples)

All endpoints below show full routes with `/api/v1` prefix.

#### 6) Assets: Types (list)

- Method: `GET /api/v1/assets/types`
- TL;DR: Lists supported asset types with optional JSON schemas so you can build UI forms.

Example:
```bash
curl -X GET \
  "$API_BASE/api/v1/assets/types" \
  -H "Authorization: Bearer $TOKEN"
```

Response: `200` with `AssetTypeInfo[]`.

#### 7) Assets: Type info

- Method: `GET /api/v1/assets/types/{asset_type}`
- TL;DR: Fetch schema/info for a specific asset type (e.g., `blog_url`, `linkedin_profile`).

Example:
```bash
curl -X GET \
  "$API_BASE/api/v1/assets/types/blog_url" \
  -H "Authorization: Bearer $TOKEN"
```

Response: `200` with `AssetTypeInfo`.

#### 8) Create asset

- Method: `POST /api/v1/assets/`
- TL;DR: Create a new asset for the active org; `app_data` is validated per asset type schema when provided.
- Permissions: `ORG_DATA_WRITE`; Header: `X-Active-Org`

Example:
```bash
curl -X POST \
  "$API_BASE/api/v1/assets/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Active-Org: $ORG_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "asset_type": "blog_url",
    "asset_name": "example.com/post-123",
    "is_shared": true,
    "app_data": {"blog_url": "https://example.com/post-123"}
  }'
```

Response: `200` with `AssetRead`.

#### 9) Get asset

- Method: `GET /api/v1/assets/{asset_id}`
- TL;DR: Read an asset by ID; optionally include only specific `app_data_fields` in the response.
- Permissions: `ORG_DATA_READ`; Header: `X-Active-Org`

Example:
```bash
curl -X GET \
  "$API_BASE/api/v1/assets/$ASSET_ID?app_data_fields=blog_url" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Active-Org: $ORG_ID"
```

Response: `200` with `AssetRead`.

#### 10) Update asset

- Method: `PATCH /api/v1/assets/{asset_id}`
- TL;DR: Partial update of asset fields or full app_data replacement; prefer this for name/shared/active toggles.
- Permissions: `ORG_DATA_WRITE`; Header: `X-Active-Org`

Example:
```bash
curl -X PATCH \
  "$API_BASE/api/v1/assets/$ASSET_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Active-Org: $ORG_ID" \
  -H "Content-Type: application/json" \
  -d '{"is_active": false}'
```

Response: `200` with `AssetRead`.

#### 11) Update asset app-data

- Method: `PATCH /api/v1/assets/{asset_id}/app-data`
- TL;DR: Targeted app_data update with `operation` in `{add_or_update|delete|replace}` and optional `path`.
- Permissions: `ORG_DATA_WRITE`; Header: `X-Active-Org`

Example:
```bash
curl -X PATCH \
  "$API_BASE/api/v1/assets/$ASSET_ID/app-data" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Active-Org: $ORG_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "add_or_update",
    "path": ["notes"],
    "value": "Track weekly"
  }'
```

Response: `200` with `AssetRead`.

#### 12) Increment asset app-data

- Method: `PATCH /api/v1/assets/{asset_id}/app-data/increment`
- TL;DR: Atomically increments a numeric field in `app_data` at `path`.
- Permissions: `ORG_DATA_WRITE`; Header: `X-Active-Org`

Example:
```bash
curl -X PATCH \
  "$API_BASE/api/v1/assets/$ASSET_ID/app-data/increment" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Active-Org: $ORG_ID" \
  -H "Content-Type: application/json" \
  -d '{"path": ["counters", "views"], "increment": 1}'
```

Response: `200` with `AssetRead`.

#### 13) Deactivate asset

- Method: `POST /api/v1/assets/{asset_id}/deactivate`
- TL;DR: Soft-deactivates an asset without deleting; useful for temporary suspensions.
- Permissions: `ORG_DATA_WRITE`; Header: `X-Active-Org`

Example:
```bash
curl -X POST \
  "$API_BASE/api/v1/assets/$ASSET_ID/deactivate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Active-Org: $ORG_ID"
```

Response: `200` with `AssetRead`.

#### 14) List managed assets

- Method: `GET /api/v1/assets/managed`
- TL;DR: Assets where the current user is the managing user; filter/sort/paginate supported.
- Permissions: `ORG_DATA_READ`; Header: `X-Active-Org`

Example:
```bash
curl -G \
  "$API_BASE/api/v1/assets/managed" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Active-Org: $ORG_ID" \
  --data-urlencode "managed_only=true" \
  --data-urlencode "asset_type=blog_url"
```

Response: `200` with `AssetRead[]`.

#### 15) List all org assets

- Method: `GET /api/v1/assets/org/all`
- TL;DR: List all assets for the active org (admin/manager view). Requires write permission by design.
- Permissions: `ORG_DATA_WRITE`; Header: `X-Active-Org`

Example:
```bash
curl -G \
  "$API_BASE/api/v1/assets/org/all" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Active-Org: $ORG_ID" \
  --data-urlencode "asset_type=linkedin_profile"
```

Response: `200` with `AssetRead[]`.

#### 16) List accessible assets

- Method: `GET /api/v1/assets/`
- TL;DR: List assets the user can access in the active org; supports filters and field selection.
- Permissions: `ORG_DATA_READ`; Header: `X-Active-Org`

Example:
```bash
curl -G \
  "$API_BASE/api/v1/assets/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Active-Org: $ORG_ID" \
  --data-urlencode "asset_type=blog_url" \
  --data-urlencode "is_active=true" \
  --data-urlencode "app_data_fields=blog_url"
```

Response: `200` with `AssetRead[]`.

### Practical integration patterns

- **Per-workflow resume**: Use `workflow_name` + `entity_tag` to group user drafts. Store UI fields in `app_metadata` and the backend run in `run_id`.
- **Per-asset resume**: Link to an `asset_id` (e.g., blog URL or LinkedIn profile). Query by `asset_id` to show the last state for that asset.
- **Frontend steps**: Use `frontend_stage` to encode the current step or screen. This helps listing and filtering quickly.
- **Stable keys**: Prefer a stable `entity_tag` (like a client-generated UUID per draft) so you can create/update/list consistently even before you have an `asset_id`.
- **One record vs many**: You may create multiple records for different drafts. If you want a single, latest record per tag, either overwrite by update or list with sorting client-side and pick the newest.

### Relation to Assets

Assets represent managed targets (e.g., `blog_url`, `linkedin_profile`) and live under `/api/v1/assets`.

Common endpoints you might use alongside resume metadata:

- `GET /api/v1/assets/{asset_id}` – fetch an asset before resuming
- `GET /api/v1/assets?managed_only=true&asset_type=blog_url` – show a list for the user to pick

When creating resume metadata linked to content, include the `asset_id` so you can list or fetch by it later. See Asset schemas in your API reference; a minimal example response looks like:

```json
{
  "id": "uuid",
  "org_id": "uuid",
  "managing_user_id": "uuid",
  "asset_type": "blog_url | linkedin_profile",
  "asset_name": "string",
  "is_shared": true,
  "is_active": true,
  "app_data": {"blog_url": "https://example.com/post"},
  "created_at": "ISO8601",
  "updated_at": "ISO8601"
}
```

### Frontend examples (TypeScript fetch)

```ts
async function createResume(
  baseUrl: string,
  token: string,
  orgId: string,
  payload: {
    workflow_name?: string;
    asset_id?: string;
    entity_tag?: string;
    frontend_stage?: string;
    run_id?: string;
    app_metadata?: unknown;
  }
) {
  const res = await fetch(`${baseUrl}/api/v1/user-app-resume/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'X-Active-Org': orgId,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error(`Create failed: ${res.status}`);
  return res.json();
}
```

```ts
async function listResumes(
  baseUrl: string,
  token: string,
  orgId: string,
  query: Record<string, string | number | boolean | undefined>
) {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(query)) if (v !== undefined) q.set(k, String(v));
  const res = await fetch(`${baseUrl}/api/v1/user-app-resume/?${q.toString()}`, {
    headers: { 'Authorization': `Bearer ${token}`, 'X-Active-Org': orgId }
  });
  if (!res.ok) throw new Error(`List failed: ${res.status}`);
  return res.json();
}
```

### Status codes and errors

- `200 OK`: Successful read or update
- `201 Created`: Not used here; create returns `200` with object
- `204 No Content`: Successful delete
- `400 Bad Request`: Invalid header, invalid UUIDs, or schema constraint violations
- `403 Forbidden`: Missing required permissions
- `404 Not Found`: Resource does not exist or not accessible

### Caveats and best practices

- Always set `X-Active-Org`. Missing header results in `400` for operations that require it.
- Maintain the identifier/data constraints across updates; otherwise updates will fail.
- Keep `app_metadata` small but sufficient; this feature is not a file store. For large data blobs, store them elsewhere and reference them.
- Use stable identifiers (`entity_tag`, `asset_id`) to avoid duplicate records and simplify list queries.
- Handle concurrency gracefully. If multiple tabs update the same record, last write wins; the backend uses a distributed lock where possible to reduce races.

### Putting it all together

1) User picks an asset (or creates a draft). You either already have an `asset_id` or generate a client `entity_tag`.
2) Create a resume record (`POST /`) with `workflow_name`, your identifier (`asset_id` or `entity_tag`), and initial `app_metadata`.
3) As the user progresses through steps, `PATCH /{id}` with updated `frontend_stage`, `app_metadata`, and/or `run_id` when a backend workflow starts.
4) To resume later, `GET /?workflow_name=...&entity_tag=...` (or `asset_id=...`) then restore the UI from `app_metadata` and route to the `run_id` if applicable.
5) Delete (`DELETE /{id}`) when a draft is published or no longer needed.

This guide is based on the following backend components: `services/kiwi_app/workflow_app/routes.py`, `services/kiwi_app/workflow_app/services.py`, and `services/kiwi_app/workflow_app/schemas.py`.


