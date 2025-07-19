from sqlalchemy.orm import Session
from . import models, schemas
from typing import List, Optional


def get_post(db: Session, post_id: int) -> Optional[models.Post]:
    return db.query(models.Post).filter(models.Post.id == post_id).first()


def get_posts(db: Session, skip: int = 0, limit: int = 10) -> List[models.Post]:
    return db.query(models.Post).offset(skip).limit(limit).all()


def create_post(db: Session, post: schemas.PostCreate) -> models.Post:
    db_post = models.Post(**post.dict())
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post


def update_post(db: Session, post_id: int, post: schemas.PostUpdate) -> Optional[models.Post]:
    db_post = get_post(db, post_id)
    if db_post is None:
        return None
    for key, value in post.dict().items():
        setattr(db_post, key, value)
    db.commit()
    db.refresh(db_post)
    return db_post


def delete_post(db: Session, post_id: int) -> bool:
    db_post = get_post(db, post_id)
    if db_post is None:
        return False
    db.delete(db_post)
    db.commit()
    return True
