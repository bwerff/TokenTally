import NextAuth from 'next-auth'
import CredentialsProvider from 'next-auth/providers/credentials'
import GoogleProvider from 'next-auth/providers/google'
import OktaProvider from 'next-auth/providers/okta'
import SAMLProvider from 'next-auth/providers/saml'

const providers = [
  CredentialsProvider({
    name: 'Credentials',
    credentials: {
      email: { label: 'Email', type: 'text' },
      password: { label: 'Password', type: 'password' },
    },
    authorize: async (credentials) => {
      if (credentials?.email && credentials.password) {
        return { id: credentials.email, email: credentials.email }
      }
      return null
    },
  }),
]

if (process.env.GOOGLE_CLIENT_ID && process.env.GOOGLE_CLIENT_SECRET) {
  providers.push(
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET,
    })
  )
}

if (process.env.OKTA_CLIENT_ID && process.env.OKTA_CLIENT_SECRET) {
  providers.push(
    OktaProvider({
      clientId: process.env.OKTA_CLIENT_ID,
      clientSecret: process.env.OKTA_CLIENT_SECRET,
      issuer: process.env.OKTA_ISSUER,
    })
  )
}

if (
  process.env.SAML_ENTRYPOINT &&
  process.env.SAML_ISSUER &&
  process.env.SAML_CERT
) {
  providers.push(
    SAMLProvider({
      entryPoint: process.env.SAML_ENTRYPOINT,
      issuer: process.env.SAML_ISSUER,
      cert: process.env.SAML_CERT,
    })
  )
}

export default NextAuth({
  providers,
})
