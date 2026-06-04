const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const cors = require('cors');
require('dotenv').config();

const app = express();
app.use(cors());

const MARKETPLACE = 'http://localhost:3001';
const SELLER = 'http://localhost:3002';
const PAYMENT = 'http://localhost:3003';
const DELIVERY = 'http://localhost:3004';

app.use('/uploads', express.static('../belikuy_backend/uploads'));

app.get('/', (req, res) => res.send('API Gateway is running on port 3000'));

// Global middleware, no express path stripping
app.use(createProxyMiddleware({
    target: MARKETPLACE, // default
    changeOrigin: true,
    router: {
        '/api/products': SELLER,
        '/api/companies': SELLER,
        '/api/categories': SELLER,
        '/api/payments': PAYMENT,
        '/api/shipments': DELIVERY,
        '/api/suppliers': SELLER
    }
}));

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`API Gateway started on port ${PORT}`));
