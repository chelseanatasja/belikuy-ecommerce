@echo off
echo Starting BeliKuy Microservices Ecosystem...

start "API Gateway (Port 3000)" cmd /c "cd belikuy_api_gateway && npm start"
start "Marketplace Service (Port 3001)" cmd /c "cd belikuy_marketplace_service && npm start"
start "Seller Service (Port 3002)" cmd /c "cd belikuy_seller_service && npm start"
start "Payment Service (Port 3003)" cmd /c "cd belikuy_payment_service && npm start"
start "Delivery Service (Port 3004)" cmd /c "cd belikuy_delivery_service && npm start"

echo All services are starting in separate windows!
pause
