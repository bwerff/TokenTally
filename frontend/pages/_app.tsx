import '../styles/globals.css'
import type { AppProps, AppContext } from 'next/app'
import NextApp from 'next/app'
import { SessionProvider } from 'next-auth/react'
import { QueryClient } from '@tanstack/react-query'
import { NextIntlProvider } from 'next-intl'
import { trpc } from '../lib/trpc'

export default function App({ Component, pageProps }: AppProps) {
  const { session, messages, locale, ...rest } = pageProps as any
  const queryClient = new QueryClient()
  return (
    <trpc.Provider client={trpc.createClient({ url: '/api/trpc' })} queryClient={queryClient}>
      <SessionProvider session={session}>
        <NextIntlProvider messages={messages} locale={locale} defaultLocale="en">
          <Component {...rest} />
        </NextIntlProvider>
      </SessionProvider>
    </trpc.Provider>
  )
}

App.getInitialProps = async (ctx: AppContext) => {
  const appProps = await NextApp.getInitialProps(ctx)
  const locale = ctx.router?.locale || ctx.ctx?.locale || 'en'
  try {
    const messages = (await import(`../messages/${locale}.json`)).default
    return { ...appProps, pageProps: { ...appProps.pageProps, messages, locale } }
  } catch {
    const messages = (await import('../messages/en.json')).default
    return { ...appProps, pageProps: { ...appProps.pageProps, messages, locale } }
  }
}
