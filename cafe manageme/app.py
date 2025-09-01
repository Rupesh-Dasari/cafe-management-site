from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafe.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Models
class MenuItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<MenuItem {self.name}>'

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_phone = db.Column(db.String(20))
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, completed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    order_items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Order {self.id}>'

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_item.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    menu_item = db.relationship('MenuItem', backref='order_items')

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin_dashboard():
    total_orders = Order.query.count()
    pending_orders = Order.query.filter_by(status='pending').count()
    completed_orders = Order.query.filter_by(status='completed').count()
    total_revenue = db.session.query(db.func.sum(Order.total_amount)).filter_by(status='completed').scalar() or 0
    
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html', 
                         total_orders=total_orders,
                         pending_orders=pending_orders,
                         completed_orders=completed_orders,
                         total_revenue=total_revenue,
                         recent_orders=recent_orders)

@app.route('/admin/menu')
def admin_menu():
    menu_items = MenuItem.query.all()
    categories = db.session.query(MenuItem.category).distinct().all()
    categories = [cat[0] for cat in categories]
    return render_template('admin/menu.html', menu_items=menu_items, categories=categories)

@app.route('/admin/menu/add', methods=['GET', 'POST'])
def add_menu_item():
    if request.method == 'POST':
        try:
            name = request.form['name']
            description = request.form['description']
            price = float(request.form['price'])
            category = request.form['category']
            
            menu_item = MenuItem(name=name, description=description, price=price, category=category)
            db.session.add(menu_item)
            db.session.commit()
            flash('Menu item added successfully!', 'success')
            return redirect(url_for('admin_menu'))
        except Exception as e:
            flash(f'Error adding menu item: {str(e)}', 'error')
    
    return render_template('admin/add_menu_item.html')

@app.route('/admin/menu/edit/<int:id>', methods=['GET', 'POST'])
def edit_menu_item(id):
    menu_item = MenuItem.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            menu_item.name = request.form['name']
            menu_item.description = request.form['description']
            menu_item.price = float(request.form['price'])
            menu_item.category = request.form['category']
            menu_item.available = 'available' in request.form
            
            db.session.commit()
            flash('Menu item updated successfully!', 'success')
            return redirect(url_for('admin_menu'))
        except Exception as e:
            flash(f'Error updating menu item: {str(e)}', 'error')
    
    return render_template('admin/edit_menu_item.html', menu_item=menu_item)

@app.route('/admin/menu/delete/<int:id>')
def delete_menu_item(id):
    try:
        menu_item = MenuItem.query.get_or_404(id)
        db.session.delete(menu_item)
        db.session.commit()
        flash('Menu item deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting menu item: {str(e)}', 'error')
    
    return redirect(url_for('admin_menu'))

@app.route('/admin/orders')
def admin_orders():
    status_filter = request.args.get('status', 'all')
    
    if status_filter == 'all':
        orders = Order.query.order_by(Order.created_at.desc()).all()
    else:
        orders = Order.query.filter_by(status=status_filter).order_by(Order.created_at.desc()).all()
    
    return render_template('admin/orders.html', orders=orders, status_filter=status_filter)

@app.route('/admin/orders/update/<int:id>/<status>')
def update_order_status(id, status):
    try:
        order = Order.query.get_or_404(id)
        order.status = status
        db.session.commit()
        flash(f'Order status updated to {status}!', 'success')
    except Exception as e:
        flash(f'Error updating order status: {str(e)}', 'error')
    
    return redirect(url_for('admin_orders'))

@app.route('/menu')
def customer_menu():
    category_filter = request.args.get('category', 'all')
    
    if category_filter == 'all':
        menu_items = MenuItem.query.filter_by(available=True).all()
    else:
        menu_items = MenuItem.query.filter_by(category=category_filter, available=True).all()
    
    categories = db.session.query(MenuItem.category).filter_by(available=True).distinct().all()
    categories = [cat[0] for cat in categories]
    
    return render_template('customer/menu.html', menu_items=menu_items, categories=categories, current_category=category_filter)

