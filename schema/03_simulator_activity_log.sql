-- Simulator Activity Log Table
-- Tracks domain-level events for the Haystack building data simulator
-- Provides audit trail and debugging information

-- Create core schema in state database (if not already exists)
CREATE SCHEMA IF NOT EXISTS core;

-- Activity log table
CREATE TABLE IF NOT EXISTS core.simulator_activity_log (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    details JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_simulator_activity_timestamp
ON core.simulator_activity_log(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_simulator_activity_event_type
ON core.simulator_activity_log(event_type);

-- Comments for documentation
COMMENT ON TABLE core.simulator_activity_log IS 'Tracks domain-level events and activity for the simulator service';
COMMENT ON COLUMN core.simulator_activity_log.timestamp IS 'When the event occurred';
COMMENT ON COLUMN core.simulator_activity_log.event_type IS 'Type of event: generation, gap_fill, error, start, stop, config_change, reset';
COMMENT ON COLUMN core.simulator_activity_log.message IS 'Human-readable event description';
COMMENT ON COLUMN core.simulator_activity_log.details IS 'Additional event context as JSON (entity counts, intervals, errors, etc.)';
