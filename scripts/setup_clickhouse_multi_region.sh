#!/usr/bin/env bash
set -euo pipefail

# Example script to configure replication for TokenTally's ClickHouse ledger
# between a US and EU cluster. Adjust the hostnames and ZooKeeper paths for
# your environment. Both clusters must share the same ZooKeeper service.

US_HOST="us-clickhouse.example.com"
EU_HOST="eu-clickhouse.example.com"
ZOOKEEPER_PATH="/tokentally/ledger"

# Create the database on both clusters
for HOST in "$US_HOST" "$EU_HOST"; do
  clickhouse-client --host "$HOST" --query "CREATE DATABASE IF NOT EXISTS ledger" || true
done

# Set up replicated tables using the same shard and replica names
clickhouse-client --host "$US_HOST" --query "\
CREATE TABLE IF NOT EXISTS ledger.usage_events (
  customer_id UInt64,
  ts DateTime,
  tokens UInt32
) ENGINE = ReplicatedReplacingMergeTree('${ZOOKEEPER_PATH}/usage_events/{shard}', 'us1')
PARTITION BY toDate(ts)
ORDER BY (customer_id, ts)
"

clickhouse-client --host "$EU_HOST" --query "\
CREATE TABLE IF NOT EXISTS ledger.usage_events (
  customer_id UInt64,
  ts DateTime,
  tokens UInt32
) ENGINE = ReplicatedReplacingMergeTree('${ZOOKEEPER_PATH}/usage_events/{shard}', 'eu1')
PARTITION BY toDate(ts)
ORDER BY (customer_id, ts)
"

# Replication is now configured. Inserts to one cluster will sync to the other.
