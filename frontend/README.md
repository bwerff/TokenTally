# TokenTally Frontend

This folder contains the Next.js admin portal. Install dependencies with `npm install` and start the dev server with `npm run dev`.

## Authentication providers

NextAuth is configured in `pages/api/auth/[...nextauth].ts`. The credentials provider is always enabled. Google and SAML providers are added if the following environment variables are present:

- `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` – enable Google sign-in.
- `SAML_ENTRYPOINT`, `SAML_ISSUER` and `SAML_CERT` – enable a generic SAML 2.0 provider.

If the variables are not set the corresponding provider is skipped.

## Organisation management

Admins can manage organisation users at `/org-users`. The page lists users and
allows adding or removing members using tRPC calls backed by a SQLite database
(`accounts.db`). Only authenticated admins may access the page.
