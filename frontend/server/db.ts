import Database from 'better-sqlite3'

const usageDb = new Database(process.env.USAGE_DB || '../usage_ledger.db')
const auditDb = new Database(process.env.AUDIT_DB || '../audit_log.db')

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
