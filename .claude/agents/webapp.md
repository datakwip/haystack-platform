# WebApp Agent

**Specialized agent for building the enterprise web application.**

---

## Scope

**Work ONLY on:**
- `/webapp/app/` - Next.js pages and routes
- `/webapp/components/` - React components
- `/webapp/lib/` - Utilities and API clients
- `/webapp/public/` - Static assets
- `/webapp/styles/` - Stylesheets
- `/webapp/package.json` - Dependencies
- `/webapp/tsconfig.json` - TypeScript config
- `/webapp/Dockerfile` - Container build

**DO NOT touch:**
- Other services (`/api`, `/simulator`)
- Database schema files
- `docker-compose.yaml` (handled by Docker Testing Agent)

---

## Service Overview

**Haystack Platform WebApp** - Enterprise web interface for building data management

### Current Status
⚠️ **Minimal Implementation** - Focus is on simulator service

The webapp is currently a placeholder. Future development will include:
1. **Dashboard**: System overview, real-time metrics
2. **Data Explorer**: Browse entities with Haystack tag filtering
3. **Time-Series Viewer**: Chart building point data
4. **Admin Panel**: Organization and user management
5. **Authentication**: AWS Cognito SSO integration

### Tech Stack
- **Framework**: Next.js 14+ (App Router)
- **Language**: TypeScript
- **UI Library**: React + shadcn/ui (or similar)
- **Styling**: Tailwind CSS
- **API Client**: fetch/axios for REST API calls
- **Port**: 3000

---

## Architecture

```
WebApp (Port 3000)
├── Frontend (Next.js)
│   ├── SSR pages for dashboards
│   ├── Client components for interactivity
│   └── API route handlers (optional)
├── API Integration
│   ├── REST client to API service (port 8000)
│   ├── Authentication (JWT tokens)
│   └── Error handling
└── State Management
    ├── React Context (or Zustand/Redux)
    └── Server/client data sync
```

---

## File Structure

```
webapp/
├── app/
│   ├── layout.tsx                    # Root layout
│   ├── page.tsx                      # Home page
│   ├── dashboard/
│   │   └── page.tsx                  # System dashboard
│   ├── explorer/
│   │   └── page.tsx                  # Data explorer
│   ├── admin/
│   │   ├── orgs/page.tsx             # Org management
│   │   └── users/page.tsx            # User management
│   └── api/                          # Optional API routes
│       └── [...nextauth]/route.ts    # Auth (future)
├── components/
│   ├── ui/                           # shadcn/ui components
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   └── ...
│   ├── dashboard/
│   │   ├── MetricsCard.tsx
│   │   └── StatusIndicator.tsx
│   ├── explorer/
│   │   ├── EntityList.tsx
│   │   ├── TagFilter.tsx
│   │   └── ValueChart.tsx
│   └── layout/
│       ├── Header.tsx
│       └── Sidebar.tsx
├── lib/
│   ├── api-client.ts                 # API service client
│   ├── auth.ts                       # Authentication utils
│   └── utils.ts                      # Helpers
├── public/
│   ├── logo.svg
│   └── ...
├── styles/
│   └── globals.css                   # Global styles
├── package.json
├── tsconfig.json
├── next.config.js
└── Dockerfile
```

---

## API Integration

### API Client (lib/api-client.ts)

```typescript
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface EntityTag {
  tag_def_id: string;
  value?: string | number | boolean;
}

interface Entity {
  id: number;
  tags: EntityTag[];
}

interface ValuePoint {
  entity_id: number;
  timestamp: string;
  value: number;
}

export class HaystackAPIClient {
  private baseUrl: string;
  private authToken?: string;

  constructor(baseUrl: string = API_URL) {
    this.baseUrl = baseUrl;
  }

  setAuthToken(token: string) {
    this.authToken = token;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.authToken) {
      headers['Authorization'] = `Bearer ${this.authToken}`;
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'API request failed');
    }

    return response.json();
  }

  // Entities
  async getEntities(orgId: number, skip = 0, limit = 100): Promise<Entity[]> {
    return this.request<Entity[]>(`/entity?org_id=${orgId}&skip=${skip}&limit=${limit}`);
  }

  async getEntity(entityId: number, orgId: number): Promise<Entity> {
    return this.request<Entity>(`/entity/${entityId}?org_id=${orgId}`);
  }

  async createEntity(orgId: number, tags: EntityTag[]): Promise<Entity> {
    return this.request<Entity>('/entity', {
      method: 'POST',
      body: JSON.stringify({ org_id: orgId, tags }),
    });
  }

  async deleteEntity(entityId: number, orgId: number): Promise<Entity> {
    return this.request<Entity>(`/entity/${entityId}`, {
      method: 'DELETE',
      body: JSON.stringify({ org_id: orgId }),
    });
  }

  // Values
  async getEntityValues(
    entityId: number,
    orgId: number,
    skip = 0,
    limit = 1000
  ): Promise<ValuePoint[]> {
    return this.request<ValuePoint[]>(
      `/value/${entityId}?org_id=${orgId}&skip=${skip}&limit=${limit}`
    );
  }

  async createValue(
    entityId: number,
    orgId: number,
    timestamp: string,
    value: number
  ): Promise<ValuePoint> {
    return this.request<ValuePoint>('/value', {
      method: 'POST',
      body: JSON.stringify({ entity_id: entityId, org_id: orgId, timestamp, value }),
    });
  }

  // Health
  async healthCheck(): Promise<{ status: string }> {
    return this.request<{ status: string }>('/health');
  }

  async databaseHealth(): Promise<any> {
    return this.request<any>('/health/databases');
  }
}

export const apiClient = new HaystackAPIClient();
```

