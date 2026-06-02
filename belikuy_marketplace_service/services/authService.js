const db = require('../config/db');

const registerUser = async (username, email, password, role) => {
    try {
        const [result] = await db.query(
            "INSERT INTO Users (username, email, password, role) VALUES (?, ?, ?, ?)",
            [username, email, password, role || 'customer']
        );
        const userId = result.insertId;
        if (role === 'seller') {
            await db.query(
                "INSERT INTO belikuy_seller_db.Companies (user_id, company_name, address) VALUES (?, ?, ?)",
                [userId, username + " Store", ""]
            );
        }
        return { userId };
    } catch (err) {
        if (err.code === 'ER_DUP_ENTRY') {
            throw new Error("Email already exists");
        }
        throw new Error("Registration failed: " + err.message);
    }
};

const loginUser = async (email, password) => {
    try {
        const [users] = await db.query("SELECT * FROM Users WHERE email = ?", [email]);
        if (users.length === 0) {
            throw new Error("Invalid credentials");
        }
        const user = users[0];
        
        if (password !== user.password) {
            throw new Error("Invalid credentials");
        }

        let company = null;
        if (user.role === 'seller') {
            const [companies] = await db.query("SELECT id AS company_id, company_name, is_active FROM belikuy_seller_db.Companies WHERE user_id = ?", [user.id]);
            if (companies.length > 0) {
                if (companies[0].is_active === 0) {
                    throw new Error("Akun toko Anda telah dinonaktifkan oleh Admin.");
                }
                company = companies[0];
            }
        }

        return {
            id: user.id,
            username: user.username,
            email: user.email,
            phone: user.phone || '',
            gender: user.gender || 'female',
            dob: user.dob || '',
            role: user.role,
            company: company
        };
    } catch (err) {
        throw new Error(err.message);
    }
};

const updateProfile = async (id, name, email, phone, gender, dob) => {
    // Attempt to alter table if columns don't exist (ignore if they do)
    try { await db.query("ALTER TABLE Users ADD COLUMN phone VARCHAR(20), ADD COLUMN gender VARCHAR(10), ADD COLUMN dob DATE"); } catch(e) {}
    
    try {
        await db.query(
            "UPDATE Users SET username=?, email=?, phone=?, gender=?, dob=? WHERE id=?",
            [name, email, phone, gender, dob, id]
        );
        const [users] = await db.query("SELECT * FROM Users WHERE id = ?", [id]);
        return users[0];
    } catch (err) {
        throw new Error("Update failed: " + err.message);
    }
};

module.exports = {
    registerUser,
    loginUser,
    updateProfile
};
