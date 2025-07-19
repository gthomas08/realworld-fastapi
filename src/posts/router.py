from typing import List
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.users.models import User
from src.users.router import current_active_user
from . import schemas, service

router = APIRouter(prefix="/posts", tags=["posts"])


@router.get("/", response_model=List[schemas.PostInDB])
def read_posts(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return service.get_posts(db, skip=skip, limit=limit)


@router.get("/{post_id}", response_model=schemas.PostInDB)
def read_post(post_id: int, db: Session = Depends(get_db)):
    db_post = service.get_post(db, post_id)
    if db_post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return db_post


@router.post("/", response_model=schemas.PostInDB, status_code=status.HTTP_201_CREATED)
def create_post(
    post: schemas.PostCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(current_active_user)
):
    """Create a new post. Authentication required."""
    user_id = current_user.id if current_user else None
    return service.create_post(db, post, user_id=user_id)


@router.put("/{post_id}", response_model=schemas.PostInDB)
def update_post(post_id: int, post: schemas.PostUpdate, db: Session = Depends(get_db)):
    db_post = service.update_post(db, post_id, post)
    if db_post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return db_post


router = APIRouter(prefix="/posts", tags=["posts"])


@router.get("/", response_model=List[schemas.PostInDB])
def read_posts(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return service.get_posts(db, skip=skip, limit=limit)


@router.get("/{post_id}", response_model=schemas.PostInDB)
def read_post(post_id: int, db: Session = Depends(get_db)):
    db_post = service.get_post(db, post_id)
    if db_post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return db_post


@router.post("/", response_model=schemas.PostInDB, status_code=status.HTTP_201_CREATED)
def create_post(post: schemas.PostCreate, db: Session = Depends(get_db)):
    """Create a new post."""
    return service.create_post(db, post)


@router.put("/{post_id}", response_model=schemas.PostInDB)
def update_post(post_id: int, post: schemas.PostUpdate, db: Session = Depends(get_db)):
    db_post = service.update_post(db, post_id, post)
    if db_post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return db_post


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: int, db: Session = Depends(get_db)):
    success = service.delete_post(db, post_id)
    if not success:
        raise HTTPException(status_code=404, detail="Post not found")
