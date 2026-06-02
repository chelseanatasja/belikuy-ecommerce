const db = require('../config/db');

// Get all active payment methods
const getPaymentMethods = async () => {
    try {
        const [methods] = await db.query("SELECT * FROM Payment_Methods WHERE status = 1 OR status = TRUE");
        return methods;
    } catch (err) {
        throw new Error("Failed to fetch payment methods: " + err.message);
    }
};

// Process a payment
const processPayment = async (orderId, paymentMethodId) => {
    // Basic validation
    if (!orderId || !paymentMethodId) {
        throw new Error("Order ID and Payment Method ID are required");
    }

    try {
        await db.query(
            "INSERT INTO Payments (order_id, payment_method_id, payment_status, paid_at) VALUES (?, ?, 'paid', NOW()) ON DUPLICATE KEY UPDATE payment_method_id=VALUES(payment_method_id), payment_status='paid'",
            [orderId, paymentMethodId]
        );
        
        // Also update order status
        await db.query("UPDATE belikuy_marketplace_db.Orders SET status = 'paid' WHERE id = ?", [orderId]);
        
        return { success: true, message: "Payment recorded successfully" };
    } catch (err) {
        throw new Error("Payment processing failed: " + err.message);
    }
};

// Process a B2B supplier payment
const processSupplierPayment = async (supplierOrderId, companyId, amount, paymentMethod) => {
    if (!supplierOrderId || !companyId || !amount || !paymentMethod) {
        throw new Error("Missing required fields for supplier payment");
    }
    try {
        // Insert B2B Payment Record
        const [result] = await db.query(
            "INSERT INTO supplier_payments (supplier_order_id, company_id, amount, payment_method, status) VALUES (?, ?, ?, ?, 'success')",
            [supplierOrderId, companyId, amount, paymentMethod]
        );
        
        // Update order status in belikuy_supplier_db
        await db.query("UPDATE belikuy_supplier_db.supplier_orders SET status = 'paid' WHERE id = ?", [supplierOrderId]);
        
        return { success: true, message: "Supplier payment recorded successfully" };
    } catch (err) {
        throw new Error("Supplier payment processing failed: " + err.message);
    }
};

module.exports = {
    getPaymentMethods,
    processPayment,
    processSupplierPayment
};
