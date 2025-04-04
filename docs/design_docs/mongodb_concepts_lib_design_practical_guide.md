# MongoDB Path-Based Document Management

## 1. Introduction to AsyncMongoDBClient

AsyncMongoDBClient is a modern, asynchronous interface for MongoDB designed for structured document management using a hierarchical path-based approach. The client handles MongoDB operations in a fully asynchronous way, making it ideal for high-performance applications built with asyncio.

```python
client = AsyncMongoDBClient(
    uri="mongodb://username:password@localhost:27017",
    database="my_app_db",
    collection="structured_documents",
    segment_names=["org", "project", "namespace", "object"],
    text_search_fields=["title", "description", "tags"]
)
```

## 2. Key MongoDB Entities Explained

### Collections
- Similar to tables in relational databases
- Group related documents together
- Typically one collection per entity type
- Our client works with a single collection specified at initialization

### Documents
- Schema-flexible JSON-like records (BSON format)
- Each document has a unique `_id` field (ObjectId by default)
- In our client, documents are organized using path segments as fields
- Contains both metadata (path segments) and actual payload data

### Indexes
- Improve query performance for frequently used fields
- Support for compound, text, and other specialized indexes
- The client automatically creates indexes on segment fields and text search fields

### Queries
- MongoDB uses a rich query language based on JSON
- Supports complex filtering, projection, and aggregation
- The client abstracts query building for path-based operations

## 3. Path-Based Document Model

The core concept of this client is organizing documents in hierarchical paths:

```
org/project/namespace/object
```

### Path Segments

- Each segment in the path becomes a field in the document
- Path segments are defined during client initialization:
  ```python
  segment_names=["org", "project", "namespace", "object"]
  ```
- Documents are stored with this structure:
  ```json
  {
    "_id": ObjectId("..."),
    "org": "acme",
    "project": "website",
    "namespace": "config",
    "object": "settings",
    "data": { "theme": "dark", "features": ["comments", "search"] }
  }
  ```

### Pattern Matching

Paths support wildcard patterns for flexible querying:

```python
# List all settings objects across all projects
await client.list_objects(pattern="acme/*/config/settings")

# Get all objects in the testing namespace
await client.list_objects(pattern="*/*/testing/*")
```

## 4. Basic Operations

### Creating Documents
```python
# Create a document with a specific path
obj_id = await client.create_object(
    path="acme/website/config/settings",
    data={"theme": "dark", "features": ["comments", "search"]}
)
```

### Retrieving Documents
```python
# Fetch by exact path
document = await client.fetch_object(path="acme/website/config/settings")

# List objects matching a pattern
objects = await client.list_objects(pattern="acme/website/*/*")
```

### Updating Documents
```python
# Update an existing document
await client.update_object(
    path="acme/website/config/settings",
    data={"theme": "light", "features": ["comments", "search", "analytics"]}
)

# Create or update (upsert)
obj_id, created = await client.create_or_update_object(
    path="acme/website/config/settings",
    data={"theme": "light", "features": ["comments", "search"]}
)
```

### Deleting Documents
```python
# Delete a specific document
await client.delete_objects(pattern="acme/website/config/settings")

# Delete all documents matching a pattern
deleted_count = await client.delete_objects(pattern="acme/legacy_project/*/*")
```

## 5. Advanced Features

### Text Search
```python
# Search for documents containing specific text
results = await client.search_objects(
    key_pattern="acme/*/*",
    text_search_query="performance optimization",
    value_filter={"status": "active"}
)
```

### Permission-Based Access Control
```python
# Restrict operations to specific path prefixes
allowed_prefixes = ["acme/project1", "acme/project2/public"]

# These operations will only access documents within allowed paths
documents = await client.list_objects(
    pattern="acme/*/*/settings",
    allowed_prefixes=allowed_prefixes
)

await client.create_object(
    path="acme/project1/config/api",
    data={"key": "abc123"},
    allowed_prefixes=allowed_prefixes
)
```

### Value Filtering
```python
# Find documents with specific data values
results = await client.search_objects(
    key_pattern="*/*/user_profiles/*",
    value_filter={"account_type": "premium", "active": True}
)
```

