# Web Application Implementation Plan for Haystack Data Simulator

**← [Back to Main README](../README.md)** | **Future Roadmap**

**Status**: Future enhancement - Not yet implemented

**Related Documentation**:
- [MCP Server Guide](MCP_SERVER_IMPLEMENTATION_GUIDE.md) - MCP integration plan
- [Service Mode](../docs/SERVICE_MODE_SUMMARY.md) - Backend service capabilities

## Overview
This document outlines the comprehensive plan for building a web application that provides a graphical interface for all functions available in the Haystack Data Simulator, including data generation control, time series visualization, hierarchical entity exploration, and data validation.

## Core Requirements

### Functional Requirements
1. **Data Generation Control** - All functions from main.py:
   - Reset data option
   - Configure days of historical data (1-365)
   - Entity-only generation mode
   - Real-time progress tracking
   - Console log viewing

2. **Hierarchical Entity Explorer**
   - Tree view of site → equipment → points hierarchy
   - Search and filter by tags
   - View current values
   - Navigate to time series from any point

3. **Time Series Visualization**
   - Multi-point plotting
   - Time range selection
   - Data aggregation options
   - Export capabilities (CSV, JSON, Excel)

4. **Data Validation Dashboard**
   - Entity count summaries
   - Data coverage analysis
   - Relationship validation
   - Coherence checks

### Non-Functional Requirements
- **Authentication**: Prepared for future implementation
- **Multi-tenancy**: Architecture ready, not yet implemented
- **Real-time Updates**: Polling initially, WebSocket ready
- **Deployment**: Local development, Docker-ready for cloud
- **Browser Support**: Modern browsers only
- **Responsive Design**: Desktop-first, mobile later
- **Extensibility**: All components designed for future enhancement

## Technology Stack

### Backend
- **Framework**: FastAPI (Python)
  - Async-first for scalability
  - Automatic API documentation
  - WebSocket support built-in
- **Existing Code**: Reuse generators and database modules
- **Background Tasks**: Celery-ready architecture
- **API Versioning**: /api/v1/ structure

### Frontend
- **Framework**: Next.js 14 (App Router)
  - Server-side rendering capability
  - API routes for BFF pattern
  - Built-in optimization
- **UI Components**: shadcn/ui
  - Radix UI primitives
  - Tailwind CSS styling
  - Full control and customization
  - Consistent design system
- **State Management**: Zustand
  - Lightweight and performant
  - TypeScript-first
  - Easy to extend
- **Data Fetching**: TanStack Query
  - Advanced caching
  - Optimistic updates
  - Pagination support
- **Charts**: Recharts
  - Composable components
  - Matches shadcn/ui styling
  - Responsive by default

### Infrastructure
- **Database**: PostgreSQL + TimescaleDB (existing)
- **Containerization**: Docker + Docker Compose
- **Development**: Hot reload for both frontend and backend

## Project Structure

