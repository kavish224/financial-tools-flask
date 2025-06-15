from flask_caching import Cache
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging

logger = logging.getLogger(__name__)

db = SQLAlchemy()
migrate = Migrate()
cache = Cache()

def register_db_event_listeners(app):
    """Register SQLAlchemy event listeners once app and db are initialized."""
    from sqlalchemy import event

    with app.app_context():
        engine = db.engine

        @event.listens_for(engine, "connect")
        def set_postgresql_settings(dbapi_connection, connection_record):
            try:
                with dbapi_connection.cursor() as cursor:
                    logger.debug("PostgreSQL connection settings applied")
            except Exception as e:
                logger.warning(f"Could not set PostgreSQL connection settings: {str(e)}")

        @event.listens_for(engine, "before_cursor_execute")
        def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            import time
            context._query_start_time = time.time()

        @event.listens_for(engine, "after_cursor_execute")
        def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            import time
            total = time.time() - context._query_start_time
            if total > 1.0:
                logger.warning(f"Slow query detected: {total:.2f}s - {statement[:100]}...")

class DatabaseManager:
    """Database connection and session management utilities."""

    @staticmethod
    def health_check():
        """Check database connectivity."""
        try:
            db.session.execute(db.text('SELECT 1'))
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return False

    @staticmethod
    def get_connection_info():
        """Get PostgreSQL database connection information."""
        try:
            engine = db.engine

            with engine.connect() as conn:
                version_result = conn.execute(db.text("SELECT version()"))
                version_info = version_result.scalar()

                db_info = conn.execute(db.text("SELECT current_database(), current_user"))
                db_name, db_user = db_info.fetchone()

                stats_query = """
                SELECT 
                    count(*) as total_connections,
                    count(*) FILTER (WHERE state = 'active') as active_connections,
                    count(*) FILTER (WHERE state = 'idle') as idle_connections
                FROM pg_stat_activity 
                WHERE datname = current_database()
                """
                stats_result = conn.execute(db.text(stats_query))
                stats = stats_result.fetchone()

            return {
                "database_type": "PostgreSQL",
                "version": version_info.split()[1] if version_info else 'unknown',
                "database_name": db_name,
                "database_user": db_user,
                "pool_size": engine.pool.size(),
                "checked_out_connections": engine.pool.checkedout(),
                "total_connections": stats[0] if stats else 'unknown',
                "active_connections": stats[1] if stats else 'unknown',
                "idle_connections": stats[2] if stats else 'unknown'
            }
        except Exception as e:
            logger.error(f"Error getting PostgreSQL database info: {str(e)}")
            return {"error": str(e)}

class CacheManager:
    """Cache management utilities."""

    @staticmethod
    def health_check():
        """Check cache connectivity."""
        try:
            cache.set('health_check', 'ok', timeout=30)
            result = cache.get('health_check')
            cache.delete('health_check')
            return result == 'ok'
        except Exception as e:
            logger.error(f"Cache health check failed: {str(e)}")
            return False

    @staticmethod
    def clear_pattern(pattern):
        """Clear cache keys matching a pattern."""
        try:
            if hasattr(cache.cache, '_read_clients'):
                client = cache.cache._read_clients[0]
                keys = client.keys(pattern)
                if keys:
                    client.delete(*keys)
                    return len(keys)
            return 0
        except Exception as e:
            logger.error(f"Error clearing cache pattern {pattern}: {str(e)}")
            return 0

db_manager = DatabaseManager()
cache_manager = CacheManager()
