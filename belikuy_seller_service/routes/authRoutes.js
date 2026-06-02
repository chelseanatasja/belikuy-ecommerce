const express = require('express');
const router = express.Router();
const authService = require('../services/authService');

// Register
router.post('/register', async (req, res) => {
    const { username, email, password, role } = req.body;
    try {
        const result = await authService.registerUser(username, email, password, role);
        res.status(201).json({ message: "User registered successfully", userId: result.userId });
    } catch (err) {
        if (err.message.includes('Email already exists')) {
            res.status(400).json({ error: err.message });
        } else {
            res.status(500).json({ error: err.message });
        }
    }
});

// Login
router.post('/login', async (req, res) => {
    const { email, password } = req.body;
    try {
        const user = await authService.loginUser(email, password);
        res.json({
            message: "Login successful",
            user: user
        });
    } catch (err) {
        if (err.message === 'Invalid credentials') {
            res.status(401).json({ error: err.message });
        } else {
            res.status(500).json({ error: err.message });
        }
    }
});

// Update Profile
router.put('/profile/:id', async (req, res) => {
    const { id } = req.params;
    const { name, email, phone, gender, dob } = req.body;
    try {
        const updated = await authService.updateProfile(id, name, email, phone, gender, dob);
        res.json({ message: "Profile updated", user: updated });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

module.exports = router;
