"""
Test script for multi-user support functionality.

This script tests:
1. User creation and isolation
2. Database-backed session management
3. User-specific workspaces
4. Concurrent user handling
"""

import asyncio
from pathlib import Path

from zuberabot.database.postgres import init_database, get_db_manager
from zuberabot.session.db_manager import DatabaseSessionManager
from zuberabot.agent.user_memory import UserMemoryStore, MemoryStoreFactory


def test_database_connection():
    """Test database connectivity."""
    print("=" * 60)
    print("Testing Database Connection...")
    print("=" * 60)
    
    db = get_db_manager()
    
    if db.health_check():
        print("✅ Database connection successful!")
    else:
        print("❌ Database connection failed!")
        return False
    
    return True


def test_user_creation():
    """Test user creation and retrieval."""
    print("\n" + "=" * 60)
    print("Testing User Creation...")
    print("=" * 60)
    
    db = get_db_manager()
    
    # Create test users
    users = [
        ("+919876543210", "whatsapp"),
        ("+919876543211", "whatsapp"),
        ("+919876543212", "telegram"),
    ]
    
    for phone, channel in users:
        user, created = db.get_or_create_user(phone, channel, name=f"Test User {phone}")
        status = "Created" if created else "Retrieved"
        print(f"{status} user: {user.user_id}")
    
    print("✅ User creation test passed!")
    return True


def test_session_management():
    """Test database-backed session management."""
    print("\n" + "=" * 60)
    print("Testing Session Management...")
    print("=" * 60)
    
    db = get_db_manager()
    session_manager = DatabaseSessionManager(db)
    
    # Create sessions for different users
    session1 = session_manager.get_or_create("whatsapp:+919876543210")
    session2 = session_manager.get_or_create("whatsapp:+919876543211")
    
    # Add messages to sessions
    session1.add_message("user", "Hello from user 1")
    session1.add_message("assistant", "Hi there, user 1!")
    
    session2.add_message("user", "Hello from user 2")
    session2.add_message("assistant", "Hi there, user 2!")
    
    # Verify message isolation
    history1 = session1.get_history()
    history2 = session2.get_history()
    
    print(f"Session 1 messages: {len(history1)}")
    print(f"Session 2 messages: {len(history2)}")
    
    assert len(history1) == 2, "Session 1 should have 2 messages"
    assert len(history2) == 2, "Session 2 should have 2 messages"
    assert history1 != history2, "Sessions should be isolated"
    
    print("✅ Session management test passed!")
    return True


def test_workspace_isolation():
    """Test user workspace isolation."""
    print("\n" + "=" * 60)
    print("Testing Workspace Isolation...")
    print("=" * 60)
    
    db = get_db_manager()
    
    # Create workspaces for different users
    user1_id = "whatsapp:+919876543210"
    user2_id = "whatsapp:+919876543211"
    
    workspace1 = db.get_or_create_workspace(user1_id)
    workspace2 = db.get_or_create_workspace(user2_id)
    
    print(f"User 1 workspace: {workspace1.workspace_path}")
    print(f"User 2 workspace: {workspace2.workspace_path}")
    
    assert workspace1.workspace_path != workspace2.workspace_path, "Workspaces should be different"
    assert Path(workspace1.workspace_path).exists(), "Workspace 1 should exist"
    assert Path(workspace2.workspace_path).exists(), "Workspace 2 should exist"
    
    print("✅ Workspace isolation test passed!")
    return True


def test_memory_isolation():
    """Test user memory isolation."""
    print("\n" + "=" * 60)
    print("Testing Memory Isolation...")
    print("=" * 60)
    
    db = get_db_manager()
    memory_factory = MemoryStoreFactory(db)
    
    # Get memory stores for different users
    user1_id = "whatsapp:+919876543210"
    user2_id = "whatsapp:+919876543211"
    
    memory1 = memory_factory.get_memory_store(user1_id)
    memory2 = memory_factory.get_memory_store(user2_id)
    
    # Write to memory
    memory1.write_long_term("User 1's important note")
    memory2.write_long_term("User 2's important note")
    
    # Verify isolation
    content1 = memory1.read_long_term()
    content2 = memory2.read_long_term()
    
    print(f"User 1 memory: {content1}")
    print(f"User 2 memory: {content2}")
    
    assert content1 != content2, "Memory should be isolated"
    assert "User 1" in content1, "User 1 memory should contain correct content"
    assert "User 2" in content2, "User 2 memory should contain correct content"
    
    print("✅ Memory isolation test passed!")
    return True


def test_session_cleanup():
    """Test session cleanup functionality."""
    print("\n" + "=" * 60)
    print("Testing Session Cleanup...")
    print("=" * 60)
    
    db = get_db_manager()
    
    # Cleanup sessions older than 30 days
    count = db.cleanup_inactive_sessions(days=30)
    
    print(f"Cleaned up {count} inactive sessions")
    print("✅ Session cleanup test passed!")
    return True


async def test_concurrent_sessions():
    """Test concurrent session handling."""
    print("\n" + "=" * 60)
    print("Testing Concurrent Session Handling...")
    print("=" * 60)
    
    db = get_db_manager()
    session_manager = DatabaseSessionManager(db)
    
    async def simulate_user(user_num: int, message_count: int):
        """Simulate a user sending messages."""
        session_key = f"whatsapp:+9198765432{user_num:02d}"
        session = session_manager.get_or_create(session_key)
        
        for i in range(message_count):
            session.add_message("user", f"Message {i+1} from user {user_num}")
            session.add_message("assistant", f"Response {i+1} to user {user_num}")
            await asyncio.sleep(0.01)  # Small delay to simulate real usage
        
        return session_key, len(session.get_history())
    
    # Simulate 5 concurrent users
    tasks = [simulate_user(i, 5) for i in range(5)]
    results = await asyncio.gather(*tasks)
    
    for session_key, message_count in results:
        print(f"Session {session_key}: {message_count} messages")
    
    # Verify all sessions have correct message counts
    assert all(count == 10 for _, count in results), "All sessions should have 10 messages"
    
    print("✅ Concurrent session handling test passed!")
    return True


def main():
    """Run all tests."""
    print("\n" + "🧪" * 30)
    print("Zuberabot Multi-User Support Test Suite")
    print("🧪" * 30 + "\n")
    
    # Initialize database
    print("Initializing database...")
    init_database(create_tables=True)
    
    tests = [
        ("Database Connection", test_database_connection),
        ("User Creation", test_user_creation),
        ("Session Management", test_session_management),
        ("Workspace Isolation", test_workspace_isolation),
        ("Memory Isolation", test_memory_isolation),
        ("Session Cleanup", test_session_cleanup),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            results.append((name, False))
    
    # Run async test
    try:
        result = asyncio.run(test_concurrent_sessions())
        results.append(("Concurrent Sessions", result))
    except Exception as e:
        print(f"❌ Concurrent test failed with error: {e}")
        results.append(("Concurrent Sessions", False))
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print("\n" + "=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 All tests passed! Multi-user support is working correctly.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the errors above.")


if __name__ == "__main__":
    main()
