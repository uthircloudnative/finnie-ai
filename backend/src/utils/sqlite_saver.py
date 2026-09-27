"""
sqlite_saver.py — Colocated SQLite Checkpointer for LangGraph (SPEC-10)
=======================================================================
Implements BaseCheckpointSaver backed by finnie.db (or configured SQLite DB).
Stores checkpoints, blobs, and pending writes directly in the application database
matching Table 7 in docs/DATA_MODEL.md.
"""
from typing import Optional, Iterator, Sequence, Any, Dict, List
import sqlite3
import threading
from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
    ChannelVersions,
    get_checkpoint_id,
    get_checkpoint_metadata,
    RunnableConfig,
    WRITES_IDX_MAP,
    JsonPlusSerializer,
)


def sanitize_for_msgpack(obj: Any) -> Any:
    """
    Recursively converts numpy scalars, numpy arrays, or non-primitive objects
    into native Python primitives (float, int, str, list, dict) so that
    ormsgpack / jsonplus serialization never fails.
    """
    if obj is None:
        return None
    if hasattr(obj, "item") and callable(getattr(obj, "item")):
        try:
            return obj.item()
        except Exception:
            pass
    if hasattr(obj, "tolist") and callable(getattr(obj, "tolist")):
        try:
            return sanitize_for_msgpack(obj.tolist())
        except Exception:
            pass
    if isinstance(obj, dict):
        return {k: sanitize_for_msgpack(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [sanitize_for_msgpack(x) for x in obj]
    return obj


class SqliteSaver(BaseCheckpointSaver):
    """
    Production-grade SQLite checkpointer for LangGraph state persistence.
    Colocates tables in finnie.db for ACID-compliant in-session memory and HITL interrupts.
    """

    def __init__(self, db_path_or_conn: Any, serde: Optional[Any] = None) -> None:
        super().__init__(serde=serde or JsonPlusSerializer())
        self._is_path = isinstance(db_path_or_conn, str)
        self._db_path = db_path_or_conn if self._is_path else None
        self._conn = None if self._is_path else db_path_or_conn
        self._lock = threading.Lock()
        self.setup()

    def _get_connection(self) -> sqlite3.Connection:
        if self._is_path:
            conn = sqlite3.connect(self._db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            return conn
        return self._conn

    def setup(self) -> None:
        """Creates checkpointer tables in SQLite matching DATA_MODEL.md Table 7."""
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS checkpoints (
                        thread_id TEXT NOT NULL,
                        checkpoint_ns TEXT NOT NULL DEFAULT '',
                        checkpoint_id TEXT NOT NULL,
                        parent_checkpoint_id TEXT,
                        type TEXT,
                        checkpoint BLOB,
                        metadata BLOB,
                        PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
                    );
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS checkpoint_blobs (
                        thread_id TEXT NOT NULL,
                        checkpoint_ns TEXT NOT NULL DEFAULT '',
                        channel TEXT NOT NULL,
                        version TEXT NOT NULL,
                        type TEXT,
                        blob BLOB,
                        PRIMARY KEY (thread_id, checkpoint_ns, channel, version)
                    );
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS checkpoint_writes (
                        thread_id TEXT NOT NULL,
                        checkpoint_ns TEXT NOT NULL DEFAULT '',
                        checkpoint_id TEXT NOT NULL,
                        task_id TEXT NOT NULL,
                        idx INTEGER NOT NULL,
                        channel TEXT NOT NULL,
                        type TEXT,
                        blob BLOB,
                        task_path TEXT,
                        PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id, task_id, idx)
                    );
                """)
                conn.commit()
            finally:
                if self._is_path:
                    conn.close()

    def _load_blobs(self, conn: sqlite3.Connection, thread_id: str, checkpoint_ns: str, versions: ChannelVersions) -> Dict[str, Any]:
        channel_values: Dict[str, Any] = {}
        cursor = conn.cursor()
        for k, v in versions.items():
            cursor.execute(
                "SELECT type, blob FROM checkpoint_blobs WHERE thread_id = ? AND checkpoint_ns = ? AND channel = ? AND version = ?",
                (thread_id, checkpoint_ns, k, str(v))
            )
            row = cursor.fetchone()
            if row:
                t, b = row["type"], row["blob"]
                if t != "empty":
                    channel_values[k] = self.serde.loads_typed((t, b))
        return channel_values

    def get_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        thread_id: str = config["configurable"]["thread_id"]
        checkpoint_ns: str = config["configurable"].get("checkpoint_ns", "")
        cid = get_checkpoint_id(config)

        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                if cid:
                    cursor.execute(
                        "SELECT checkpoint_id, parent_checkpoint_id, type, checkpoint, metadata FROM checkpoints WHERE thread_id = ? AND checkpoint_ns = ? AND checkpoint_id = ?",
                        (thread_id, checkpoint_ns, cid)
                    )
                else:
                    cursor.execute(
                        "SELECT checkpoint_id, parent_checkpoint_id, type, checkpoint, metadata FROM checkpoints WHERE thread_id = ? AND checkpoint_ns = ? ORDER BY checkpoint_id DESC LIMIT 1",
                        (thread_id, checkpoint_ns)
                    )
                row = cursor.fetchone()
                if not row:
                    return None

                checkpoint_id = row["checkpoint_id"]
                parent_checkpoint_id = row["parent_checkpoint_id"]
                checkpoint_ = self.serde.loads_typed((row["type"], row["checkpoint"]))
                metadata = self.serde.loads_typed((row["type"], row["metadata"]))

                # Fetch pending writes
                cursor.execute(
                    "SELECT task_id, channel, type, blob FROM checkpoint_writes WHERE thread_id = ? AND checkpoint_ns = ? AND checkpoint_id = ? ORDER BY idx ASC",
                    (thread_id, checkpoint_ns, checkpoint_id)
                )
                write_rows = cursor.fetchall()
                pending_writes = [
                    (w["task_id"], w["channel"], self.serde.loads_typed((w["type"], w["blob"])))
                    for w in write_rows
                ]

                # Load channel blobs
                channel_values = self._load_blobs(conn, thread_id, checkpoint_ns, checkpoint_["channel_versions"])

                return CheckpointTuple(
                    config={
                        "configurable": {
                            "thread_id": thread_id,
                            "checkpoint_ns": checkpoint_ns,
                            "checkpoint_id": checkpoint_id,
                        }
                    },
                    checkpoint={
                        **checkpoint_,
                        "channel_values": channel_values,
                    },
                    metadata=metadata,
                    parent_config=(
                        {
                            "configurable": {
                                "thread_id": thread_id,
                                "checkpoint_ns": checkpoint_ns,
                                "checkpoint_id": parent_checkpoint_id,
                            }
                        }
                        if parent_checkpoint_id
                        else None
                    ),
                    pending_writes=pending_writes,
                )
            finally:
                if self._is_path:
                    conn.close()

    def list(
        self,
        config: Optional[RunnableConfig],
        *,
        filter: Optional[Dict[str, Any]] = None,
        before: Optional[RunnableConfig] = None,
        limit: Optional[int] = None,
    ) -> Iterator[CheckpointTuple]:
        thread_id = config["configurable"]["thread_id"] if config else None
        checkpoint_ns = config["configurable"].get("checkpoint_ns") if config else None
        before_cid = get_checkpoint_id(before) if before else None

        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                query = "SELECT thread_id, checkpoint_ns, checkpoint_id, parent_checkpoint_id, type, checkpoint, metadata FROM checkpoints WHERE 1=1"
                params: List[Any] = []
                if thread_id:
                    query += " AND thread_id = ?"
                    params.append(thread_id)
                if checkpoint_ns:
                    query += " AND checkpoint_ns = ?"
                    params.append(checkpoint_ns)
                if before_cid:
                    query += " AND checkpoint_id < ?"
                    params.append(before_cid)
                query += " ORDER BY checkpoint_id DESC"
                if limit:
                    query += " LIMIT ?"
                    params.append(limit)

                cursor.execute(query, params)
                rows = cursor.fetchall()
                for row in rows:
                    t_id = row["thread_id"]
                    ns = row["checkpoint_ns"]
                    c_id = row["checkpoint_id"]
                    parent_c_id = row["parent_checkpoint_id"]
                    metadata = self.serde.loads_typed((row["type"], row["metadata"]))

                    if filter and not all(metadata.get(k) == v for k, v in filter.items()):
                        continue

                    checkpoint_ = self.serde.loads_typed((row["type"], row["checkpoint"]))
                    channel_values = self._load_blobs(conn, t_id, ns, checkpoint_["channel_versions"])

                    # Fetch writes
                    cursor.execute(
                        "SELECT task_id, channel, type, blob FROM checkpoint_writes WHERE thread_id = ? AND checkpoint_ns = ? AND checkpoint_id = ? ORDER BY idx ASC",
                        (t_id, ns, c_id)
                    )
                    write_rows = cursor.fetchall()
                    pending_writes = [
                        (w["task_id"], w["channel"], self.serde.loads_typed((w["type"], w["blob"])))
                        for w in write_rows
                    ]

                    yield CheckpointTuple(
                        config={
                            "configurable": {
                                "thread_id": t_id,
                                "checkpoint_ns": ns,
                                "checkpoint_id": c_id,
                            }
                        },
                        checkpoint={
                            **checkpoint_,
                            "channel_values": channel_values,
                        },
                        metadata=metadata,
                        parent_config=(
                            {
                                "configurable": {
                                    "thread_id": t_id,
                                    "checkpoint_ns": ns,
                                    "checkpoint_id": parent_c_id,
                                }
                            }
                            if parent_c_id
                            else None
                        ),
                        pending_writes=pending_writes,
                    )
            finally:
                if self._is_path:
                    conn.close()

    def put(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
        c = sanitize_for_msgpack(checkpoint.copy())
        values: Dict[str, Any] = c.pop("channel_values")

        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                # 1. Save Blobs
                for k, v in new_versions.items():
                    if k in values:
                        clean_v = sanitize_for_msgpack(values[k])
                        t, b = self.serde.dumps_typed(clean_v)
                    else:
                        t, b = ("empty", b"")
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO checkpoint_blobs (thread_id, checkpoint_ns, channel, version, type, blob)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (thread_id, checkpoint_ns, k, str(v), t, b)
                    )

                # 2. Save Checkpoint & Metadata
                c_type, c_blob = self.serde.dumps_typed(c)
                meta_obj = sanitize_for_msgpack(get_checkpoint_metadata(config, metadata))
                m_type, m_blob = self.serde.dumps_typed(meta_obj)
                parent_id = config["configurable"].get("checkpoint_id")

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO checkpoints (thread_id, checkpoint_ns, checkpoint_id, parent_checkpoint_id, type, checkpoint, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (thread_id, checkpoint_ns, checkpoint["id"], parent_id, c_type, c_blob, m_blob)
                )
                conn.commit()
            finally:
                if self._is_path:
                    conn.close()

        return {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_ns": checkpoint_ns,
                "checkpoint_id": checkpoint["id"],
            }
        }

    def put_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
        checkpoint_id = config["configurable"]["checkpoint_id"]

        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                for idx, (channel, val) in enumerate(writes):
                    write_idx = WRITES_IDX_MAP.get(channel, idx)
                    clean_val = sanitize_for_msgpack(val)
                    t, b = self.serde.dumps_typed(clean_val)
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO checkpoint_writes (thread_id, checkpoint_ns, checkpoint_id, task_id, idx, channel, type, blob, task_path)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (thread_id, checkpoint_ns, checkpoint_id, task_id, write_idx, channel, t, b, task_path)
                    )
                conn.commit()
            finally:
                if self._is_path:
                    conn.close()

    def delete_thread(self, thread_id: str) -> None:
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM checkpoints WHERE thread_id = ?", (thread_id,))
                cursor.execute("DELETE FROM checkpoint_blobs WHERE thread_id = ?", (thread_id,))
                cursor.execute("DELETE FROM checkpoint_writes WHERE thread_id = ?", (thread_id,))
                conn.commit()
            finally:
                if self._is_path:
                    conn.close()

    async def aget_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        return self.get_tuple(config)

    async def alist(
        self,
        config: Optional[RunnableConfig],
        *,
        filter: Optional[Dict[str, Any]] = None,
        before: Optional[RunnableConfig] = None,
        limit: Optional[int] = None,
    ) -> Iterator[CheckpointTuple]:
        for item in self.list(config, filter=filter, before=before, limit=limit):
            yield item

    async def aput(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        return self.put(config, checkpoint, metadata, new_versions)

    async def aput_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        return self.put_writes(config, writes, task_id, task_path)

    async def adelete_thread(self, thread_id: str) -> None:
        return self.delete_thread(thread_id)
