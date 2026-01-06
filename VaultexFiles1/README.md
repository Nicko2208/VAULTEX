# Inventory Portal

A sleek, Apple-inspired inventory management system for connecting sellers, listers, and buyers.

## Features

- **Selling**: Upload items to the inventory portal
- **Inventory**: Browse all items and create listings
- **Buying**: Browse and find items to purchase with pricing and commission information

## Setup

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the Flask application:
   ```bash
   python app.py
   ```

3. Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

## Project Structure

```
VaultexFiles/
├── app.py                 # Flask application
├── templates/             # HTML templates
│   ├── index.html
│   ├── selling.html
│   ├── inventory.html
│   ├── list_item.html
│   └── buying.html
├── static/                # Static files
│   ├── style.css         # Styling
│   └── main.js           # JavaScript
├── data.json             # Data storage (auto-generated)
└── requirements.txt      # Python dependencies
```

## Usage

1. **Selling**: Go to the Selling page and upload items with descriptions
2. **Inventory**: View all uploaded items and click "List Item" to create a listing
3. **Listing**: Add a pitch, price, and commission percentage for an item
4. **Buying**: Browse all listed items with search functionality

Data is stored in `data.json` and persists between sessions.

