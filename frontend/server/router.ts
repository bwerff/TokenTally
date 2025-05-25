import { initTRPC } from '@trpc/server'
import { z } from 'zod'
import { listUsage, listAudit } from './db'

const t = initTRPC.create()

export const appRouter = t.router({
  usage: t.procedure
    .input(
      z.object({
        start: z.string().optional(),
        end: z.string().optional(),
        customer: z.string().optional(),
      }),
    )
    .query(({ input }) => listUsage(input)),
  audit: t.procedure.query(() => listAudit()),
})

export type AppRouter = typeof appRouter
