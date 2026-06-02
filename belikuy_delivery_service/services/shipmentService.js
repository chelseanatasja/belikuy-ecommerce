const db = require('../config/db');

const getShipmentCompanies = async () => {
    const [rows] = await db.query("SELECT * FROM Shipment_Companies");
    return rows;
};

const createShipments = async (orderId, companyIds, shippingMethodId) => {
    for (const companyId of companyIds) {
        await db.query(
            "INSERT INTO Shipments (order_id, company_id, shipment_company_id, shipping_status) VALUES (?, ?, ?, 'pending')",
            [orderId, companyId, shippingMethodId || null]
        );
    }
    return { success: true };
};

const getShipmentsByOrderIds = async (orderIds) => {
    if (!orderIds || orderIds.length === 0) return [];
    const [rows] = await db.query(`
        SELECT s.*, sc.company_name AS shipment_company, sc.service_type AS shipment_service
        FROM Shipments s
        LEFT JOIN Shipment_Companies sc ON s.shipment_company_id = sc.id
        WHERE s.order_id IN (?)
    `, [orderIds]);
    return rows;
};

module.exports = {
    getShipmentCompanies,
    createShipments,
    getShipmentsByOrderIds
};