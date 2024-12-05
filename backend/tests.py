#TODO build this out with unit tests
import unittest
from app import create_app, db
from app.models import Band, User, Release, Review
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'

class BandModelCase(unittest.TestCase):
    
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    #get band includes list of all releases and aggregates reviews correctly
    def test_get_band(self):
        b = Band(name='test band', status='active', band_picture='test_band_pic_url.png')
        db.session.add(b)
        db.session.commit()

        u1 = User(username='test_user_1', email='testuser1@gmail.com')
        u2 = User(username='test_user_2', email='testuser2@gmail.com')
        u3 = User(username='test_user_3', email='testuser3@gmail.com')
        db.session.add_all([u1,u2,u3])
        db.session.commit()

        r1 = Release(name='release 1', length=123, art='release_1_art.png', release_type='LP', band=b)
        r2 = Release(name='release 2', length=123, art='release_2_art.png', release_type='EP', band=b)
        r3 = Release(name='release 3', length=123, art='release_3_art.png', release_type='LP', band=b)
        db.session.add_all([r1,r2,r3])
        db.session.commit()

        rev1 = Review(score=10, review_text='very good', release=r1, author=u1)
        rev2 = Review(score=4, review_text='no good', release=r1, author=u2)
        rev3 = Review(score=8, review_text='ok :)', release=r1, author=u3)
        rev4 = Review(score=2, review_text='no good', release=r2, author=u1)
        rev5 = Review(score=10, review_text='very good', release=r2, author=u2)
        rev6 = Review(score=5, review_text='ok', release=r2, author=u3)
        rev7 = Review(score=1, review_text='bad :(', release=r3, author=u1)
        rev8 = Review(score=10, review_text='very good', release=r3, author=u2)
        db.session.add_all([rev1,rev2,rev3,rev4,rev5,rev6,rev7,rev8])
        db.session.commit()

        releases = db.session.scalars(b.releases.select()).all()
        release_list = []
        for release in releases:
            review_count = release.reviews_count()
            avg_review = release.avg_review_score()
            release_list.append({
                'release': release.name,
                'review_count': review_count,
                'avg_review': avg_review
            })
        print({'band': b.name, 'releases': release_list})

if __name__ == '__main__':
    unittest.main(verbosity=2)