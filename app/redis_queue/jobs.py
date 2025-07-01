import requests
from sqlmodel import Session
from app.core.database import engine
from app.services.products_service import create_product
from urllib.parse import quote
from app.parsers import daraz

def scrape_daraz_products_by_keyword(keyword: str):
    encoded_keyword = quote(keyword)
    url = f"https://www.daraz.com.np/catalog/?ajax=true&isFirstRequest=true&page=1&q={encoded_keyword}"
    response = requests.get(url)
    products = daraz.parse_products(response.json())
    with Session(engine) as session:
        for product in products:
            db_product = create_product(session, product["name"], product["price"], product["image"])
            print(f"Inserted product: {db_product.name} (ID: {db_product.id})")

def scrape_products_dynamic(url: str):
    if "daraz" in url:
        response = requests.get(url)
        products = daraz.parse_products(response.json())
        with Session(engine) as session:
            for product in products:
                db_product = create_product(session, product["name"], product["price"], product["image"])
                print(f"Inserted product: {db_product.name} (ID: {db_product.id})")
    else:
        print("No parser available for this site.")