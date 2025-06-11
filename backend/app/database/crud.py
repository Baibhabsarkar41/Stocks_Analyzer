from sqlalchemy.orm import Session
from . import models
from passlib.context import CryptContext
from datetime import datetime

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- User Functions (unchanged) ---
def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, username: str, email: str, password: str):
    hashed_password = pwd_context.hash(password)
    db_user = models.User(
        username=username,
        email=email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

# --- Trending News Functions ---
def create_trending_news(db: Session, headline: str, link: str, snippet: str, article: str):
    db_news = models.TrendingNews(
        headline=headline,
        link=link,
        snippet=snippet,
        article=article,
        fetched_at=datetime.utcnow()
    )
    db.add(db_news)
    try:
        db.commit()
        db.refresh(db_news)
        return db_news
    except Exception as e:
        db.rollback()
        # Optionally handle duplicate link error here
        return None

def get_trending_news_by_link(db: Session, link: str):
    return db.query(models.TrendingNews).filter(models.TrendingNews.link == link).first()

def get_latest_trending_news(db: Session, limit: int = 10):
    return db.query(models.TrendingNews).order_by(models.TrendingNews.fetched_at.desc()).limit(limit).all()
