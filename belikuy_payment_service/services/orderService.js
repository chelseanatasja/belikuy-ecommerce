const db = require('../config/db');

const createOrder = async (userId, addressId, totalPrice, cartItems, paymentMethodId, shippingMethodId) => {
    const connection = await db.getConnection();
    try {
        await connection.beginTransaction();

        // 1. Create Order
        const [orderResult] = await connection.query(
            "INSERT INTO Orders (user_id, address_id, total_price, status) VALUES (?, ?, ?, 'pending')",
            [userId, addressId, totalPrice]
        );
        const orderId = orderResult.insertId;

        // 1b. Create Pending Payment if method is provided
        if (paymentMethodId) {
            await connection.query(
                "INSERT INTO Payments (order_id, payment_method_id, payment_status) VALUES (?, ?, 'pending')",
                [orderId, paymentMethodId]
            );
        }

        // 2. Insert Order Items & Deduct Stock & Find Companies
        const companyShipments = new Set();
        for (const item of cartItems) {
            await connection.query(
                "INSERT INTO Order_Items (order_id, product_id, quantity, price, subtotal) VALUES (?, ?, ?, ?, ?)",
                [orderId, item.product_id, item.quantity, item.price, item.subtotal]
            );
            
            // Deduct Stock
            await connection.query(
                "UPDATE Products SET stock = stock - ? WHERE id = ?",
                [item.quantity, item.product_id]
            );

            companyShipments.add(item.company_id);
        }

        // 3. Create Shipment entries per company
        for (const companyId of companyShipments) {
            await connection.query(
                "INSERT INTO Shipments (order_id, company_id, shipment_company_id, shipping_status) VALUES (?, ?, ?, 'pending')",
                [orderId, companyId, shippingMethodId || null]
            );
        }

        await connection.commit();
        return { success: true, orderId };
    } catch (err) {
        await connection.rollback();
        throw new Error("Checkout transaction failed: " + err.message);
    } finally {
        connection.release();
    }
};

const getUserOrders = async (userId) => {
    // Fetch all orders for this user
    const [orders] = await db.query(`
        SELECT o.id AS order_id, o.created_at, o.total_price, o.status,
               pm.institution_name AS payment_method, pay.payment_status
        FROM Orders o
        LEFT JOIN Payments pay ON o.id = pay.order_id
        LEFT JOIN Payment_Methods pm ON pay.payment_method_id = pm.id
        WHERE o.user_id = ?
        ORDER BY o.created_at DESC
    `, [userId]);

    if (!orders.length) return [];

    // Fetch all items for these orders in one query
    const orderIds = orders.map(o => o.order_id);
    const [items] = await db.query(`
        SELECT oi.order_id, oi.quantity, oi.subtotal,
               p.product_name, p.image_url,
               c.company_name AS seller_name
        FROM Order_Items oi
        JOIN Products p ON oi.product_id = p.id
        JOIN Companies c ON p.company_id = c.id
        WHERE oi.order_id IN (?)
        ORDER BY oi.id ASC
    `, [orderIds]);

    // Fetch shipment info per order (one shipment per company per order, pick first for customer view)
    const [shipments] = await db.query(`
        SELECT s.order_id, s.shipping_status, s.tracking_number,
               sc.company_name AS shipment_company, sc.service_type AS shipment_service
        FROM Shipments s
        LEFT JOIN Shipment_Companies sc ON s.shipment_company_id = sc.id
        WHERE s.order_id IN (?)
        ORDER BY s.id ASC
    `, [orderIds]);

    // Group items and shipments by order_id
    const itemsByOrder = {};
    for (const item of items) {
        if (!itemsByOrder[item.order_id]) itemsByOrder[item.order_id] = [];
        itemsByOrder[item.order_id].push(item);
    }
    const shipmentByOrder = {};
    for (const s of shipments) {
        if (!shipmentByOrder[s.order_id]) shipmentByOrder[s.order_id] = s;
    }

    return orders.map(o => ({
        ...o,
        items: itemsByOrder[o.order_id] || [],
        shipment: shipmentByOrder[o.order_id] || null,
    }));
};


const updateOrderStatus = async (orderId, status, companyId) => {
    // Update main order status
    await db.query("UPDATE Orders SET status = ? WHERE id = ?", [status, orderId]);
    
    // Only update shipment status if companyId is provided (seller action)
    if (companyId) {
        if (status === 'shipped') {
            await db.query("UPDATE Shipments SET shipping_status = 'shipped' WHERE order_id = ? AND company_id = ?", [orderId, companyId]);
        } else if (status === 'completed') {
            await db.query("UPDATE Shipments SET shipping_status = 'delivered' WHERE order_id = ? AND company_id = ?", [orderId, companyId]);
        }
    } else if (status === 'completed') {
        // Customer confirming — mark all shipments for this order as delivered
        await db.query("UPDATE Shipments SET shipping_status = 'delivered' WHERE order_id = ?", [orderId]);
    }
    return { success: true };
};

const updateShipmentStatus = async (orderId, companyId, trackingNumber, shipmentCompanyId) => {
    // Update Shipments table (tracking number + shipping_status)
    await db.query(
        `UPDATE Shipments 
         SET tracking_number = ?, shipping_status = 'shipped'
             ${shipmentCompanyId ? ', shipment_company_id = ?' : ''}
         WHERE order_id = ? AND company_id = ?`,
        shipmentCompanyId
            ? [trackingNumber, shipmentCompanyId, orderId, companyId]
            : [trackingNumber, orderId, companyId]
    );
    // Also update Orders.status so frontend filter is consistent
    await db.query("UPDATE Orders SET status = 'shipped' WHERE id = ?", [orderId]);
    return { success: true };
};

module.exports = {
    createOrder,
    getUserOrders,
    updateOrderStatus,
    updateShipmentStatus
};
