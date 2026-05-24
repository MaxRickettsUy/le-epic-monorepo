This is a [Next.js](https://nextjs.org/) project bootstrapped with [`create-next-app`](https://github.com/vercel/next.js/tree/canary/packages/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

## Configuration

Data is fetched server-side from the backend API. Configure its base URL with the
`API_URL` environment variable (server-only — it is never shipped to the browser).
Copy `.env.example` to `.env.local` and adjust as needed:

```bash
cp .env.example .env.local
```

`API_URL` defaults to `http://127.0.0.1:8000` (the local FastAPI backend in `../backend`).

The typed data layer lives in `lib/api/`; writes go through Server Actions in `app/actions.ts`.

## Scripts

- `npm run dev` — start the dev server
- `npm run build` / `npm run start` — production build / serve
- `npm run lint` — ESLint (`next/core-web-vitals` + Prettier)
- `npm run typecheck` — `tsc --noEmit`
- `npm run format` / `npm run format:check` — Prettier write / check

This project uses [`next/font`](https://nextjs.org/docs/basic-features/font-optimization) to automatically optimize and load Inter, a custom Google Font.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js/) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/deployment) for more details.
