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
        await db.query("UPDATE Orders SET status = 'paid' WHERE id = ?", [orderId]);
        
        return { success: true, message: "Payment recorded successfully" };
    } catch (err) {
        throw new Error("Payment processing failed: " + err.message);
    }
};

module.exports = {
    getPaymentMethods,
    processPayment
};
