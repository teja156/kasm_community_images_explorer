# Kasm Community Registry

React + Vite application that showcases community-built Kasm workspaces. The interface leans on shadcn/ui components and Tailwind CSS to match the dark card-based gallery shown in the reference screenshot.

## Features

- Responsive gallery of workspace cards with shadcn/ui `Card`, `Badge`, `Button`, and `Select` components.
- Responsive search that ranks exact and prefix matches across workspace name, author, registry slug, or GitHub pages URL while allowing partial substrings.
- Filters for author and minimum star count with Radix-powered selects.
- Progressive loading renders 24 cards at a time with a `Load more` control to avoid UI slowdowns while still searching the full dataset.
- Star badges reflect the `stars` value provided in `sample_workspaces_data.json`, defaulting to `0` when absent.
- Tailwind-powered dark theme with subtle gradients inspired by the Kasm community catalog.

## Getting Started

```bash
npm install
npm run dev
```

Open the local URL printed by Vite (defaults to `http://localhost:5173`) to browse the registry. The production build runs with:

```bash
npm run build
npm run preview
```

## Customize the Listings

1. Edit `src/data/sample_workspaces_data.json` to add, update, or remove registry entries. Each registry can expose multiple workspace objects, and the UI will flatten them automatically.
2. Icons and visual affordances come from `lucide-react`; adjust them inside `src/components/workspace-card.tsx` if you want different metaphors.
3. Tailwind design tokens live in `tailwind.config.js` and `src/index.css`. Tweak the color variables or gradients to brand the gallery for your organization.

## Available Scripts

- `npm run dev` – Start the Vite dev server with hot module replacement.
- `npm run build` – Type-check and output the production build to `dist/`.
- `npm run preview` – Preview a built bundle locally.
- `npm run lint` – Run ESLint over the project.

## Tech Stack

- React 19 + TypeScript
- Vite build tooling
- Tailwind CSS with shadcn/ui component patterns
- Radix UI primitives and lucide-react icons
