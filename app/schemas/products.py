from pydantic import BaseModel

class ProductCreate(BaseModel):
    name: str
    price: str
    image: str

class ProductRead(ProductCreate):
    id: int