```
haystack-simulator-web/
├── backend/
│   ├── api/
│   │   ├── v1/                      # Versioned API
│   │   │   ├── endpoints/
│   │   │   │   ├── generation.py    # Data generation endpoints
│   │   │   │   ├── entities.py      # Entity CRUD and hierarchy
│   │   │   │   ├── timeseries.py    # Time series queries
│   │   │   │   └── validation.py    # Validation endpoints
│   │   │   ├── deps.py              # Dependency injection
│   │   │   └── middleware/          # Auth, CORS, rate limiting
│   │   └── v2/                      # Future API versions
│   ├── core/
│   │   ├── config.py                # Settings management
│   │   ├── security.py              # Auth scaffolding
│   │   ├── database.py              # DB connection
│   │   └── exceptions.py            # Custom exceptions
│   ├── services/                    # Business logic layer
│   │   ├── generation/
│   │   │   ├── manager.py           # Generation orchestration
│   │   │   └── progress.py          # Progress tracking
│   │   ├── validation/
│   │   │   ├── coherence.py         # Data coherence checks
│   │   │   └── coverage.py          # Coverage analysis
│   │   └── analytics/
│   │       ├── aggregation.py       # Data aggregation
│   │       └── export.py            # Export functionality
│   ├── models/                      # Pydantic models
│   │   ├── request/                 # Request schemas
│   │   └── response/                # Response schemas
│   ├── tests/                       # Backend tests
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── app/                         # Next.js App Router
│   │   ├── (auth)/                  # Future auth routes
│   │   │   ├── login/
│   │   │   └── layout.tsx
│   │   ├── (dashboard)/              # Main app
│   │   │   ├── layout.tsx           # Dashboard layout
│   │   │   ├── page.tsx             # Dashboard home
│   │   │   ├── generate/
│   │   │   │   └── page.tsx         # Generation control
│   │   │   ├── explorer/
│   │   │   │   ├── page.tsx         # Entity tree
│   │   │   │   └── [id]/            # Entity detail
│   │   │   ├── analytics/
│   │   │   │   └── page.tsx         # Time series charts
│   │   │   └── validate/
│   │   │       └── page.tsx         # Validation dashboard
│   │   └── api/                     # API route handlers
│   ├── components/
│   │   ├── ui/                      # shadcn/ui components
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── form.tsx
│   │   │   └── [other shadcn components]
│   │   ├── features/                # Feature-specific
│   │   │   ├── generation/
│   │   │   │   ├── generation-form.tsx
│   │   │   │   └── progress-display.tsx
│   │   │   ├── explorer/
│   │   │   │   ├── entity-tree.tsx
│   │   │   │   └── entity-detail.tsx
│   │   │   ├── analytics/
│   │   │   │   ├── time-series-chart.tsx
│   │   │   │   └── chart-controls.tsx
│   │   │   └── validation/
│   │   │       ├── validation-summary.tsx
│   │   │       └── coverage-heatmap.tsx
│   │   └── layouts/
│   │       ├── dashboard-header.tsx
│   │       ├── sidebar-nav.tsx
│   │       └── breadcrumbs.tsx
│   ├── lib/
│   │   ├── api-client.ts            # Centralized API client
│   │   ├── stores/                  # Zustand stores
│   │   │   ├── generation-store.ts
│   │   │   ├── entity-store.ts
│   │   │   └── ui-store.ts
│   │   ├── hooks/                   # Custom hooks
│   │   │   ├── use-entities.ts
│   │   │   └── use-time-series.ts
│   │   └── utils/
│   │       ├── formatters.ts
│   │       └── validators.ts
│   ├── styles/
│   │   └── globals.css              # Tailwind imports
│   ├── tests/                       # Frontend tests
│   ├── package.json
│   ├── tailwind.config.ts
│   ├── components.json              # shadcn/ui config
│   └── Dockerfile
│
├── docker-compose.yml                # Full stack deployment
├── docker-compose.dev.yml            # Development overrides
├── .env.example                      # Environment variables template
└── README.md                         # Setup and usage instructions
```

## API Design

### RESTful Endpoints

```python
# Generation Control
POST   /api/v1/generation/start      # Start generation job
GET    /api/v1/generation/status/{task_id}  # Get job status
GET    /api/v1/generation/history    # List past generations
DELETE /api/v1/generation/cancel/{task_id}  # Cancel running job

# Data Management
DELETE /api/v1/data/reset            # Reset all data
GET    /api/v1/data/summary          # Data statistics

# Entity Hierarchy
GET    /api/v1/entities              # List all entities
GET    /api/v1/entities/tree         # Hierarchical structure
GET    /api/v1/entities/{id}         # Entity details
GET    /api/v1/entities/{id}/children  # Child entities
GET    /api/v1/entities/{id}/points  # Entity points
GET    /api/v1/entities/{id}/tags    # Entity tags
GET    /api/v1/entities/search       # Search entities

# Time Series
GET    /api/v1/timeseries            # Query time series data
GET    /api/v1/timeseries/current    # Current values
GET    /api/v1/timeseries/aggregate  # Aggregated data
POST   /api/v1/timeseries/export     # Export data

# Validation
GET    /api/v1/validation/summary    # Overall validation status
GET    /api/v1/validation/coverage   # Data coverage report
GET    /api/v1/validation/coherence  # Coherence check results
GET    /api/v1/validation/relationships  # Relationship validation
```

