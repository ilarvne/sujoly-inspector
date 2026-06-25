import sys
import os

# Ensure src is in pythonpath
sys.path.append(os.path.join(os.getcwd(), "src"))

from agent.memory import AgentMemory

def test_memory():
    print("Initializing AgentMemory...")
    mem = AgentMemory()
    
    user_id = "test_user_123"
    print(f"Adding memory for user {user_id}...")
    mem.add("My name is Lain.", user_id=user_id)
    
    print("Searching for memory...")
    results = mem.search("What is my name?", user_id=user_id)
    
    print(f"Results: {results}")
    
    found = any("Lain" in r.get("memory", "") for r in results)
    if found:
        print("SUCCESS: Memory recalled!")
    else:
        print("FAILURE: Memory not found.")

if __name__ == "__main__":
    test_memory()
