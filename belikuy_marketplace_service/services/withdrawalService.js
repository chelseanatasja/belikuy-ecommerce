const db = require('../config/db');

// Seller: get own withdrawals
const getWithdrawals = async (companyId) => {
    const [rows] = await db.query(
        `SELECT w.*, c.company_name 
         FROM Withdrawals w
         JOIN belikuy_seller_db.Companies c ON w.company_id = c.id
         WHERE w.company_id = ? ORDER BY w.created_at DESC`,
        [companyId]
    );
    return rows;
};

// Admin: get ALL withdrawals from all sellers
const getAllWithdrawals = async () => {
    const [rows] = await db.query(
        `SELECT w.*, c.company_name 
         FROM Withdrawals w
         JOIN belikuy_seller_db.Companies c ON w.company_id = c.id
         ORDER BY w.created_at DESC`
    );
    return rows;
};

const createWithdrawal = async (companyId, amount, bankName, accountNumber, accountHolder) => {
    const [result] = await db.query(
        `INSERT INTO Withdrawals (company_id, amount, bank_name, account_number, account_holder, status)
         VALUES (?, ?, ?, ?, ?, 'pending')`,
        [companyId, amount, bankName, accountNumber, accountHolder]
    );
    return { withdrawalId: result.insertId };
};

// Admin: update status
const updateWithdrawalStatus = async (withdrawalId, status) => {
    await db.query(
        `UPDATE Withdrawals SET status = ? WHERE id = ?`,
        [status, withdrawalId]
    );
    return true;
};

module.exports = { getWithdrawals, getAllWithdrawals, createWithdrawal, updateWithdrawalStatus };