### Request/Response Models

```python
# Generation Request
class GenerationRequest(BaseModel):
    days: int = Field(ge=1, le=365, default=30)
    reset: bool = False
    entities_only: bool = False
    # Extensibility fields
    organization_id: Optional[int] = None
    site_filter: Optional[List[str]] = None
    custom_config: Optional[Dict] = None

# Time Series Query
class TimeSeriesQuery(BaseModel):
    entity_ids: List[int]
    start_time: datetime
    end_time: datetime
    aggregation: Optional[str] = None  # raw, hourly, daily
    page: int = 1
    page_size: int = Field(le=10000, default=1000)
```

## UI Component Architecture

### Layout Structure

```tsx
// Main Dashboard Layout
<DashboardLayout>
  <DashboardHeader>
    <Breadcrumbs />
    <UserMenu />  {/* Future auth */}
  </DashboardHeader>
  
  <div className="flex h-full">
    <SidebarNav />
    <main className="flex-1 overflow-auto">
      <PageContent />
    </main>
  </div>
</DashboardLayout>
```

### Key Components

#### Generation Control
```tsx
interface GenerationFormData {
  days: number;
  reset: boolean;
  entitiesOnly: boolean;
}

<Card>
  <CardHeader>
    <CardTitle>Data Generation</CardTitle>
    <CardDescription>
      Configure and run data generation
    </CardDescription>
  </CardHeader>
  <CardContent>
    <Form<GenerationFormData>>
      {/* Reset Toggle with Warning */}
      <FormField name="reset">
        <Switch />
        <FormLabel>Reset existing data</FormLabel>
        {field.value && <Alert>Warning: This will delete all data</Alert>}
      </FormField>
      
      {/* Days Slider */}
      <FormField name="days">
        <FormLabel>Days to generate: {value}</FormLabel>
        <Slider min={1} max={365} />
      </FormField>
      
      {/* Entities Only Checkbox */}
      <FormField name="entitiesOnly">
        <Checkbox />
        <FormLabel>Generate entities only</FormLabel>
      </FormField>
    </Form>
  </CardContent>
  <CardFooter>
    <Button onClick={handleGenerate}>
      <Play className="mr-2 h-4 w-4" />
      Generate Data
    </Button>
  </CardFooter>
</Card>

{/* Progress Display */}
{isGenerating && (
  <Card className="mt-4">
    <CardContent>
      <Progress value={progress} />
      <ScrollArea className="h-48 mt-4">
        <pre>{logs}</pre>
      </ScrollArea>
    </CardContent>
  </Card>
)}
```

#### Entity Explorer
```tsx
interface EntityNode {
  id: number;
  name: string;
  type: string;
  tags: string[];
  children?: EntityNode[];
  points?: Point[];
}

<div className="flex h-full">
  {/* Tree Panel */}
  <div className="w-80 border-r">
    <div className="p-4">
      <Input 
        placeholder="Search entities..." 
        value={searchTerm}
        onChange={handleSearch}
      />
    </div>
    <ScrollArea className="h-full">
      <EntityTree 
        nodes={filteredNodes}
        selectedId={selectedEntityId}
        onSelect={handleEntitySelect}
      />
    </ScrollArea>
  </div>
  
  {/* Detail Panel */}
  <div className="flex-1">
    {selectedEntity && (
      <EntityDetail 
        entity={selectedEntity}
        onViewTimeSeries={handleViewTimeSeries}
      />
    )}
  </div>
</div>
```

