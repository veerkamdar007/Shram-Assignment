''' CLI INTERFACE'''
import os
import sys
from typing import List, Dict
from memory_manager import MemoryManager
from database import MemoryDatabase
import json

class MemoryCLI:
    def __init__(self):
        self.memory_manager = MemoryManager()
        self.current_user = "demo_user"
        self.conversation_history = []
        
    def display_banner(self):
        """Display welcome banner"""
        print("=" * 60)
        print("LLM Memory System - Interactive Demo")
        print("=" * 60)
        print("This system demonstrates long-term memory for LLM conversations.")
        print("The system will remember information about you across conversations.")
        print("\nAvailable commands:")
        print(" chat <message>     - Chat with memory-enabled GPT")
        print(" memories           - View your stored memories")
        print(" search <query>     - Search your memories")
        print(" stats              - View memory statistics")
        print(" delete <keyword>   - Delete memories containing keyword")
        print(" clear              - Clear all memories")
        print(" demo               - Run demonstration scenario")
        print(" help               - Show this help message")
        print(" quit               - Exit the program")
        print("=" * 60)
    
    def display_help(self):
        """Display help information"""
        print("\n Help - LLM Memory System")
        print("-" * 40)
        print("CHAT COMMAND:")
        print("  Usage: chat <your message>")
        print("  Example: chat I use Python and love machine learning")
        print("  The system will automatically extract and store memories from your message.")
        print()
        print("MEMORY EXTRACTION:")
        print("  The system automatically detects patterns like:")
        print("  - 'I use/work with/like/prefer [something]'")
        print("  - 'My [attribute] is [value]'")
        print("  - 'I don't use/like [something]'")
        print("  - 'Remember that [information]'")
        print()
        print("MEMORY MANAGEMENT:")
        print("  - memories: View all stored memories")
        print("  - search <query>: Find specific memories")
        print("  - delete <keyword>: Remove memories containing keyword")
        print("  - stats: View memory statistics")
        print("-" * 40)
    
    def run_demo_scenario(self):
        """Run a demonstration scenario"""
        print("\n Running Demo Scenario...")
        print("This will simulate a conversation to show memory functionality.\n")
        
        demo_messages = [
            "I use Shram and Magnet as productivity tools",
            "My favorite programming language is Python",
            "I work at a tech startup",
            "I don't like using Microsoft Excel for data analysis",
            "Remember that I prefer VS Code as my editor"
        ]
        
        print("Demo User Messages:")
        for i, message in enumerate(demo_messages, 1):
            print(f"{i}. {message}")
        
        print("\nProcessing messages and creating memories...")
        
        for message in demo_messages:
            response, memory_ids = self.memory_manager.chat_with_memory(
                self.current_user, message, self.conversation_history
            )
            
            self.conversation_history.append({"role": "user", "content": message})
            self.conversation_history.append({"role": "assistant", "content": response})
            
            if memory_ids:
                print(f" Created {len(memory_ids)} memories from: '{message[:50]}...'")
        
        print("\n Now let's test memory recall...")
        test_query = "What are the productivity tools that I use?"
        
        response, _ = self.memory_manager.chat_with_memory(
            self.current_user, test_query, self.conversation_history
        )
        
        print(f"\nQuery: {test_query}")
        print(f"Response: {response}")
        
        print("\n Demo completed! The system remembered your preferences.")
    
    def display_memories(self):
        """Display user's memories"""
        memories = self.memory_manager.db.get_memories(self.current_user, limit=20)
        
        if not memories:
            print("\n No memories stored yet.")
            print("Try chatting with the system to create some memories!")
            return
        
        print(f"\n Your Memories ({len(memories)} total):")
        print("-" * 50)
        
        for i, memory in enumerate(memories, 1):
            print(f"{i}. {memory['content']}")
            print(f"  Created: {memory['created_at'][:19]}")
            print(f"  Importance: {memory['importance_score']:.2f}")
            print(f"  Accessed: {memory['access_count']} times")
            if memory['tags']:
                print(f" Tags: {', '.join(memory['tags'])}")
            print()
    
    def search_memories(self, query: str):
        """Search memories"""
        if not query.strip():
            print(" Please provide a search query.")
            return
        
        memories = self.memory_manager.db.search_memories(self.current_user, query, limit=10)
        
        if not memories:
            print(f"\n No memories found for query: '{query}'")
            return
        
        print(f"\n Search Results for '{query}' ({len(memories)} found):")
        print("-" * 50)
        
        for i, memory in enumerate(memories, 1):
            print(f"{i}. {memory['content']}")
            print(f"    Created: {memory['created_at'][:19]}")
            print(f"    Importance: {memory['importance_score']:.2f}")
            print()
    
    def display_stats(self):
        """Display memory statistics"""
        stats = self.memory_manager.get_user_memory_stats(self.current_user)
        
        print(f"\n Memory Statistics for {self.current_user}:")
        print("-" * 40)
        print(f"Total Memories: {stats['total_memories']}")
        print(f"Average Importance: {stats['avg_importance']}")
        print(f"Recent Memories (7 days): {stats['recent_memories']}")
        
        if stats['most_accessed']:
            print(f"Most Accessed Memory: '{stats['most_accessed']['content'][:50]}...'")
            print(f"  (Accessed {stats['most_accessed']['access_count']} times)")
    
    def delete_memories(self, keyword: str):
        """Delete memories by keyword"""
        if not keyword.strip():
            print(" Please provide a keyword to delete.")
            return
        
        deleted_count = self.memory_manager.delete_memories_by_keyword(self.current_user, keyword)
        
        if deleted_count > 0:
            print(f" Deleted {deleted_count} memories containing '{keyword}'")
        else:
            print(f" No memories found containing '{keyword}'")
    
    def clear_all_memories(self):
        """Clear all user memories"""
        confirm = input(" Are you sure you want to delete ALL memories? (yes/no): ")
        
        if confirm.lower() == 'yes':
            deleted_count = self.memory_manager.db.delete_user_memories(self.current_user)
            print(f" Deleted {deleted_count} memories.")
            self.conversation_history = []
        else:
            print(" Operation cancelled.")
    
    def chat(self, message: str):
        """Chat with memory-enabled GPT"""
        if not message.strip():
            print(" Please provide a message to chat.")
            return
        
        print(f"\n You: {message}")
        print(" Assistant: ", end="", flush=True)
        
        try:
            response, memory_ids = self.memory_manager.chat_with_memory(
                self.current_user, message, self.conversation_history
            )
            
            print(response)
            
            # Update conversation history
            self.conversation_history.append({"role": "user", "content": message})
            self.conversation_history.append({"role": "assistant", "content": response})
            
            # Show memory creation info
            if memory_ids:
                print(f"\n Created {len(memory_ids)} new memories from this conversation.")
            
        except Exception as e:
            print(f" Error: {str(e)}")
            print("Make sure you have set your OPENAI_API_KEY in the .env file.")
    
    def run(self):
        """Main CLI loop"""
        self.display_banner()
        
        while True:
            try:
                user_input = input("\n Enter command: ").strip()
                
                if not user_input:
                    continue
                
                parts = user_input.split(' ', 1)
                command = parts[0].lower()
                args = parts[1] if len(parts) > 1 else ""
                
                if command == 'quit' or command == 'exit':
                    print(" Goodbye!")
                    break
                
                elif command == 'help':
                    self.display_help()
                
                elif command == 'demo':
                    self.run_demo_scenario()
                
                elif command == 'chat':
                    self.chat(args)
                
                elif command == 'memories':
                    self.display_memories()
                
                elif command == 'search':
                    self.search_memories(args)
                
                elif command == 'stats':
                    self.display_stats()
                
                elif command == 'delete':
                    self.delete_memories(args)
                
                elif command == 'clear':
                    self.clear_all_memories()
                
                else:
                    print(f" Unknown command: {command}")
                    print("Type 'help' for available commands.")
            
            except KeyboardInterrupt:
                print("\n Goodbye!")
                break
            except Exception as e:
                print(f" Error: {str(e)}")

def main():
    """Main entry point"""
    # Check if .env file exists
    if not os.path.exists('.env'):
        print(" Warning: .env file not found!")
        print("Please create a .env file with your OPENAI_API_KEY.")
        print("You can copy .env.example to .env and fill in your API key.")
        print()
        
        # Ask if user wants to continue anyway
        continue_anyway = input("Continue anyway? (y/n): ")
        if continue_anyway.lower() != 'y':
            return
    
    cli = MemoryCLI()
    cli.run()

if __name__ == "__main__":
    main()