---

## Example Pages

### Dashboard (app/dashboard/page.tsx)

```typescript
'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { apiClient } from '@/lib/api-client';

export default function Dashboard() {
  const [health, setHealth] = useState<any>(null);
  const [entities, setEntities] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [healthData, entitiesData] = await Promise.all([
          apiClient.databaseHealth(),
          apiClient.getEntities(1, 0, 10), // org_id = 1
        ]);

        setHealth(healthData);
        setEntities(entitiesData);
      } catch (error) {
        console.error('Failed to fetch data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return <div className="p-8">Loading...</div>;
  }

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">System Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <Card>
          <CardHeader>
            <CardTitle>API Status</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">
              {health?.status === 'healthy' ? '🟢 Online' : '🔴 Offline'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Entities</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{entities.length}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Database</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm">
              {health?.databases?.map((db: any) => db.name).join(', ')}
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Entities</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2">
            {entities.map((entity) => (
              <li key={entity.id} className="border-b pb-2">
                <span className="font-semibold">Entity {entity.id}</span>
                <span className="text-sm text-gray-600 ml-4">
                  {entity.tags.length} tags
                </span>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
```

### Data Explorer (app/explorer/page.tsx)

```typescript
'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api-client';
import { EntityList } from '@/components/explorer/EntityList';
import { TagFilter } from '@/components/explorer/TagFilter';

export default function DataExplorer() {
  const [entities, setEntities] = useState<any[]>([]);
  const [filteredEntities, setFilteredEntities] = useState<any[]>([]);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);

  useEffect(() => {
    const fetchEntities = async () => {
      const data = await apiClient.getEntities(1, 0, 1000);
      setEntities(data);
      setFilteredEntities(data);
    };

    fetchEntities();
  }, []);

  useEffect(() => {
    // Filter entities by selected tags
    if (selectedTags.length === 0) {
      setFilteredEntities(entities);
    } else {
      const filtered = entities.filter((entity) =>
        selectedTags.every((tag) =>
          entity.tags.some((t: any) => t.tag_def_id === tag)
        )
      );
      setFilteredEntities(filtered);
    }
  }, [selectedTags, entities]);

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Data Explorer</h1>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="md:col-span-1">
          <TagFilter
            entities={entities}
            selectedTags={selectedTags}
            onTagsChange={setSelectedTags}
          />
        </div>

        <div className="md:col-span-3">
          <EntityList entities={filteredEntities} />
        </div>
      </div>
    </div>
  );
}
```

### Entity List Component (components/explorer/EntityList.tsx)

```typescript
'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface EntityListProps {
  entities: any[];
}

export function EntityList({ entities }: EntityListProps) {
  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold">
        {entities.length} Entities
      </h2>

      {entities.map((entity) => (
        <Card key={entity.id}>
          <CardHeader>
            <CardTitle>Entity {entity.id}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {entity.tags.map((tag: any, idx: number) => (
                <Badge key={idx} variant="outline">
                  {tag.tag_def_id}
                  {tag.value !== null && tag.value !== undefined && `: ${tag.value}`}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      ))}

      {entities.length === 0 && (
        <p className="text-gray-500">No entities found</p>
      )}
    </div>
  );
}
```

---

## Authentication (Future)

### NextAuth.js Integration

```typescript
// app/api/auth/[...nextauth]/route.ts

import NextAuth from 'next-auth';
import CognitoProvider from 'next-auth/providers/cognito';

const handler = NextAuth({
  providers: [
    CognitoProvider({
      clientId: process.env.COGNITO_CLIENT_ID!,
      clientSecret: process.env.COGNITO_CLIENT_SECRET!,
      issuer: process.env.COGNITO_ISSUER!,
    }),
  ],
  callbacks: {
    async jwt({ token, account }) {
      if (account) {
        token.accessToken = account.access_token;
      }
      return token;
    },
    async session({ session, token }) {
      session.accessToken = token.accessToken;
      return session;
    },
  },
});

export { handler as GET, handler as POST };
```

### Protected Pages

