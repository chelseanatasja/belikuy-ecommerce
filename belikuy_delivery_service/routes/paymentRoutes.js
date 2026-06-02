const express = require('express');
const router = express.Router();
const paymentService = require('../services/paymentService');

// Get all active payment methods
router.get('/methods', async (req, res) => {
    try {
        const methods = await paymentService.getPaymentMethods();
        res.json(methods);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// Process Payment
router.post('/pay', async (req, res) => {
    // Note: The frontend sends 'payment_method_id' instead of 'payment_method' string
    const { order_id, payment_method_id } = req.body;
    try {
        const result = await paymentService.processPayment(order_id, payment_method_id);
        res.json(result);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

module.exports = router;
