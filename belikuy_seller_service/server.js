const express = require('express');
const cors = require('cors');
require('dotenv').config();

const app = express();
app.use(cors());
app.use(express.json());

// Routes


app.use('/api/auth', require('./routes/authRoutes'));
app.use('/api/users', require('./routes/addressRoutes')); // Assuming user address is here or just mount it
app.use('/api/addresses', require('./routes/addressRoutes'));
app.use('/api/orders', require('./routes/orderRoutes'));
app.use('/api/products', require('./routes/productRoutes'));
app.use('/api/companies', require('./routes/companyRoutes'));
app.use('/api/categories', require('./routes/categoryRoutes'));
app.use('/api/payments', require('./routes/paymentRoutes'));
app.use('/api/admin', require('./routes/adminRoutes'));
app.use('/api/withdrawals', require('./routes/withdrawalRoutes'));
app.use('/api/suppliers', require('./routes/supplierRoutes'));

const PORT = process.env.PORT || 3002;
app.listen(PORT, () => console.log(`Seller Service running on port ${PORT}`));
