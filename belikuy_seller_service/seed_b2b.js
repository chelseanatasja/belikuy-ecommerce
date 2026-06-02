const mysql = require('mysql2/promise');
const bcrypt = require('bcryptjs');

async function seed() {
    const connMarket = await mysql.createConnection({host: '127.0.0.1', user: 'root', database: 'belikuy_marketplace_db'});
    const connSeller = await mysql.createConnection({host: '127.0.0.1', user: 'root', database: 'belikuy_seller_db'});
    const connPayment = await mysql.createConnection({host: '127.0.0.1', user: 'root', database: 'belikuy_payment_db'});
    const connDelivery = await mysql.createConnection({host: '127.0.0.1', user: 'root', database: 'belikuy_delivery_db'});

    const pwdHash = await bcrypt.hash('password123', 10);

    async function createUser(username, email, role) {
        try {
            const [result] = await connMarket.execute(
                "INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)",
                [username, email, pwdHash, role]
            );
            return result.insertId;
        } catch (err) {
            if (err.code === 'ER_DUP_ENTRY') {
                const [rows] = await connMarket.execute("SELECT id FROM users WHERE email = ?", [email]);
                return rows[0].id;
            }
            throw err;
        }
    }

    // 1. Suppliers
    const [suppliers] = await connSeller.execute("SELECT id, supply_company_name FROM supply_companies WHERE user_id IS NULL");
    for (const s of suppliers) {
        const uname = s.supply_company_name.replace(/\s+/g, '').toLowerCase();
        const email = `${uname}@supplier.com`;
        const userId = await createUser(s.supply_company_name, email, 'supplier');
        await connSeller.execute("UPDATE supply_companies SET user_id = ? WHERE id = ?", [userId, s.id]);
        console.log(`Created Supplier User: ${email}`);
    }

    // 2. Fintechs
    const [payments] = await connPayment.execute("SELECT id, institution_name FROM payment_methods WHERE user_id IS NULL");
    for (const p of payments) {
        const uname = p.institution_name.replace(/\s+/g, '').toLowerCase();
        const email = `${uname}@fintech.com`;
        const userId = await createUser(p.institution_name, email, 'fintech');
        await connPayment.execute("UPDATE payment_methods SET user_id = ? WHERE id = ?", [userId, p.id]);
        console.log(`Created Fintech User: ${email}`);
    }

    // 3. Delivery
    const [deliveries] = await connDelivery.execute("SELECT id, company_name FROM shipment_companies WHERE user_id IS NULL");
    for (const d of deliveries) {
        const uname = d.company_name.replace(/\s+/g, '').toLowerCase();
        const email = `${uname}@delivery.com`;
        const userId = await createUser(d.company_name, email, 'delivery');
        await connDelivery.execute("UPDATE shipment_companies SET user_id = ? WHERE id = ?", [userId, d.id]);
        console.log(`Created Delivery User: ${email}`);
    }

    console.log("Seeding complete!");
    process.exit(0);
}
seed().catch(console.error);
