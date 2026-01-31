"""
Supabase PostgreSQL 데이터베이스 연결 모듈
"""

import os
from contextlib import contextmanager
from urllib.parse import quote_plus
import psycopg2
from psycopg2.extras import RealDictCursor

# Supabase 연결 정보
DB_CONFIG = {
    "host": os.getenv("SUPABASE_DB_HOST", "aws-1-ap-south-1.pooler.supabase.com"),
    "port": int(os.getenv("SUPABASE_DB_PORT", "5432")),
    "database": os.getenv("SUPABASE_DB_NAME", "postgres"),
    "user": os.getenv("SUPABASE_DB_USER", "postgres.wwyttrjmrwdrubupkhri"),
    "password": os.getenv("SUPABASE_DB_PASSWORD", "3Qr$H58gFJB.f3z"),
    "sslmode": "require",
}


def get_connection_string():
    """URL 인코딩된 연결 문자열 반환"""
    encoded_password = quote_plus(DB_CONFIG["password"])
    return (
        f"postgresql://{DB_CONFIG['user']}:{encoded_password}"
        f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        f"?sslmode={DB_CONFIG['sslmode']}"
    )


def get_connection():
    """데이터베이스 연결 반환"""
    return psycopg2.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        database=DB_CONFIG["database"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        sslmode=DB_CONFIG["sslmode"],
        cursor_factory=RealDictCursor,
    )


@contextmanager
def get_db():
    """컨텍스트 매니저로 DB 연결 관리"""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


@contextmanager
def get_cursor():
    """컨텍스트 매니저로 커서 관리"""
    with get_db() as conn:
        cursor = conn.cursor()
        try:
            yield cursor
        finally:
            cursor.close()


def test_connection():
    """연결 테스트"""
    try:
        with get_cursor() as cur:
            cur.execute("SELECT 1;")
            result = cur.fetchone()
            return {"status": "ok", "result": dict(result) if result else None}
    except Exception as e:
        return {"status": "error", "message": str(e)}
