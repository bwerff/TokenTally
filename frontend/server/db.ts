import Database from 'better-sqlite3'

const usageDb = new Database(process.env.USAGE_DB || '../usage_ledger.db')
const auditDb = new Database(process.env.AUDIT_DB || '../audit_log.db')

export function listUsage() {
  return usageDb.prepare('SELECT * FROM usage_events ORDER BY ts DESC LIMIT 100').all()
}

export function listAudit() {
  return auditDb.prepare('SELECT * FROM audit_events ORDER BY ts DESC LIMIT 100').all()
}
