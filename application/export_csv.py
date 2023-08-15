import csv
  # Import your model classes

def export_products_to_csv(products):
    with open('application/exports/products.csv', 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['id', 'name', 'price', 'stock', 'description', 'category_id']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for product in products:
            writer.writerow({
                'id': product.id,
                'name': product.name,
                'price': product.price,
                'stock': product.stock,
                'description': product.description,
                'category_id': product.category_id
            })

def export_orders_to_csv(orders):
    with open('application/exports/orders.csv', 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['id', 'user_id', 'order_date', 'total_amount']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for order in orders:
            writer.writerow({
                'id': order.id,
                'user_id': order.user_id,
                'order_date': order.order_date,
                'total_amount': order.total_amount
            })

# Retrieve data using the queries
