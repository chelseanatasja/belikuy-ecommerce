const express = require('express');
const router = express.Router();
const catalogService = require('../services/catalogService');

// Get all categories
router.get('/', async (req, res) => {
    try {
        const categories = await catalogService.getCategories();
        res.json(categories);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

module.exports = router;
