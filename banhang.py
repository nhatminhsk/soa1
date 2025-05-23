from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import uuid

app = Flask(__name__)
CORS(app)  # Cho phép cross-origin requests

# =================================
# Câu 1: Cơ sở dữ liệu sản phẩm
# =================================

# Database giả lập trong memory
products_db = [
    {
        "id": 1,
        "name": "Laptop Dell XPS 13",
        "price": 25000000,
        "stock": 5,
        "category": "Laptop",
        "description": "Laptop cao cấp Dell XPS 13 inch"
    },
    {
        "id": 2,
        "name": "iPhone 15 Pro",
        "price": 28000000,
        "stock": 10,
        "category": "Smartphone", 
        "description": "Điện thoại iPhone 15 Pro mới nhất"
    },
    {
        "id": 3,
        "name": "Samsung Galaxy S24",
        "price": 22000000,
        "stock": 8,
        "category": "Smartphone",
        "description": "Điện thoại Samsung Galaxy S24"
    },
    {
        "id": 4,
        "name": "MacBook Air M2",
        "price": 30000000,
        "stock": 3,
        "category": "Laptop",
        "description": "MacBook Air với chip M2"
    },
    {
        "id": 5,
        "name": "AirPods Pro",
        "price": 6000000,
        "stock": 15,
        "category": "Phụ kiện",
        "description": "Tai nghe AirPods Pro không dây"
    }
]

# Câu 2: Danh mục đơn hàng (giỏ hàng)
cart_db = {}  # Dictionary để lưu giỏ hàng theo session
orders_db = []  # Lưu trữ các đơn hàng đã hoàn thành

# =================================
# PRODUCT APIs - Quản lý sản phẩm
# =================================

@app.route('/api/products', methods=['GET'])
def get_all_products():
    """Lấy danh sách tất cả sản phẩm"""
    return jsonify({
        "success": True,
        "data": products_db,
        "total": len(products_db)
    })

