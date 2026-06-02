const express = require('express');
const router = express.Router();
const supplierService = require('../services/supplierService');

// Get all active suppliers
router.get('/', async (req, res) => {
    try {
        const suppliers = await supplierService.getSuppliers();
        res.json({ success: true, data: suppliers });
    } catch (err) {
        res.status(500).json({ success: false, error: err.message });
    }
});

// Get catalog for a specific supplier
router.get('/:id/catalog', async (req, res) => {
    try {
        const catalog = await supplierService.getCatalog(req.params.id);
        res.json({ success: true, data: catalog });
    } catch (err) {
        res.status(500).json({ success: false, error: err.message });
    }
});

// Create B2B order
router.post('/orders', async (req, res) => {
    // req.user must have company_id if they are a seller
    const { company_id, supplier_id, items } = req.body;
    if (!company_id || !supplier_id || !items || !items.length) {
        return res.status(400).json({ success: false, error: 'Invalid input' });
    }
    try {
        const result = await supplierService.createOrder(company_id, supplier_id, items);
        res.json({ success: true, data: result });
    } catch (err) {
        res.status(500).json({ success: false, error: err.message });
    }
});

// Get orders placed by a seller company
router.get('/orders/:companyId', async (req, res) => {
    try {
        const orders = await supplierService.getOrders(req.params.companyId);
        res.json({ success: true, data: orders });
    } catch (err) {
        res.status(500).json({ success: false, error: err.message });
    }
});

// Receive order and update stock
router.put('/orders/:id/receive', async (req, res) => {
    const { company_id } = req.body;
    try {
        const result = await supplierService.receiveOrder(req.params.id, company_id);
        res.json({ success: true, data: result });
    } catch (err) {
        res.status(500).json({ success: false, error: err.message });
    }
});

// Admin ONLY: Add catalog item
router.post('/:id/catalog', async (req, res) => {
    const { item_name, price, stock } = req.body;
    try {
        const result = await supplierService.addCatalogItem(req.params.id, item_name, price, stock || 0);
        res.json({ success: true, data: result });
    } catch (err) {
        res.status(500).json({ success: false, error: err.message });
    }
});

module.exports = router;