@app.route('/order', methods=['GET', 'POST'])
def place_order():
    if request.method == 'POST':
        try:
            customer_name = request.form['customer_name']
            customer_phone = request.form.get('customer_phone', '')
            
            # Get cart items from form
            cart_items = []
            for key, value in request.form.items():
                if key.startswith('quantity_') and int(value) > 0:
                    menu_item_id = int(key.split('_')[1])
                    quantity = int(value)
                    menu_item = MenuItem.query.get(menu_item_id)
                    if menu_item:
                        cart_items.append({
                            'menu_item': menu_item,
                            'quantity': quantity,
                            'subtotal': menu_item.price * quantity
                        })
            
            if not cart_items:
                flash('Please select at least one item!', 'error')
                return redirect(url_for('customer_menu'))
            
            # Calculate total
            total_amount = sum(item['subtotal'] for item in cart_items)
            
            # Create order
            order = Order(customer_name=customer_name, customer_phone=customer_phone, total_amount=total_amount)
            db.session.add(order)
            db.session.flush()  # Get the order ID
            
            # Add order items
            for item in cart_items:
                order_item = OrderItem(
                    order_id=order.id,
                    menu_item_id=item['menu_item'].id,
                    quantity=item['quantity'],
                    price=item['menu_item'].price
                )
                db.session.add(order_item)
            
            db.session.commit()
            flash(f'Order placed successfully! Order ID: {order.id}', 'success')
            return redirect(url_for('order_confirmation', order_id=order.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error placing order: {str(e)}', 'error')
    
    menu_items = MenuItem.query.filter_by(available=True).all()
    categories = db.session.query(MenuItem.category).filter_by(available=True).distinct().all()
    categories = [cat[0] for cat in categories]
    
    return render_template('customer/order.html', menu_items=menu_items, categories=categories)

@app.route('/order/confirmation/<int:order_id>')
def order_confirmation(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template('customer/order_confirmation.html', order=order)

@app.route('/track')
def track_order():
    return render_template('customer/track_order.html')

@app.route('/api/track/<int:order_id>')
def api_track_order(order_id):
    order = Order.query.get(order_id)
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    
    return jsonify({
        'id': order.id,
        'customer_name': order.customer_name,
        'status': order.status,
        'total_amount': order.total_amount,
        'created_at': order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'items': [{
            'name': item.menu_item.name,
            'quantity': item.quantity,
            'price': item.price
        } for item in order.order_items]
    })

# Initialize database
def init_db():
    with app.app_context():
        db.create_all()
        
        # Add sample menu items if none exist
        if MenuItem.query.count() == 0:
            sample_items = [
                MenuItem(name='Espresso', description='Strong black coffee', price=2.50, category='Coffee'),
                MenuItem(name='Cappuccino', description='Espresso with steamed milk foam', price=3.50, category='Coffee'),
                MenuItem(name='Latte', description='Espresso with steamed milk', price=4.00, category='Coffee'),
                MenuItem(name='Americano', description='Espresso with hot water', price=3.00, category='Coffee'),
                MenuItem(name='Green Tea', description='Fresh green tea', price=2.00, category='Tea'),
                MenuItem(name='Earl Grey', description='Classic English tea', price=2.50, category='Tea'),
                MenuItem(name='Chocolate Croissant', description='Buttery pastry with chocolate', price=3.50, category='Pastries'),
                MenuItem(name='Blueberry Muffin', description='Fresh baked muffin', price=2.75, category='Pastries'),
                MenuItem(name='Caesar Salad', description='Fresh romaine with parmesan', price=8.50, category='Food'),
                MenuItem(name='Grilled Sandwich', description='Toasted sandwich with cheese', price=6.50, category='Food'),
            ]
            
            for item in sample_items:
                db.session.add(item)
            
            db.session.commit()

if __name__ == '__main__':
    init_db()
    app.run(debug=True)