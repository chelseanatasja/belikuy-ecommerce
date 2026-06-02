const db = require('../config/db');

const getUserAddresses = async (userId) => {
    const [rows] = await db.query('SELECT * FROM User_Addresses WHERE user_id = ? ORDER BY is_default DESC', [userId]);
    return rows;
};

const addAddress = async (userId, address, city, postalCode, isDefault) => {
    if (isDefault) {
        await db.query('UPDATE User_Addresses SET is_default = FALSE WHERE user_id = ?', [userId]);
    }
    const [result] = await db.query(
        'INSERT INTO User_Addresses (user_id, address, city, postal_code, is_default) VALUES (?, ?, ?, ?, ?)',
        [userId, address, city, postalCode, isDefault || false]
    );
    return { id: result.insertId };
};

const setDefaultAddress = async (userId, addressId) => {
    await db.query('UPDATE User_Addresses SET is_default = FALSE WHERE user_id = ?', [userId]);
    await db.query('UPDATE User_Addresses SET is_default = TRUE WHERE id = ? AND user_id = ?', [addressId, userId]);
    return true;
};

const deleteAddress = async (addressId) => {
    await db.query('DELETE FROM User_Addresses WHERE id = ?', [addressId]);
    return true;
};

const getShipmentCompanies = async () => {
    const [rows] = await db.query('SELECT * FROM Shipment_Companies ORDER BY company_name ASC');
    return rows;
};

module.exports = {
    getUserAddresses,
    addAddress,
    setDefaultAddress,
    deleteAddress,
    getShipmentCompanies
};
