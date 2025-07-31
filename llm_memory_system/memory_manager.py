import openai
import re
from typing import List, Dict, Optional, Tuple
from database import MemoryDatabase
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class MemoryManager:
    def __init__(self, api_key: str = None, db_path: str = None):
        api_key = api_key or os.getenv('OPENAI_API_KEY')
        if api_key and api_key != 'your_openai_api_key_here':
            try:
                self.client = openai.OpenAI(api_key=api_key)
            except Exception as e:
                print(f"Warning: OpenAI client initialization failed: {e}")
                self.client = None
        else:
            print("Warning: No valid OpenAI API key found. Chat functionality will be limited.")
            self.client = None
        
        self.db = MemoryDatabase(db_path or os.getenv('DATABASE_PATH', 'memory_database.db'))
        
    def extract_memories_from_text(self, text: str, user_id: str) -> List[str]:
        """Extract potential memories from user input using pattern matching"""
        memory_patterns = [
            r"I (?:use|work with|like|prefer|have|am|do) (.+)",
            r"My (.+) is (.+)",
            r"I don't (?:use|like|want|have) (.+)",
            r"Remember that (.+)",
            r"(?:FYI|Note|Important): (.+)",
        ]
        
        memories = []
        for pattern in memory_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    memory = " ".join(match)
                else:
                    memory = match
                
                if len(memory.strip()) > 5:  # Only meaningful memories
                    memories.append(memory.strip())
        
        return memories
    
    def analyze_importance(self, memory_content: str, context: str = "") -> float:
        """Analyze the importance of a memory using simple heuristics"""
        importance_score = 0.5  # Base score
        
        # Keywords that indicate high importance
        high_importance_keywords = [
            'important', 'critical', 'always', 'never', 'prefer', 'hate', 
            'love', 'essential', 'must', 'required', 'need'
        ]
        
        # Keywords that indicate medium importance
        medium_importance_keywords = [
            'like', 'use', 'work', 'project', 'team', 'company', 'usually'
        ]
        
        text_to_analyze = (memory_content + " " + context).lower()
        
        # Check for high importance keywords
        for keyword in high_importance_keywords:
            if keyword in text_to_analyze:
                importance_score += 0.2
        
        # Check for medium importance keywords
        for keyword in medium_importance_keywords:
            if keyword in text_to_analyze:
                importance_score += 0.1
        
        # Length-based scoring (longer memories might be more detailed/important)
        if len(memory_content) > 100:
            importance_score += 0.1
        
        # Cap the score at 1.0
        return min(importance_score, 1.0)
    
    def create_memory(self, user_id: str, memory_content: str, context: str = "", 
                     tags: List[str] = None) -> str:
        """Create a new memory with automatic importance scoring"""
        importance_score = self.analyze_importance(memory_content, context)
        
        memory_id = self.db.create_memory(
            user_id=user_id,
            memory_content=memory_content,
            context=context,
            tags=tags or [],
            importance_score=importance_score
        )
        
        return memory_id
    
    def process_user_input(self, user_id: str, user_input: str, context: str = "") -> List[str]:
        """Process user input and automatically create memories"""
        extracted_memories = self.extract_memories_from_text(user_input, user_id)
        created_memory_ids = []
        
        for memory_content in extracted_memories:
            memory_id = self.create_memory(
                user_id=user_id,
                memory_content=memory_content,
                context=f"From conversation: {context}"
            )
            created_memory_ids.append(memory_id)
        
        return created_memory_ids
    
    def get_relevant_memories(self, user_id: str, query: str = "", limit: int = 5) -> List[Dict]:
        """Get relevant memories for context"""
        if query:
            # Search for specific memories
            memories = self.db.search_memories(user_id, query, limit)
        else:
            # Get recent important memories
            memories = self.db.get_memories(user_id, limit)
        
        # Update access count for retrieved memories
        for memory in memories:
            self.db.update_memory_access(memory['id'])
        
        return memories
    
    def format_memories_for_context(self, memories: List[Dict]) -> str:
        """Format memories for inclusion in GPT context"""
        if not memories:
            return ""
        
        context_parts = ["Here's what I remember about you:"]
        
        for memory in memories:
            context_parts.append(f"- {memory['content']}")
            if memory['tags']:
                context_parts.append(f"  (Tags: {', '.join(memory['tags'])})")
        
        return "\n".join(context_parts)
    
    def chat_with_memory(self, user_id: str, user_message: str, 
                        conversation_history: List[Dict] = None) -> Tuple[str, List[str]]:
        """Chat with GPT while incorporating memory context"""
        
        # Process user input for new memories
        new_memory_ids = self.process_user_input(user_id, user_message)
        
        # Get relevant memories for context
        relevant_memories = self.get_relevant_memories(user_id, user_message, limit=5)
        memory_context = self.format_memories_for_context(relevant_memories)
        
        # Check if OpenAI client is available
        if not self.client:
            return ("OpenAI API key not configured. Please add your API key to the .env file. "
                   f"However, I created {len(new_memory_ids)} memories from your message: '{user_message}'"), new_memory_ids
        
        # Prepare messages for GPT
        messages = []
        
        # Add system message with memory context
        system_message = "You are a helpful assistant with access to user memories."
        if memory_context:
            system_message += f"\n\n{memory_context}"
        
        messages.append({"role": "system", "content": system_message})
        
        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        # Get response from GPT
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )
            
            assistant_response = response.choices[0].message.content
            
            # Process assistant response for potential memories
            assistant_memory_ids = self.process_user_input(
                user_id, 
                assistant_response, 
                context="Assistant response"
            )
            
            all_new_memory_ids = new_memory_ids + assistant_memory_ids
            
            return assistant_response, all_new_memory_ids
            
        except Exception as e:
            return f"Error communicating with OpenAI: {str(e)}. Please check your API key and internet connection.", new_memory_ids
    
    def delete_memories_by_keyword(self, user_id: str, keyword: str) -> int:
        """Delete memories containing a specific keyword"""
        return self.db.delete_user_memories(user_id, keyword)
    
    def get_user_memory_stats(self, user_id: str) -> Dict:
        """Get statistics about user's memories"""
        all_memories = self.db.get_memories(user_id, limit=1000)
        
        if not all_memories:
            return {
                'total_memories': 0,
                'avg_importance': 0,
                'most_accessed': None,
                'recent_memories': 0
            }
        
        total_memories = len(all_memories)
        avg_importance = sum(m['importance_score'] for m in all_memories) / total_memories
        most_accessed = max(all_memories, key=lambda x: x['access_count'])
        
        # Count recent memories (last 7 days)
        from datetime import datetime, timedelta
        week_ago = datetime.now() - timedelta(days=7)
        recent_memories = sum(1 for m in all_memories 
                            if datetime.fromisoformat(m['created_at'].replace('Z', '+00:00')) > week_ago)
        
        return {
            'total_memories': total_memories,
            'avg_importance': round(avg_importance, 2),
            'most_accessed': most_accessed,
            'recent_memories': recent_memories
        }
    
    def cleanup_old_memories(self, days: int = 365) -> int:
        """Clean up old, low-importance memories"""
        return self.db.cleanup_old_memories(days)
