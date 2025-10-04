'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { getActivity, type ActivityEvent } from '@/lib/api-client'

export default function ActivityPage() {
  const [events, setEvents] = useState<ActivityEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filter, setFilter] = useState<string | null>(null)
  const [offset, setOffset] = useState(0)
  const [hasMore, setHasMore] = useState(true)
  const limit = 50

  useEffect(() => {
    fetchEvents()
  }, [filter, offset])

  const fetchEvents = async () => {
    try {
      setError(null)
      const data = await getActivity(limit, offset, filter || undefined)

      if (offset === 0) {
        setEvents(data.events)
      } else {
        setEvents(prev => [...prev, ...data.events])
      }

      setHasMore(data.count === limit)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch activity log')
    } finally {
      setLoading(false)
    }
  }

  const handleFilterChange = (newFilter: string | null) => {
    setFilter(newFilter)
    setOffset(0)
    setEvents([])
    setLoading(true)
  }

  const handleLoadMore = () => {
    setOffset(prev => prev + limit)
  }

  const getEventBadgeVariant = (eventType: string) => {
    switch (eventType) {
      case 'generation':
        return 'default'
      case 'start':
        return 'default'
      case 'stop':
        return 'secondary'
      case 'error':
        return 'destructive'
      case 'gap_fill':
        return 'secondary'
      case 'config_change':
        return 'outline'
      case 'reset':
        return 'outline'
      default:
        return 'outline'
    }
  }

  const formatTimestamp = (timestamp: string) => {
    try {
      const date = new Date(timestamp)
      return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      })
    } catch {
      return timestamp
    }
  }

  const eventTypes = ['generation', 'gap_fill', 'start', 'stop', 'error', 'config_change', 'reset']

  if (loading && events.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Loading activity log...</div>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6 space-y-6 max-w-6xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold tracking-tight">Activity Timeline</h1>
          <p className="text-muted-foreground mt-2">
            Monitor simulator events and operations
          </p>
        </div>
        <Link href="/">
          <Button variant="outline">← Back to Dashboard</Button>
        </Link>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-destructive/10 border border-destructive text-destructive px-4 py-3 rounded">
          {error}
        </div>
      )}

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Filter Events</CardTitle>
          <CardDescription>Filter by event type</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            <Button
              variant={filter === null ? 'default' : 'outline'}
              size="sm"
              onClick={() => handleFilterChange(null)}
            >
              All Events
            </Button>
            {eventTypes.map((type) => (
              <Button
                key={type}
                variant={filter === type ? 'default' : 'outline'}
                size="sm"
                onClick={() => handleFilterChange(type)}
              >
                {type.replace('_', ' ')}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Activity Timeline */}
      <Card>
        <CardHeader>
          <CardTitle>
            Recent Activity
            {filter && <span className="text-sm font-normal ml-2">({filter.replace('_', ' ')})</span>}
          </CardTitle>
          <CardDescription>
            {events.length} event{events.length !== 1 ? 's' : ''} shown
          </CardDescription>
        </CardHeader>
        <CardContent>
          {events.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No events found
            </div>
          ) : (
            <div className="space-y-4">
              {events.map((event) => (
                <div
                  key={event.id}
                  className="border rounded-lg p-4 hover:bg-accent/50 transition-colors"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 space-y-2">
                      <div className="flex items-center gap-2">
                        <Badge variant={getEventBadgeVariant(event.event_type)}>
                          {event.event_type}
                        </Badge>
                        <span className="text-sm text-muted-foreground">
                          {formatTimestamp(event.timestamp)}
                        </span>
                      </div>
                      <p className="text-sm">{event.message}</p>
                      {event.details && Object.keys(event.details).length > 0 && (
                        <details className="text-xs">
                          <summary className="cursor-pointer text-muted-foreground hover:text-foreground">
                            Show details
                          </summary>
                          <pre className="mt-2 p-2 bg-muted rounded overflow-auto">
                            {JSON.stringify(event.details, null, 2)}
                          </pre>
                        </details>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Load More */}
          {hasMore && events.length > 0 && (
            <div className="mt-6 text-center">
              <Button
                onClick={handleLoadMore}
                variant="outline"
                disabled={loading}
              >
                {loading ? 'Loading...' : 'Load More'}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
