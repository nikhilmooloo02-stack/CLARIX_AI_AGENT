# CLARIX AI Assistant for ShaNeal Distributors

![Streamlit Cloud](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)

CLARIX is a professional AI-powered customer service assistant for **ShaNeal Distributors**, a stationery, PPE, office equipment and household consumables distributor based in Pretoria, South Africa.

## Features

**Intelligent Product Recommendations** - AI-powered product suggestions based on customer needs  
**Professional Quote Generation** - Automatic PDF quote creation with VAT calculations  
**Chat-Based Interface** - Natural language conversations with Claude 3.5 Sonnet  
**Knowledge Base Integration** - ChromaDB semantic search for product information  
**Financial Calculations** - Automatic VAT (15%) and cost breakdown calculations  
**Human Escalation** - Automatic routing for complex issues via WhatsApp  
**Cloud-Ready** - Optimized for Streamlit Cloud deployment  

## Product Catalog

### Paper
- Butterfly A4 Paper 80gsm 500 sheets - R89.00
- Rotatrim A4 Paper 75gsm 500 sheets - R75.00
- A3 Paper 80gsm 500 sheets - R165.00
- Letterhead Paper A4 100 sheets - R45.00

### Pens & Writing
- Bic Ballpoint Pens Blue Box of 50 - R120.00
- Pilot G2 Gel Pens Black Pack of 12 - R95.00
- Staedtler Permanent Markers Pack of 10 - R85.00
- Highlighters Assorted Pack of 5 - R55.00

### PPE
- Surgical Face Masks Box of 50 - R95.00
- Nitrile Gloves Box of 100 - R180.00
- Safety Goggles - R45.00
- Reflective Safety Vest - R120.00

### Office Equipment
- Bantex A4 Lever Arch File - R45.00
- Stapler Heavy Duty - R135.00
- Calculator Scientific - R250.00
- Whiteboard A1 - R850.00
- Shredder 10 Sheet - R1200.00

### Household Consumables
- Refuse Bags Black Roll of 20 - R35.00
- Hand Sanitiser 500ml - R65.00
- Multipurpose Cleaning Spray 750ml - R45.00
- Toilet Paper 9 Roll Pack - R55.00

## Getting Started

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/nikhilmooloo02-stack/CLARIX_AI_AGENT.git
   cd CLARIX_AI_AGENT
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   export ANTHROPIC_API_KEY="your-api-key-here"
   ```

5. **Run the app**
   ```bash
   streamlit run streamlit_app.py
   ```

### Streamlit Cloud Deployment

1. **Push code to GitHub**
   ```bash
   git add .
   git commit -m "Deploy CLARIX AI Assistant"
   git push origin main
   ```

2. **Go to [Streamlit Cloud](https://share.streamlit.io/)**
   - Click "Create app"
   - Connect your GitHub repository
   - Select the branch and set main file to `streamlit_app.py`

3. **Add secrets**
   - In Streamlit Cloud dashboard, go to "Secrets"
   - Add `ANTHROPIC_API_KEY` with your API key
   ```
   ANTHROPIC_API_KEY = "sk-..."
   ```

4. **Deploy!**
   - Streamlit will automatically deploy your app
   - Your app will be live at `https://[username]-[app-name].streamlit.app`

## Configuration

All configuration is centralized in the `CONFIG` dictionary at the top of `streamlit_app.py`:

```python
CONFIG = {
    "APP_TITLE": "CLARIX — ShaNeal Distributors",
    "WHATSAPP_NUMBER": "27723304651",
    "API_MODEL": "claude-sonnet-4-5",
    "MAX_TOKENS": 1000,
    "VAT_RATE": 0.15,
    "QUOTE_VALIDITY_DAYS": 30,
    # ... more config
}
```

### Updating Prices

To update product prices and details, edit the `PRODUCTS_CATALOG` dictionary:

```python
PRODUCTS_CATALOG = {
    "Paper": {
        "butterfly a4 paper": {"name": "Butterfly A4 Paper 80gsm 500 sheets", "price": 89.00},
        # ... more products
    }
}
```

## Architecture

### Components

- **Streamlit UI** - Clean, responsive web interface
- **Claude 3.5 Sonnet** - Advanced AI for natural conversations and analysis
- **ChromaDB** - Vector database for semantic product search
- **ReportLab** - PDF generation for professional quotes
- **In-Memory PDF Generation** - Secure cloud-friendly quote creation

### Data Flow

```
User Input
    ↓
Product Context (ChromaDB)
    ↓
Enhanced Message → Claude API
    ↓
Response Processing
    ├─ Quote Generation → PDF (BytesIO)
    ├─ Human Escalation → WhatsApp Link
    └─ Chat Response
    ↓
Streamlit UI Display
```

## Key Improvements (v2)

**Centralized Configuration** - Single `CONFIG` dictionary for all settings  
**Single Source of Truth** - Products defined once, used everywhere  
**In-Memory PDF Generation** - Better for cloud environments (no disk I/O)  
**Enhanced Error Handling** - Specific exception catching with logging  
**Comprehensive Logging** - Track all operations for debugging  
**Type Hints** - Better code documentation and IDE support  
**Caching Strategy** - Optimized performance with smart caching  
**Modular Functions** - Easier to test and maintain  
**Security** - Proper secret handling for API keys  
**Production-Ready** - Streamlit Cloud optimizations  

## API Keys Required

- **Anthropic API Key** - Get from [console.anthropic.com](https://console.anthropic.com)
  - Requires payment method on file
  - Free trial credits available

## Support

**ShaNeal Distributors Contact:**
- Phone: 070 070 0770
- Email: ShaNeal@lantic.co.za
- Address: 332 Paul Kruger Street, Capital Park, Pretoria 0084
- Website: www.ShaNealonline.co.za
- Hours: Monday to Friday, 8am to 6pm

## License

This project is proprietary to ShaNeal Distributors.

## Author

**Nikhil Dante Mooloo**  
AI Business Operations Specialist  
Pretoria, South Africa

---

**Built with love using Streamlit, Claude AI, and ChromaDB**
