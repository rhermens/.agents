---
name: mongodb-cli
description: Inspect and query MongoDB databases using `mongosh` and MongoDB database tools instead of the MongoDB MCP server. Use for listing databases/collections, reading documents, counting, aggregating, explaining queries, checking indexes, and exporting data.
---

# MongoDB CLI Skill

Use this skill for MongoDB tasks. Prefer `mongosh` and MongoDB CLI tools over MCP.

## Requirements

- `mongosh` should be installed.
- Optional tools: `mongoexport`, `mongoimport`, `mongodump`, `mongorestore` from MongoDB Database Tools.
- Default local connection: `mongodb://localhost:27017`.
- If the user provides a different connection string, use that for the task.

Use this connection pattern:

```bash
MONGODB_URI="${MONGODB_URI:-mongodb://localhost:27017}"
mongosh "$MONGODB_URI" --quiet --eval 'EJSON.stringify(db.adminCommand({ ping: 1 }))'
```

If `mongosh` is not installed but Nix is available, run one-off commands with:

```bash
nix shell nixpkgs#mongosh -c mongosh "$MONGODB_URI" --quiet --eval 'EJSON.stringify(db.adminCommand({ ping: 1 }))'
```

## Safety

- Treat MongoDB access as read-only by default.
- Do not run writes unless the user explicitly asks for the mutation and confirms the exact database, collection, filter, and operation.
- Write operations include: insert, update, replace, delete, drop, create/drop index, rename collection, `eval` scripts that modify state, import/restore.
- Before a destructive command, first run a read-only preview such as `countDocuments(filter)` or `find(filter).limit(5)`.
- Avoid printing secrets embedded in connection strings. Redact credentials in summaries.
- Always use limits for exploratory reads.

## Output Conventions

Use `EJSON.stringify(...)` so ObjectIds, Dates, Decimal128, and BSON types survive in output:

```bash
mongosh "$MONGODB_URI" --quiet --eval 'EJSON.stringify(db.getSiblingDB("DB").COLL.find({}).limit(5).toArray(), null, 2)'
```

Prefer compact JSON for agent processing. Add `null, 2` only when human readability matters.

## Common Read Operations

### List databases

```bash
mongosh "$MONGODB_URI" --quiet --eval 'EJSON.stringify(db.adminCommand({ listDatabases: 1 }).databases, null, 2)'
```

### List collections

```bash
mongosh "$MONGODB_URI" --quiet --eval 'EJSON.stringify(db.getSiblingDB("DB").getCollectionNames(), null, 2)'
```

### Count documents

```bash
mongosh "$MONGODB_URI" --quiet --eval 'EJSON.stringify(db.getSiblingDB("DB").COLL.countDocuments({}), null, 2)'
```

With a filter:

```bash
mongosh "$MONGODB_URI" --quiet --eval 'EJSON.stringify(db.getSiblingDB("DB").COLL.countDocuments({ status: "active" }), null, 2)'
```

### Find documents

```bash
mongosh "$MONGODB_URI" --quiet --eval 'EJSON.stringify(db.getSiblingDB("DB").COLL.find({}).limit(10).toArray(), null, 2)'
```

With projection and sort:

```bash
mongosh "$MONGODB_URI" --quiet --eval 'EJSON.stringify(db.getSiblingDB("DB").COLL.find({ status: "active" }, { name: 1, createdAt: 1 }).sort({ createdAt: -1 }).limit(10).toArray(), null, 2)'
```

### Aggregation

```bash
mongosh "$MONGODB_URI" --quiet --eval 'EJSON.stringify(db.getSiblingDB("DB").COLL.aggregate([
  { $match: { status: "active" } },
  { $group: { _id: "$type", count: { $sum: 1 } } },
  { $sort: { count: -1 } },
  { $limit: 20 }
]).toArray(), null, 2)'
```

### Indexes

```bash
mongosh "$MONGODB_URI" --quiet --eval 'EJSON.stringify(db.getSiblingDB("DB").COLL.getIndexes(), null, 2)'
```

### Database stats

```bash
mongosh "$MONGODB_URI" --quiet --eval 'EJSON.stringify(db.getSiblingDB("DB").stats(), null, 2)'
```

### Collection stats

```bash
mongosh "$MONGODB_URI" --quiet --eval 'EJSON.stringify(db.getSiblingDB("DB").runCommand({ collStats: "COLL" }), null, 2)'
```

### Explain a query

```bash
mongosh "$MONGODB_URI" --quiet --eval 'EJSON.stringify(db.getSiblingDB("DB").COLL.find({ status: "active" }).limit(10).explain("executionStats"), null, 2)'
```

### Sample schema

MongoDB has flexible schemas. Infer fields from samples:

```bash
mongosh "$MONGODB_URI" --quiet --eval '
const docs = db.getSiblingDB("DB").COLL.aggregate([{ $sample: { size: 50 } }]).toArray();
const fields = {};
for (const doc of docs) {
  for (const [k, v] of Object.entries(doc)) {
    const t = v === null ? "null" : Array.isArray(v) ? "array" : v && v._bsontype ? v._bsontype : typeof v;
    fields[k] ??= {};
    fields[k][t] = (fields[k][t] || 0) + 1;
  }
}
print(EJSON.stringify({ sampleSize: docs.length, fields }, null, 2));
'
```

### Recent MongoDB logs

For a local server managed by systemd:

```bash
journalctl -u mongodb -u mongod --since '1 hour ago' --no-pager | tail -200
```

If running in Docker:

```bash
docker ps --format '{{.Names}}' | rg 'mongo|mongodb'
docker logs --tail 200 CONTAINER_NAME
```

## Export Data

Use exports only when the user asks for a file. Keep filters and limits explicit.

```bash
mongoexport --uri "$MONGODB_URI" --db DB --collection COLL --query '{"status":"active"}' --limit 1000 --jsonFormat=canonical --out export.json
```

For CSV:

```bash
mongoexport --uri "$MONGODB_URI" --db DB --collection COLL --type=csv --fields _id,name,status --out export.csv
```

## Mutations

Only after explicit confirmation:

```bash
# Preview
mongosh "$MONGODB_URI" --quiet --eval 'EJSON.stringify(db.getSiblingDB("DB").COLL.find(FILTER).limit(5).toArray(), null, 2)'

# Update
mongosh "$MONGODB_URI" --quiet --eval 'EJSON.stringify(db.getSiblingDB("DB").COLL.updateMany(FILTER, UPDATE), null, 2)'

# Delete
mongosh "$MONGODB_URI" --quiet --eval 'EJSON.stringify(db.getSiblingDB("DB").COLL.deleteMany(FILTER), null, 2)'
```

## MCP Replacement Map

Use these CLI equivalents instead of MongoDB MCP tools:

- connect/ping: `mongosh "$MONGODB_URI" --eval 'db.adminCommand({ ping: 1 })'`
- list databases: `db.adminCommand({ listDatabases: 1 })`
- list collections: `db.getSiblingDB("DB").getCollectionNames()`
- find/count/aggregate: `find()`, `countDocuments()`, `aggregate()` in `mongosh`
- indexes/schema/stats: `getIndexes()`, sampled aggregation, `db.stats()`, `collStats`
- explain: `find(...).explain(...)` or `aggregate(...).explain(...)`
- export: `mongoexport`
- logs: `journalctl`, `docker logs`, or service-specific logs