#### Time Series Visualization
```tsx
<Card>
  <CardHeader>
    <div className="flex justify-between">
      <CardTitle>Time Series Analysis</CardTitle>
      <div className="flex gap-2">
        <DateRangePicker 
          value={dateRange}
          onChange={setDateRange}
        />
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline">
              <Download className="mr-2 h-4 w-4" />
              Export
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem onClick={() => handleExport('csv')}>
              CSV
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => handleExport('json')}>
              JSON
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => handleExport('excel')}>
              Excel
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  </CardHeader>
  <CardContent>
    <Tabs defaultValue="chart">
      <TabsList>
        <TabsTrigger value="chart">Chart</TabsTrigger>
        <TabsTrigger value="table">Table</TabsTrigger>
        <TabsTrigger value="statistics">Statistics</TabsTrigger>
      </TabsList>
      <TabsContent value="chart">
        <TimeSeriesChart 
          data={timeSeriesData}
          config={chartConfig}
        />
      </TabsContent>
      <TabsContent value="table">
        <DataTable data={timeSeriesData} />
      </TabsContent>
      <TabsContent value="statistics">
        <StatisticsSummary data={timeSeriesData} />
      </TabsContent>
    </Tabs>
  </CardContent>
</Card>
```

## State Management

### Zustand Stores

```typescript
// Generation Store
interface GenerationStore {
  status: 'idle' | 'running' | 'completed' | 'error';
  progress: number;
  logs: string[];
  taskId: string | null;
  
  startGeneration: (params: GenerationParams) => Promise<void>;
  checkStatus: () => Promise<void>;
  reset: () => void;
}

// Entity Store
interface EntityStore {
  entities: EntityNode[];
  selectedEntity: EntityNode | null;
  loading: boolean;
  
  fetchEntities: () => Promise<void>;
  selectEntity: (id: number) => void;
  searchEntities: (term: string) => void;
}

// UI Store
interface UIStore {
  sidebarOpen: boolean;
  theme: 'light' | 'dark';
  
  toggleSidebar: () => void;
  setTheme: (theme: 'light' | 'dark') => void;
}
```

## Docker Configuration

### docker-compose.yml
```yaml
version: '3.8'

services:
  postgres:
    image: timescale/timescaledb:latest-pg15
    environment:
      POSTGRES_DB: ${DB_NAME:-haystack}
      POSTGRES_USER: ${DB_USER:-haystack}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-password}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "${DB_PORT:-5432}:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-haystack}"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build: 
      context: ./backend
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
      SECRET_KEY: ${SECRET_KEY:-development-only-change-in-production}
      ALGORITHM: ${ALGORITHM:-HS256}
      ACCESS_TOKEN_EXPIRE_MINUTES: ${TOKEN_EXPIRE:-30}
      CORS_ORIGINS: ${CORS_ORIGINS:-http://localhost:3000}
    depends_on:
      postgres:
        condition: service_healthy
    ports:
      - "${API_PORT:-8000}:8000"
    volumes:
      - ./backend:/app
      - ./src:/app/legacy  # Access to existing code
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    environment:
      NEXT_PUBLIC_API_URL: ${API_URL:-http://localhost:8000}
      NEXT_PUBLIC_AUTH_ENABLED: ${AUTH_ENABLED:-false}
    depends_on:
      - backend
    ports:
      - "${WEB_PORT:-3000}:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
      - /app/.next
    command: npm run dev

volumes:
  postgres_data:

networks:
  default:
    name: haystack-network
```

### docker-compose.dev.yml
```yaml
version: '3.8'

services:
  backend:
    volumes:
      - ./backend:/app
      - ./src:/app/legacy
    environment:
      DEBUG: "true"
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    volumes:
      - ./frontend:/app
      - /app/node_modules
      - /app/.next
    environment:
      NODE_ENV: development
```

