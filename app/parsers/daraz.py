def parse_products(response_json):
    products = []
    if 'mods' in response_json and 'listItems' in response_json['mods']:
        for product in response_json['mods']['listItems']:
            products.append({
                "name": product.get("name"),
                "price": product.get("price"),
                "image": product.get("image")
            })
    return products 