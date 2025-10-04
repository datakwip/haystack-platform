'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  getStatus,
  getMetrics,
  startSimulator,
  stopSimulator,
  resetSimulator,
  type StatusResponse,
  type MetricsResponse,
} from '@/lib/api-client'

export default function DashboardPage() {
  const [status, setStatus] = useState<StatusResponse | null>(null)
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchData = async () => {
    try {
      setError(null)
      const [statusData, metricsData] = await Promise.all([
        getStatus(),
        getMetrics(),
      ])
      setStatus(statusData)
      setMetrics(metricsData)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch data')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
    // Poll every 5 seconds
    const interval = setInterval(fetchData, 5000)
    return () => clearInterval(interval)
  }, [])

  const handleStart = async () => {
    setActionLoading(true)
    try {
      await startSimulator()
      await fetchData()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start simulator')
    } finally {
      setActionLoading(false)
    }
  }

  const handleStop = async () => {
    setActionLoading(true)
    try {
      await stopSimulator()
      await fetchData()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to stop simulator')
    } finally {
      setActionLoading(false)
    }
  }

  const handleReset = async () => {
    if (!confirm('Are you sure you want to reset the simulator? This will clear the state.')) {
      return
    }

    setActionLoading(true)
    try {
      await resetSimulator(false)
      await fetchData()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reset simulator')
    } finally {
      setActionLoading(false)
    }
  }

  const handleResetWithData = async () => {
    if (!confirm('Are you sure? This will CLEAR ALL GENERATED DATA. This cannot be undone.')) {
      return
    }

    setActionLoading(true)
    try {
      await resetSimulator(true)
      await fetchData()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reset simulator')
    } finally {
      setActionLoading(false)
    }
  }

  const getStatusBadgeVariant = (status: string | undefined) => {
    if (!status) return 'outline'
    switch (status.toLowerCase()) {
      case 'running':
        return 'default'
      case 'stopped':
        return 'secondary'
      case 'error':
        return 'destructive'
      default:
        return 'outline'
    }
  }

  const formatUptime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    return `${hours}h ${minutes}m`
  }

  const formatNumber = (num: number | null | undefined) => {
    if (num === null || num === undefined) return 'N/A'
    return num.toLocaleString()
  }

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'Never'
    try {
      return new Date(dateStr).toLocaleString()
    } catch {
      return dateStr
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Loading...</div>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold tracking-tight">Haystack Simulator</h1>
          <p className="text-muted-foreground mt-2">
            Control and monitor your building data generator
          </p>
        </div>
        <div className="flex gap-2">
          <Link href="/config">
            <Button variant="outline">Configuration</Button>
          </Link>
          <Link href="/activity">
            <Button variant="outline">Activity Log</Button>
          </Link>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-destructive/10 border border-destructive text-destructive px-4 py-3 rounded">
          {error}
        </div>
      )}

      {/* Status Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <Badge variant={getStatusBadgeVariant(status?.status)}>
                {status?.status || 'Unknown'}
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              Current simulator state
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Last Run</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatDate(status?.last_run || null)}
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              Most recent generation
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Points Generated</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatNumber(status?.points_generated_total)}
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              Total data points
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Uptime</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {metrics?.uptime_seconds ? formatUptime(metrics.uptime_seconds) : 'N/A'}
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              Service running time
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Control Panel */}
      <Card>
        <CardHeader>
          <CardTitle>Control Panel</CardTitle>
          <CardDescription>
            Start, stop, or reset the simulator
          </CardDescription>
        </CardHeader>
        <CardContent className="flex gap-3">
          <Button
            onClick={handleStart}
            disabled={actionLoading || status?.status === 'running'}
          >
            Start
          </Button>
          <Button
            onClick={handleStop}
            disabled={actionLoading || status?.status !== 'running'}
            variant="secondary"
          >
            Stop
          </Button>
          <Button
            onClick={handleReset}
            disabled={actionLoading}
            variant="outline"
          >
            Reset State
          </Button>
          <Button
            onClick={handleResetWithData}
            disabled={actionLoading}
            variant="destructive"
          >
            Reset + Clear Data
          </Button>
        </CardContent>
      </Card>

      {/* Metrics */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Generation Metrics</CardTitle>
            <CardDescription>Performance statistics</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Total Entities:</span>
              <span className="font-medium">{formatNumber(metrics?.total_entities)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Generation Rate:</span>
              <span className="font-medium">
                {metrics?.generation_rate_per_min
                  ? `${metrics.generation_rate_per_min.toFixed(1)} pts/min`
                  : 'N/A'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Errors (24h):</span>
              <span className="font-medium">{formatNumber(metrics?.error_count_24h)}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Quick Links</CardTitle>
            <CardDescription>Navigate to other sections</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            <Link href="/config">
              <Button variant="ghost" className="w-full justify-start">
                → Configuration Editor
              </Button>
            </Link>
            <Link href="/activity">
              <Button variant="ghost" className="w-full justify-start">
                → Activity Timeline
              </Button>
            </Link>
            <a href={`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080'}/docs`} target="_blank" rel="noopener noreferrer">
              <Button variant="ghost" className="w-full justify-start">
                → API Documentation
              </Button>
            </a>
          </CardContent>
        </Card>
      </div>

      {/* Error Message */}
      {status?.error_message && (
        <Card className="border-destructive">
          <CardHeader>
            <CardTitle className="text-destructive">Error</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="text-sm whitespace-pre-wrap">{status.error_message}</pre>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
