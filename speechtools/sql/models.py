
from polyglotdb.sql.models import *

class SoundFile(Base):
    __tablename__ = 'sound_file'

    id = Column(Integer, primary_key = True)

    filepath = Column(String(250), nullable = False)

    duration = Column(Float, nullable = False)

    sampling_rate = Column(Integer, nullable = False)

    n_channels = Column(SmallInteger, nullable = False)

    discourse_id = Column(Integer, ForeignKey('discourse.id'), nullable = False)
    discourse = relationship(Discourse)

class Formants(Base):
    __tablename__ = 'formants'

    id = Column(Integer, primary_key = True)

    file_id = Column(Integer, ForeignKey('sound_file.id'), nullable = False)
    sound_file = relationship(SoundFile)

    time = Column(Float, nullable = False)

    F1 = Column(Integer, nullable = False)

    F2 = Column(Integer, nullable = False)

    F3 = Column(Integer, nullable = False)

    source = Column(String(250), nullable = False)

class Pitch(Base):
    __tablename__ = 'pitch'

    id = Column(Integer, primary_key = True)

    file_id = Column(Integer, ForeignKey('sound_file.id'), nullable = False)
    sound_file = relationship(SoundFile)

    time = Column(Float, nullable = False)

    F0 = Column(Float, nullable = False)

    source = Column(String(250), nullable = False)
