const express = require('express');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

// Serve frontend
app.use(express.static(path.join(__dirname, 'public')));
// Serve sinais_libras (imagens) as static
app.use('/sinais_libras', express.static(path.join(__dirname, 'sinais_libras')));

app.get('/health', (req, res) => res.send('ok'));

app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
