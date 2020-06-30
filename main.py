import requests
import urllib.parse
import json
import urllib3
import time
import random

profit_threshold = 40
sale_threshold = 10

def get_nike():
    base_endpoint = "https://api.nike.com/cic/browse/v1"
    query = {
        "queryid": "products",
        "anonymousId": "7CE0EA46874C9E9F8DD84A713A17987F",
        "endpoint": "/product_feed/rollup_threads/v2?filter=marketplace%28US%29&filter=language%28en%29&filter=employeePrice%28true%29&filter=attributeIds%2816633190-45e5-4830-a068-232ac7aea82c%2C5b21a62a-0503-400c-8336-3ccfbff2a684%29&anchor=0&consumerChannelId=d9a5bc42-4b9c-4976-858a-f159cf99c647&count=50"
    }
    r = requests.get(base_endpoint, params = query).json()

    product_dict = {}

    while "next" in r["data"]["products"]["pages"]:
        print("Scraping page...")
        for product in r["data"]["products"]["products"]:
            main_sku = product["url"].split("/")[-1]
            main_price = product["price"]["currentPrice"]
            product_dict[main_sku] = main_price
            for variant in product["colorways"]:
                sku = variant["pdpUrl"].split("/")[-1]
                price = variant["price"]["currentPrice"]
                product_dict[sku] = price

        query["endpoint"] = r['data']['products']['pages']['next']

        r = requests.get(base_endpoint, params = query).json()
        if r["data"]["products"]["pages"]["next"] == "":
            break
    
    print(product_dict)
    return product_dict

def get_stockx(sku, price):
    json_string = json.dumps({"params": f"query={sku}&hitsPerPage=20&facets=*"})
    byte_payload = bytes(json_string, 'utf-8')
    algolia = {
        "x-algolia-agent": "Algolia for vanilla JavaScript 3.32.0", 
        "x-algolia-application-id": "XW7SBCT9V6", 
        "x-algolia-api-key": "6bfb5abee4dcd8cea8f0ca1ca085c2b3"
    }
    header = {
        'accept': '*/*',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'en-US,en;q=0.9,ja-JP;q=0.8,ja;q=0.7,la;q=0.6',
        'appos': 'web',
        'appversion': '0.1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
    }

    r = requests.post("https://xw7sbct9v6-dsn.algolia.net/1/indexes/products/query", params=algolia, verify=False, data=byte_payload, timeout=30)
    try:
        results = r.json()["hits"][0]
        apiurl = f"https://stockx.com/api/products/{results['url']}?includes=market,360&currency=USD"
        response = requests.get(apiurl, verify=False, headers=header)
        prices = response.json()
        sizes = prices['Product']['children']
        market = prices['Product']['market']
        try:
            if market['salesLast72Hours'] > sale_threshold:
                size_list = ""
                for size in sizes:
                    profit = round(((sizes[size]['market']['lowestAsk'] * 0.89) - price), 2)
                    if profit > profit_threshold:
                        print(sizes[size]['shoeSize'])
                        size_list += f"{sizes[size]['shoeSize']}"

                with open("stockX.txt", "a") as f:
                    f.write(f"https://nike.com/t/-/{sku} {size_list} https://stockx.com/{results['url']}\n")
                    print(f"{response} {sku} is profitable.")
        except:
            print(f"{response} {sku} is not profitable.")
    except:
        print(f"{r} {sku} not found on StockX.")

# def get_goat():

def get_proxies(file):
    proxy_list = []
    with open("proxies.txt") as f:
        for proxy in f:
            p = proxy.split(":")
            try:
                proxy_list.append(f"{p[2]}:{p[3]}@{p[0]}:{p[1]}/")
            except:
                proxy_list.append(f"{p[0]}:{p[1]}/")
    return proxy_list

def main():
    products = get_nike()
    for sku, price in products.items():
        get_stockx(sku, price)
        time.sleep(1)

if __name__ == "__main__":
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    main()