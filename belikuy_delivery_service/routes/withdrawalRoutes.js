const express = require('express');
const router = express.Router();
const withdrawalService = require('../services/withdrawalService');

// [ADMIN] Get ALL withdrawals across all sellers
router.get('/', async (req, res) => {
    try {
        const withdrawals = await withdrawalService.getAllWithdrawals();
        res.json(withdrawals);
    } catch (err) { res.status(500).json({ error: err.message }); }
});

// [ADMIN] Update withdrawal status (approve / reject)
router.patch('/:id/status', async (req, res) => {
    const { status } = req.body;
    const validStatuses = ['pending', 'processed', 'completed', 'rejected'];
    if (!validStatuses.includes(status)) {
        return res.status(400).json({ error: 'Status tidak valid' });
    }
    try {
        await withdrawalService.updateWithdrawalStatus(req.params.id, status);
        res.json({ message: 'Status penarikan diperbarui' });
    } catch (err) { res.status(500).json({ error: err.message }); }
});

// [SELLER] Get withdrawals for a specific company
router.get('/:company_id', async (req, res) => {
    try {
        const withdrawals = await withdrawalService.getWithdrawals(req.params.company_id);
        res.json(withdrawals);
    } catch (err) { res.status(500).json({ error: err.message }); }
});

// [SELLER] Create withdrawal request
router.post('/', async (req, res) => {
    const { company_id, amount, bank_name, account_number, account_holder } = req.body;
    if (!company_id || !amount || !bank_name || !account_number || !account_holder) {
        return res.status(400).json({ error: 'Semua field wajib diisi' });
    }
    try {
        const result = await withdrawalService.createWithdrawal(
            company_id, amount, bank_name, account_number, account_holder
        );
        res.status(201).json({ message: 'Permintaan tarik dana berhasil dikirim', withdrawalId: result.withdrawalId });
    } catch (err) { res.status(500).json({ error: err.message }); }
});

module.exports = router;
