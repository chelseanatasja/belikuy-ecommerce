const express = require('express');
const router = express.Router();
const catalogService = require('../services/catalogService');

// Get all products (Storefront) with optional search, category, and price filter
router.get('/', async (req, res) => {
    try {
        const products = await catalogService.getProducts(req.query);
        res.json(products);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// Get products by company (Seller Center) — must be before /:id to avoid clash
router.get('/seller/:company_id', async (req, res) => {
    try {
        const products = await catalogService.getProductsByCompany(req.params.company_id);
        res.json(products);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// Get single product by ID
router.get('/:id', async (req, res) => {
    try {
        const product = await catalogService.getProductById(req.params.id);
        if (!product) return res.status(404).json({ error: 'Product not found' });
        res.json(product);
    } catch (err) { res.status(500).json({ error: err.message }); }
});

// Get product reviews
router.get('/:id/reviews', async (req, res) => {
    try {
        const reviews = await catalogService.getProductReviews(req.params.id);
        res.json(reviews);
    } catch (err) { res.status(500).json({ error: err.message }); }
});

// Create product (Seller Center)
router.post('/', async (req, res) => {
    try {
        const result = await catalogService.createProduct(req.body);
        res.status(201).json({ message: "Product created successfully", productId: result.productId });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// Update product (Seller Center)
router.put('/:id', async (req, res) => {
    try {
        const success = await catalogService.updateProduct(req.params.id, req.body.company_id, req.body);
        if (!success) {
            return res.status(404).json({ error: "Product not found or unauthorized" });
        }
        res.json({ message: "Product updated successfully" });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// Toggle active/inactive (Seller Center)
router.patch('/:id/toggle', async (req, res) => {
    try {
        const { company_id, is_active } = req.body;
        const success = await catalogService.toggleProductActive(req.params.id, company_id, is_active);
        if (!success) return res.status(404).json({ error: "Product not found or unauthorized" });
        res.json({ message: "Product status updated" });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// Delete product
router.delete('/:id', async (req, res) => {
    try {
        await catalogService.deleteProduct(req.params.id);
        res.json({ message: 'Product deleted successfully' });
    } catch (err) { res.status(500).json({ error: err.message }); }
});




router.get('/internal/by-ids', async (req, res) => {
    try {
        const { ids } = req.query;
        if (!ids) return res.json([]);
        const idArray = ids.split(',').map(Number);
        const products = await catalogService.getProductsByIds(idArray);
        res.json(products);
    } catch (err) { res.status(500).json({ error: err.message }); }
});

router.post('/internal/deduct-stock', async (req, res) => {
    try {
        const { items } = req.body;
        await catalogService.deductStock(items);
        res.json({ success: true });
    } catch (err) { res.status(500).json({ error: err.message }); }
});

module.exports = router;
