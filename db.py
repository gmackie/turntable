from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.schema import Column
from sqlalchemy.types import DateTime, Integer, Unicode

engine = create_engine('postgresql:///turntable')
session = scoped_session(sessionmaker(bind=engine, autoflush=False))

Base = declarative_base(bind=engine)

### Yonder Tables

class Song(Base):
    __tablename__ = 'songs'

    id = Column(Integer, primary_key=True, nullable=False)
    title = Column(Unicode, nullable=False)
    song_title = Column(Unicode, nullable=False)
    artist = Column(Unicode, nullable=False)
    yt_hash = Column(Unicode, nullable=False)
    last_played = Column(DateTime, nullable=True)
    added_on = Column(DateTime, nullable=False, index=True)

    def __init__(self, **kwargs):
        kwargs.setdefault('added_on', datetime.utcnow())

        super(Song, self).__init__(**kwargs)

