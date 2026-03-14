import asyncio
import time
from collections import defaultdict
from typing import Dict, List, Any

class LogCollector:
    """
    Collects logs from multiple roles for the same message ID 
    and prints them as a single consolidated block once all are received.
    """
    def __init__(self):
        self.expected_roles = 0
        self.buffers: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
        self.content_cache: Dict[int, str] = {}
        self.lock = asyncio.Lock()
        self.flush_timeout = 5.0 # Seconds to wait before partial flush

    def set_expected_roles(self, count: int):
        self.expected_roles = count
    async def collect(self, message_id: int, content: str, role_name: str, decision: Any, reply_text: str, threshold: float, will_reply: bool):
        async with self.lock:
            if message_id not in self.content_cache:
                self.content_cache[message_id] = content
                # 容错：如果某个 Bot 挂了或太慢，5秒后强制刷新已有的日志
                asyncio.create_task(self._timeout_flush(message_id))
            
            entry = {
                "role": role_name,
                "priority": decision.priority,
                "threshold": threshold,
                "status": "回复" if will_reply else "忽略",
                "reason": decision.reason,
                "reply": reply_text or "（不回复）"
            }
            
            self.buffers[message_id].append(entry)
            
            if len(self.buffers[message_id]) >= self.expected_roles:
                await self._flush(message_id)

    async def _timeout_flush(self, message_id: int):
        await asyncio.sleep(self.flush_timeout)
        async with self.lock:
            if message_id in self.buffers:
                # 依然在缓存中，说明没收齐，执行部分刷新
                await self._flush(message_id)

    async def _flush(self, message_id: int):
        entries = self.buffers.pop(message_id, [])
        content = self.content_cache.pop(message_id, "Unknown")
        
        if not entries:
            return

        box_width = 100
        print("\n" + "━" * box_width)
        print(f" 📥 收到内容: {content[:box_width-15]}")
        print("─" * box_width)
        
        # Sort by role name for consistency
        entries.sort(key=lambda x: x["role"])
        
        for e in entries:
            # Compact line: Role | Score | Status | Reason | Reply
            status_tag = f"[{e['status']}]" if e['status'] == "回复" else f"({e['status']})"
            reason_clean = e['reason'].replace("\n", " ").strip()[:30]
            reply_clean = e['reply'].replace("\n", " ").strip()[:40]
            
            line = f" {e['role']:<10} | 分数: {e['priority']:.2f}/{e['threshold']:.2f} | {status_tag:<6} | 理由: {reason_clean:<25} | 🔊: {reply_clean}"
            print(line[:box_width-2])
            
        print("━" * box_width + "\n")

# Global singleton
log_collector = LogCollector()