## Implementation Phases

**Starting with Time Series Visualization as Priority #1** - This provides immediate value for exploring and understanding the existing data, making it the logical foundation for validating data generation results.

### Phase 1: Time Series Analytics Foundation (Week 1)
- [ ] Create basic project structure
- [ ] Setup Next.js with TypeScript and shadcn/ui
- [ ] Setup FastAPI backend with minimal configuration
- [ ] Create time series API endpoints with pagination
- [ ] Build time series query logic with proper filtering
- [ ] Integrate Recharts for visualization
- [ ] Create basic chart component with shadcn/ui layout
- [ ] Add simple entity/point selector

### Phase 2: Time Series Enhancement (Week 2)
- [ ] Build advanced chart controls (zoom, pan, toggle series)
- [ ] Add comprehensive date range picker
- [ ] Implement data aggregation (raw, hourly, daily)
- [ ] Create multi-point plotting capability
- [ ] Add export functionality (CSV, JSON, Excel)
- [ ] Build statistics view and correlation analysis
- [ ] Add chart configuration persistence
- [ ] Implement graceful timeout handling for large queries

### Phase 3: Foundation & Infrastructure (Week 3)
- [ ] Setup complete Docker configuration
- [ ] Configure Zustand stores for state management
- [ ] Setup TanStack Query with intelligent caching
- [ ] Add error boundaries and loading states
- [ ] Implement proper error handling and user feedback
- [ ] Create development scripts and tooling
- [ ] Add basic authentication scaffolding
- [ ] Setup logging and performance monitoring

### Phase 4: Entity Explorer Integration (Week 4)
- [ ] Create entity hierarchy API endpoints
- [ ] Build hierarchical tree component with shadcn/ui
- [ ] Implement search and filter functionality
- [ ] Add entity detail views with current values
- [ ] Create tag badges and entity type indicators
- [ ] Connect Entity Explorer to Time Series (click to chart)
- [ ] Add breadcrumb navigation between views
- [ ] Implement entity relationship visualization

### Phase 5: Data Generation Control (Week 5)
- [ ] Create generation API endpoints
- [ ] Implement background task processing
- [ ] Build generation form with shadcn/ui
- [ ] Add real-time progress tracking (polling initially)
- [ ] Create console log viewer with streaming
- [ ] Add reset confirmation dialog with warnings
- [ ] Implement generation task history
- [ ] Connect generation completion to chart updates

### Phase 6: Validation Dashboard & Polish (Week 6)
- [ ] Create validation API endpoints
- [ ] Build validation dashboard with entity summaries
- [ ] Add data coverage analysis and heatmaps
- [ ] Create data coherence checks and alerts
- [ ] Implement relationship validator
- [ ] Add advanced analytics features
- [ ] Final UI/UX polish and optimization
- [ ] Complete documentation and deployment guides

## Development Scripts

### package.json (root)
```json
{
  "name": "haystack-simulator-web",
  "scripts": {
    "dev": "docker-compose -f docker-compose.yml -f docker-compose.dev.yml up",
    "dev:backend": "cd backend && uvicorn main:app --reload",
    "dev:frontend": "cd frontend && npm run dev",
    "build": "docker-compose build",
    "start": "docker-compose up -d",
    "stop": "docker-compose down",
    "logs": "docker-compose logs -f",
    "db:reset": "docker-compose exec backend python -m scripts.reset_db",
    "test": "npm run test:backend && npm run test:frontend",
    "test:backend": "cd backend && pytest",
    "test:frontend": "cd frontend && npm test",
    "shadcn:add": "cd frontend && npx shadcn-ui@latest add"
  }
}
```

## Configuration Management

