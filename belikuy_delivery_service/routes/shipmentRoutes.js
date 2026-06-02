const express = require('express');
const router = express.Router();
const shipmentService = require('../services/shipmentService');

router.get('/companies', async (req, res) => {
    try {
        const companies = await shipmentService.getShipmentCompanies();
        res.json(companies);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

router.post('/internal/create', async (req, res) => {
    try {
        const { orderId, companyIds, shippingMethodId } = req.body;
        await shipmentService.createShipments(orderId, companyIds, shippingMethodId);
        res.json({ success: true });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

router.get('/internal/by-orders', async (req, res) => {
    try {
        const { ids } = req.query;
        if (!ids) return res.json([]);
        const idArray = ids.split(',').map(Number);
        const shipments = await shipmentService.getShipmentsByOrderIds(idArray);
        res.json(shipments);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

module.exports = router;