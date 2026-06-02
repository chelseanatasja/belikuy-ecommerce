const db = require('../config/db');

const getSuppliers = async () => {
    const [rows] = await db.query('SELECT * FROM belikuy_supplier_db.supply_companies WHERE status = "active"');
    return rows;
};

const getCatalog = async (supplierId) => {
    const [rows] = await db.query('SELECT * FROM products WHERE supply_company_id = ?', [supplierId]);
    return rows;
};

const createOrder = async (companyId, supplierId, items) => {
    const connection = await db.getConnection();
    try {
        await connection.beginTransaction();

        let totalPrice = 0;
        for (let item of items) {
            totalPrice += item.subtotal;
        }

        const [orderResult] = await connection.query(
            'INSERT INTO belikuy_supplier_db.supplier_orders (company_id, supplier_id, total_price, status) VALUES (?, ?, ?, ?)',
            [companyId, supplierId, totalPrice, 'pending']
        );
        const orderId = orderResult.insertId;

        for (let item of items) {
            await connection.query(
                'INSERT INTO belikuy_supplier_db.supplier_order_items (supplier_order_id, product_id, quantity, price) VALUES (?, ?, ?, ?)',
                [orderId, item.catalog_id, item.quantity, item.price]
            );
            await connection.query(
                'UPDATE products SET stock = stock - ? WHERE id = ?',
                [item.quantity, item.catalog_id]
            );
        }

        await connection.commit();
        return { orderId };
    } catch (err) {
        await connection.rollback();
        throw err;
    } finally {
        connection.release();
    }
};

const getOrders = async (companyId) => {
    const [rows] = await db.query(`
        SELECT so.*, sc.supply_company_name
        FROM belikuy_supplier_db.supplier_orders so
        JOIN belikuy_supplier_db.supply_companies sc ON so.supplier_id = sc.id
        WHERE so.company_id = ?
        ORDER BY so.created_at DESC
    `, [companyId]);
    
    for (let order of rows) {
        const [items] = await db.query(`
            SELECT soi.*, c.product_name as item_name
            FROM belikuy_supplier_db.supplier_order_items soi
            JOIN belikuy_seller_db.products c ON soi.product_id = c.id
            WHERE soi.supplier_order_id = ?
        `, [order.id]);
        order.items = items;
    }
    return rows;
};

const addCatalogItem = async (supplierId, itemName, price, stock) => {
    const [result] = await db.query(
        'INSERT INTO products (supply_company_id, product_name, price, stock, category_id) VALUES (?, ?, ?, ?, 1)',
        [supplierId, itemName, price, stock]
    );
    return { id: result.insertId };
};

const receiveOrder = async (orderId, companyId) => {
    const connection = await db.getConnection();
    try {
        await connection.beginTransaction();

        // Check order
        const [orders] = await connection.query('SELECT * FROM belikuy_supplier_db.supplier_orders WHERE id = ? AND company_id = ?', [orderId, companyId]);
        if (orders.length === 0) throw new Error("Order not found or unauthorized");
        const order = orders[0];
        if (order.status !== 'shipped') throw new Error("Order is not in shipped status");

        // Get items
        const [items] = await connection.query(`
            SELECT soi.*, c.product_name, c.category_id, c.image_url, c.brand
            FROM belikuy_supplier_db.supplier_order_items soi
            JOIN belikuy_seller_db.products c ON soi.product_id = c.id
            WHERE soi.supplier_order_id = ?
        `, [orderId]);

        // Process each item
        for (let item of items) {
            // Check if seller already has this product
            const [sellerProducts] = await connection.query(
                'SELECT * FROM belikuy_seller_db.products WHERE company_id = ? AND product_name = ?',
                [companyId, item.product_name]
            );

            if (sellerProducts.length > 0) {
                // Add stock
                await connection.query(
                    'UPDATE belikuy_seller_db.products SET stock = stock + ? WHERE id = ?',
                    [item.quantity, sellerProducts[0].id]
                );
            } else {
                // Auto-listing with 20% markup
                const markupPrice = parseFloat(item.price) * 1.2;
                await connection.query(
                    'INSERT INTO belikuy_seller_db.products (company_id, supply_company_id, product_name, price, stock, category_id, description, image_url, brand) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    [companyId, order.supplier_id, item.product_name, markupPrice, item.quantity, item.category_id, 'Produk B2B ' + item.product_name, item.image_url || '', item.brand || 'No Brand']
                );
            }
        }

        // Update status
        await connection.query('UPDATE belikuy_supplier_db.supplier_orders SET status = "completed" WHERE id = ?', [orderId]);

        await connection.commit();
        return { success: true };
    } catch (err) {
        await connection.rollback();
        throw err;
    } finally {
        connection.release();
    }
};

module.exports = {
    getSuppliers,
    getCatalog,
    createOrder,
    getOrders,
    addCatalogItem,
    receiveOrder
};
