const axios = require('axios');
const SELLER_API = 'http://localhost:3002/api';
const db = require('../config/db');

const createOrder = async (userId, addressId, totalPrice, cartItems, paymentMethodId, shippingMethodId) => {
    const connection = await db.getConnection();
    try {
        await connection.beginTransaction();

        // 1. Create Order
        const [orderResult] = await connection.query(
            "INSERT INTO belikuy_marketplace_db.Orders (user_id, address_id, total_price, status) VALUES (?, ?, ?, 'pending')",
            [userId, addressId, totalPrice]
        );
        const orderId = orderResult.insertId;

        // 1b. Create Pending Payment if method is provided
        if (paymentMethodId) {
            await connection.query(
                "INSERT INTO belikuy_payment_db.Payments (order_id, payment_method_id, payment_status) VALUES (?, ?, 'pending')",
                [orderId, paymentMethodId]
            );
        }

        // 2. Insert Order Items & Deduct Stock & Find Companies
        const companyShipments = new Set();
        for (const item of cartItems) {
            await connection.query(
                "INSERT INTO belikuy_marketplace_db.Order_Items (order_id, product_id, quantity, price, subtotal) VALUES (?, ?, ?, ?, ?)",
                [orderId, item.product_id, item.quantity, item.price, item.subtotal]
            );
            
            // Deduct Stock
            await connection.query(
                "UPDATE belikuy_seller_db.Products SET stock = stock - ? WHERE id = ?",
                [item.quantity, item.product_id]
            );

            companyShipments.add(item.company_id);
        }

        // 3. Create Shipment entries per company
        for (const companyId of companyShipments) {
            await connection.query(
                "INSERT INTO belikuy_delivery_db.Shipments (order_id, company_id, shipment_company_id, shipping_status) VALUES (?, ?, ?, 'pending')",
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
    const [orders] = await db.query(`
        SELECT o.id AS order_id, o.created_at, o.total_price, o.status,
               (SELECT pm.institution_name FROM belikuy_payment_db.Payments p JOIN belikuy_payment_db.Payment_Methods pm ON p.payment_method_id = pm.id WHERE p.order_id = o.id ORDER BY p.id DESC LIMIT 1) AS payment_method,
               (SELECT p.payment_status FROM belikuy_payment_db.Payments p WHERE p.order_id = o.id ORDER BY p.id DESC LIMIT 1) AS payment_status
        FROM belikuy_marketplace_db.Orders o
        WHERE o.user_id = ?
        ORDER BY o.created_at DESC
    `, [userId]);

    if (!orders.length) return [];

    const orderIds = orders.map(o => o.order_id);
    const [items] = await db.query(`
        SELECT oi.order_id, oi.quantity, oi.subtotal,
               p.product_name, p.image_url,
               c.company_name AS seller_name
        FROM belikuy_marketplace_db.Order_Items oi
        JOIN belikuy_seller_db.Products p ON oi.product_id = p.id
        JOIN belikuy_seller_db.Companies c ON p.company_id = c.id
        WHERE oi.order_id IN (?)
        ORDER BY oi.id ASC
    `, [orderIds]);

    const [shipments] = await db.query(`
        SELECT s.order_id, s.shipping_status, s.tracking_number,
               sc.company_name AS shipment_company, sc.service_type AS shipment_service
        FROM belikuy_delivery_db.Shipments s
        LEFT JOIN belikuy_delivery_db.Shipment_Companies sc ON s.shipment_company_id = sc.id
        WHERE s.order_id IN (?)
        ORDER BY s.id ASC
    `, [orderIds]);

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
    await db.query("UPDATE belikuy_marketplace_db.Orders SET status = ? WHERE id = ?", [status, orderId]);
    if (companyId) {
        if (status === 'shipped') {
            await db.query("UPDATE belikuy_delivery_db.Shipments SET shipping_status = 'shipped' WHERE order_id = ? AND company_id = ?", [orderId, companyId]);
        } else if (status === 'completed') {
            await db.query("UPDATE belikuy_delivery_db.Shipments SET shipping_status = 'delivered' WHERE order_id = ? AND company_id = ?", [orderId, companyId]);
        }
    } else if (status === 'completed') {
        await db.query("UPDATE belikuy_delivery_db.Shipments SET shipping_status = 'delivered' WHERE order_id = ?", [orderId]);
    }
    return { success: true };
};

const updateShipmentStatus = async (orderId, companyId, trackingNumber, shipmentCompanyId) => {
    await db.query(
        `UPDATE belikuy_delivery_db.Shipments 
         SET tracking_number = ?, shipping_status = 'shipped'
             ${shipmentCompanyId ? ', shipment_company_id = ?' : ''}
         WHERE order_id = ? AND company_id = ?`,
        shipmentCompanyId
            ? [trackingNumber, shipmentCompanyId, orderId, companyId]
            : [trackingNumber, orderId, companyId]
    );
    await db.query("UPDATE belikuy_marketplace_db.Orders SET status = 'shipped' WHERE id = ?", [orderId]);
    return { success: true };
};

module.exports = {
    createOrder,
    getUserOrders,
    updateOrderStatus,
    updateShipmentStatus
};
