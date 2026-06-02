const db = require('../config/db');

const getCompanies = async () => {
    const [rows] = await db.query('SELECT * FROM Companies ORDER BY rating DESC');
    return rows;
};

const getCompanyById = async (companyId) => {
    const [rows] = await db.query('SELECT * FROM Companies WHERE id = ?', [companyId]);
    if (!rows.length) return null;
    return rows[0];
};

const getCompanyIncome = async (companyId) => {
    const [rows] = await db.query(`
        SELECT SUM(oi.subtotal) AS total_omzet, COUNT(DISTINCT o.id) AS total_pesanan
        FROM Order_Items oi
        JOIN Products p ON oi.product_id = p.id
        JOIN Orders o ON oi.order_id = o.id
        WHERE p.company_id = ? AND o.status = 'completed'
    `, [companyId]);

    const [monthlyRows] = await db.query(`
        SELECT DATE_FORMAT(o.created_at, '%Y-%m') AS month, SUM(oi.subtotal) AS omzet
        FROM Order_Items oi
        JOIN Orders o ON oi.order_id = o.id
        JOIN Products p ON oi.product_id = p.id
        WHERE p.company_id = ? AND o.status = 'completed'
        GROUP BY month
        ORDER BY month ASC
    `, [companyId]);

    return {
        total_omzet: rows[0]?.total_omzet || 0,
        total_pesanan: rows[0]?.total_pesanan || 0,
        monthly_omzet: monthlyRows
    };
};

const getCompanyOrders = async (companyId) => {
    const [rows] = await db.query(`
        SELECT o.id AS order_id, o.created_at, o.status AS order_status,
               u.username AS customer_name,
               oi.quantity, p.product_name, p.image_url, oi.subtotal,
               s.shipping_status, s.tracking_number,
               sc.company_name AS shipment_company_name, sc.service_type AS shipment_service
        FROM Orders o
        JOIN Order_Items oi ON o.id = oi.order_id
        JOIN Products p ON oi.product_id = p.id
        JOIN Users u ON o.user_id = u.id
        LEFT JOIN Shipments s ON o.id = s.order_id AND s.company_id = ?
        LEFT JOIN Shipment_Companies sc ON s.shipment_company_id = sc.id
        WHERE p.company_id = ?
        ORDER BY o.created_at DESC LIMIT 500
    `, [companyId, companyId]);
    return rows;
};


const createCompany = async (userId, companyName, address) => {
    const [result] = await db.query(
        'INSERT INTO Companies (user_id, company_name, address) VALUES (?, ?, ?)',
        [userId, companyName, address]
    );
    return { companyId: result.insertId };
};

const updateCompany = async (companyId, companyName, address) => {
    await db.query(
        'UPDATE Companies SET company_name = ?, address = ? WHERE id = ?',
        [companyName, address, companyId]
    );
    return true;
};

module.exports = {
    getCompanies,
    getCompanyById,
    getCompanyIncome,
    getCompanyOrders,
    createCompany,
    updateCompany
};
