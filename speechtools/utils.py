import os
import wave

from polyglotdb.sql import get_or_create

from speechtools.sql.models import (SoundFile, Discourse)

def add_default_annotations(corpus_context, linguistic_type, defaults, subset = None):
    atype = getattr(corpus_context, linguistic_type)
    q = corpus_context.query_graph(atype)
    if subset is not None:
        q = q.filter(atype.label.in_(subset))

    las = q.all()
    for a in las:
        for d in defaults:
            t, b, e, props = d
            if b < 0 or b > 1 or e < 0 or e > 1:
                raise(ValueError('Beginnings and ends of subannotations must be specified as relative duration (0-1).'))

            dur = a.end - a.begin

            props['begin'] = a.begin + (b * dur)
            props['end'] = a.begin + (e * dur)
            a.add_subannotation(t, **props)

def update_sound_files(corpus_context, new_directory):
    corpus_context.sql_session.expire_all()
    q = corpus_context.sql_session.query(SoundFile)
    q.delete()
    for root, subdirs, files in os.walk(new_directory, followlinks = True):
        for f in files:
            if not f.lower().endswith('.wav'):
                continue
            name, _ = os.path.splitext(f)
            q = corpus_context.sql_session.query(Discourse)
            q = q.filter(Discourse.name == name)
            discourse = q.first()
            if discourse is None:
                continue
            path = os.path.join(root, f)
            with wave.open(path,'rb') as f:
                sample_rate = f.getframerate()
                n_channels = f.getnchannels()
                n_samples = f.getnframes()
                duration = n_samples / sample_rate
            sf = get_or_create(corpus_context.sql_session, SoundFile, filepath = path,
                duration = duration, sampling_rate = sample_rate,
                n_channels = n_channels, discourse = discourse)
