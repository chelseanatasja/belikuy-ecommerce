const express = require('express');
const router = express.Router();
const logisticService = require('../services/logisticService');

// Get all user addresses
router.get('/:user_id', async (req, res) => {
    try {
        const addresses = await logisticService.getUserAddresses(req.params.user_id);
        res.json(addresses);
    } catch (err) { res.status(500).json({ error: err.message }); }
});

// Add new address
router.post('/', async (req, res) => {
    const { user_id, address, city, postal_code, is_default } = req.body;
    try {
        const result = await logisticService.addAddress(user_id, address, city, postal_code, is_default);
        res.status(201).json({ message: 'Address added', id: result.id });
    } catch (err) { res.status(500).json({ error: err.message }); }
});

// Set default address
router.put('/:id/default', async (req, res) => {
    const { user_id } = req.body;
    try {
        await logisticService.setDefaultAddress(user_id, req.params.id);
        res.json({ message: 'Default address updated' });
    } catch (err) { res.status(500).json({ error: err.message }); }
});

// Delete address
router.delete('/:id', async (req, res) => {
    try {
        await logisticService.deleteAddress(req.params.id);
        res.json({ message: 'Address deleted' });
    } catch (err) { res.status(500).json({ error: err.message }); }
});

module.exports = router;
