import json

# Conversion rate: 1 USD = 83 INR
USD_TO_INR = 83

# Read products
products = []
with open('products.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            products.append(json.loads(line.strip()))

# Convert prices to INR and round to nearest 5
for product in products:
    usd_price = product['price']
    inr_price = round((usd_price * USD_TO_INR) / 5) * 5  # Round to nearest 5
    product['price'] = inr_price

# Write back
with open('products.jsonl', 'w', encoding='utf-8') as f:
    for product in products:
        f.write(json.dumps(product, ensure_ascii=False) + '\n')

print("Prices converted to INR successfully!")
for p in products[:5]:
    print(f"{p['name']}: ₹{p['price']}")









































