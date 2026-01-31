import os

from sqlalchemy import create_engine, inspect, text

from config import Env
from app.models.base import Base
from app.models import History  # noqa: F401

database_path = os.path.abspath(os.path.join(Env.DATA_DIR, "app.db"))
engine = create_engine(f"sqlite:///{database_path}")


def migrate_and_restore():
    with engine.begin() as conn:
        inspector = inspect(engine)
        if "histories" in inspector.get_table_names():
            print("📦 기존 데이터를 백업합니다 (histories -> histories_old)")
            conn.execute(text("ALTER TABLE histories RENAME TO histories_old;"))

            Base.metadata.create_all(conn)
            print("✨ 인덱스가 포함된 새 테이블을 생성했습니다.")

            print("🚀 데이터를 복구하는 중...")
            conn.execute(
                text("""
                INSERT INTO histories (id, timestamp, balance, price, ratio)
                SELECT id, timestamp, balance, price, ratio FROM histories_old;
                """)
            )

            conn.execute(text("DROP TABLE histories_old;"))
            print("✅ 마이그레이션 및 데이터 복구 완료!")
        else:
            Base.metadata.create_all(conn)
            print("🆕 신규 테이블을 생성했습니다.")


if __name__ == "__main__":
    migrate_and_restore()
