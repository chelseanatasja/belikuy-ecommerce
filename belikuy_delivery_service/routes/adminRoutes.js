const express = require('express');
const router = express.Router();
const adminService = require('../services/adminService');

// Global transaction monitoring
router.get('/transactions', async (req, res) => {
    try {
        const transactions = await adminService.getTransactions();
        res.json(transactions);
    } catch (err) { res.status(500).json({ error: err.message }); }
});

// Get all vendors/companies
router.get('/vendors', async (req, res) => {
    try {
        const vendors = await adminService.getVendors();
        res.json(vendors);
    } catch (err) { res.status(500).json({ error: err.message }); }
});

// Delete vendor
router.delete('/vendors/:id', async (req, res) => {
    try {
        await adminService.deleteVendor(req.params.id);
        res.json({ message: 'Vendor deleted' });
    } catch (err) { res.status(500).json({ error: err.message }); }
});

// CRUD Shipment Companies
router.get('/shipment-companies', async (req, res) => {
    try {
        const shipmentCos = await adminService.getShipmentCompanies();
        res.json(shipmentCos);
    } catch (err) { res.status(500).json({ error: err.message }); }
});

router.post('/shipment-companies', async (req, res) => {
    const { company_name, service_type } = req.body;
    try {
        const result = await adminService.addShipmentCompany(company_name, service_type);
        res.status(201).json({ message: 'Shipment company added', id: result.id });
    } catch (err) { res.status(500).json({ error: err.message }); }
});

router.put('/shipment-companies/:id', async (req, res) => {
    const { company_name, service_type } = req.body;
    try {
        await adminService.updateShipmentCompany(req.params.id, company_name, service_type);
        res.json({ message: 'Shipment company updated' });
    } catch (err) { res.status(500).json({ error: err.message }); }
});

router.delete('/shipment-companies/:id', async (req, res) => {
    try {
        await adminService.deleteShipmentCompany(req.params.id);
        res.json({ message: 'Shipment company deleted' });
    } catch (err) { res.status(500).json({ error: err.message }); }
});

// CRUD Supply Companies
router.get('/supply-companies', async (req, res) => {
    try {
        const supplyCos = await adminService.getSupplyCompanies();
        res.json(supplyCos);
    } catch (err) { res.status(500).json({ error: err.message }); }
});

router.post('/supply-companies', async (req, res) => {
    const { supply_company_name, contact_number, address } = req.body;
    try {
        const result = await adminService.addSupplyCompany(supply_company_name, contact_number, address);
        res.status(201).json({ message: 'Supply company added', id: result.id });
    } catch (err) { res.status(500).json({ error: err.message }); }
});

router.put('/supply-companies/:id', async (req, res) => {
    const { supply_company_name, contact_number, address } = req.body;
    try {
        await adminService.updateSupplyCompany(req.params.id, supply_company_name, contact_number, address);
        res.json({ message: 'Supply company updated' });
    } catch (err) { res.status(500).json({ error: err.message }); }
});

router.delete('/supply-companies/:id', async (req, res) => {
    try {
        await adminService.deleteSupplyCompany(req.params.id);
        res.json({ message: 'Supply company deleted' });
    } catch (err) { res.status(500).json({ error: err.message }); }
});

// Platform stats overview
router.get('/stats', async (req, res) => {
    try {
        const stats = await adminService.getStats();
        res.json(stats);
    } catch (err) { res.status(500).json({ error: err.message }); }
});

// List all users (Admin)
router.get('/users', async (req, res) => {
    try {
        const users = await adminService.getUsers();
        res.json(users);
    } catch (err) { res.status(500).json({ error: err.message }); }
});

// Delete user (Admin)
router.delete('/users/:id', async (req, res) => {
    try {
        await adminService.deleteUser(req.params.id);
        res.json({ message: 'User deleted' });
    } catch (err) { res.status(500).json({ error: err.message }); }
});

module.exports = router;
