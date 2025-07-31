# LLM Memory System

A comprehensive long-term memory system for Large Language Models (LLMs) that enables persistent conversation context and intelligent memory management.

## Project Overview

This system demonstrates how to implement long-term memory for AI conversations using OpenAI's GPT models. It automatically extracts, stores, and retrieves relevant information from conversations, allowing the AI to remember user preferences, facts, and context across multiple sessions.

### Key Features

- **Automatic Memory Extraction**: Intelligently identifies and stores important information from conversations
- **Smart Memory Retrieval**: Retrieves relevant memories based on conversation context
- **Importance Scoring**: Ranks memories by importance for better context management
- **Memory Management**: Create, search, update, and delete memories
- **Persistent Storage**: SQLite database for reliable memory persistence

### Core Components

1. **MemoryDatabase** (`database.py`): Handles all database operations
2. **MemoryManager** (`memory_manager.py`): Core logic for memory processing
3. **CLI Interface** (`cli_interface.py`): Command-line demonstration


### Prerequisites

- Python 3.8+
- OpenAI API key

### Installation

1. **Clone/Download the project**
   ```bash
   cd llm_memory_system
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

4. **Run the CLI interface**
   ```bash
   python cli_interface.py
   ```

##  How It Works

### Memory Extraction

The system automatically detects and extracts memories from conversation patterns:

- `"I use Python for programming"` --> Memory: "use Python for programming"
- `"My favorite editor is VS Code"` --> Memory: "favorite editor is VS Code"
- `"I don't like Microsoft Excel"` --> Memory: "don't like Microsoft Excel"
- `"Remember that I work at a startup"` --> Memory: "work at a startup"

### Memory Scoring

Each memory is assigned an importance score (0.0-1.0) based on:
- **Keywords**: High-importance words like "important", "always", "never"
- **Context**: Conversation context and user emphasis
- **Length**: Longer, more detailed memories may be more important

### Memory Retrieval

When processing new messages, the system:
1. Searches for relevant existing memories
2. Includes top-ranked memories in the GPT context
3. Updates access counts for retrieved memories
4. Creates new memories from the conversation

## Demo Scenarios

### CLI Demo
```bash
python cli_interface.py
```

Available commands:
- `demo` - Run automated demonstration
- `chat <message>` - Chat with memory-enabled GPT
- `memories` - View stored memories
- `search <query>` - Search memories
- `stats` - View memory statistics
- `clear` - Clear all memories

## Example Usage

```python
from memory_manager import MemoryManager

# Initialize the memory manager
memory_manager = MemoryManager()

# Chat with memory
response, memory_ids = memory_manager.chat_with_memory(
    user_id="user123",
    user_message="I use Shram and Magnet as productivity tools",
    conversation_history=[]
)

print(f"Response: {response}")
print(f"Created {len(memory_ids)} new memories")


response, _ = memory_manager.chat_with_memory(
    user_id="user123",
    user_message="What productivity tools do I use?",
    conversation_history=[]
)
```

## Database Schema

### Memories Table
- `id`: Unique memory identifier
- `user_id`: User identifier
- `memory_content`: The actual memory text
- `context`: Additional context information
- `created_at`: Creation timestamp
- `last_accessed`: Last access timestamp
- `access_count`: Number of times accessed
- `tags`: JSON array of tags
- `importance_score`: Importance score (0.0-1.0)

### Conversations Table
- `id`: Conversation identifier
- `user_id`: User identifier
- `conversation_data`: JSON conversation data
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

## Configuration

### Environment Variables (.env)
```
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_PATH=memory_database.db
MAX_MEMORIES_PER_USER=1000
MEMORY_RETENTION_DAYS=365
```

### Memory Patterns

You can customize memory extraction patterns in `memory_manager.py`:

```python
memory_patterns = [
    r"I (?:use|work with|like|prefer|have|am|do) (.+)",
    r"My (.+) is (.+)",
    r"I don't (?:use|like|want|have) (.+)",
    r"Remember that (.+)",
    r"(?:FYI|Note|Important): (.+)",
]
```

### Key Technical Decisions

- **SQLite**: Chosen for simplicity and portability
- **Pattern Matching**: Regex-based extraction for reliability
- **Importance Scoring**: Heuristic-based approach for practical implementation
- **Error Handling**: Comprehensive error handling throughout



## Testing the System

### Basic Test Flow

1. **Memory Creation**: 
   - Input: "I use Python and love machine learning"
   - Expected: Creates memory about Python and ML preferences

2. **Memory Retrieval**:
   - Input: "What programming languages do I use?"
   - Expected: Response mentions Python based on stored memory

3. **Memory Management**:
   - Search for "Python" --> Should find relevant memories
   - Delete memories containing "Python" --> Should remove related memories

### Demo Scenario

The built-in demo runs through this scenario:
1. Creates memories about productivity tools (Shram, Magnet)
2. Stores programming preferences (Python)
3. Records work environment (tech startup)
4. Notes dislikes (Excel for data analysis)
5. Tests recall by asking about productivity tools
