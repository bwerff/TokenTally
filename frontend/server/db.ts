import Database from 'better-sqlite3'
import crypto from 'crypto'

const usageDb = new Database(process.env.USAGE_DB || '../usage_ledger.db')
const auditDb = new Database(process.env.AUDIT_DB || '../audit_log.db')
const accountsDb = new Database(process.env.ACCOUNTS_DB || '../accounts.db')

accountsDb
  .prepare(
    `CREATE TABLE IF NOT EXISTS organisations (
       id TEXT PRIMARY KEY,
       name TEXT NOT NULL
     )`,
  )
  .run()

accountsDb
  .prepare(
    `CREATE TABLE IF NOT EXISTS users (
       id TEXT PRIMARY KEY,
       org_id TEXT NOT NULL,
       email TEXT NOT NULL,
       role TEXT NOT NULL,
       FOREIGN KEY(org_id) REFERENCES organisations(id)
     )`,
  )
  .run()

export interface UsageQuery {
  start?: string
  end?: string
  customer?: string
}

export function listUsage(query: UsageQuery = {}) {
  const clauses: string[] = []
  const params: Record<string, string> = {}
  if (query.start) {
    clauses.push('ts >= @start')
    params.start = query.start
  }
  if (query.end) {
    clauses.push('ts <= @end')
    params.end = query.end
  }
  if (query.customer) {
    clauses.push('customer_id = @customer')
    params.customer = query.customer
  }
  const where = clauses.length ? `WHERE ${clauses.join(' AND ')}` : ''
  const stmt = `SELECT * FROM usage_events ${where} ORDER BY ts DESC LIMIT 100`
  return usageDb.prepare(stmt).all(params)
}

export function listAudit() {
  return auditDb.prepare('SELECT * FROM audit_events ORDER BY ts DESC LIMIT 100').all()
}

export function listUsers(orgId: string) {
  return accountsDb
    .prepare('SELECT email, role FROM users WHERE org_id = ? ORDER BY email')
    .all(orgId)
}

export function addUser(orgId: string, email: string, role: string) {
  const id = crypto.randomUUID()
  accountsDb
    .prepare('INSERT OR REPLACE INTO users (id, org_id, email, role) VALUES (?, ?, ?, ?)')
    .run(id, orgId, email, role)
}

export function removeUser(orgId: string, email: string) {
  accountsDb.prepare('DELETE FROM users WHERE org_id = ? AND email = ?').run(orgId, email)
}

export function createOrg(name: string) {
  const id = crypto.randomUUID()
  accountsDb.prepare('INSERT INTO organisations (id, name) VALUES (?, ?)').run(id, name)
  return { id, name }
}
