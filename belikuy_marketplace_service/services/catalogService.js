const db = require('../config/db');

const getProducts = async (filters) => {
    const { search, category_id, min_price, max_price } = filters;
    let query = `
        SELECT p.id, p.product_name, p.price, p.image_url, c.company_name, c.rating AS company_rating, cat.category_name,
               COALESCE((SELECT AVG(rating) FROM Reviews WHERE product_id = p.id), 0) AS product_rating,
               (SELECT COUNT(id) FROM Reviews WHERE product_id = p.id) AS review_count
        FROM Products p
        JOIN Companies c ON p.company_id = c.id
        JOIN Categories cat ON p.category_id = cat.id
        WHERE c.is_active = 1
    `;
    const queryParams = [];

    if (search) {
        query += ` AND p.product_name LIKE ?`;
        queryParams.push(`%${search}%`);
    }
    if (category_id) {
        query += ` AND p.category_id = ?`;
        queryParams.push(category_id);
    }
    if (min_price) {
        query += ` AND p.price >= ?`;
        queryParams.push(min_price);
    }
    if (max_price) {
        query += ` AND p.price <= ?`;
        queryParams.push(max_price);
    }

    query += ` ORDER BY p.price ASC`;

    const [products] = await db.query(query, queryParams);
    return products;
};

const getProductById = async (id) => {
    const [rows] = await db.query(`
        SELECT p.*, c.company_name, c.rating AS company_rating, cat.category_name,
               COALESCE((SELECT AVG(rating) FROM Reviews WHERE product_id = p.id), 0) AS product_rating,
               (SELECT COUNT(id) FROM Reviews WHERE product_id = p.id) AS review_count
        FROM Products p
        JOIN Companies c ON p.company_id = c.id
        JOIN Categories cat ON p.category_id = cat.id
        WHERE p.id = ?
    `, [id]);
    if (!rows.length) return null;
    return rows[0];
};

const getProductsByCompany = async (companyId) => {
    const [products] = await db.query(`
        SELECT p.id, p.product_name, p.price, p.stock, p.image_url, p.is_active,
               p.description, p.brand, cat.category_name, cat.id AS category_id,
               sc.supply_company_name, sc.id AS supply_company_id, sc.contact_number AS supply_contact,
               COALESCE((SELECT AVG(rating) FROM Reviews WHERE product_id = p.id), 0) AS product_rating,
               (SELECT COUNT(id) FROM Reviews WHERE product_id = p.id) AS review_count
        FROM Products p
        LEFT JOIN Categories cat ON p.category_id = cat.id
        LEFT JOIN Supply_Companies sc ON p.supply_company_id = sc.id
        WHERE p.company_id = ?
        ORDER BY p.created_at DESC
    `, [companyId]);
    return products;
};


const toggleProductActive = async (id, companyId, isActive) => {
    const [result] = await db.query(
        "UPDATE Products SET is_active = ? WHERE id = ? AND company_id = ?",
        [isActive ? 1 : 0, id, companyId]
    );
    return result.affectedRows > 0;
};

const createProduct = async (productData) => {
    const { company_id, category_id, supply_company_id, brand, product_name, size, color, description, price, stock, image_url } = productData;
    const [result] = await db.query(
        `INSERT INTO Products (company_id, category_id, supply_company_id, brand, product_name, size, color, description, price, stock, image_url) 
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
        [company_id, category_id, supply_company_id, brand, product_name, size, color, description, price, stock, image_url]
    );
    return { productId: result.insertId };
};

const updateProduct = async (id, companyId, updateData) => {
    const { product_name, price, stock, category_id, supply_company_id } = updateData;
    const fields = [];
    const vals = [];
    if (product_name !== undefined)    { fields.push('product_name = ?');    vals.push(product_name); }
    if (price !== undefined)           { fields.push('price = ?');            vals.push(price); }
    if (stock !== undefined)           { fields.push('stock = ?');            vals.push(stock); }
    if (category_id !== undefined)     { fields.push('category_id = ?');     vals.push(category_id); }
    if (supply_company_id !== undefined) { fields.push('supply_company_id = ?'); vals.push(supply_company_id || null); }
    if (!fields.length) return false;
    vals.push(id, companyId);
    const [result] = await db.query(
        `UPDATE Products SET ${fields.join(', ')} WHERE id = ? AND company_id = ?`, vals
    );
    return result.affectedRows > 0;
};


const deleteProduct = async (id) => {
    const [result] = await db.query("DELETE FROM Products WHERE id = ?", [id]);
    return result.affectedRows > 0;
};

const getCategories = async () => {
    const [categories] = await db.query("SELECT * FROM Categories ORDER BY category_name ASC");
    return categories;
};

const getProductReviews = async (productId) => {
    const [reviews] = await db.query(`
        SELECT r.id, r.rating, r.comment, r.created_at, u.username
        FROM Reviews r
        LEFT JOIN Users u ON r.user_id = u.id
        WHERE r.product_id = ?
        ORDER BY r.created_at DESC
    `, [productId]);
    return reviews;
};

module.exports = {
    getProducts,
    getProductById,
    getProductsByCompany,
    createProduct,
    updateProduct,
    toggleProductActive,
    deleteProduct,
    getCategories,
    getProductReviews
};
