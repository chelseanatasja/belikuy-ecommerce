const express = require('express');
const router = express.Router();
const orderService = require('../services/orderService');

// Checkout: Create Order with Items and deduct stock
router.post('/checkout', async (req, res) => {
    const { user_id, address_id, total_price, cart_items, payment_method_id, shipping_method_id } = req.body;
    try {
        const result = await orderService.createOrder(user_id, address_id, total_price, cart_items, payment_method_id, shipping_method_id);
        res.status(201).json({ message: "Order placed successfully", orderId: result.orderId });
    } catch (err) {
        res.status(500).json({ error: "Transaction failed", details: err.message });
    }
});

// Get User Orders
router.get('/user/:user_id', async (req, res) => {
    const { user_id } = req.params;
    try {
        const orders = await orderService.getUserOrders(user_id);
        res.json(orders);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// Update Order Status (Seller OR Customer confirm)
router.put('/:order_id/status', async (req, res) => {
    const { order_id } = req.params;
    const { status, company_id, user_id } = req.body;
    try {
        // If customer is confirming receipt, just update main order status
        if (status === 'completed' && user_id && !company_id) {
            await orderService.updateOrderStatus(order_id, 'completed', null);
        } else {
            await orderService.updateOrderStatus(order_id, status, company_id);
        }
        res.json({ message: 'Order status updated' });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// Update shipment status (Seller confirms dispatch)
router.put('/shipment/:order_id', async (req, res) => {
    const { order_id } = req.params;
    const { company_id, tracking_number, shipment_company_id } = req.body;
    try {
        await orderService.updateShipmentStatus(order_id, company_id, tracking_number || '', shipment_company_id || null);
        res.json({ message: 'Shipment status updated' });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

module.exports = router;
