## Customer Data Service – Frontend Integration Guide

This guide explains how to use the Customer Data Service from a frontend client. It documents all public endpoints, the data model and pathing conventions, and best practices for choosing between versioned and unversioned documents. It is written for frontend developers who do not have access to backend code and need a clear, practical reference.

Notes:
- The overview table below shows full API paths including the API prefix and router prefix (e.g., `/api/v1/customer-data/...`).
- Detailed sections show method/path relative to the `customer-data` router for readability.
- The service automatically resolves the active organization and authenticated user from your auth session; you rarely pass `org_id` or `user_id` directly.
- The active organization is read from an "active org" header (e.g., `X-Active-Org`). Ensure your frontend sets this header to the current org UUID.

### Endpoints overview table

Quick, linked index of all endpoints. Click the number to jump to details.

| No. | Category | Method | Path | Summary | Notes |
| --- | --- | --- | --- | --- | --- |
| [01](#api-01) | Versioned | POST | `/api/v1/customer-data/versioned/{namespace}/{docname}` | Initialize a new versioned document with optional schema and initial data. | 409 if exists; prefer Upsert if existence uncertain. |
| [02](#api-02) | Versioned | PUT | `/api/v1/customer-data/versioned/{namespace}/{docname}` | Update active or specific version; merges JSON objects, replaces primitives. | Optional schema update before data write. |
| [03](#api-03) | Versioned | GET | `/api/v1/customer-data/versioned/{namespace}/{docname}` | Read active or specific version of a versioned document. | Requires `is_shared` query param. |
| [04](#api-04) | Versioned | DELETE | `/api/v1/customer-data/versioned/{namespace}/{docname}` | Delete the entire versioned document (all versions). | 204 on success. |
| [05](#api-05) | Versioned | GET | `/api/v1/customer-data/versioned/{namespace}/{docname}/versions` | List all versions with active flag, timestamps and edit counts. | Useful for version pickers. |
| [06](#api-06) | Versioned | POST | `/api/v1/customer-data/versioned/{namespace}/{docname}/versions` | Create a new named version (branch), optionally from another. | Does not switch active automatically. |
| [07](#api-07) | Versioned | POST | `/api/v1/customer-data/versioned/{namespace}/{docname}/active-version` | Set the active version to serve by default. | Promote tested versions. |
| [08](#api-08) | Versioned | GET | `/api/v1/customer-data/versioned/{namespace}/{docname}/history` | Get JSON Patch history for a version; supports limit and version filter. | Use for diffs/audit UI. |
| [09](#api-09) | Versioned | GET | `/api/v1/customer-data/versioned/{namespace}/{docname}/preview-restore/{sequence}` | Preview the document at a prior history sequence. | No mutation; safe preview. |
| [10](#api-10) | Versioned | POST | `/api/v1/customer-data/versioned/{namespace}/{docname}/restore` | Restore a versioned document to a historic sequence. | Mutates; consider confirming in UI. |
| [11](#api-11) | Versioned | GET | `/api/v1/customer-data/versioned/{namespace}/{docname}/schema` | Fetch the JSON Schema attached to a versioned document. | May be null if not set. |
| [12](#api-12) | Versioned | PUT | `/api/v1/customer-data/versioned/{namespace}/{docname}/schema` | Attach or update the JSON Schema template for a document. | Affects validation on subsequent writes. |
| [13](#api-13) | Versioned | POST | `/api/v1/customer-data/versioned/{namespace}/{docname}/upsert` | Create or update; auto-initializes or branches missing versions. | Recommended default for writes. |
| [14](#api-14) | Unversioned | PUT | `/api/v1/customer-data/unversioned/{namespace}/{docname}` | Upsert unversioned document; merges JSON objects, replaces primitives. | Optional schema validation via template. |
| [15](#api-15) | Unversioned | GET | `/api/v1/customer-data/unversioned/{namespace}/{docname}` | Read unversioned document data. | 400 if path is actually versioned. |
| [16](#api-16) | Unversioned | DELETE | `/api/v1/customer-data/unversioned/{namespace}/{docname}` | Delete unversioned document. | 204 on success. |
| [17](#api-17) | Listing/Meta | GET | `/api/v1/customer-data/list` | List documents accessible to the user with filters/sort. | Supports shared/user/system filters. |
| [18](#api-18) | Listing/Meta | POST | `/api/v1/customer-data/search` | Search by namespace pattern, text, and value filters. | Returns metadata + content subset. |
| [19](#api-19) | Listing/Meta | GET | `/api/v1/customer-data/metadata/{namespace}/{docname}` | Get metadata for a path (is_versioned, shared/system, etc.). | Use to decide versioned vs unversioned flows. |
| [20](#api-20) | Admin | DELETE | `/api/v1/customer-data/delete-by-pattern` | Delete multiple docs by wildcard patterns. | Superuser only; use `dry_run` first. |

---


### Core concepts (TL;DR)
- **Where data lives**: Documents are stored in MongoDB in a hierarchical path:
  - `[org_id_or_system, user_id_or_shared_placeholder, namespace, docname]`
  - For normal data: `org_id` and `user_id` are your current org and user.
  - For org-shared data: the user segment is a shared placeholder.
  - For system data: the org segment is a system placeholder; data can be shared or private.
- **Ownership**: Every document is owned by either an organization (org scope) or the platform (system scope).
- **Versioned vs Unversioned**:
  - Use **versioned** documents when you need named versions, active version switching, history, restore, and schema enforcement.
  - Use **unversioned** for simple, latest-only JSON objects with upserts/merges.
- **Permissions**:
  - Regular users can read/write within their org and user scope, and read/write shared org docs.
  - Superusers can act on behalf of a user (`on_behalf_of_user_id`) and access system entities.
  - Shared org docs are readable (and typically writable where allowed) by all members of the same org.
  - Some shared system docs are workflow-only and not exposed to regular users via the public API; superusers can perform full CRUD on system docs, including private system docs.
- **Schemas (JSON Schema)**: Versioned docs can attach/update a JSON Schema template; unversioned docs can validate against a template on write.
- **Naming**:
  - `namespace` groups related docs (e.g., `user_preferences`, `assets`, `workflow_runs`).
  - `docname` is the unique name/id within a namespace (e.g., `ui_theme`, `asset-<uuid>`).

### Pathing model
- Normal org/user document: `[org_id, user_id, namespace, docname]`
- Org-shared document: `[org_id, _shared_, namespace, docname]`
- System document (superuser only): `[_system_, _shared_|_private_, namespace, docname]`

The placeholders `_shared_`, `_private_`, and `_system_` are reserved identifiers handled by the backend (you don’t pass these directly; they derive from flags like `is_shared` and `is_system_entity`).

### Error model (common)
- 400 Bad Request: Validation errors (schema violations, invalid parameters)
- 403 Forbidden: Insufficient permissions (e.g., using `on_behalf_of_user_id` without superuser)
- 404 Not Found: Document or version not found
- 409 Conflict: Initialize attempted on a path that already exists
- 500 Internal Server Error: Unexpected server issue

---

## Choosing the right storage pattern

- Use **unversioned** when:
  - You only need the latest state (e.g., UI preferences, simple settings objects)
  - You want a lightweight upsert with partial merge of JSON objects

- Use **versioned** when:
  - You need named versions and a concept of an “active” version
  - You need full history, preview-restore, or time travel
  - You want to enforce/upgrade a JSON Schema over time

Integration tip: default to the versioned upsert endpoint for critical configs and content; use unversioned for user preferences and ephemeral UI state.

---

## Authentication and org context

- All endpoints require an authenticated user.
- The backend enforces the “active organization” using an `Active-Org-Id` header (name may be environment-specific). Your frontend must include this header with the current org UUID. You typically do not pass `org_id` in bodies.

---

 

## Versioned Documents

<a id="api-01"></a>
### 01. Initialize versioned document
- Method/Path: POST `/versioned/{namespace}/{docname}`
- Purpose: Create a new versioned document, optionally with schema and initial data.

#### TL;DR
- Creates the document at the path; fails with 409 if it exists.
- Optionally sets schema from a named template.

#### Request body
```json
{
  "is_shared": false,
  "initial_version": "default",
  "schema_template_name": "optional_schema_name",
  "schema_template_version": "optional_version",
  "initial_data": {},
  "is_complete": false,
  "is_system_entity": false,
  "on_behalf_of_user_id": null
}
```

Key fields:
- `is_shared`: true for org-shared, false for user-specific
- `is_system_entity`: superuser-only; stores under system scope
- `on_behalf_of_user_id`: superuser-only; for user-specific docs
- `initial_version`: defaults to `default`

#### Response
```json
{ "data": true }
```
Returns true on success.

#### Example (fetch)
```ts
await fetch(`${BASE}/versioned/user_profiles/john_doe`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ is_shared: false, initial_data: { bio: "Hi" } })
});
```

#### Caveats
- 409 if the path already exists.
- Use Upsert (below) when you don’t care if it exists.

---

<a id="api-02"></a>
### 02. Update versioned document
- Method/Path: PUT `/versioned/{namespace}/{docname}`
- Purpose: Update data for the active version or a specific version; optionally update schema first.

#### TL;DR
- Partial updates for JSON objects are merged; primitives are replaced.
- You can target a specific `version` or default to the active version.

#### Request body
```json
{
  "is_shared": false,
  "data": { "display_name": "John" },
  "version": null,
  "is_complete": null,
  "schema_template_name": null,
  "schema_template_version": null,
  "is_system_entity": false,
  "on_behalf_of_user_id": null,
  "create_only_fields": [],
  "keep_create_fields_if_missing": false
}
```

Field notes:
- `create_only_fields`: keys to remove from the payload during update (useful for fields only allowed on creation)
- `keep_create_fields_if_missing`: if true, keeps those fields if they don’t exist in the current document

#### Response
```json
{ "data": true }
```

#### Caveats
- 404 if document (or targeted version) not found.

---

<a id="api-03"></a>
### 03. Get versioned document
- Method/Path: GET `/versioned/{namespace}/{docname}`

#### TL;DR
- Fetch current data for `version` (or the active version if omitted).

#### Query params
- `is_shared`: boolean (required)
- `version`: string | null
- `is_system_entity`: boolean (default false)
- `on_behalf_of_user_id`: UUID (superuser only)

#### Response
```json
{ "data": { /* your document */ } }
```

---

<a id="api-04"></a>
### 04. Delete versioned document
- Method/Path: DELETE `/versioned/{namespace}/{docname}`

#### TL;DR
- Deletes the entire document (all versions).

#### Query params
- `is_shared` (required), `is_system_entity`, `on_behalf_of_user_id`

#### Response
- 204 No Content

---

<a id="api-05"></a>
### 05. List versions
- Method/Path: GET `/versioned/{namespace}/{docname}/versions`

#### Response
```json
[
  {
    "version": "v1",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-02T00:00:00Z",
    "is_complete": true,
    "edit_count": 3
  }
]
```

---

<a id="api-06"></a>
### 06. Create version (branch)
- Method/Path: POST `/versioned/{namespace}/{docname}/versions`

#### Request body
```json
{
  "is_shared": false,
  "new_version": "draft-2",
  "from_version": null,
  "is_system_entity": false,
  "on_behalf_of_user_id": null
}
```

#### Response
```json
{ "version": "draft-2", "is_active": false, "created_at": null, "updated_at": null, "is_complete": false, "edit_count": 0 }
```

---

<a id="api-07"></a>
### 07. Set active version
- Method/Path: POST `/versioned/{namespace}/{docname}/active-version`

#### Request body
```json
{ "is_shared": false, "version": "v1", "is_system_entity": false, "on_behalf_of_user_id": null }
```

#### Response
```json
{ "version": "v1", "is_active": true, "created_at": null, "updated_at": null, "is_complete": true, "edit_count": 3 }
```

---

<a id="api-08"></a>
### 08. Version history
- Method/Path: GET `/versioned/{namespace}/{docname}/history`

#### Query params
- `is_shared` (required), `version` (optional), `limit` (default 100), `is_system_entity`, `on_behalf_of_user_id`

#### Response
```json
[
  { "timestamp": "2024-01-02T00:00:00Z", "sequence": 12, "patch": "[ {\"op\":\"replace\",...} ]", "is_primitive": false }
]
```

---

<a id="api-09"></a>
### 09. Preview restore
- Method/Path: GET `/versioned/{namespace}/{docname}/preview-restore/{sequence}`

#### Query params
- `is_shared` (required), `version` (optional), `is_system_entity`, `on_behalf_of_user_id`

#### Response
```json
{ "data": { /* document as of the given sequence */ } }
```

---

<a id="api-10"></a>
### 10. Restore document
- Method/Path: POST `/versioned/{namespace}/{docname}/restore`

#### Request body
```json
{ "is_shared": false, "sequence": 12, "version": null, "is_system_entity": false, "on_behalf_of_user_id": null }
```

#### Response
```json
{ "data": true }
```

---

<a id="api-11"></a>
### 11. Get document schema
- Method/Path: GET `/versioned/{namespace}/{docname}/schema`

#### Response
```json
{ /* JSON Schema object or null */ }
```

---

<a id="api-12"></a>
### 12. Update document schema
- Method/Path: PUT `/versioned/{namespace}/{docname}/schema`

#### Request body
```json
{ "is_shared": false, "schema_template_name": "my_schema", "schema_template_version": "1.0", "is_system_entity": false, "on_behalf_of_user_id": null }
```

#### Response
```json
{ /* Updated JSON Schema object */ }
```

---

<a id="api-13"></a>
### 13. Upsert versioned document (recommended default)
- Method/Path: POST `/versioned/{namespace}/{docname}/upsert`

#### TL;DR
- If doc exists and is versioned: update it (active or a specified version).
- If the target version doesn’t exist: it creates the version (optionally from `from_version`) then updates.
- If it doesn’t exist: it initializes the doc with the provided data (version defaults to `default`).

#### Request body
```json
{
  "is_shared": false,
  "data": { "title": "Hello" },
  "version": null,
  "from_version": null,
  "is_complete": null,
  "schema_template_name": null,
  "schema_template_version": null,
  "is_system_entity": false,
  "on_behalf_of_user_id": null,
  "set_active_version": true,
  "create_only_fields": [],
  "keep_create_fields_if_missing": false
}
```

#### Response
```json
{
  "operation_performed": "updated_$active | updated_<version> | created_and_updated_version_<v> | initialized_version_<v>",
  "document_identifier": {
    "doc_path_segments": { "org_id_segment": "...", "user_id_segment": "...", "namespace": "...", "docname": "..." },
    "operation_params": { "org_id": "...", "is_shared": false, "on_behalf_of_user_id": null, "is_system_entity": false, "namespace": "...", "docname": "...", "set_active_version": true, "is_complete": null },
    "version": null
  }
}
```

#### Caveats
- Fails with 400 if an existing doc is unversioned at the same path.

---

## Unversioned Documents

<a id="api-14"></a>
### 14. Create or update unversioned document
- Method/Path: PUT `/unversioned/{namespace}/{docname}`

#### TL;DR
- Always upserts; JSON objects are merged (partial update), primitives replaced.
- Optionally validates against a schema template on write.

#### Request body
```json
{
  "is_shared": false,
  "data": { "theme": "dark" },
  "schema_template_name": null,
  "schema_template_version": null,
  "is_system_entity": false,
  "on_behalf_of_user_id": null,
  "create_only_fields": [],
  "keep_create_fields_if_missing": false
}
```

#### Response
```json
{ "data": ["<document_id>", true] }
```
The second value indicates whether it was created.

---

<a id="api-15"></a>
### 15. Get unversioned document
- Method/Path: GET `/unversioned/{namespace}/{docname}`

#### Query params
- `is_shared` (required), `is_system_entity`, `on_behalf_of_user_id`

#### Response
```json
{ "data": { /* your object */ } }
```

#### Caveats
- 400 if the path refers to a versioned document (use versioned GET instead).

---

<a id="api-16"></a>
### 16. Delete unversioned document
- Method/Path: DELETE `/unversioned/{namespace}/{docname}`

#### Query params
- `is_shared` (required), `is_system_entity`, `on_behalf_of_user_id`

#### Response
- 204 No Content

---

## Listing, Searching, Metadata

<a id="api-17"></a>
### 17. List documents
- Method/Path: GET `/list`

#### Query params
- `namespace`: string (optional)
- `include_shared`: boolean (default true)
- `include_user_specific`: boolean (default true)
- `include_system_entities`: boolean (default false; superuser only for private system docs)
- `on_behalf_of_user_id`: UUID (superuser only)
- `skip`: int (default 0)
- `limit`: int (default 100)
- `sort_by`: `created_at | updated_at` (optional)
- `sort_order`: `asc | desc` (optional)

#### Response (array of metadata)
```json
[
  {
    "versionless_path": "<org_or_system>/<user_or_shared>/<namespace>/<docname>",
    "id": "<internal_id>",
    "org_id": "<uuid or null for system>",
    "user_id_or_shared_placeholder": "<user_id or _shared_>",
    "namespace": "...",
    "docname": "...",
    "is_versioned": true,
    "is_shared": false,
    "is_system_entity": false,
    "version": "v1" /* present only when listing concrete versions */,
    "is_active_version": true
  }
]
```

<a id="api-18"></a>
### 18. Search documents
- Method/Path: POST `/search`

#### Request body
```json
{
  "namespace_filter": "assets*",
  "text_search_query": null,
  "value_filter": { "status": "active" },
  "include_shared": true,
  "include_user_specific": true,
  "skip": 0,
  "limit": 50,
  "on_behalf_of_user_id": null,
  "include_system_entities": false,
  "sort_by": null,
  "sort_order": "desc"
}
```

#### Response (array of search results)
```json
[
  {
    "metadata": {
      "versionless_path": "...",
      "id": "...",
      "org_id": "...",
      "user_id_or_shared_placeholder": "...",
      "namespace": "...",
      "docname": "...",
      "is_versioned": true,
      "is_shared": false,
      "is_system_entity": false,
      "version": "v1",
      "is_versioning_metadata": false,
      "is_active_version": true
    },
    "document_contents": { /* partial or full data, excluding internal fields */ }
  }
]
```

<a id="api-19"></a>
### 19. Get document metadata by path
- Method/Path: GET `/metadata/{namespace}/{docname}`

#### Query params
- `is_shared` (required), `is_system_entity`, `on_behalf_of_user_id`

#### Response
```json
{
  "versionless_path": "...",
  "id": "...",
  "org_id": "...",
  "user_id_or_shared_placeholder": "...",
  "namespace": "...",
  "docname": "...",
  "is_versioned": true,
  "is_shared": false,
  "is_system_entity": false,
  "version": null,
  "is_active_version": null
}
```

---

## Administrative – Delete by pattern (superuser)

<a id="api-20"></a>
### 20. Delete by pattern
- Method/Path: DELETE `/delete-by-pattern`
- Purpose: Delete multiple documents (versioned and/or unversioned) matching wildcard patterns.

#### Request body
```json
{
  "is_shared": false,
  "namespace": "invoice*",
  "docname": "2024*",
  "is_system_entity": false,
  "on_behalf_of_user_id": null,
  "dry_run": true
}
```

#### Response
```json
{ "deleted_count": 42, "dry_run": true }
```

---

## Practical integration patterns

### 1) User preferences (unversioned)
- Namespace: `user_preferences`
- Docname: simple key (e.g., `ui_theme`)
- Endpoint: PUT `/unversioned/user_preferences/ui_theme`
- Body: `{ is_shared: false, data: { theme: "dark" } }`

### 2) Org-shared configuration (unversioned or versioned)
- Namespace: `org_settings`
- Docname: `editor_defaults`
- `is_shared: true` so every user in the org reads the same configuration.

### 3) Content with releases (versioned)
- Namespace: `content_templates`
- Docname: `product_announcement`
- Use Upsert with explicit `version` and then `active-version` to promote.

### 4) Asset-scoped data
- Namespace: `assets`
- Docname: `asset-<uuid>` or a deterministic name
- Either unversioned (latest-only status) or versioned (to keep audit/history).

### 5) Safe writes using Upsert (versioned)
- Prefer POST `/versioned/{ns}/{name}/upsert` so you don’t need to check existence.
- If targeting a non-existent version, pass `from_version` to branch from active.

---

## Frontend helper examples

Replace `BASE` with your API base path for the customer-data routes.

```ts
type SortOrder = 'asc' | 'desc';

async function upsertVersionedDoc(BASE: string, namespace: string, docname: string, payload: any) {
  const res = await fetch(`${BASE}/versioned/${encodeURIComponent(namespace)}/${encodeURIComponent(docname)}/upsert`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error(`Upsert failed: ${res.status}`);
  return res.json();
}

async function getVersionedDoc(BASE: string, namespace: string, docname: string, isShared: boolean, version?: string) {
  const params = new URLSearchParams({ is_shared: String(isShared) });
  if (version) params.set('version', version);
  const res = await fetch(`${BASE}/versioned/${encodeURIComponent(namespace)}/${encodeURIComponent(docname)}?${params}`);
  if (!res.ok) throw new Error(`Get failed: ${res.status}`);
  return res.json();
}

async function putUnversioned(BASE: string, namespace: string, docname: string, body: any) {
  const res = await fetch(`${BASE}/unversioned/${encodeURIComponent(namespace)}/${encodeURIComponent(docname)}`, {
    method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body)
  });
  if (!res.ok) throw new Error(`PUT failed: ${res.status}`);
  return res.json();
}

async function search(BASE: string, payload: any) {
  const res = await fetch(`${BASE}/search`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error(`Search failed: ${res.status}`);
  return res.json();
}
```

---

## Schema reference (selected)

The service uses the following request/response shapes (simplified for clients). See endpoint sections for placement.

### Versioned initialize (request)
```json
{
  "is_shared": false,
  "initial_version": "default",
  "schema_template_name": "<optional>",
  "schema_template_version": "<optional>",
  "initial_data": {},
  "is_complete": false,
  "is_system_entity": false,
  "on_behalf_of_user_id": null
}
```

### Versioned update (request)
```json
{
  "is_shared": false,
  "data": {},
  "version": null,
  "is_complete": null,
  "schema_template_name": null,
  "schema_template_version": null,
  "is_system_entity": false,
  "on_behalf_of_user_id": null,
  "create_only_fields": [],
  "keep_create_fields_if_missing": false
}
```

### Versioned upsert (request)
```json
{
  "is_shared": false,
  "data": {},
  "version": null,
  "from_version": null,
  "is_complete": null,
  "schema_template_name": null,
  "schema_template_version": null,
  "is_system_entity": false,
  "on_behalf_of_user_id": null,
  "set_active_version": true,
  "create_only_fields": [],
  "keep_create_fields_if_missing": false
}
```

### Unversioned create/update (request)
```json
{
  "is_shared": false,
  "data": {},
  "schema_template_name": null,
  "schema_template_version": null,
  "is_system_entity": false,
  "on_behalf_of_user_id": null,
  "create_only_fields": [],
  "keep_create_fields_if_missing": false
}
```

### Common metadata (response)
```json
{
  "versionless_path": "<org_or_system>/<user_or_shared>/<namespace>/<docname>",
  "id": "<internal_id>",
  "org_id": "<uuid or null>",
  "user_id_or_shared_placeholder": "<user_uuid or _shared_>",
  "namespace": "...",
  "docname": "...",
  "is_versioned": true,
  "is_shared": false,
  "is_system_entity": false,
  "version": null,
  "is_active_version": null
}
```

---

## Caveats and best practices

- **Namespaces and naming**: Adopt clear, product-aligned namespaces (e.g., `user_preferences`, `assets`, `workflow_config`). Use stable, deterministic `docname` keys if you’ll reference them from multiple places.
- **Prefer Upsert for versioned**: It handles create-or-update seamlessly and will auto-create missing versions when targeting a non-existent version.
- **Schema upgrades**: Use the schema update endpoint to roll in new JSON Schemas, then update data. For unversioned writes, pass a `schema_template_name` to validate payloads.
- **Shared vs user-specific**: Shared docs (`is_shared: true`) are accessible to all users in an org. Use user-specific for personalized state.
- **System entities**: Reserved for platform-wide defaults or templates. Requires superuser; do not attempt from regular user clients.
- **Partial merges**: JSON object updates merge into existing objects; to remove keys, send explicit nulls and have the backend logic handle deletion if your schema expects it, or write a full replacement for primitives.
- **Pagination**: `list` and `search` support `skip`/`limit`; prefer server-side pagination for large sets.

---

## Troubleshooting

- 403 on writes: You might be attempting a superuser-only operation (`on_behalf_of_user_id` or `is_system_entity`).
- 404 on update: The document or targeted version may not exist. Use versioned Upsert or initialize first.
- 400 on unversioned GET: The path is actually a versioned document; use the versioned GET endpoint.
- 409 on initialize: The document already exists; use Upsert or Update.

---

## Glossary

- **Active version**: The version returned when no version is specified.
- **Shared document**: Document whose user segment is `_shared_` and is readable within the org.
- **System entity**: Document in the system scope (`_system_`) with either shared or private user segment; superuser-only.
- **Schema template**: Named JSON Schema stored centrally and referenced by name/version.

---

## Quick index of endpoints

- Versioned
  - POST `/versioned/{namespace}/{docname}` – Initialize
  - PUT `/versioned/{namespace}/{docname}` – Update
  - GET `/versioned/{namespace}/{docname}` – Read
  - DELETE `/versioned/{namespace}/{docname}` – Delete
  - GET `/versioned/{namespace}/{docname}/versions` – List versions
  - POST `/versioned/{namespace}/{docname}/versions` – Create version
  - POST `/versioned/{namespace}/{docname}/active-version` – Set active version
  - GET `/versioned/{namespace}/{docname}/history` – Version history
  - GET `/versioned/{namespace}/{docname}/preview-restore/{sequence}` – Preview restore
  - POST `/versioned/{namespace}/{docname}/restore` – Restore
  - GET `/versioned/{namespace}/{docname}/schema` – Get schema
  - PUT `/versioned/{namespace}/{docname}/schema` – Update schema
  - POST `/versioned/{namespace}/{docname}/upsert` – Upsert (recommended)

- Unversioned
  - PUT `/unversioned/{namespace}/{docname}` – Create/Update
  - GET `/unversioned/{namespace}/{docname}` – Read
  - DELETE `/unversioned/{namespace}/{docname}` – Delete

- Listing/Search/Meta
  - GET `/list` – List documents
  - POST `/search` – Search documents
  - GET `/metadata/{namespace}/{docname}` – Get metadata

- Admin
  - DELETE `/delete-by-pattern` – Delete multiple by pattern (superuser)

---

If you need examples tailored to your specific workflow, share your intended `namespace`, `docname` scheme, and whether you require versioning, and we’ll provide exact request samples.


