import '../styles/globals.css'
import type { AppProps } from 'next/app'
import { SessionProvider } from 'next-auth/react'
import { QueryClient } from '@tanstack/react-query'
import { trpc } from '../lib/trpc'

export default function App({ Component, pageProps }: AppProps) {
  const { session, ...rest } = pageProps as any
  const queryClient = new QueryClient()
  return (
    <trpc.Provider client={trpc.createClient({ url: '/api/trpc' })} queryClient={queryClient}>
      <SessionProvider session={session}>
        <Component {...rest} />
      </SessionProvider>
    </trpc.Provider>
  )
}
