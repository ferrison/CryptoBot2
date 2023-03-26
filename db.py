import time

from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker, Session

import config

CONNECTION_ATTEMPTS_COUNT = 3
TIMEOUT_BETWEEN_ATTEMPTS = 5


engine = create_engine(f"mysql+pymysql://{config.DB_USER}:{config.DB_PASSWORD}@{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}", pool_pre_ping=True)
get_session = sessionmaker(bind=engine)

with Session(engine) as session:
    for _ in range(CONNECTION_ATTEMPTS_COUNT):
        try:
            session.execute("SELECT 1")
            break
        except OperationalError:
            time.sleep(TIMEOUT_BETWEEN_ATTEMPTS)
