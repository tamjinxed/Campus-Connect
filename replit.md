# Workspace

## Overview

pnpm workspace monorepo using TypeScript. Each package manages its own dependencies.

## Projects

### CampusConnect Hub (Primary App)
- **Location**: `artifacts/campus-connect/`
- **Stack**: Flask (Python 3.11), PostgreSQL, HTML5, Vanilla JavaScript, Tailwind CSS CDN
- **Port**: 5000
- **Workflow**: "CampusConnect"
- **Start command**: `cd artifacts/campus-connect && python run.py`

### Backend API Server (Node.js)
- **Location**: `artifacts/api-server/`
- **Stack**: Express 5, TypeScript, PostgreSQL, Drizzle ORM

### Mockup Sandbox
- **Location**: `artifacts/mockup-sandbox/`
- **Stack**: React + Vite

## CampusConnect Features (Phase 2 — Complete)
- **Authentication**: Flask-Login + bcrypt (RBAC: Student / Teacher)
- **UI**: Dark sidebar navigation (desktop) + bottom navigation bar (mobile), Tailwind CSS
- **Campus Feed**: Events + Announcements with smart department filtering & quick actions
- **Event Management**: Create, register, unregister, moderate events (teacher approval)
- **Calendar**: Monthly calendar grid showing events; day-view; personal registered events
- **Notices/Announcements**: Post notices with priority levels (normal/important/urgent); teacher moderation
- **Classroom Module**: Teachers create rooms with unique codes; students join; upload course materials
- **Real-Time Chat**: SocketIO — global campus room + per-classroom rooms
- **AI Assistant**: Rule-based AI chat at /chat/ai — answers questions about events, notices, classrooms, campus life using live DB data
- **Content Moderation**: Teachers approve/reject student events & notices from /moderation dashboard
- **Profile**: User profile with bio, department, intake; stats on events & registrations

## Demo Accounts (password: password123)
- Teacher: `masud@bubt.edu.bd`
- Student: `tamjid@bubt.edu.bd`
- Student: `musfika@bubt.edu.bd`

## Tech Stack (CampusConnect)
- **Monorepo tool**: pnpm workspaces (Node.js side)
- **Python version**: 3.11
- **Backend**: Flask 3.x, Flask-Login, Flask-SocketIO, Flask-SQLAlchemy, Flask-Bcrypt
- **Database**: PostgreSQL v14+ (via DATABASE_URL secret)
- **Frontend**: HTML5, Vanilla JavaScript, Tailwind CSS (CDN), Socket.IO client
- **Real-time**: Flask-SocketIO with Eventlet

## Key Commands (CampusConnect)
- `cd artifacts/campus-connect && python run.py` — start server
- `cd artifacts/campus-connect && python seed.py` — seed demo data

## Node.js/TypeScript Key Commands
- `pnpm run typecheck` — full typecheck across all packages
- `pnpm run build` — typecheck + build all packages
- `pnpm --filter @workspace/api-spec run codegen` — regenerate API hooks and Zod schemas from OpenAPI spec
- `pnpm --filter @workspace/db run push` — push DB schema changes (dev only)