## 6. Connection Management

### Automatic Connection Handling
The client manages MongoDB connections automatically:

```python
# Connection happens automatically on first operation
await client.fetch_object(path="acme/website/config/settings")

# Explicit connection check
is_connected = await client.ping()

# Explicitly close connections when done
await client.close()
```

### Connection Lifecycle

```python
# Best practice is to use async context manager pattern
async def process_data():
    client = AsyncMongoDBClient(...)
    try:
        await client.setup()  # Create necessary indexes
        # Perform operations...
    finally:
        await client.close()  # Always close connections
```

## 7. Performance Considerations

### Indexing Strategy
```python
# The client creates two types of indexes automatically:
# 1. Compound index on all segment fields
# 2. Text index on specified fields in the data payload

# Custom text search fields for specific use cases
client = AsyncMongoDBClient(
    uri="mongodb://localhost:27017",
    database="my_db",
    collection="my_collection",
    segment_names=["org", "project", "type", "name"],
    text_search_fields=["title", "description", "tags", "content"]
)
```

### Query Optimization
```python
# More specific patterns perform better than broad wildcards
# Better:
await client.list_objects(pattern="acme/website/*/*")
# Less efficient:
await client.list_objects(pattern="*/*/*")

# Use projection to limit returned fields when possible
docs = await client.list_objects(pattern="acme/*/*", include_data=False)
```

### Batch Operations
```python
# For bulk operations, consider using MongoDB's native bulk operations API
# The client currently processes one document at a time
```

## 8. Error Handling Patterns

### Connection Errors
```python
try:
    result = await client.fetch_object(path="acme/project/config/settings")
except ConnectionError as e:
    logging.error(f"MongoDB connection failed: {e}")
    # Implement retry or fallback logic
```

### Permission Denied
```python
result = await client.fetch_object(
    path="acme/project/config/settings",
    allowed_prefixes=["acme/other_project"]
)
# Returns None if path doesn't match allowed prefixes
if result is None:
    logging.warning("Access denied or document not found")
```

### Invalid Paths
```python
try:
    await client.create_object(path="invalid//path", data={})
except ValueError as e:
    logging.error(f"Invalid path format: {e}")
```

## 9. Advanced Patterns

### Hierarchical Data Management
```python
# Group related documents by shared path prefixes
await client.create_object(
    path="org/project/config/database",
    data={"host": "db.example.com", "port": 5432}
)
await client.create_object(
    path="org/project/config/cache",
    data={"host": "cache.example.com", "port": 6379}
)

# Then retrieve the entire configuration group
config_objects = await client.list_objects(
    pattern="org/project/config/*",
    include_data=True
)
```

### Dynamic Permission Management
```python
# User-specific permissions based on role
async def get_user_documents(user_id, user_role):
    allowed_prefixes = []
    
    if user_role == "admin":
        allowed_prefixes = ["org/*"]  # Admin sees everything
    elif user_role == "project_manager":
        allowed_prefixes = [f"org/{user_id}/*"]  # Manager sees their projects
    else:
        allowed_prefixes = [f"org/*/public/*"]  # Regular users see public docs
        
    return await client.list_objects(
        pattern="org/*/*",
        allowed_prefixes=allowed_prefixes
    )
```

### Versioning Documents
```python
# Implement simple versioning using path segments
await client.create_object(
    path=f"org/project/document/file_v1",
    data={"content": "Initial version"}
)
await client.create_object(
    path=f"org/project/document/file_v2",
    data={"content": "Updated version"}
)

# Get latest version
versions = await client.list_objects(pattern="org/project/document/file_*")
latest_version = sorted(versions)[-1]
```

## 10. Collection Management

### Setup and Maintenance
```python
# Initialize indexes and collection structure
await client.setup()

# Reset collection (danger zone!)
await client.reset_collection(confirm=True)

# Drop entire collection including indexes
await client.drop_collection(confirm=True)
```

The AsyncMongoDBClient provides a structured approach to document management, combining MongoDB's flexibility with a path-based organization that makes hierarchical data easier to work with in complex applications.
