'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { getConfig, updateConfig, type ControlResponse } from '@/lib/api-client'

export default function ConfigPage() {
  const [config, setConfig] = useState<Record<string, any> | null>(null)
  const [editedConfig, setEditedConfig] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [isEditing, setIsEditing] = useState(false)

  useEffect(() => {
    fetchConfig()
  }, [])

  const fetchConfig = async () => {
    try {
      setError(null)
      const data = await getConfig()
      setConfig(data)
      setEditedConfig(JSON.stringify(data, null, 2))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch configuration')
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    setSaving(true)
    setError(null)
    setSuccess(null)

    try {
      // Parse the JSON
      const parsedConfig = JSON.parse(editedConfig)

      // Update via API
      const response = await updateConfig(parsedConfig)

      setSuccess(response.message || 'Configuration saved successfully')
      setConfig(parsedConfig)
      setIsEditing(false)

      // Refresh after 2 seconds
      setTimeout(fetchConfig, 2000)
    } catch (err) {
      if (err instanceof SyntaxError) {
        setError('Invalid JSON format. Please check your syntax.')
      } else {
        setError(err instanceof Error ? err.message : 'Failed to save configuration')
      }
    } finally {
      setSaving(false)
    }
  }

  const handleReset = () => {
    if (config) {
      setEditedConfig(JSON.stringify(config, null, 2))
      setError(null)
      setSuccess(null)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Loading configuration...</div>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6 space-y-6 max-w-6xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold tracking-tight">Configuration</h1>
          <p className="text-muted-foreground mt-2">
            View and edit simulator configuration
          </p>
        </div>
        <Link href="/">
          <Button variant="outline">← Back to Dashboard</Button>
        </Link>
      </div>

      {/* Success Message */}
      {success && (
        <div className="bg-green-50 border border-green-200 text-green-800 px-4 py-3 rounded">
          {success}
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="bg-destructive/10 border border-destructive text-destructive px-4 py-3 rounded">
          {error}
        </div>
      )}

      {/* Configuration Editor */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Simulator Configuration</CardTitle>
              <CardDescription>
                Edit the JSON configuration below
              </CardDescription>
            </div>
            <div className="flex gap-2">
              {!isEditing ? (
                <Button onClick={() => setIsEditing(true)}>
                  Edit
                </Button>
              ) : (
                <>
                  <Button
                    onClick={handleReset}
                    variant="outline"
                    disabled={saving}
                  >
                    Reset
                  </Button>
                  <Button
                    onClick={() => {
                      setIsEditing(false)
                      handleReset()
                    }}
                    variant="secondary"
                    disabled={saving}
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={handleSave}
                    disabled={saving}
                  >
                    {saving ? 'Saving...' : 'Save'}
                  </Button>
                </>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {isEditing ? (
            <textarea
              className="w-full h-[600px] font-mono text-sm p-4 border rounded bg-muted"
              value={editedConfig}
              onChange={(e) => setEditedConfig(e.target.value)}
              spellCheck={false}
            />
          ) : (
            <pre className="w-full h-[600px] overflow-auto font-mono text-sm p-4 border rounded bg-muted">
              {config ? JSON.stringify(config, null, 2) : 'No configuration available'}
            </pre>
          )}
        </CardContent>
      </Card>

      {/* Info Card */}
      <Card>
        <CardHeader>
          <CardTitle>Configuration Notes</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <p>
            <strong>Note:</strong> Configuration changes will be applied immediately after saving.
          </p>
          <p>
            The configuration is stored in the simulator state database and persists across restarts.
          </p>
          <p>
            <strong>Warning:</strong> Invalid configuration may cause the simulator to fail on next restart.
            Always ensure your JSON is valid before saving.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
