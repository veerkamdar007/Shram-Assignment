import sqlite3
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os

class MemoryDatabase:
    def __init__(self, db_path: str = "memory_database.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create memories table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                memory_content TEXT NOT NULL,
                context TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                access_count INTEGER DEFAULT 0,
                tags TEXT,
                importance_score REAL DEFAULT 0.5
            )
        ''')
        
        # Create conversations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                conversation_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_memories ON memories(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_conversations ON conversations(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_memory_created ON memories(created_at)')
        
        conn.commit()
        conn.close()
    
    def create_memory(self, user_id: str, memory_content: str, context: str = "", 
                     tags: List[str] = None, importance_score: float = 0.5) -> str:
        """Create a new memory entry"""
        memory_id = str(uuid.uuid4())
        tags_json = json.dumps(tags) if tags else json.dumps([])
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO memories (id, user_id, memory_content, context, tags, importance_score)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (memory_id, user_id, memory_content, context, tags_json, importance_score))
        
        conn.commit()
        conn.close()
        
        return memory_id
    
    def get_memories(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Retrieve memories for a user, ordered by importance and recency"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, memory_content, context, created_at, last_accessed, 
                   access_count, tags, importance_score
            FROM memories 
            WHERE user_id = ?
            ORDER BY importance_score DESC, last_accessed DESC
            LIMIT ?
        ''', (user_id, limit))
        
        memories = []
        for row in cursor.fetchall():
            memory = {
                'id': row[0],
                'content': row[1],
                'context': row[2],
                'created_at': row[3],
                'last_accessed': row[4],
                'access_count': row[5],
                'tags': json.loads(row[6]) if row[6] else [],
                'importance_score': row[7]
            }
            memories.append(memory)
        
        conn.close()
        return memories
    
    def search_memories(self, user_id: str, query: str, limit: int = 5) -> List[Dict]:
        """Search memories by content"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, memory_content, context, created_at, last_accessed, 
                   access_count, tags, importance_score
            FROM memories 
            WHERE user_id = ? AND (memory_content LIKE ? OR context LIKE ?)
            ORDER BY importance_score DESC, last_accessed DESC
            LIMIT ?
        ''', (user_id, f'%{query}%', f'%{query}%', limit))
        
        memories = []
        for row in cursor.fetchall():
            memory = {
                'id': row[0],
                'content': row[1],
                'context': row[2],
                'created_at': row[3],
                'last_accessed': row[4],
                'access_count': row[5],
                'tags': json.loads(row[6]) if row[6] else [],
                'importance_score': row[7]
            }
            memories.append(memory)
        
        conn.close()
        return memories
    
    def update_memory_access(self, memory_id: str):
        """Update memory access timestamp and count"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE memories 
            SET last_accessed = CURRENT_TIMESTAMP, access_count = access_count + 1
            WHERE id = ?
        ''', (memory_id,))
        
        conn.commit()
        conn.close()
    
    def delete_memory(self, user_id: str, memory_id: str) -> bool:
        """Delete a specific memory"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM memories WHERE id = ? AND user_id = ?', (memory_id, user_id))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return deleted
    
    def delete_user_memories(self, user_id: str, keyword: str = None) -> int:
        """Delete memories for a user, optionally filtered by keyword"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if keyword:
            cursor.execute('''
                DELETE FROM memories 
                WHERE user_id = ? AND (memory_content LIKE ? OR context LIKE ?)
            ''', (user_id, f'%{keyword}%', f'%{keyword}%'))
        else:
            cursor.execute('DELETE FROM memories WHERE user_id = ?', (user_id,))
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        return deleted_count
    
    def save_conversation(self, user_id: str, conversation_data: Dict) -> str:
        """Save conversation data"""
        conversation_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO conversations (id, user_id, conversation_data)
            VALUES (?, ?, ?)
        ''', (conversation_id, user_id, json.dumps(conversation_data)))
        
        conn.commit()
        conn.close()
        
        return conversation_id
    
    def get_conversation(self, user_id: str, conversation_id: str) -> Optional[Dict]:
        """Retrieve a specific conversation"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT conversation_data FROM conversations 
            WHERE id = ? AND user_id = ?
        ''', (conversation_id, user_id))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return json.loads(result[0])
        return None
    
    def cleanup_old_memories(self, days: int = 365):
        """Clean up old memories based on retention policy"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM memories 
            WHERE created_at < ? AND importance_score < 0.7
        ''', (cutoff_date.isoformat(),))
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        return deleted_count