@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Lấy thông tin một sản phẩm"""
    product = next((p for p in products_db if p["id"] == product_id), None)
    if not product:
        return jsonify({"success": False, "message": "Sản phẩm không tồn tại"}), 404
    return jsonify({"success": True, "data": product})

@app.route('/api/products', methods=['POST'])
def create_product():
    """Thêm sản phẩm mới"""
    data = request.get_json()
    
    # Validation
    required_fields = ['name', 'price', 'stock']
    for field in required_fields:
        if field not in data:
            return jsonify({"success": False, "message": f"Thiếu trường {field}"}), 400
    
    # Tạo ID mới
    new_id = max([p["id"] for p in products_db]) + 1 if products_db else 1
    
    new_product = {
        "id": new_id,
        "name": data["name"],
        "price": data["price"],
        "stock": data["stock"],
        "category": data.get("category", ""),
        "description": data.get("description", "")
    }
    
    products_db.append(new_product)
    return jsonify({"success": True, "data": new_product}), 201

@app.route('/api/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """Cập nhật sản phẩm"""
    product = next((p for p in products_db if p["id"] == product_id), None)
    if not product:
        return jsonify({"success": False, "message": "Sản phẩm không tồn tại"}), 404
    
    data = request.get_json()
    product.update({
        "name": data.get("name", product["name"]),
        "price": data.get("price", product["price"]),
        "stock": data.get("stock", product["stock"]),
        "category": data.get("category", product["category"]),
        "description": data.get("description", product["description"])
    })
    
    return jsonify({"success": True, "data": product})

@app.route('/api/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """Xóa sản phẩm"""
    global products_db
    products_db = [p for p in products_db if p["id"] != product_id]
    return jsonify({"success": True, "message": "Đã xóa sản phẩm"})

# =================================
# CART APIs - Câu 2: Quản lý giỏ hàng
# =================================

@app.route('/api/cart/<session_id>', methods=['GET'])
def get_cart(session_id):
    """Lấy giỏ hàng theo session"""
    cart = cart_db.get(session_id, [])
    total_amount = calculate_cart_total(cart)
    
    return jsonify({
        "success": True,
        "data": {
            "items": cart,
            "total_items": len(cart),
            "total_amount": total_amount
        }
    })

@app.route('/api/cart/<session_id>/add', methods=['POST'])
def add_to_cart(session_id):
    """Thêm sản phẩm vào giỏ hàng"""
    data = request.get_json()
    product_id = data.get("product_id")
    quantity = data.get("quantity", 1)
    
    # Kiểm tra sản phẩm có tồn tại
    product = next((p for p in products_db if p["id"] == product_id), None)
    if not product:
        return jsonify({"success": False, "message": "Sản phẩm không tồn tại"}), 404
    
    # Kiểm tra tồn kho
    if product["stock"] < quantity:
        return jsonify({"success": False, "message": "Không đủ hàng trong kho"}), 400
    
    # Khởi tạo giỏ hàng nếu chưa có
    if session_id not in cart_db:
        cart_db[session_id] = []
    
    cart = cart_db[session_id]
    
    # Kiểm tra sản phẩm đã có trong giỏ chưa
    existing_item = next((item for item in cart if item["product_id"] == product_id), None)
    
    if existing_item:
        # Cập nhật số lượng
        new_quantity = existing_item["quantity"] + quantity
        if product["stock"] < new_quantity:
            return jsonify({"success": False, "message": "Không đủ hàng trong kho"}), 400
        existing_item["quantity"] = new_quantity
        existing_item["total_price"] = calculate_item_total(existing_item)
    else:
        # Thêm mới vào giỏ
        cart_item = {
            "product_id": product_id,
            "product_name": product["name"],
            "unit_price": product["price"],
            "quantity": quantity,
            "total_price": calculate_item_total({"quantity": quantity, "unit_price": product["price"]})
        }
        cart.append(cart_item)
    
    return jsonify({
        "success": True,
        "message": "Đã thêm vào giỏ hàng",
        "data": {
            "items": cart,
            "total_amount": calculate_cart_total(cart)
        }
    })

@app.route('/api/cart/<session_id>/update', methods=['PUT'])
def update_cart_item(session_id):
    """Cập nhật số lượng sản phẩm trong giỏ"""
    data = request.get_json()
    product_id = data.get("product_id")
    quantity = data.get("quantity")
    
    if session_id not in cart_db:
        return jsonify({"success": False, "message": "Giỏ hàng không tồn tại"}), 404
    
    cart = cart_db[session_id]
    cart_item = next((item for item in cart if item["product_id"] == product_id), None)
    
    if not cart_item:
        return jsonify({"success": False, "message": "Sản phẩm không có trong giỏ"}), 404
    
    # Kiểm tra tồn kho
    product = next((p for p in products_db if p["id"] == product_id), None)
    if product["stock"] < quantity:
        return jsonify({"success": False, "message": "Không đủ hàng trong kho"}), 400
    
    # Cập nhật số lượng và tính lại thành tiền
    cart_item["quantity"] = quantity
    cart_item["total_price"] = calculate_item_total(cart_item)
    
    return jsonify({
        "success": True,
        "message": "Đã cập nhật giỏ hàng",
        "data": {
            "items": cart,
            "total_amount": calculate_cart_total(cart)
        }
    })

@app.route('/api/cart/<session_id>/remove/<int:product_id>', methods=['DELETE'])
def remove_from_cart(session_id, product_id):
    """Xóa sản phẩm khỏi giỏ hàng"""
    if session_id not in cart_db:
        return jsonify({"success": False, "message": "Giỏ hàng không tồn tại"}), 404
    
    cart_db[session_id] = [item for item in cart_db[session_id] if item["product_id"] != product_id]
    
    return jsonify({
        "success": True,
        "message": "Đã xóa khỏi giỏ hàng",
        "data": {
            "items": cart_db[session_id],
            "total_amount": calculate_cart_total(cart_db[session_id])
        }
    })

# =================================
# CALCULATION APIs - Câu 3, 4: Tính toán
# =================================

def calculate_item_total(item):
    """Câu 3: Tính thành tiền = số lượng × đơn giá"""
    return item["quantity"] * item["unit_price"]

def calculate_cart_total(cart):
    """Câu 4: Tính tổng thành tiền các đơn hàng"""
    return sum(item["total_price"] for item in cart)

@app.route('/api/calculate/item', methods=['POST'])
def calculate_item_price():
    """API tính thành tiền cho một sản phẩm"""
    data = request.get_json()
    quantity = data.get("quantity", 0)
    unit_price = data.get("unit_price", 0)
    
    total_price = quantity * unit_price
    
    return jsonify({
        "success": True,
        "data": {
            "quantity": quantity,
            "unit_price": unit_price,
            "total_price": total_price,
            "formula": f"{quantity} × {unit_price:,} = {total_price:,}"
        }
    })

@app.route('/api/calculate/cart/<session_id>', methods=['GET'])
def calculate_cart_summary(session_id):
    """API tính tổng giỏ hàng"""
    cart = cart_db.get(session_id, [])
    
    summary = {
        "items": [],
        "subtotal": 0,
        "tax": 0,
        "total": 0
    }
    
    for item in cart:
        item_total = calculate_item_total(item)
        summary["items"].append({
            "product_name": item["product_name"],
            "quantity": item["quantity"],
            "unit_price": item["unit_price"],
            "total_price": item_total
        })
        summary["subtotal"] += item_total
    
    # Tính thuế 10%
    summary["tax"] = summary["subtotal"] * 0.1
    summary["total"] = summary["subtotal"] + summary["tax"]
    
    return jsonify({
        "success": True,
        "data": summary
    })

# =================================
# ORDER APIs - Câu 5: Đặt hàng và hiển thị
# =================================

@app.route('/api/orders', methods=['POST'])
def create_order():
    """Tạo đơn hàng mới từ giỏ hàng"""
    data = request.get_json()
    session_id = data.get("session_id")
    customer_info = data.get("customer", {})
    
    if session_id not in cart_db or not cart_db[session_id]:
        return jsonify({"success": False, "message": "Giỏ hàng trống"}), 400
    
    cart = cart_db[session_id]
    
    # Kiểm tra tồn kho một lần nữa
    for item in cart:
        product = next((p for p in products_db if p["id"] == item["product_id"]), None)
        if not product or product["stock"] < item["quantity"]:
            return jsonify({
                "success": False, 
                "message": f"Sản phẩm {item['product_name']} không đủ hàng"
            }), 400
    
    # Tạo đơn hàng
    order = {
        "order_id": str(uuid.uuid4())[:8].upper(),
        "date": datetime.now().isoformat(),
        "customer": customer_info,
        "items": cart.copy(),
        "order_total": calculate_cart_total(cart),
        "status": "Đã đặt hàng"
    }
    
    # Cập nhật tồn kho
    for item in cart:
        product = next((p for p in products_db if p["id"] == item["product_id"]), None)
        product["stock"] -= item["quantity"]
    
    # Lưu đơn hàng và xóa giỏ hàng
    orders_db.append(order)
    cart_db[session_id] = []
    
    return jsonify({
        "success": True,
        "message": "Đặt hàng thành công!",
        "data": order
    }), 201

@app.route('/api/orders', methods=['GET'])
def get_all_orders():
    """Lấy danh sách tất cả đơn hàng"""
    return jsonify({
        "success": True,
        "data": orders_db,
        "total": len(orders_db)
    })

@app.route('/api/orders/<order_id>', methods=['GET'])
def get_order(order_id):
    """Lấy thông tin một đơn hàng"""
    order = next((o for o in orders_db if o["order_id"] == order_id), None)
    if not order:
        return jsonify({"success": False, "message": "Đơn hàng không tồn tại"}), 404
    return jsonify({"success": True, "data": order})

@app.route('/api/orders/<order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    """Cập nhật trạng thái đơn hàng"""
    data = request.get_json()
    new_status = data.get("status")
    
    order = next((o for o in orders_db if o["order_id"] == order_id), None)
    if not order:
        return jsonify({"success": False, "message": "Đơn hàng không tồn tại"}), 404
    
    order["status"] = new_status
    return jsonify({
        "success": True,
        "message": "Đã cập nhật trạng thái đơn hàng",
        "data": order
    })

# =================================
# DASHBOARD APIs - Thống kê
# =================================

@app.route('/api/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """Lấy thống kê tổng quan"""
    total_products = len(products_db)
    total_orders = len(orders_db)
    total_revenue = sum(order["order_total"] for order in orders_db)
    
    # Sản phẩm bán chạy
    product_sales = {}
    for order in orders_db:
        for item in order["items"]:
            product_id = item["product_id"]
            if product_id not in product_sales:
                product_sales[product_id] = {
                    "name": item["product_name"],
                    "quantity": 0,
                    "revenue": 0
                }
            product_sales[product_id]["quantity"] += item["quantity"]
            product_sales[product_id]["revenue"] += item["total_price"]
    
    best_selling = sorted(product_sales.values(), key=lambda x: x["quantity"], reverse=True)[:5]
    
    return jsonify({
        "success": True,
        "data": {
            "total_products": total_products,
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "best_selling_products": best_selling,
            "low_stock_products": [p for p in products_db if p["stock"] < 5]
        }
    })

# =================================
# ERROR HANDLERS
# =================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({"success": False, "message": "Endpoint không tồn tại"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"success": False, "message": "Lỗi server nội bộ"}), 500

# =================================
# MAIN
# =================================

@app.route('/', methods=['GET'])
def home():
    """API Documentation"""
    return jsonify({
        "message": "🛒 RESTful API Hệ Thống Bán Hàng Trực Tuyến",
        "version": "1.0.0",
        "endpoints": {
            "products": {
                "GET /api/products": "Lấy danh sách sản phẩm",
                "GET /api/products/<id>": "Lấy thông tin sản phẩm",
                "POST /api/products": "Thêm sản phẩm mới",
                "PUT /api/products/<id>": "Cập nhật sản phẩm",
                "DELETE /api/products/<id>": "Xóa sản phẩm"
            },
            "cart": {
                "GET /api/cart/<session_id>": "Lấy giỏ hàng",
                "POST /api/cart/<session_id>/add": "Thêm vào giỏ hàng",
                "PUT /api/cart/<session_id>/update": "Cập nhật giỏ hàng",
                "DELETE /api/cart/<session_id>/remove/<product_id>": "Xóa khỏi giỏ hàng"
            },
            "orders": {
                "GET /api/orders": "Lấy danh sách đơn hàng",
                "GET /api/orders/<id>": "Lấy thông tin đơn hàng",
                "POST /api/orders": "Tạo đơn hàng mới",
                "PUT /api/orders/<id>/status": "Cập nhật trạng thái đơn hàng"
            },
            "calculate": {
                "POST /api/calculate/item": "Tính thành tiền sản phẩm",
                "GET /api/calculate/cart/<session_id>": "Tính tổng giỏ hàng"
            },
            "dashboard": {
                "GET /api/dashboard/stats": "Thống kê tổng quan"
            }
        },
        "services_implemented": [
            "Câu 1: Cơ sở dữ liệu sản phẩm",
            "Câu 2: Dịch vụ quản lý danh mục đơn hàng",
            "Câu 3: Dịch vụ tính thành tiền = số lượng × đơn giá",
            "Câu 4: Dịch vụ tính tổng thành tiền các đơn hàng",
            "Câu 5: Hiển thị danh mục đơn hàng, tính toán và thanh toán"
        ]
    })

if __name__ == '__main__':
    print("🚀 Starting Online Store RESTful API...")
    print("📖 API Documentation: http://localhost:5000/")
    print("🛒 Products API: http://localhost:5000/api/products")
    app.run(debug=True, host='0.0.0.0', port=5000)