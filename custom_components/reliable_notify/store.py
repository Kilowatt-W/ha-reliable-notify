"""Durable SQLite queue: one transaction per fan-out operation, at-least-once."""
from __future__ import annotations
import asyncio
import json
import hashlib
import os
import shutil
import tempfile
import sqlite3
import time
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
import hashlib
from pathlib import Path

MAX_COMPLETED_ARCHIVE_BYTES = 32 * 1024 * 1024

def _ensure_companion_tag(payload, key):
    updated=dict(payload)
    nested=dict(updated.get("data") or {})
    nested.setdefault("tag","rn_"+hashlib.sha256(key.encode("utf-8")).hexdigest()[:24])
    updated["data"]=nested
    return updated


PRIORITY_ORDER = "CASE priority WHEN 'critical' THEN 0 WHEN 'warning' THEN 1 ELSE 2 END"


class QueueStore:
    def __init__(self, path):
        self.path = Path(path)
        self._lock = asyncio.Lock()

    def _execute(self, op, *args):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(self.path, timeout=15)
        try:
            con.execute("PRAGMA busy_timeout=15000")
            con.execute("PRAGMA journal_mode=WAL")
            con.execute("""CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT NOT NULL, title TEXT, target TEXT NOT NULL,
                priority TEXT NOT NULL, dedup_key TEXT, expires_at REAL,
                attempts INTEGER NOT NULL DEFAULT 0, next_attempt REAL NOT NULL,
                created_at REAL NOT NULL, last_error TEXT)""")
            cols = {r[1] for r in con.execute("PRAGMA table_info(messages)")}
            for name, definition in (("action", "TEXT NOT NULL DEFAULT 'notify.send_message'"),
                                     ("payload_json", "TEXT NOT NULL DEFAULT '{}'"),
                                     ("lease_until", "REAL"), ("media_path", "TEXT"),
                                     ("media_paths_json", "TEXT NOT NULL DEFAULT '[]'")):
                if name not in cols:
                    con.execute(f"ALTER TABLE messages ADD COLUMN {name} {definition}")
            con.execute("""CREATE TABLE IF NOT EXISTS acknowledgements (
                ack_key TEXT PRIMARY KEY, message_id INTEGER NOT NULL,
                title TEXT, message TEXT NOT NULL, priority TEXT NOT NULL,
                created_at REAL NOT NULL, steps_json TEXT NOT NULL,
                next_step INTEGER NOT NULL DEFAULT 0,
                acknowledged_at REAL, acknowledged_by TEXT
            )""")
            cols_ack={r[1] for r in con.execute("PRAGMA table_info(acknowledgements)")}
            if "action_id" not in cols_ack:
                con.execute("ALTER TABLE acknowledgements ADD COLUMN action_id TEXT")
            for (key,) in con.execute("SELECT ack_key FROM acknowledgements WHERE action_id IS NULL"):
                digest=hashlib.sha256(key.encode("utf8")).hexdigest()[:16]
                con.execute("UPDATE acknowledgements SET action_id=? WHERE ack_key=?",(digest,key))
            con.execute("CREATE INDEX IF NOT EXISTS idx_ack_action ON acknowledgements(action_id)")
            con.execute("CREATE INDEX IF NOT EXISTS idx_ack_active ON acknowledgements(acknowledged_at,created_at)")
            con.execute("""CREATE TABLE IF NOT EXISTS send_rate_windows (
                bucket TEXT PRIMARY KEY, window_start REAL NOT NULL,
                attempts INTEGER NOT NULL DEFAULT 0)""")
            message_cols = {r[1] for r in con.execute("PRAGMA table_info(messages)")}
            if "occurrences" not in message_cols:
                con.execute("ALTER TABLE messages ADD COLUMN occurrences INTEGER NOT NULL DEFAULT 1")
            con.execute("CREATE INDEX IF NOT EXISTS idx_due ON messages(next_attempt)")
            con.execute("CREATE INDEX IF NOT EXISTS idx_dedup ON messages(dedup_key,target,action)")
            con.execute("CREATE TABLE IF NOT EXISTS metrics (key TEXT PRIMARY KEY,value INTEGER NOT NULL DEFAULT 0)")
            con.execute("""CREATE TABLE IF NOT EXISTS dead_letters (
                id INTEGER PRIMARY KEY, message TEXT NOT NULL, title TEXT,
                target TEXT NOT NULL, priority TEXT NOT NULL, dedup_key TEXT,
                expires_at REAL, attempts INTEGER NOT NULL, next_attempt REAL NOT NULL,
                created_at REAL NOT NULL, last_error TEXT, action TEXT NOT NULL,
                payload_json TEXT NOT NULL, lease_until REAL, failed_at REAL NOT NULL, media_path TEXT)""")
            dead_cols = {r[1] for r in con.execute("PRAGMA table_info(dead_letters)")}
            if "media_path" not in dead_cols:
                con.execute("ALTER TABLE dead_letters ADD COLUMN media_path TEXT")
            if "media_paths_json" not in dead_cols:
                con.execute("ALTER TABLE dead_letters ADD COLUMN media_paths_json TEXT NOT NULL DEFAULT '[]'")
            if "occurrences" not in dead_cols:
                con.execute("ALTER TABLE dead_letters ADD COLUMN occurrences INTEGER NOT NULL DEFAULT 1")
            con.execute("""CREATE TABLE IF NOT EXISTS delivery_history (
                history_id INTEGER PRIMARY KEY AUTOINCREMENT, message_id INTEGER,
                target TEXT NOT NULL, action TEXT NOT NULL, priority TEXT NOT NULL,
                status TEXT NOT NULL, attempts INTEGER NOT NULL, occurred_at REAL NOT NULL,
                detail TEXT)""")
            history_cols={col[1] for col in con.execute("PRAGMA table_info(delivery_history)")}
            if "duration_ms" not in history_cols:
                con.execute("ALTER TABLE delivery_history ADD COLUMN duration_ms INTEGER")
            con.execute("CREATE INDEX IF NOT EXISTS idx_history_time ON delivery_history(occurred_at)")
            con.execute("""CREATE TABLE IF NOT EXISTS message_archive (
                id INTEGER PRIMARY KEY, title TEXT, message TEXT NOT NULL,
                target TEXT NOT NULL, action TEXT NOT NULL, priority TEXT NOT NULL,
                status TEXT NOT NULL, created_at REAL NOT NULL, updated_at REAL NOT NULL,
                attempts INTEGER NOT NULL DEFAULT 0, last_error TEXT)""")
            con.execute("CREATE INDEX IF NOT EXISTS idx_archive_recent ON message_archive(created_at DESC)")
            archive_cols = {r[1] for r in con.execute("PRAGMA table_info(message_archive)")}
            if "message_type" not in archive_cols:
                con.execute("ALTER TABLE message_archive ADD COLUMN message_type TEXT NOT NULL DEFAULT 'info'")
            if "retention_days" not in archive_cols:
                con.execute("ALTER TABLE message_archive ADD COLUMN retention_days INTEGER NOT NULL DEFAULT 30")
            con.execute("""DELETE FROM message_archive WHERE
                (retention_days=0 OR updated_at <= ?-(retention_days*86400))
                AND id NOT IN (SELECT id FROM messages UNION SELECT id FROM dead_letters)""",
                (time.time(),))
            con.execute("""DELETE FROM message_archive WHERE id IN (
                SELECT id FROM message_archive WHERE id NOT IN
                (SELECT id FROM messages UNION SELECT id FROM dead_letters)
                ORDER BY updated_at DESC,id DESC LIMIT -1 OFFSET 2000)""")
            # Cap completed message bodies at 32 MiB even if individual
            # messages are unusually long. Pending/dead bodies are protected.
            con.execute("""DELETE FROM message_archive WHERE id IN (
                SELECT id FROM (
                    SELECT id, SUM(LENGTH(CAST(message AS BLOB))
                      + LENGTH(CAST(COALESCE(title,'') AS BLOB)))
                      OVER (ORDER BY updated_at DESC,id DESC) AS running_bytes
                    FROM message_archive WHERE id NOT IN
                    (SELECT id FROM messages UNION SELECT id FROM dead_letters)
                ) WHERE running_bytes > ?)""",(MAX_COMPLETED_ARCHIVE_BYTES,))
            result = op(con, *args)
            con.commit()
            return result
        finally:
            con.close()

    async def _run(self, op, *args):
        async with self._lock:
            return await asyncio.to_thread(self._execute, op, *args)

    async def enqueue_many(self, items, limit):
        now = time.time()
        def op(con):
            con.execute("""UPDATE message_archive SET status='expired',updated_at=?
                WHERE id IN (SELECT id FROM messages WHERE expires_at IS NOT NULL AND expires_at<=?)""",(now,now))
            con.execute("DELETE FROM messages WHERE expires_at IS NOT NULL AND expires_at<=?", (now,))
            current = con.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
            replacements = set()
            for item in items:
                if item.get("strategy") == "replace" and item.get("dedup_key"):
                    row = con.execute("""SELECT COUNT(*) FROM messages
                        WHERE dedup_key=? AND target=? AND action=?
                        AND (lease_until IS NULL OR lease_until<=?)""",
                        (item["dedup_key"], item["target"], item["action"], now)).fetchone()
                    # The conservative reservation counts duplicates at most once.
                    replacements.add((item["dedup_key"], item["target"], item["action"]))
            removable = sum(con.execute("""SELECT COUNT(*) FROM messages WHERE
                dedup_key=? AND target=? AND action=? AND (lease_until IS NULL OR lease_until<=?)""",
                (*k, now)).fetchone()[0] for k in replacements)
            if current - removable + len(items) > limit:
                raise OverflowError("Reliable Notify queue capacity exceeded")
            ids = []
            for item in items:
                if item.get("strategy") == "replace" and item.get("dedup_key"):
                    key=(item["dedup_key"],item["target"],item["action"],now)
                    con.execute("""UPDATE message_archive SET status='replaced',updated_at=?
                        WHERE id IN (SELECT id FROM messages WHERE dedup_key=? AND target=? AND action=?
                        AND (lease_until IS NULL OR lease_until<=?))""",(now,*key))
                    con.execute("""DELETE FROM messages WHERE dedup_key=? AND target=? AND action=?
                        AND (lease_until IS NULL OR lease_until<=?)""",key)
                transport_payload=item.get("payload") or {}
                if item.get("dedup_key") and item["action"].startswith("notify.mobile_app_"):
                    transport_payload=_ensure_companion_tag(transport_payload,item["dedup_key"])
                payload = json.dumps(transport_payload, ensure_ascii=False, allow_nan=False)
                if item.get("strategy")=="digest":
                    if not item.get("dedup_key"):
                        raise ValueError("digest requires dedup_key")
                    existing=con.execute("""SELECT id,occurrences FROM messages WHERE
                        dedup_key=? AND action=? AND target=? AND priority=?
                        AND next_attempt>? AND (lease_until IS NULL OR lease_until<=?)
                        ORDER BY id DESC LIMIT 1""",
                        (item["dedup_key"],item["action"],item["target"],item["priority"],now,now)).fetchone()
                    if existing:
                        count=existing[1]+1
                        summary=f"{count} events (latest): {item['message']}"
                        # Preserve the first queued transport payload (including
                        # Companion deep links and tags) for the entire digest.
                        con.execute("""UPDATE messages SET message=?,occurrences=?
                            WHERE id=?""",(summary,count,existing[0]))
                        con.execute("UPDATE message_archive SET message=?,updated_at=? WHERE id=?",
                                    (summary,now,existing[0]))
                        ids.append(existing[0])
                        continue
                cur = con.execute("""INSERT INTO messages(message,title,target,priority,dedup_key,
                    expires_at,next_attempt,created_at,action,payload_json,media_path,media_paths_json)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (item["message"], item.get("title"), item["target"], item["priority"],
                     item.get("dedup_key"), now + item["ttl"] if item.get("ttl") else None,
                     max(now,item.get("not_before",now),
                         now+item.get("digest_window_seconds",0) if item.get("strategy")=="digest" else now),
                     now, item["action"], payload, item.get("media_path"),
                     json.dumps(item.get("media_paths", []))))
                ident = cur.lastrowid
                ids.append(ident)
                status = 'staged' if item["action"] == 'reliable_notify.staged' else 'queued'
                con.execute("""INSERT INTO message_archive
                    (id,title,message,target,action,priority,status,created_at,updated_at,
                     message_type,retention_days)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                    (ident,item.get('title'),item['message'],item['target'],
                     item['action'],item['priority'],status,now,now,
                     item.get('message_type') or item['priority'],
                     item.get('archive_days',30)))
                archive_url = item.get('archive_url')
                if archive_url and item.get('archive_days',30) > 0 and item['action'].startswith('notify.mobile_app_'):
                    notification = dict(transport_payload)
                    phone_data = dict(notification.get('data') or {})
                    if not phone_data.get('url') and not phone_data.get('clickAction'):
                        parts = urlsplit(archive_url)
                        query = [(k,v) for k,v in parse_qsl(parts.query,keep_blank_values=True) if k!='rn_message']
                        query.append(('rn_message',str(ident)))
                        link = urlunsplit((parts.scheme,parts.netloc,parts.path,urlencode(query),parts.fragment))
                        phone_data['url'] = link
                        phone_data['clickAction'] = link
                        notification['data'] = phone_data
                        con.execute("UPDATE messages SET payload_json=? WHERE id=?",
                                    (json.dumps(notification,ensure_ascii=False),ident))
            # Register acknowledgement plan in the same transaction as enqueue.
            if items and items[0].get("ack_plan"):
                ack=items[0]["ack_plan"]
                con.execute("""INSERT INTO acknowledgements(
                    ack_key,message_id,title,message,priority,created_at,steps_json,
                    next_step,acknowledged_at,acknowledged_by,action_id)
                    VALUES(?,?,?,?,?,?,?,0,NULL,NULL,?)
                    ON CONFLICT(ack_key) DO UPDATE SET
                    message_id=excluded.message_id,title=excluded.title,
                    message=excluded.message,priority=excluded.priority,
                    created_at=excluded.created_at,steps_json=excluded.steps_json,
                    next_step=0,acknowledged_at=NULL,acknowledged_by=NULL,
                    action_id=excluded.action_id""",
                    (ack["key"],ids[0],items[0].get("title"),items[0]["message"],
                     items[0]["priority"],now,json.dumps(ack["steps"]),
                     hashlib.sha256(ack["key"].encode("utf8")).hexdigest()[:16]))
            return ids
        return await self._run(op)

    async def enqueue(self, message, title, target, priority, ttl, dedup_key,
                      strategy, limit, action="notify.send_message", payload=None):
        result = await self.enqueue_many([dict(message=message, title=title, target=target,
            priority=priority, ttl=ttl, dedup_key=dedup_key, strategy=strategy,
            action=action, payload=payload)], limit)
        return result[0]

    async def claim_due(self, lease_seconds=90, lane=None, rate_limit_per_minute=10):
        """Claim one due job, atomically reserving noncritical send-rate budget."""
        if type(rate_limit_per_minute) is not int or not 1<=rate_limit_per_minute<=1000:
            raise ValueError("rate_limit_per_minute must be 1..1000")
        now = time.time()
        def op(con):
            con.execute("""UPDATE message_archive SET status='expired',updated_at=?
                WHERE id IN (SELECT id FROM messages WHERE expires_at IS NOT NULL AND expires_at<=?)""",(now,now))
            con.execute("DELETE FROM messages WHERE expires_at IS NOT NULL AND expires_at<=?", (now,))
            con.row_factory=sqlite3.Row
            lane_clause = ("AND action LIKE 'telegram_bot.%'" if lane == "telegram" else
                           "AND action NOT LIKE 'telegram_bot.%' AND action != 'smtp.send_message' AND action != 'reliable_notify.staged'" if lane == "notify" else
                           "AND action = 'smtp.send_message'" if lane == "smtp" else "AND action != 'reliable_notify.staged'")
            candidates=con.execute(f"""SELECT * FROM messages WHERE next_attempt<=?
                AND (lease_until IS NULL OR lease_until<=?)
                AND (expires_at IS NULL OR expires_at>?) {lane_clause}
                ORDER BY {PRIORITY_ORDER},created_at,id LIMIT 500""",(now,now,now)).fetchall()
            for item in candidates:
                if item["priority"]!="critical":
                    bucket=item["action"]+":"+item["target"]
                    row=con.execute("SELECT window_start,attempts FROM send_rate_windows WHERE bucket=?",
                                    (bucket,)).fetchone()
                    if row and now-row["window_start"]<60 and row["attempts"]>=rate_limit_per_minute:
                        until=max(now+1,row["window_start"]+60)
                        con.execute("UPDATE messages SET next_attempt=? WHERE id=?",(until,item["id"]))
                        continue
                    if row and now-row["window_start"]<60:
                        con.execute("UPDATE send_rate_windows SET attempts=attempts+1 WHERE bucket=?",(bucket,))
                    else:
                        con.execute("""INSERT INTO send_rate_windows(bucket,window_start,attempts)
                            VALUES(?,?,1) ON CONFLICT(bucket) DO UPDATE
                            SET window_start=excluded.window_start,attempts=1""",(bucket,now))
                con.execute("UPDATE messages SET lease_until=? WHERE id=?",(now+lease_seconds,item["id"]))
                return dict(item)
            return None
        return await self._run(op)

    async def next_due(self):
        now = time.time()
        def op(con):
            con.row_factory = sqlite3.Row
            row = con.execute(f"""SELECT * FROM messages WHERE next_attempt<=?
                AND (lease_until IS NULL OR lease_until<=?)
                AND (expires_at IS NULL OR expires_at>?) AND action != 'reliable_notify.staged'
                ORDER BY {PRIORITY_ORDER},created_at,id LIMIT 1""", (now,now,now)).fetchone()
            return dict(row) if row else None
        return await self._run(op)

    async def suppress(self, identifier):
        """Permanently drop an obsolete state-guarded delivery, not a failure."""
        now=time.time()
        def op(con):
            row=con.execute("SELECT target,action,priority,attempts FROM messages WHERE id=?",(identifier,)).fetchone()
            if con.execute("DELETE FROM messages WHERE id=?",(identifier,)).rowcount:
                self._history(con,identifier,row,"suppressed",None)
                con.execute("UPDATE message_archive SET status='suppressed',updated_at=? WHERE id=?",(now,identifier))
                con.execute("DELETE FROM message_archive WHERE id=? AND retention_days=0",(identifier,))
                return 1
            return 0
        return await self._run(op)

    async def succeeded(self, identifier):
        def op(con):
            row = con.execute("SELECT target,action,priority,attempts FROM messages WHERE id=?",(identifier,)).fetchone()
            if con.execute("DELETE FROM messages WHERE id=?", (identifier,)).rowcount:
                self._inc(con,"sent")
                self._history(con, identifier, row, "sent", None)
                con.execute("UPDATE message_archive SET status='sent',updated_at=?,attempts=? WHERE id=?",
                            (time.time(), (row[3] if row else 0)+1, identifier))
                con.execute("DELETE FROM message_archive WHERE id=? AND retention_days=0",(identifier,))
        await self._run(op)

    @staticmethod
    def _inc(con, key):
        con.execute("INSERT INTO metrics(key,value) VALUES (?,1) ON CONFLICT(key) DO UPDATE SET value=value+1", (key,))

    @staticmethod
    def _history(con, identifier, row, status, detail):
        if row is not None:
            created=con.execute("SELECT created_at FROM message_archive WHERE id=?",(identifier,)).fetchone()
            duration=max(0,int((time.time()-created[0])*1000)) if created else None
            con.execute("""INSERT INTO delivery_history(message_id,target,action,priority,status,
                attempts,occurred_at,detail,duration_ms) VALUES (?,?,?,?,?,?,?,?,?)""",
                (identifier,row[0],row[1],row[2],status,row[3],time.time(),(detail or "")[:300],duration))
            # Bound history to 2000 entries and 30 days.
            con.execute("DELETE FROM delivery_history WHERE occurred_at<?",(time.time()-30*86400,))
            con.execute("""DELETE FROM delivery_history WHERE history_id NOT IN
                (SELECT history_id FROM delivery_history ORDER BY history_id DESC LIMIT 2000)""")

    async def failed(self, identifier, attempts, error, base_interval, max_attempts=12,
                     permanent=False, max_delay=3600, retry_after=None, category='unknown'):
        delay = min(max_delay, base_interval * (2 ** min(max(0,attempts-1),10)))
        if retry_after is not None:
            delay = max(delay, retry_after)
        def op(con):
            con.row_factory = sqlite3.Row
            row = con.execute("SELECT * FROM messages WHERE id=?", (identifier,)).fetchone()
            if not row:
                return
            self._inc(con,"failures")
            if permanent or (max_attempts is not None and attempts >= max_attempts):
                record = dict(row)
                record.update(attempts=attempts, last_error=f"[{category}] {error}"[:1000], lease_until=None)
                fields = [k for k in record if k != "failed_at"]
                con.execute(f"INSERT INTO dead_letters ({','.join(fields)},failed_at) VALUES ({','.join('?' for _ in fields)},?)",
                            (*[record[k] for k in fields], time.time()))
                con.execute("DELETE FROM messages WHERE id=?", (identifier,))
                con.execute("UPDATE message_archive SET status='dead',updated_at=?,attempts=?,last_error=? WHERE id=?",
                            (time.time(), attempts, f'[{category}]'[:120], identifier))
                self._inc(con,"dead_letters")
                self._history(con,identifier,(row["target"],row["action"],row["priority"],attempts),"dead",error)
            else:
                con.execute("""UPDATE messages SET attempts=?,last_error=?,next_attempt=?,lease_until=NULL
                    WHERE id=?""", (attempts,f"[{category}] {error}"[:1000],time.time()+delay,identifier))
                con.execute("UPDATE message_archive SET status='retry',updated_at=?,attempts=?,last_error=? WHERE id=?",
                            (time.time(),attempts,f'[{category}]'[:120],identifier))
        await self._run(op)

    async def staged_count(self):
        return await self._run(lambda con: con.execute("SELECT COUNT(*) FROM messages WHERE action='reliable_notify.staged' AND (expires_at IS NULL OR expires_at>?)", (time.time(),)).fetchone()[0])

    async def staged(self, limit=100):
        """Admin-only preview of intentionally undelivered messages."""
        def op(con):
            con.row_factory = sqlite3.Row
            return [dict(row) for row in con.execute("""SELECT id,title,message,priority,created_at,expires_at,dedup_key FROM messages
                WHERE action='reliable_notify.staged' AND (expires_at IS NULL OR expires_at>?)
                ORDER BY id DESC LIMIT ?""", (time.time(), min(200,max(1,int(limit)))))]
        return await self._run(op)

    async def assign_staged(self, identifier, action, target, payload):
        """Assign a staged message to a specific previously validated recipient."""
        now=time.time()
        def op(con):
            updated = con.execute("""UPDATE messages SET action=?,target=?,payload_json=?,next_attempt=?,lease_until=NULL
                WHERE id=? AND action='reliable_notify.staged' AND (expires_at IS NULL OR expires_at>?)""",
                (action,target,json.dumps(payload,ensure_ascii=False),now,identifier,now)).rowcount
            if updated:
                con.execute("UPDATE message_archive SET target=?,action=?,status=\'queued\',updated_at=? WHERE id=?",(target,action,now,identifier))
            return updated
        return await self._run(op)

    async def online_backup(self,directory,keep=3,min_free_bytes=100*1024*1024):
        """Online-consistent SQLite snapshot, including uncheckpointed WAL data.

        Never copy the live .db file directly. Backup uses SQLite backup API
        under the store lock; failure leaves no final/partial backup file.
        """
        if type(keep) is not int or not 1<=keep<=20:
            raise ValueError("backup retention must be 1..20")
        path=Path(directory)
        async with self._lock:
            return await asyncio.to_thread(
                self._online_backup_sync,path,keep,min_free_bytes)

    def _online_backup_sync(self,directory,keep,min_free_bytes):
        directory.mkdir(parents=True,exist_ok=True)
        source_size=self.path.stat().st_size if self.path.exists() else 0
        if shutil.disk_usage(directory).free < max(source_size*2,10*1024*1024)+min_free_bytes:
            raise OSError("not enough space for online SQLite snapshot")
        stamp=time.strftime("%Y%m%d-%H%M%S",time.localtime())
        destination=directory/f"reliable_notify-{stamp}-{time.time_ns()}.sqlite3"
        fd,temp=tempfile.mkstemp(prefix=".rn-backup-",suffix=".sqlite3",dir=directory)
        os.close(fd)
        try:
            source=sqlite3.connect(self.path,timeout=15)
            target=sqlite3.connect(temp,timeout=15)
            try:
                source.backup(target,pages=128,sleep=0.1)
                result=target.execute("PRAGMA quick_check(1)").fetchone()[0]
                if result!="ok":
                    raise OSError("backup integrity check failed")
                target.commit()
            finally:
                target.close()
                source.close()
            os.replace(temp,destination)
            backups=sorted(directory.glob("reliable_notify-*.sqlite3"),
                           key=lambda p:p.stat().st_mtime,reverse=True)
            for old in backups[keep:]:
                old.unlink(missing_ok=True)
            return {"filename":destination.name,"bytes":destination.stat().st_size,
                    "integrity":"ok"}
        finally:
            Path(temp).unlink(missing_ok=True)

    async def maintenance(self, dead_letter_days=30):
        """Prune old noncritical failures and inspect database health.

        Critical dead letters are deliberately excluded from automatic
        deletion. Checkpoint uses PASSIVE and never forces active writers.
        """
        if type(dead_letter_days) is not int or not 1 <= dead_letter_days <= 365:
            raise ValueError("dead_letter_days must be an integer 1..365")
        now=time.time()
        def prune(con):
            candidates=[row[0] for row in con.execute(
                """SELECT id FROM dead_letters WHERE priority!='critical'
                   AND failed_at<?""",(now-dead_letter_days*86400,))]
            for (ident,) in [(x,) for x in candidates]:
                con.execute("DELETE FROM dead_letters WHERE id=?",(ident,))
                con.execute("UPDATE message_archive SET status='dead_expired',updated_at=? WHERE id=?",
                            (now,ident))
            con.execute("DELETE FROM send_rate_windows WHERE window_start<?",(now-300,))
            con.execute("""DELETE FROM acknowledgements
                WHERE acknowledged_at IS NOT NULL AND acknowledged_at<?""",
                (now-30*86400,))
            # Unacknowledged critical incidents are retained; stale noncritical
            # records are not allowed to accumulate indefinitely.
            con.execute("""DELETE FROM acknowledgements
                WHERE acknowledged_at IS NULL AND priority!='critical'
                AND created_at<?""",(now-90*86400,))
            return len(candidates)
        removed=await self._run(prune)
        async with self._lock:
            result=await asyncio.to_thread(self._maintenance_probe)
        result["removed_dead_letters"]=removed
        return result

    def _maintenance_probe(self):
        con=sqlite3.connect(self.path, timeout=15)
        try:
            con.execute("PRAGMA busy_timeout=15000")
            integrity=con.execute("PRAGMA quick_check(1)").fetchone()[0]
            checkpoint=con.execute("PRAGMA wal_checkpoint(PASSIVE)").fetchone()
            size=sum(p.stat().st_size for p in (
                self.path, Path(str(self.path)+"-wal"), Path(str(self.path)+"-shm")
            ) if p.exists())
            dead=con.execute("SELECT COUNT(*) FROM dead_letters").fetchone()[0]
            critical=con.execute("SELECT COUNT(*) FROM dead_letters WHERE priority='critical'").fetchone()[0]
            return {"integrity":integrity,"checkpoint_busy":checkpoint[0],
                    "database_bytes":size,"dead_letters":dead,"critical_dead_letters":critical}
        finally:
            con.close()

    async def acknowledgement(self, key, by="manual"):
        now=time.time()
        def op(con):
            return con.execute("""UPDATE acknowledgements SET acknowledged_at=?,acknowledged_by=?
                WHERE ack_key=? AND acknowledged_at IS NULL""",(now,by[:100],key)).rowcount
        return await self._run(op)

    async def active_acknowledgements(self, limit=50):
        def op(con):
            con.row_factory=sqlite3.Row
            records=[dict(row) for row in con.execute("""SELECT ack_key,message_id,title,priority,
                created_at,steps_json,next_step FROM acknowledgements
                WHERE acknowledged_at IS NULL ORDER BY created_at DESC LIMIT ?""",(limit,))]
            for record in records:
                record["steps"]=json.loads(record.pop("steps_json"))
            return records
        return await self._run(op)

    async def due_escalations(self, now=None):
        now=now or time.time()
        def op(con):
            con.row_factory=sqlite3.Row
            rows=con.execute("""SELECT ack_key,title,message,priority,created_at,
                steps_json,next_step FROM acknowledgements
                WHERE acknowledged_at IS NULL AND next_step<8""").fetchall()
            due=[]
            for row in rows:
                steps=json.loads(row["steps_json"])
                index=row["next_step"]
                if index < len(steps) and row["created_at"]+steps[index]["after"] <= now:
                    due.append({**dict(row),"step_index":index,"step":steps[index]})
            return due
        return await self._run(op)

    async def escalation_completed(self, key, index):
        def op(con):
            return con.execute("""UPDATE acknowledgements SET next_step=next_step+1
                WHERE ack_key=? AND next_step=? AND acknowledged_at IS NULL""",
                (key,index)).rowcount
        return await self._run(op)

    async def enqueue_escalation_atomic(self, key, index, recipients, limit=1000):
        """Commit escalation jobs and stage advancement in one SQLite transaction.

        No duplicate jobs after process restart/crash at the enqueue boundary.
        Recipients are already validated by the HA routing layer. Only text
        transport jobs are accepted (no media/attachments).
        """
        now=time.time()
        def op(con):
            con.row_factory=sqlite3.Row
            ack=con.execute("""SELECT ack_key,message,title,priority,created_at,
                steps_json,next_step,acknowledged_at FROM acknowledgements
                WHERE ack_key=?""",(key,)).fetchone()
            if not ack or ack["acknowledged_at"] is not None or ack["next_step"]!=index:
                return []
            steps=json.loads(ack["steps_json"])
            if index>=len(steps) or ack["created_at"]+steps[index]["after"]>now:
                return []
            if con.execute("SELECT COUNT(*) FROM messages").fetchone()[0]+len(recipients)>limit:
                raise OverflowError("queue full; escalation deferred")
            ids=[]
            for name,rec in recipients:
                action=rec.get("action","notify.send_message")
                if action=="reliable_notify.staged" or action=="telegram_bot.send_photo":
                    raise ValueError("escalation text only")
                target=rec.get("target_entity","") if action in ("notify.send_message","smtp.send_message") else name
                payload=json.dumps(rec.get("data",{}),ensure_ascii=False,allow_nan=False)
                cur=con.execute("""INSERT INTO messages(message,title,target,priority,dedup_key,
                    expires_at,next_attempt,created_at,action,payload_json,media_paths_json)
                    VALUES(?,?,?,?,?,NULL,?,?,?,?,?)""",
                    (ack["message"],ack["title"],target,ack["priority"],
                     "rn_esc_"+hashlib.sha256(key.encode("utf8")).hexdigest()[:16],
                     now,now,action,payload,"[]"))
                ident=cur.lastrowid
                ids.append(ident)
                con.execute("""INSERT INTO message_archive(
                    id,title,message,target,action,priority,status,created_at,updated_at,message_type,retention_days)
                    VALUES(?,?,?,?,?,?,'queued',?,?,?,?)""",
                    (ident,ack["title"],ack["message"],target,action,ack["priority"],
                     now,now,ack["priority"],30))
            con.execute("UPDATE acknowledgements SET next_step=next_step+1 WHERE ack_key=?",(key,))
            return ids
        return await self._run(op)

    async def incident_key_from_action_id(self,identity):
        def op(con):
            row=con.execute("SELECT ack_key FROM acknowledgements WHERE action_id=?",(identity,)).fetchone()
            return row[0] if row else None
        return await self._run(op)

    async def act_on_incident(self,key,action,by="callback"):
        """Atomic ACK, snooze (15m), or immediate next-step escalation."""
        if action not in ("ack","snooze","escalate"):
            raise ValueError("unsupported incident action")
        now=time.time()
        def op(con):
            con.row_factory=sqlite3.Row
            row=con.execute("""SELECT next_step,steps_json FROM acknowledgements
                WHERE ack_key=? AND acknowledged_at IS NULL""",(key,)).fetchone()
            if row is None:
                return False
            if action=="ack":
                con.execute("""UPDATE acknowledgements
                    SET acknowledged_at=?,acknowledged_by=? WHERE ack_key=?""",
                    (now,by[:100],key))
                # Cancel unsent escalation stages only; never touch an in-flight lease.
                esc_key="rn_esc_"+hashlib.sha256(key.encode("utf8")).hexdigest()[:16]
                ids=[r[0] for r in con.execute("""SELECT id FROM messages
                    WHERE dedup_key=? AND (lease_until IS NULL OR lease_until<=?)""",
                    (esc_key,now))]
                con.executemany("DELETE FROM messages WHERE id=?",[(ident,) for ident in ids])
                con.executemany("UPDATE message_archive SET status='cancelled',updated_at=? WHERE id=?",
                                [(now,ident) for ident in ids])
            elif action=="snooze":
                con.execute("UPDATE acknowledgements SET created_at=created_at+900 WHERE ack_key=?",(key,))
            else:
                steps=json.loads(row["steps_json"])
                if row["next_step"]>=len(steps):
                    return False
                required=steps[row["next_step"]]["after"]
                con.execute("UPDATE acknowledgements SET created_at=? WHERE ack_key=?",
                            (now-required-1,key))
            return True
        return await self._run(op)

    async def archive_list(self, limit=40, search=""):
        """Admin-only searchable index; intentionally no message bodies."""
        def op(con):
            con.row_factory=sqlite3.Row
            return [dict(row) for row in con.execute("""
                SELECT id,title,target,action,priority,status,created_at,updated_at,attempts,
                       message_type,retention_days
                FROM message_archive
                WHERE (? = '' OR instr(lower(message),lower(?)) > 0
                       OR instr(lower(coalesce(title,'')),lower(?)) > 0)
                ORDER BY id DESC LIMIT ?""",
                (search,search,search,min(100,max(1,int(limit)))))]
        return await self._run(op)

    async def archive_detail(self, identifier):
        """Admin-only full text; no payloads, credentials or attachments."""
        def op(con):
            con.row_factory=sqlite3.Row
            row=con.execute("""SELECT id,title,message,target,action,priority,status,
                created_at,updated_at,attempts,last_error,message_type,retention_days FROM message_archive
                WHERE id=?""",(identifier,)).fetchone()
            return dict(row) if row else None
        return await self._run(op)

    async def count(self):
        return await self._run(lambda con: con.execute("SELECT COUNT(*) FROM messages WHERE expires_at IS NULL OR expires_at>?", (time.time(),)).fetchone()[0])

    async def dead_count(self):
        return await self._run(lambda con: con.execute("SELECT COUNT(*) FROM dead_letters").fetchone()[0])

    async def statistics(self, days=7):
        """Aggregated metadata only: no message text, tokens, or payloads."""
        if type(days) is not int or not 1<=days<=30:
            raise ValueError("days must be 1..30")
        cutoff=time.time()-days*86400
        def op(con):
            con.row_factory=sqlite3.Row
            transport=[dict(row) for row in con.execute("""
                SELECT action,COUNT(*) AS events,
                  SUM(CASE WHEN status='sent' THEN 1 ELSE 0 END) AS sent,
                  SUM(CASE WHEN status='dead' THEN 1 ELSE 0 END) AS failed,
                  ROUND(AVG(CASE WHEN status='sent' THEN duration_ms END)/1000.0,2) AS avg_delivery_seconds,
                  MAX(occurred_at) AS last_event
                FROM delivery_history WHERE occurred_at>=?
                GROUP BY action ORDER BY events DESC""",(cutoff,))]
            byday=[dict(row) for row in con.execute("""
                SELECT date(occurred_at,'unixepoch') AS day,status,
                  COUNT(*) AS count FROM delivery_history
                WHERE occurred_at>=? GROUP BY day,status ORDER BY day""",(cutoff,))]
            ack=con.execute("""SELECT COUNT(*),SUM(acknowledged_at IS NOT NULL),
                AVG(CASE WHEN acknowledged_at IS NOT NULL
                    THEN acknowledged_at-created_at END)
                FROM acknowledgements WHERE created_at>=?""",(cutoff,)).fetchone()
            queued=con.execute("SELECT COUNT(*),MIN(created_at) FROM messages WHERE action!='reliable_notify.staged'").fetchone()
            return {"transports":transport,"timeline":byday,
                    "acknowledgements":{"total":ack[0],"confirmed":ack[1] or 0,
                                        "avg_seconds":round(ack[2],1) if ack[2] is not None else None},
                    "queued":queued[0],"oldest_queued_seconds":
                        round(time.time()-queued[1],1) if queued[1] else None}
        return await self._run(op)

    async def metrics(self):
        return await self._run(lambda con: dict(con.execute("SELECT key,value FROM metrics").fetchall()))

    async def retry_all(self):
        now = time.time()
        await self._run(lambda con: con.execute("UPDATE messages SET next_attempt=? WHERE lease_until IS NULL OR lease_until<=?", (now,now)))

    async def retry_dead(self):
        def op(con):
            count = con.execute("SELECT COUNT(*) FROM dead_letters").fetchone()[0]
            con.execute("""INSERT INTO messages (id,message,title,target,priority,dedup_key,expires_at,
                attempts,next_attempt,created_at,last_error,action,payload_json,lease_until,media_path,media_paths_json)
                SELECT id,message,title,target,priority,dedup_key,expires_at,0,?,created_at,NULL,
                action,payload_json,NULL,media_path,media_paths_json FROM dead_letters WHERE expires_at IS NULL OR expires_at>?""", (time.time(),time.time()))
            con.execute("DELETE FROM dead_letters")
            con.execute("UPDATE message_archive SET status='queued',updated_at=? WHERE id IN (SELECT id FROM messages) AND status='dead'",(time.time(),))
            return count
        return await self._run(op)

    async def cancel(self, key, target=None):
        def op(con):
            now=time.time()
            sql="SELECT id FROM messages WHERE dedup_key=? AND (lease_until IS NULL OR lease_until<=?)"
            params=[key,now]
            if target:
                sql+=" AND target=?"
                params.append(target)
            ids=[row[0] for row in con.execute(sql,params)]
            if not ids:
                return 0
            con.executemany("DELETE FROM messages WHERE id=?",[(i,) for i in ids])
            con.executemany("UPDATE message_archive SET status='cancelled',updated_at=? WHERE id=?",
                            [(now,i) for i in ids])
            return len(ids)
        return await self._run(op)

    async def clear(self):
        def op(con):
            now=time.time()
            ids=[row[0] for row in con.execute(
                "SELECT id FROM messages WHERE lease_until IS NULL OR lease_until<=?",(now,))]
            con.executemany("DELETE FROM messages WHERE id=?",[(i,) for i in ids])
            con.executemany("UPDATE message_archive SET status='cleared',updated_at=? WHERE id=?",
                            [(now,i) for i in ids])
        await self._run(op)

    async def retry_one(self, identifier: int, dead: bool = False):
        """Retry a single eligible job; never mutate a currently leased job."""
        now = time.time()
        def op(con):
            if not dead:
                updated=con.execute("""UPDATE messages SET next_attempt=?,lease_until=NULL
                    WHERE id=? AND action!='reliable_notify.staged' AND (lease_until IS NULL OR lease_until<=?)""",
                    (now,identifier,now)).rowcount
                if updated:
                    con.execute("UPDATE message_archive SET status='queued',updated_at=? WHERE id=?",(now,identifier))
                return updated
            row = con.execute("SELECT * FROM dead_letters WHERE id=? AND (expires_at IS NULL OR expires_at>?)",(identifier,now)).fetchone()
            if not row:
                return 0
            con.row_factory = sqlite3.Row
            record = con.execute("SELECT * FROM dead_letters WHERE id=?",(identifier,)).fetchone()
            columns = ['id','message','title','target','priority','dedup_key','expires_at','attempts',
                       'next_attempt','created_at','last_error','action','payload_json','lease_until','media_path','media_paths_json']
            values = [record[col] for col in columns]
            values[7],values[8],values[10],values[13] = 0,now,None,None
            con.execute(f"INSERT INTO messages ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})",values)
            con.execute("DELETE FROM dead_letters WHERE id=?",(identifier,))
            con.execute("UPDATE message_archive SET status='queued',updated_at=?,attempts=0 WHERE id=?",(now,identifier))
            return 1
        return await self._run(op)

    async def delete_one(self, identifier: int, dead: bool = False):
        table = 'dead_letters' if dead else 'messages'
        now = time.time()
        def op(con):
            row = con.execute(f"SELECT target,action,priority,attempts FROM {table} WHERE id=?",(identifier,)).fetchone()
            if not dead:
                count = con.execute("""DELETE FROM messages WHERE id=? AND
                    (lease_until IS NULL OR lease_until<=?)""",(identifier,now)).rowcount
            else:
                count = con.execute("DELETE FROM dead_letters WHERE id=?",(identifier,)).rowcount
            if count:
                self._history(con,identifier,row,"deleted",None)
                con.execute("UPDATE message_archive SET status='deleted',updated_at=? WHERE id=?",(time.time(),identifier))
            return count
        return await self._run(op)

    async def history(self, limit=20):
        def op(con):
            con.row_factory = sqlite3.Row
            return [dict(row) for row in con.execute("""SELECT message_id AS id,target,action,priority,
                status,attempts,occurred_at,detail FROM delivery_history
                ORDER BY history_id DESC LIMIT ?""",(min(100,max(1,int(limit))),))]
        return await self._run(op)

    async def pending_media_paths(self):
        """Media references still used by queued or dead-letter jobs."""
        def op(con):
            files = set()
            for table in ('messages', 'dead_letters'):
                for path, encoded in con.execute(f"SELECT media_path,media_paths_json FROM {table}"):
                    if path:
                        files.add(path)
                    try:
                        files.update(json.loads(encoded or '[]'))
                    except (ValueError, TypeError):
                        pass
            return files
        return await self._run(op)

    async def recent(self, limit=40, dead=False):
        """Sanitized queue data for monitoring; never expose payload credentials."""
        table = "dead_letters" if dead else "messages"
        def op(con):
            con.row_factory = sqlite3.Row
            return [dict(row) for row in con.execute(
                f"SELECT id,target,priority,action,attempts,created_at,next_attempt,last_error "
                f"FROM {table} ORDER BY id DESC LIMIT ?", (min(200,max(1,int(limit))),))]
        return await self._run(op)