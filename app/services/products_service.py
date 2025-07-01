from sqlmodel import Session
from app.models.products import Product

def create_product(session: Session, name: str, price: str, image: str):
    product = Product(name=name, price=price, image=image)
    session.add(product)
    session.commit()
    session.refresh(product)
    return product

def get_products(session: Session):
    return session.query(Product).all() 