### Environment Variables (.env.example)
```bash
# Database
DB_NAME=haystack
DB_USER=haystack
DB_PASSWORD=change-in-production
DB_PORT=5432

# Backend
API_PORT=8000
SECRET_KEY=change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
CORS_ORIGINS=http://localhost:3000

# Frontend
WEB_PORT=3000
API_URL=http://localhost:8000
AUTH_ENABLED=false

# Feature Flags (for extensibility)
ENABLE_MULTI_TENANCY=false
ENABLE_REALTIME_UPDATES=false
ENABLE_ADVANCED_ANALYTICS=false
```

## Security Considerations

### Current Implementation
- CORS configuration for local development
- Environment-based configuration
- SQL injection prevention via ORM
- Input validation with Pydantic

### Future Enhancements
- JWT authentication scaffolding ready
- Role-based access control structure
- API rate limiting preparation
- Audit logging capability
- Data encryption at rest

## Performance Optimizations

### Backend
- Async request handling
- Database connection pooling
- Query result caching
- Pagination for large datasets
- Background task processing

### Frontend
- Server-side rendering capability
- Code splitting by route
- Image optimization
- API response caching
- Virtualized lists for large datasets

## Testing Strategy

### Backend Testing
```python
# tests/test_generation.py
def test_generation_start():
    """Test generation job creation"""
    
def test_generation_progress():
    """Test progress tracking"""
    
def test_generation_cancel():
    """Test job cancellation"""
```

### Frontend Testing
```typescript
// tests/generation.test.tsx
describe('Generation Form', () => {
  it('should validate input parameters');
  it('should show warning on reset');
  it('should track progress');
});
```

## Monitoring and Observability

### Metrics to Track
- Generation job duration
- API response times
- Database query performance
- Error rates
- User interactions

### Logging Strategy
- Structured logging with context
- Log aggregation ready
- Error tracking integration points

## Documentation Requirements

### API Documentation
- Auto-generated with FastAPI/Swagger
- Example requests and responses
- Error code definitions

### User Documentation
- Setup guide
- User manual
- Troubleshooting guide
- FAQ section

### Developer Documentation
- Architecture overview
- Component documentation
- State management guide
- Contribution guidelines

## Future Enhancements

### Short-term (3-6 months)
- [ ] User authentication
- [ ] WebSocket for real-time updates
- [ ] Advanced search filters
- [ ] Custom chart configurations
- [ ] Scheduled generation jobs

### Medium-term (6-12 months)
- [ ] Multi-tenancy support
- [ ] Mobile responsive design
- [ ] Advanced analytics dashboard
- [ ] Machine learning anomaly detection
- [ ] Integration with external systems

### Long-term (12+ months)
- [ ] Cloud-native deployment (Kubernetes)
- [ ] Horizontal scaling
- [ ] Real-time collaboration
- [ ] API monetization
- [ ] White-label customization

## Success Metrics

### Technical Metrics
- Page load time < 2 seconds
- API response time < 500ms for queries
- 99.9% uptime
- Zero data loss during generation

### User Experience Metrics
- Time to first generation < 5 minutes
- Successful generation rate > 95%
- User task completion rate > 90%
- Error recovery rate > 80%

## Risk Mitigation

### Technical Risks
- **Database performance**: Implement caching and pagination
- **Memory usage**: Stream large datasets
- **Concurrent users**: Queue management for generation jobs
- **Data consistency**: Transaction management

### Business Risks
- **Scalability**: Cloud-ready architecture
- **Maintenance**: Comprehensive documentation
- **Security**: Regular updates and audits
- **Vendor lock-in**: Use open standards

## Conclusion

This implementation plan provides a solid foundation for building a modern, extensible web application for the Haystack Data Simulator. The architecture prioritizes:

1. **Developer Experience**: Modern tools and clear structure
2. **User Experience**: Clean UI with shadcn/ui components
3. **Extensibility**: Prepared for future enhancements
4. **Maintainability**: Clear separation of concerns
5. **Performance**: Optimized for large datasets

The phased approach ensures incremental delivery of value while maintaining system stability and quality throughout the development process.