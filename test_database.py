"""Test database setup and connectivity."""

from zuberabot.database import init_database, User, UserPreferences, Verification
from loguru import logger


def test_database_setup():
    """Test database initialization and basic operations."""
    
    logger.info("=== Testing Database Setup ===")
    
    # Initialize database (will use DATABASE_URL env var or default to local)
    logger.info("1. Initializing database...")
    db_manager = init_database(create_tables=True)
    
    # Health check
    logger.info("2. Running health check...")
    if db_manager.health_check():
        logger.success("✅ Database connection successful!")
    else:
        logger.error("❌ Database connection failed!")
        return
    
    # Test creating a user
    logger.info("3. Testing user creation...")
    try:
        with db_manager.get_session() as session:
            # Create test user
            test_user = User(
                user_id="whatsapp:test123",
                phone_number="+919876543210",
                name="Test User",
               age=30,
                profession="Software Engineer",
                risk_profile="moderate"
            )
            session.add(test_user)
            session.commit()
            logger.success("✅ Test user created successfully!")
            
            # Query user
            found_user = session.query(User).filter_by(user_id="whatsapp:test123").first()
            if found_user:
                logger.success(f"✅ User retrieved: {found_user.name}")
                logger.info(f"   User data: {found_user.to_dict()}")
            
            # Clean up
            session.delete(found_user)
            session.commit()
            logger.info("   Test user deleted (cleanup)")
            
    except Exception as e:
        logger.error(f"❌ User creation failed: {e}")
        return
    
    logger.success("\n🎉 All database tests passed!")
    logger.info("\nNext steps:")
    logger.info("1. Set DATABASE_URL environment variable for production")
    logger.info("2. Create user profile tool")
    logger.info("3. Integrate with chatbot")


if __name__ == "__main__":
    test_database_setup()
