#!/usr/bin/env python3

# batch_worker.py — Redis Streams → ClickHouse ingestion daemon

# Reads message data from Redis Streams (written by Node servers via XADD)
# and batch-inserts into ClickHouse for analytics.

# Flush triggers:
#   - Buffer reaches BATCH_SIZE entries (default 1000)
#   - FLUSH_INTERVAL seconds elapsed since last flush (default 10s)

# Usage:
#   python -m src.utils.batch_worker
#   python -m src.utils.batch_worker --batch-size 500 --flush-interval 5
#   python -m src.utils.batch_worker --redis-host localhost --redis-port 6379
#                                    --ch-host localhost --ch-port 8123


import argparse
import signal
import sys
import time

import redis
import clickhouse_connect


# Defaults
BATCH_SIZE = 1000
FLUSH_INTERVAL = 10  # seconds
CONSUMER_GROUP = "eirc_batch_workers"
CONSUMER_NAME = "worker-1"
STREAM_PATTERN = "eirc:stream:*"
BLOCK_TIMEOUT = 5000  # ms — XREADGROUP block timeout


class BatchWorker:

    def __init__(self, redis_client, ch_client,
                 batch_size=BATCH_SIZE, flush_interval=FLUSH_INTERVAL):

        self.redis = redis_client
        self.ch = ch_client
        self.batch_size = batch_size
        self.flush_interval = flush_interval

        self.buffer = []        # [(node_name, user_id, body, date), ...]
        self.pending_acks = {}  # {stream_key: [message_id, ...]}
        self.last_flush = time.time()
        self.running = True

        # Graceful shutdown
        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)


    def _shutdown(self, signum, frame):
        print(f"\nReceived signal {signum}, flushing buffer and shutting down...")
        self.running = False


    def _discover_streams(self):
        # Find all eirc:stream:* keys currently in Redis.

        keys = []
        cursor = 0
        while True:
            cursor, batch = self.redis.scan(cursor, match=STREAM_PATTERN, count=100)
            keys.extend(batch)
            if cursor == 0:
                break
        return keys


    def _ensure_consumer_groups(self, streams):
        # Create consumer groups on streams that don't have one yet.

        for stream in streams:
            try:
                self.redis.xgroup_create(stream, CONSUMER_GROUP, id="0", mkstream=False)
                print(f"Created consumer group '{CONSUMER_GROUP}' on {stream}")
            except redis.exceptions.ResponseError as e:
                # Group already exists — expected on restart
                if "BUSYGROUP" in str(e):
                    pass
                else:
                    raise


    def _flush(self):
        # Batch-insert buffered entries into ClickHouse, then ACK in Redis.

        if not self.buffer:
            self.last_flush = time.time()
            return

        rows = self.buffer
        count = len(rows)

        try:
            self.ch.insert(
                "eirc.messages",
                rows,
                column_names=["node_name", "user_id", "body", "date"]
            )
            print(f"Inserted {count} rows into ClickHouse")

        except Exception as e:
            # On ClickHouse failure, keep buffer for retry on next cycle
            print(f"ClickHouse insert failed ({count} rows kept in buffer): {e}")
            self.last_flush = time.time()
            return

        # ACK successfully inserted entries
        for stream_key, msg_ids in self.pending_acks.items():
            if msg_ids:
                self.redis.xack(stream_key, CONSUMER_GROUP, *msg_ids)

        self.buffer.clear()
        self.pending_acks.clear()
        self.last_flush = time.time()


    def _should_flush(self):
        # Check if flush triggers are met.

        if len(self.buffer) >= self.batch_size:
            return True
        if time.time() - self.last_flush >= self.flush_interval:
            return True
        return False


    def run(self):
        # Main loop: discover streams, read, buffer, flush.

        print(f"Batch worker started (batch_size={self.batch_size}, "
              f"flush_interval={self.flush_interval}s)")

        while self.running:
            try:
                # Discover streams (new Nodes may appear at any time)
                streams = self._discover_streams()
                if not streams:
                    time.sleep(1)
                    continue

                self._ensure_consumer_groups(streams)

                # Build the streams dict for XREADGROUP: {stream: ">"} reads new messages
                stream_dict = {s: ">" for s in streams}

                # Blocking read — returns after BLOCK_TIMEOUT ms or when data arrives
                results = self.redis.xreadgroup(
                    CONSUMER_GROUP, CONSUMER_NAME,
                    stream_dict,
                    count=self.batch_size,
                    block=BLOCK_TIMEOUT
                )

                if results:
                    for stream_key, messages in results:
                        # stream_key may be bytes or str depending on decode_responses
                        if isinstance(stream_key, bytes):
                            stream_key = stream_key.decode()

                        # Extract node name from stream key: "eirc:stream:{node_name}"
                        node_name = stream_key.split(":", 2)[2] if stream_key.count(":") >= 2 else stream_key

                        if stream_key not in self.pending_acks:
                            self.pending_acks[stream_key] = []

                        for msg_id, fields in messages:
                            user = fields.get("user", "")
                            body = fields.get("body", "")
                            date = fields.get("date", "")

                            self.buffer.append((node_name, user, body, date))
                            self.pending_acks[stream_key].append(msg_id)

                # Check flush triggers
                if self._should_flush():
                    self._flush()

            except redis.exceptions.ConnectionError as e:
                print(f"Redis connection lost: {e}. Retrying in 5s...")
                time.sleep(5)

            except Exception as e:
                print(f"Unexpected error: {e}")
                time.sleep(1)

        # Final flush on shutdown
        self._flush()
        print("Batch worker stopped.")



def main():

    parser = argparse.ArgumentParser(description="eIRC Batch Worker: Redis Streams → ClickHouse")

    # Redis
    parser.add_argument("--redis-host", default="localhost")
    parser.add_argument("--redis-port", type=int, default=6379)
    parser.add_argument("--redis-db", type=int, default=0)

    # ClickHouse
    parser.add_argument("--ch-host", default="localhost")
    parser.add_argument("--ch-port", type=int, default=8123)
    parser.add_argument("--ch-user", default="default")
    parser.add_argument("--ch-password", default="")

    # Worker tuning
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE,
                        help=f"Flush after N entries (default {BATCH_SIZE})")
    parser.add_argument("--flush-interval", type=float, default=FLUSH_INTERVAL,
                        help=f"Flush after N seconds (default {FLUSH_INTERVAL})")

    args = parser.parse_args()

    # Connect to Redis
    redis_client = redis.Redis(
        host=args.redis_host, port=args.redis_port, db=args.redis_db,
        decode_responses=True
    )
    redis_client.ping()
    print(f"Redis connected at {args.redis_host}:{args.redis_port}")

    # Connect to ClickHouse
    ch_client = clickhouse_connect.get_client(
        host=args.ch_host, port=args.ch_port,
        username=args.ch_user, password=args.ch_password
    )
    ch_version = ch_client.server_version
    print(f"ClickHouse connected at {args.ch_host}:{args.ch_port} (v{ch_version})")

    worker = BatchWorker(redis_client, ch_client,
                         batch_size=args.batch_size,
                         flush_interval=args.flush_interval)
    worker.run()


if __name__ == "__main__":
    main()
