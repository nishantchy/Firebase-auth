from bs4 import BeautifulSoup

def parse_products(response_text):
    products = []
    soup = BeautifulSoup(response_text, "html.parser")
    for card in soup.select("div._1AtVbE"):
        name = card.select_one("div._4rR01T")
        price = card.select_one("div._30jeq3")
        image = card.select_one("img._396cs4")
        if name and price and image:
            products.append({
                "name": name.text,
                "price": price.text,
                "image": image["src"]
            })
    return products 