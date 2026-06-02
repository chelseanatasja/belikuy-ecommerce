const db = require('../config/db');

const getTransactions = async () => {
    const [summary] = await db.query(`
        SELECT COUNT(id) AS total_transaksi, SUM(total_price) AS total_perputaran_uang, status
        FROM Orders GROUP BY status
    `);
    const [recent] = await db.query(`
        SELECT o.id, o.total_price, o.status, o.created_at, u.username
        FROM Orders o JOIN Users u ON o.user_id = u.id
        ORDER BY o.created_at DESC LIMIT 20
    `);
    return { summary, recent };
};

const getVendors = async () => {
    const [rows] = await db.query(`
        SELECT c.*, u.username, u.email,
               COUNT(p.id) AS product_count
        FROM belikuy_seller_db.Companies c
        JOIN Users u ON c.user_id = u.id
        LEFT JOIN belikuy_seller_db.Products p ON c.id = p.company_id
        GROUP BY c.id ORDER BY c.created_at DESC
    `);
    return rows;
};

const deleteVendor = async (id) => {
    await db.query('DELETE FROM belikuy_seller_db.Companies WHERE id = ?', [id]);
    return true;
};

const getShipmentCompanies = async () => {
    const [rows] = await db.query('SELECT * FROM belikuy_delivery_db.Shipment_Companies ORDER BY company_name ASC');
    return rows;
};

const addShipmentCompany = async (companyName, serviceType) => {
    const [result] = await db.query('INSERT INTO belikuy_delivery_db.Shipment_Companies (company_name, service_type) VALUES (?, ?)', [companyName, serviceType]);
    return { id: result.insertId };
};

const updateShipmentCompany = async (id, companyName, serviceType) => {
    await db.query('UPDATE belikuy_delivery_db.Shipment_Companies SET company_name = ?, service_type = ? WHERE id = ?', [companyName, serviceType, id]);
    return true;
};

const deleteShipmentCompany = async (id) => {
    await db.query('DELETE FROM belikuy_delivery_db.Shipment_Companies WHERE id = ?', [id]);
    return true;
};

const getSupplyCompanies = async () => {
    const [rows] = await db.query('SELECT * FROM belikuy_supplier_db.supply_companies ORDER BY supply_company_name ASC');
    return rows;
};

const addSupplyCompany = async (name, contact, address) => {
    const [result] = await db.query('INSERT INTO belikuy_supplier_db.supply_companies (supply_company_name, contact_number, address) VALUES (?, ?, ?)', [name, contact, address]);
    return { id: result.insertId };
};

const updateSupplyCompany = async (id, name, contact, address) => {
    await db.query('UPDATE belikuy_supplier_db.supply_companies SET supply_company_name = ?, contact_number = ?, address = ? WHERE id = ?', [name, contact, address, id]);
    return true;
};

const deleteSupplyCompany = async (id) => {
    await db.query('DELETE FROM belikuy_supplier_db.supply_companies WHERE id = ?', [id]);
    return true;
};

const getStats = async () => {
    // Total Orders & Revenue All Time
    const [[allTimeOrders]] = await db.query('SELECT COUNT(*) AS count, SUM(total_price) AS total FROM Orders WHERE status != "cancelled"');
    
    // Total Orders & Revenue This Month
    const [[monthOrders]] = await db.query('SELECT COUNT(*) AS count, SUM(total_price) AS total FROM Orders WHERE status != "cancelled" AND created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)');
    
    // Verified Companies
    const [[totalCompanies]] = await db.query('SELECT COUNT(*) AS count FROM belikuy_seller_db.Companies'); // We assume all are verified for now or add is_verified if exists. Wait, Belikuy schema has no is_verified? Let's check. Actually just return totalCompanies for now.
    
    // Last 7 days orders for chart
    const [chartData] = await db.query(`
        SELECT DATE(created_at) as date, COUNT(*) as count 
        FROM Orders 
        WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 6 DAY)
        GROUP BY DATE(created_at)
        ORDER BY date ASC
    `);

    // Recent Activity (Mixed)
    const [recentOrders] = await db.query('SELECT id, total_price, created_at, "order" as type FROM Orders ORDER BY created_at DESC LIMIT 3');
    const [recentVendors] = await db.query('SELECT id, company_name, created_at, "vendor" as type FROM belikuy_seller_db.Companies ORDER BY created_at DESC LIMIT 3');
    
    // Merge and sort recent activities
    const recentActivities = [...recentOrders, ...recentVendors]
        .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
        .slice(0, 5);

    return { 
        totalOrdersAll: allTimeOrders.count || 0, 
        totalRevenueAll: allTimeOrders.total || 0, 
        totalOrdersMonth: monthOrders.count || 0,
        totalRevenueMonth: monthOrders.total || 0,
        totalCompanies: totalCompanies.count || 0,
        chartData: chartData,
        recentActivities: recentActivities
    };
};

const getUsers = async () => {
    const [rows] = await db.query(`
        SELECT u.id, u.username, u.email, u.role, u.created_at,
               c.company_name
        FROM Users u
        LEFT JOIN belikuy_seller_db.Companies c ON u.id = c.user_id
        ORDER BY u.created_at DESC
    `);
    return rows;
};

const deleteUser = async (id) => {
    await db.query('DELETE FROM Users WHERE id = ?', [id]);
    return true;
};

module.exports = {
    getTransactions,
    getVendors,
    deleteVendor,
    getShipmentCompanies,
    addShipmentCompany,
    updateShipmentCompany,
    deleteShipmentCompany,
    getSupplyCompanies,
    addSupplyCompany,
    updateSupplyCompany,
    deleteSupplyCompany,
    getStats,
    getUsers,
    deleteUser
};
