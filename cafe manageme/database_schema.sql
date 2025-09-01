-- Café Management System Database Schema
-- This file shows the database structure that will be created by SQLAlchemy

-- Menu Items Table
CREATE TABLE menu_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price FLOAT NOT NULL,
    category VARCHAR(50) NOT NULL,
    available BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Orders Table
CREATE TABLE "order" (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name VARCHAR(100) NOT NULL,
    customer_phone VARCHAR(20),
    total_amount FLOAT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending', -- pending, completed, cancelled
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Order Items Table (Junction table for orders and menu items)
CREATE TABLE order_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    menu_item_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    price FLOAT NOT NULL, -- Price at time of order
    FOREIGN KEY (order_id) REFERENCES "order"(id) ON DELETE CASCADE,
    FOREIGN KEY (menu_item_id) REFERENCES menu_item(id)
);

-- Sample Data
INSERT INTO menu_item (name, description, price, category) VALUES 
('Espresso', 'Strong black coffee', 2.50, 'Coffee'),
('Cappuccino', 'Espresso with steamed milk foam', 3.50, 'Coffee'),
('Latte', 'Espresso with steamed milk', 4.00, 'Coffee'),
('Americano', 'Espresso with hot water', 3.00, 'Coffee'),
('Green Tea', 'Fresh green tea', 2.00, 'Tea'),
('Earl Grey', 'Classic English tea', 2.50, 'Tea'),
('Chocolate Croissant', 'Buttery pastry with chocolate', 3.50, 'Pastries'),
('Blueberry Muffin', 'Fresh baked muffin', 2.75, 'Pastries'),
('Caesar Salad', 'Fresh romaine with parmesan', 8.50, 'Food'),
('Grilled Sandwich', 'Toasted sandwich with cheese', 6.50, 'Food');

-- Indexes for better performance
CREATE INDEX idx_menu_item_category ON menu_item(category);
CREATE INDEX idx_menu_item_available ON menu_item(available);
CREATE INDEX idx_order_status ON "order"(status);
CREATE INDEX idx_order_created_at ON "order"(created_at);
CREATE INDEX idx_order_item_order_id ON order_item(order_id);
CREATE INDEX idx_order_item_menu_item_id ON order_item(menu_item_id);