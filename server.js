const express = require('express');
const cors = require('cors');
const fs = require('fs');

const app = express();
const PORT = 3000;

app.use(cors());
app.use(express.json());

let gestures = [];

app.post('/api/gesture', (req, res) => {
    const gesture = {
        word: req.body.word,
        timestamp: req.body.timestamp,
    };

    gestures.unshift(gesture); // Add to top
    if (gestures.length > 10) gestures.pop(); // Keep only 10

    res.send({ status: "success", received: gesture });
});

app.get('/api/gesture', (req, res) => {
    res.send(gestures);
});

app.listen(PORT, () => {
    console.log(`Gesture API listening on http://localhost:${PORT}`);
});