```typescript
// app/dashboard/page.tsx
'use client';

import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

export default function Dashboard() {
  const { data: session, status } = useSession();
  const router = useRouter();

  useEffect(() => {
    if (status === 'unauthenticated') {
      router.push('/login');
    }
  }, [status, router]);

  if (status === 'loading') {
    return <div>Loading...</div>;
  }

  // Set API client token
  apiClient.setAuthToken(session?.accessToken);

  return <div>Dashboard content...</div>;
}
```

---

## Environment Variables

```bash
# .env.local

# API Service
NEXT_PUBLIC_API_URL=http://localhost:8000

# Authentication (Future)
COGNITO_CLIENT_ID=your_client_id
COGNITO_CLIENT_SECRET=your_client_secret
COGNITO_ISSUER=https://cognito-idp.us-east-1.amazonaws.com/us-east-1_XXXXXXXXX

# NextAuth
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your_secret_key
```

---

## Styling with Tailwind CSS

### globals.css

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --primary: 221.2 83.2% 53.3%;
    --primary-foreground: 210 40% 98%;
    /* ... other CSS variables */
  }

  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    /* ... dark mode variables */
  }
}

@layer components {
  .container {
    @apply max-w-7xl mx-auto px-4 sm:px-6 lg:px-8;
  }
}
```

---

## Component Library (shadcn/ui)

### Installation

```bash
cd webapp
npx shadcn@latest init
npx shadcn@latest add button card badge
```

### Usage

```typescript
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';

export function Example() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Title</CardTitle>
      </CardHeader>
      <CardContent>
        <Button>Click me</Button>
      </CardContent>
    </Card>
  );
}
```

---

## Development Workflow

### Local Development

```bash
# Install dependencies
cd webapp
npm install

# Run dev server
npm run dev

# Access: http://localhost:3000

# Build for production
npm run build

# Start production server
npm start
```

### Docker Development

```bash
# Build and run
docker-compose up webapp

# Rebuild after changes
docker-compose up --build webapp
```

---

## Testing (Future)

### Component Tests (Vitest + React Testing Library)

```typescript
// __tests__/components/EntityList.test.tsx

import { render, screen } from '@testing-library/react';
import { EntityList } from '@/components/explorer/EntityList';

describe('EntityList', () => {
  it('renders entities', () => {
    const entities = [
      { id: 1, tags: [{ tag_def_id: 'site', value: 'Building A' }] },
      { id: 2, tags: [{ tag_def_id: 'equip', value: null }] },
    ];

    render(<EntityList entities={entities} />);

    expect(screen.getByText('Entity 1')).toBeInTheDocument();
    expect(screen.getByText('Entity 2')).toBeInTheDocument();
  });

  it('shows empty state', () => {
    render(<EntityList entities={[]} />);

    expect(screen.getByText('No entities found')).toBeInTheDocument();
  });
});
```

---

## Handoff Points

**To API Development Agent:**
- When API endpoints are missing
- When API response format changes

**To Docker Testing Agent:**
- When testing full stack integration
- When webapp needs to interact with all services

---

## Critical Design Principles

### 1. Server-Side Rendering (SSR)
Use Next.js App Router for optimal performance:
- Server components for static content
- Client components ('use client') for interactivity
- API route handlers for BFF pattern (optional)

### 2. Error Handling
```typescript
try {
  const data = await apiClient.getEntities(orgId);
  setEntities(data);
} catch (error) {
  console.error('Failed to fetch entities:', error);
  // Show user-friendly error message
  toast.error('Failed to load entities. Please try again.');
}
```

### 3. Loading States
Always show loading indicators:
```typescript
const [loading, setLoading] = useState(true);

if (loading) {
  return <Skeleton />;
}
```

### 4. Responsive Design
Use Tailwind responsive utilities:
```tsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  {/* Cards */}
</div>
```

---

## Related Documentation

- [Next.js Docs](https://nextjs.org/docs)
- [shadcn/ui](https://ui.shadcn.com/)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [Parent CLAUDE.md](../CLAUDE.md)

---

## Agent Boundaries

**✅ CAN:**
- Modify webapp code
- Add new pages and components
- Update UI library
- Configure Next.js
- Integrate with API service
- Request API endpoints from API Development Agent

**❌ CANNOT:**
- Modify API service
- Modify simulator service
- Change database schema (Haystack Database Agent)
- Run docker-compose (Docker Testing Agent)

---

## Current Implementation Status

**Implemented:**
- Basic Next.js setup
- Dockerfile for deployment

**Pending (Future Development):**
- Dashboard page
- Data explorer with tag filtering
- Time-series charts
- Admin panel (orgs, users)
- AWS Cognito authentication
- Comprehensive component library
- Unit and integration tests

When building features, prioritize in this order:
1. Data explorer (browse entities)
2. Time-series viewer (chart values)
3. Dashboard (system overview)
4. Admin panel (org/user management)
5. Authentication (AWS Cognito SSO)
