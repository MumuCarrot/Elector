# Vote FE

This project is a React-based front-end for an online voting platform. It uses Create React App, React Router, Tailwind CSS, and Axios to communicate with a backend API.

## Prerequisites

- **Node.js**: recommended LTS version (for example 18 or 20)
- **npm**: comes together with Node.js

## Install dependencies

All required libraries are defined in `package.json`. To install them, run:

```bash
npm install
```

## Development server

To start the development server:

```bash
npm start
```

This will:
- start the React development server on `http://localhost:3000`
- watch for file changes and automatically reload the page

## Environment variables

Create a `.env` by example file `.env.example`.

## Build for production

To create an optimized production build:

```bash
npm run build
```

The build output will be placed in the `build` directory and can be served by any static file server or integrated with your backend.

## Run with Docker

You can build and run this React application inside a Docker container using the provided `Dockerfile`.

### Build Docker image

From the project root (where `Dockerfile` is located), run:

```bash
docker build -t vote-fe .
```

### Run Docker container

To start a container and expose the app on `http://localhost:3000`:

```bash
docker run -p 3000:80 --name vote-fe-container vote-fe
```

### Stop and remove container

To stop and remove the running container:

```bash
docker stop vote-fe-container
docker rm vote-fe-container
```

## Running tests

The project uses Jest and React Testing Library (already configured by Create React App) together with the tests added in `src/components`, `src/contexts`, and `src/services`.

To run tests in watch mode:

```bash
npm test
```

To run tests once in CI mode (for example in CI pipelines or local one-time run), you can use:

```bash
CI=true npm test
```

## Scripts summary

From `package.json`:

- `npm start` – start the development server
- `npm run build` – build the app for production
- `npm test` – run tests (Jest + React Testing Library)


