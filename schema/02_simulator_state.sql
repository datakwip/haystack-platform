-- Simulator State Tracking Table
-- This table maintains the state of the continuous data simulator
-- allowing it to resume operations after restarts

-- Create core schema in state database
CREATE SCHEMA IF NOT EXISTS core;

CREATE TABLE IF NOT EXISTS core.simulator_state (
    id SERIAL PRIMARY KEY,
    service_name VARCHAR(100) NOT NULL DEFAULT 'haystack_simulator',
    last_run_timestamp TIMESTAMPTZ,
    totalizers JSONB,
    status VARCHAR(50) NOT NULL DEFAULT 'stopped',
    config JSONB,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for quick lookups by service name
CREATE INDEX IF NOT EXISTS idx_simulator_state_service_name
ON core.simulator_state(service_name);

-- Index for status queries
CREATE INDEX IF NOT EXISTS idx_simulator_state_status
ON core.simulator_state(status);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_simulator_state_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_simulator_state_timestamp
    BEFORE UPDATE ON core.simulator_state
    FOR EACH ROW
    EXECUTE FUNCTION update_simulator_state_timestamp();

-- Initialize default state record if not exists
INSERT INTO core.simulator_state (service_name, status, totalizers, config)
VALUES (
    'haystack_simulator',
    'initialized',
    '{"electric_energy": 0.0, "gas_volume": 0.0, "water_volume": 0.0, "chiller_energy": {}}',
    '{"version": "1.0", "mode": "continuous"}'
)
ON CONFLICT DO NOTHING;

-- Comments for documentation
COMMENT ON TABLE core.simulator_state IS 'Tracks the operational state of the continuous data simulator';
COMMENT ON COLUMN core.simulator_state.service_name IS 'Unique identifier for the simulator service instance';
COMMENT ON COLUMN core.simulator_state.last_run_timestamp IS 'Timestamp of the last successful data generation';
COMMENT ON COLUMN core.simulator_state.totalizers IS 'JSON object storing last known totalizer values (energy, volume meters)';
COMMENT ON COLUMN core.simulator_state.status IS 'Current status: initialized, running, stopped, error';
COMMENT ON COLUMN core.simulator_state.config IS 'Service configuration and metadata';
COMMENT ON COLUMN core.simulator_state.error_message IS 'Last error message if status is error';
