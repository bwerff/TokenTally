import { initTRPC } from '@trpc/server'
import { listUsage, listAudit } from './db'

const t = initTRPC.create()

export const appRouter = t.router({
  usage: t.procedure.query(() => listUsage()),
  audit: t.procedure.query(() => listAudit()),
})

export type AppRouter = typeof appRouter
