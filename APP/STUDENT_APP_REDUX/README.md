# Student App Redux

Consolidated student dashboard for DSAT practice, built with React 18, TypeScript, and Vite.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Copy `.env.example` to `.env` and set your test user token:
```bash
cp .env.example .env
```

3. Start the development server:
```bash
npm run dev
```

The app will be available at `http://localhost:5173`

## Architecture

- **React 18** with TypeScript
- **Vite** for fast dev experience and optimized builds
- **React Router v7** for navigation
- **React Query** for server state management
- **Tailwind CSS** for styling
- **Radix UI** for accessible components

## Project Structure

```
src/
├── main.tsx              # Entry point
├── App.tsx               # Root component with routing
├── index.css             # Tailwind directives
├── api/
│   └── client.ts         # API communication
├── hooks/                # Custom React hooks
├── components/           # React components
├── pages/                # Page components
└── types/                # TypeScript type definitions
```

## Commands

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run lint` - Run ESLint
- `npm run preview` - Preview production build

## Task Tracker

See `../../STUDENT_UI_TASKS.md` for detailed Phase 1 implementation tasks (Grammar page port).
