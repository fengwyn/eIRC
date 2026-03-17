-- ClickHouse schema for eIRC analytics ingestion
-- Run with: clickhouse-client < clickhouse_schema.sql

CREATE DATABASE IF NOT EXISTS eirc;

-- Time-series table for sensor/message data ingested via batch_worker.py
-- Sorted by (node_name, user_id, timestamp) for fast per-device time-range queries
-- Example: SELECT * FROM eirc.messages
--          WHERE node_name = 'SensorRoom' AND user_id = 'ArduinoUno_MovementSensor_Room3'
--          AND timestamp > now() - INTERVAL 1 HOUR
--          ORDER BY timestamp;

CREATE TABLE IF NOT EXISTS eirc.messages (
    timestamp   DateTime64(3) DEFAULT now64(3),
    node_name   String,
    user_id     String,
    body        String,
    date        String
) ENGINE = MergeTree()
ORDER BY (node_name, user_id, timestamp);
