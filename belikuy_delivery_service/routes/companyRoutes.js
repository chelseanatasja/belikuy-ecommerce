const express = require('express');
const router = express.Router();
const companyService = require('../services/companyService');

// Get all companies
router.get('/', async (req, res) => {
    try {
        const companies = await companyService.getCompanies();
        res.json(companies);
    } catch (err) { res.status(500).json({ error: err.message }); }
});

// Get company info for seller
router.get('/:company_id', async (req, res) => {
    try {
        const company = await companyService.getCompanyById(req.params.company_id);
        if (!company) return res.status(404).json({ error: 'Company not found' });
        res.json(company);
    } catch (err) { res.status(500).json({ error: err.message }); }
});

// Seller income report
router.get('/:company_id/income', async (req, res) => {
    try {
        const income = await companyService.getCompanyIncome(req.params.company_id);
        res.json(income);
    } catch (err) { res.status(500).json({ error: err.message }); }
});

// Seller recent orders
router.get('/:company_id/orders', async (req, res) => {
    try {
        const orders = await companyService.getCompanyOrders(req.params.company_id);
        res.json(orders);
    } catch (err) { res.status(500).json({ error: err.message }); }
});

// Create company (store) for a seller
router.post('/', async (req, res) => {
    const { user_id, company_name, address } = req.body;
    try {
        const result = await companyService.createCompany(user_id, company_name, address);
        res.status(201).json({ message: 'Store created', company_id: result.companyId });
    } catch (err) { res.status(500).json({ error: err.message }); }
});

// Update company info (Seller Settings)
router.put('/:company_id', async (req, res) => {
    try {
        const { company_name, address } = req.body;
        await companyService.updateCompany(req.params.company_id, company_name, address);
        res.json({ message: 'Company updated' });
    } catch (err) { res.status(500).json({ error: err.message }); }
});

module.exports = router;
