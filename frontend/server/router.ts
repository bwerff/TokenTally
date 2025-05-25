import { initTRPC } from '@trpc/server'
import { z } from 'zod'
import { listUsage, listAudit, listUsers, addUser, removeUser } from './db'

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
  users: t.router({
    list: t.procedure
      .input(z.object({ orgId: z.string() }))
      .query(({ input }) => listUsers(input.orgId)),
    add: t.procedure
      .input(
        z.object({
          orgId: z.string(),
          email: z.string().email(),
          role: z.enum(['admin', 'member']),
        }),
      )
      .mutation(({ input }) => {
        addUser(input.orgId, input.email, input.role)
        return true
      }),
    remove: t.procedure
      .input(z.object({ orgId: z.string(), email: z.string() }))
      .mutation(({ input }) => {
        removeUser(input.orgId, input.email)
        return true
      }),
  }),
})

export type AppRouter = typeof appRouter
