"""Durable SQLite queue: one transaction per fan-out operation, at-least-once."""
from __future__ import annotations
import asyncio
import json
import sqlite3
import time
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from pathlib import Path

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
            con.execute("""CREATE TABLE IF NOT EXISTS delivery_history (
                history_id INTEGER PRIMARY KEY AUTOINCREMENT, message_id INTEGER,
                target TEXT NOT NULL, action TEXT NOT NULL, priority TEXT NOT NULL,
                status TEXT NOT NULL, attempts INTEGER NOT NULL, occurred_at REAL NOT NULL,
                detail TEXT)""")
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
                payload = json.dumps(item.get("payload") or {}, ensure_ascii=False, allow_nan=False)
                cur = con.execute("""INSERT INTO messages(message,title,target,priority,dedup_key,
                    expires_at,next_attempt,created_at,action,payload_json,media_path,media_paths_json)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (item["message"], item.get("title"), item["target"], item["priority"],
                     item.get("dedup_key"), now + item["ttl"] if item.get("ttl") else None,
                     now, now, item["action"], payload, item.get("media_path"),
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
                    notification = dict(item.get('payload') or {})
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
            return ids
        return await self._run(op)

    async def enqueue(self, message, title, target, priority, ttl, dedup_key,
                      strategy, limit, action="notify.send_message", payload=None):
        result = await self.enqueue_many([dict(message=message, title=title, target=target,
            priority=priority, ttl=ttl, dedup_key=dedup_key, strategy=strategy,
            action=action, payload=payload)], limit)
        return result[0]

    async def claim_due(self, lease_seconds=90, lane=None):
        now = time.time()
        def op(con):
            con.execute("""UPDATE message_archive SET status='expired',updated_at=?
                WHERE id IN (SELECT id FROM messages WHERE expires_at IS NOT NULL AND expires_at<=?)""",(now,now))
            con.execute("DELETE FROM messages WHERE expires_at IS NOT NULL AND expires_at<=?", (now,))
            con.row_factory = sqlite3.Row
            lane_clause = ("AND action LIKE 'telegram_bot.%'" if lane == "telegram" else
                           "AND action NOT LIKE 'telegram_bot.%' AND action != 'smtp.send_message' AND action != 'reliable_notify.staged'" if lane == "notify" else
                           "AND action = 'smtp.send_message'" if lane == "smtp" else "AND action != 'reliable_notify.staged'")
            item = con.execute(f"""SELECT * FROM messages WHERE next_attempt<=?
                AND (lease_until IS NULL OR lease_until<=?) {lane_clause}
                ORDER BY {PRIORITY_ORDER},created_at,id LIMIT 1""", (now, now)).fetchone()
            if item:
                con.execute("UPDATE messages SET lease_until=? WHERE id=?", (now+lease_seconds,item["id"]))
            return dict(item) if item else None
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

    async def succeeded(self, identifier):
        def op(con):
            row = con.execute("SELECT target,action,priority,attempts FROM messages WHERE id=?",(identifier,)).fetchone()
            if con.execute("DELETE FROM messages WHERE id=?", (identifier,)).rowcount:
                self._inc(con,"sent")
                self._history(con, identifier, row, "sent", None)
                con.execute("UPDATE message_archive SET status='sent',updated_at=?,attempts=? WHERE id=?",
                            (time.time(), (row[3] if row else 0)+1, identifier))
        await self._run(op)

    @staticmethod
    def _inc(con, key):
        con.execute("INSERT INTO metrics(key,value) VALUES (?,1) ON CONFLICT(key) DO UPDATE SET value=value+1", (key,))

    @staticmethod
    def _history(con, identifier, row, status, detail):
        if row is not None:
            con.execute("""INSERT INTO delivery_history(message_id,target,action,priority,status,
                attempts,occurred_at,detail) VALUES (?,?,?,?,?,?,?,?)""",
                (identifier,row[0],row[1],row[2],status,row[3],time.time(),(detail or "")[:300]))
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

    async def archive_list(self, limit=40, search=""):
        """Admin-only searchable index; intentionally no message bodies."""
        def op(con):
            con.row_factory=sqlite3.Row
            return [dict(row) for row in con.execute("""
                SELECT id,title,target,action,priority,status,created_at,updated_at,attempts
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
                created_at,updated_at,attempts,last_error FROM message_archive
                WHERE id=?""",(identifier,)).fetchone()
            return dict(row) if row else None
        return await self._run(op)

    async def count(self):
        return await self._run(lambda con: con.execute("SELECT COUNT(*) FROM messages WHERE expires_at IS NULL OR expires_at>?", (time.time(),)).fetchone()[0])

    async def dead_count(self):
        return await self._run(lambda con: con.execute("SELECT COUNT(*) FROM dead_letters").fetchone()[0])

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