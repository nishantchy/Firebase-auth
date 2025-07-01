import requests
from sqlmodel import Session
from app.core.database import engine
from app.services.products_service import create_product

def scrape_daraz_products():
    url = "https://www.daraz.com.np/catalog/?_keyori=ss&ajax=true&from=search_history&isFirstRequest=true&page=1&q=laptop"
    response = requests.get(url)
    data = response.json()
    products = data['mods']['listItems']

    with Session(engine) as session:
        for product in products:
            name = product.get('name')
            price = product.get('price')
            image = product.get('image')
            db_product = create_product(session, name, price, image)
            print(f"Inserted product: {db_product.name} (ID: {db_product.id})")