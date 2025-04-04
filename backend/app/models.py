from typing import Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login
from flask_login import UserMixin
from datetime import timedelta
import secrets

#TODO probably delete but keep here in case i need a many to many table
#followers = sa.Table(
#    'followers',
#    db.metadata,
#    sa.Column('follower_id', sa.Integer, sa.ForeignKey('user.id'),
#              primary_key=True),
#    sa.Column('followed_id', sa.Integer, sa.ForeignKey('user.id'),
#              primary_key=True)
#)

class Band(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(100), index=True)
    status: so.Mapped[str] = so.mapped_column(sa.String(25))
    band_picture: so.Mapped[Optional[str]] = so.mapped_column(sa.String(150))

    releases: so.WriteOnlyMapped['Release'] = so.relationship(back_populates='band', passive_deletes=True)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class User(UserMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True, unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    token: so.Mapped[Optional[str]] = so.mapped_column(sa.String(32), index=True, unique=True)
    token_expiration: so.Mapped[Optional[datetime]]

    reviews: so.WriteOnlyMapped['Review'] = so.relationship(back_populates='author', passive_deletes=True)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_token(self, expires_in=3600):
        now = datetime.now(timezone.utc)
        if self.token and self.token_expiration.replace(
            tzinfo=timezone.utc) > now + timedelta(seconds=60):
            return self.token
        self.token = secrets.token_hex(16)
        self.token_expiration = now + timedelta(seconds=expires_in)
        db.session.add(self)
        return self.token
    
    def revoke_token(self):
        self.token_expiration = datetime.now(timezone.utc) - timedelta(seconds=1)

    @staticmethod
    def check_token(token):
        user = db.session.scalar(sa.select(User).where(User.token == token))
        if user is None or user.token_expiration.replace(
            tzinfo=timezone.utc) < datetime.now(timezone.utc):
            return None
        return user

@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))

class Release(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(100))
    #have length in seconds?
    length: so.Mapped[Optional[int]] = so.mapped_column(sa.Integer())
    art: so.Mapped[Optional[str]] = so.mapped_column(sa.String(150))
    release_type: so.Mapped[str] = so.mapped_column(sa.String(10))

    band_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Band.id), index=True)

    band: so.Mapped[Band] = so.relationship(back_populates='releases')

    tracks: so.WriteOnlyMapped['Track'] = so.relationship(back_populates='release', passive_deletes=True)

    reviews: so.WriteOnlyMapped['Review'] = so.relationship(back_populates='release', passive_deletes=True)

    #TODO hacky way to do this i think
    #for some reason sa func avg docs are bad and online examples are also, find better way at some point
    def avg_review_score(self):
        reviews = db.session.scalars(self.reviews.select()).all()
        review_count = len(reviews)
        review_scores = []
        for review in reviews:
            review_scores.append(review.score)
        avg_review = sum(review_scores) / review_count
        return avg_review

    def reviews_count(self):
        query = sa.select(sa.func.count()).select_from(
            self.reviews.select().subquery())
        return db.session.scalar(query)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Track(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(100))
    track_number: so.Mapped[int] = so.mapped_column(sa.Integer())
    length: so.Mapped[Optional[int]] = so.mapped_column(sa.Integer())
    lyrics: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))

    release_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Release.id), index=True)
    
    release: so.Mapped[Release] = so.relationship(back_populates='tracks')

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Review(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    score: so.Mapped[int] = so.mapped_column(sa.Integer())
    review_text: so.Mapped[str] = so.mapped_column(sa.String(500))

    release_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Release.id), index=True)

    release: so.Mapped[Release] = so.relationship(back_populates='reviews')

    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True)

    author: so.Mapped[User] = so.relationship(back_populates='reviews')

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
