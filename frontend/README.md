# Elector — Frontend (vote-fe)

Single-page application for **Elector**, a voting platform where users can register, sign in, browse elections, create polls (with candidates and optional settings), cast votes, and view results. The UI is built with **React**, **React Router**, **Tailwind CSS**, and talks to a backend API over HTTP (session cookies / refresh flow).

## Requirements

- **Node.js** (LTS recommended, e.g. 18+)
- **npm** (comes with Node)

## Install dependencies

From this directory (`frontend/`):

```bash
npm install
```

## Configuration

The API base URL is read from the environment. Copy the example file and adjust if your backend is not on the default host:

```bash
copy .env.example .env
```

On macOS/Linux:

```bash
cp .env.example .env
```

Edit `.env` and set `REACT_APP_API_URL` to your backend origin (e.g. `http://localhost:8000`). If unset, the app falls back to `http://localhost:8000`.

## Run the development server

```bash
npm start
```

Opens the app in the browser (by default [http://localhost:3000](http://localhost:3000)) with hot reload.

## Production build

```bash
npm run build
```

Outputs an optimized build under `build/`, suitable for static hosting; it must still be able to reach the configured API (CORS and cookies as required by your backend).

## Run tests

Interactive watch mode (default):

```bash
npm test
```

Single run (e.g. for CI or a one-off check):

```bash
npm test -- --watchAll=false
```

Tests use **Jest** and **React Testing Library** via Create React App (`react-scripts`).

## Project scripts (summary)

| Command              | Description                    |
| -------------------- | ------------------------------ |
| `npm start`          | Dev server                     |
| `npm run build`      | Production build               |
| `npm test`           | Unit/integration tests (Jest)  |
| `npm run eject`      | Eject CRA config (irreversible) |
