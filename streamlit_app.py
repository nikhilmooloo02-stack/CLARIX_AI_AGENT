# streamlit_app.py
# CLARIX AI Assistant for ShaNeal Distributors - Optimized for Streamlit Cloud

# ========== ENVIRONMENT SETUP ==========
try:
    __import__("pysqlite3")
    import sys
    sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")
except Exception:
    pass

# ========== IMPORTS ==========
import streamlit as st
import anthropic
import chromadb
import re
import datetime
import random
import logging
from urllib.parse import quote
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm

# ========== LOGGING SETUP ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ========== CONFIGURATION ==========
CONFIG = {
    "APP_TITLE": "CLARIX — ShaNeal Distributors",
    "WHATSAPP_NUMBER": "27723304651",
    "API_MODEL": "claude-sonnet-4-5",
    "MAX_TOKENS": 1000,
    "VAT_RATE": 0.15,
    "QUOTE_VALIDITY_DAYS": 30,
    "COMPANY_NAME": "ShaNeal Distributors",
    "COMPANY_PHONE": "070 070 0770",
    "COMPANY_EMAIL": "ShaNeal@lantic.co.za",
    "COMPANY_ADDRESS": "332 Paul Kruger Street, Corner Van Heerden Street, Capital Park, Pretoria 0084",
    "COMPANY_WEBSITE": "www.ShaNealonline.co.za",
    "BUSINESS_HOURS": "Monday to Friday, 8am to 6pm",
    "PRIMARY_COLOR": "#2D6A2D",
    "ACCENT_COLOR": "#D4A017",
}

# ========== PRODUCT CATALOG ==========
PRODUCTS_CATALOG = {
    "Paper": {
        "butterfly a4 paper": {"name": "Butterfly A4 Paper 80gsm 500 sheets", "price": 89.00},
        "rotatrim a4 paper": {"name": "Rotatrim A4 Paper 75gsm 500 sheets", "price": 75.00},
        "a3 paper": {"name": "A3 Paper 80gsm 500 sheets", "price": 165.00},
        "letterhead paper": {"name": "Letterhead Paper A4 100 sheets", "price": 45.00},
    },
    "Pens and Writing": {
        "bic ballpoint pens": {"name": "Bic Ballpoint Pens Blue Box of 50", "price": 120.00},
        "pilot g2 gel pens": {"name": "Pilot G2 Gel Pens Black Pack of 12", "price": 95.00},
        "staedtler permanent markers": {"name": "Staedtler Permanent Markers Pack of 10", "price": 85.00},
        "highlighters": {"name": "Highlighters Assorted Pack of 5", "price": 55.00},
    },
    "PPE": {
        "surgical face masks": {"name": "Surgical Face Masks Box of 50", "price": 95.00},
        "nitrile gloves": {"name": "Nitrile Gloves Box of 100", "price": 180.00},
        "safety goggles": {"name": "Safety Goggles", "price": 45.00},
        "reflective safety vest": {"name": "Reflective Safety Vest", "price": 120.00},
    },
    "Office Equipment": {
        "bantex a4 lever arch file": {"name": "Bantex A4 Lever Arch File", "price": 45.00},
        "stapler heavy duty": {"name": "Stapler Heavy Duty", "price": 135.00},
        "calculator scientific": {"name": "Calculator Scientific", "price": 250.00},
        "whiteboard a1": {"name": "Whiteboard A1", "price": 850.00},
        "shredder 10 sheet": {"name": "Shredder 10 Sheet", "price": 1200.00},
    },
    "Household Consumables": {
        "refuse bags": {"name": "Refuse Bags Black Roll of 20", "price": 35.00},
        "hand sanitiser": {"name": "Hand Sanitiser 500ml", "price": 65.00},
        "multipurpose cleaning spray": {"name": "Multipurpose Cleaning Spray 750ml", "price": 45.00},
        "toilet paper": {"name": "Toilet Paper 9 Roll Pack", "price": 55.00},
    },
}

# Create flat price list for quick lookup
PRICE_LIST = {}
for category, products in PRODUCTS_CATALOG.items():
    for key, product_info in products.items():
        PRICE_LIST[key] = product_info["price"]

# ========== PRODUCT KNOWLEDGE BASE ==========
@st.cache_resource
def load_knowledge_base():
    """Load and initialize ChromaDB knowledge base with products."""
    try:
        chroma_client = chromadb.Client()
        
        # Delete existing collection if it exists
        try:
            chroma_client.delete_collection("shaneal_products")
        except Exception:
            pass
        
        knowledge_base = chroma_client.create_collection(
            name="shaneal_products"
        )
        
        # Create product documentation
        products_text = _generate_product_documentation()
        
        knowledge_base.add(
            documents=[products_text],
            ids=["shaneal_product_list"]
        )
        
        logger.info("Knowledge base loaded successfully")
        return knowledge_base
    
    except Exception as e:
        logger.error(f"Error loading knowledge base: {str(e)}")
        st.error("❌ Failed to load product knowledge base. Please refresh the page.")
        st.stop()


def _generate_product_documentation():
    """Generate product documentation from catalog."""
    doc = ""
    for category, products in PRODUCTS_CATALOG.items():
        doc += f"\n{category.upper()}:\n"
        for key, product_info in products.items():
            doc += f"- {product_info['name']} - R{product_info['price']:.2f}\n"
    return doc


knowledge_base = load_knowledge_base()

# ========== SYSTEM PROMPT ==========
SYSTEM_PROMPT = f"""You are CLARIX, the professional AI assistant for
{CONFIG['COMPANY_NAME']} — a stationery, PPE, office equipment and household
consumables distributor based in Pretoria, South Africa.

You serve retail customers and bulk business and school clients.

PRODUCTS AND PRICING:
PAPER: Butterfly A4 Paper 80gsm 500 sheets R89.00 | Rotatrim A4 Paper
75gsm 500 sheets R75.00 | A3 Paper 80gsm 500 sheets R165.00 |
Letterhead Paper A4 100 sheets R45.00
PENS: Bic Ballpoint Pens Blue Box of 50 R120.00 | Pilot G2 Gel Pens
Black Pack of 12 R95.00 | Staedtler Permanent Markers Pack of 10 R85.00
| Highlighters Assorted Pack of 5 R55.00
PPE: Surgical Face Masks Box of 50 R95.00 | Nitrile Gloves Box of 100
R180.00 | Safety Goggles R45.00 | Reflective Safety Vest R120.00
OFFICE EQUIPMENT: Bantex A4 Lever Arch File R45.00 | Stapler Heavy Duty
R135.00 | Calculator Scientific R250.00 | Whiteboard A1 R850.00 |
Shredder 10 Sheet R1200.00
HOUSEHOLD CONSUMABLES: Refuse Bags Black Roll of 20 R35.00 | Hand
Sanitiser 500ml R65.00 | Multipurpose Cleaning Spray 750ml R45.00 |
Toilet Paper 9 Roll Pack R55.00

CONTACT INFORMATION:
- Phone: {CONFIG['COMPANY_PHONE']}
- Email: {CONFIG['COMPANY_EMAIL']}
- Address: {CONFIG['COMPANY_ADDRESS']}
- Website: {CONFIG['COMPANY_WEBSITE']}
- Business Hours: {CONFIG['BUSINESS_HOURS']}

BEHAVIOUR:
- Recommend specific products with prices
- Cross-sell related products naturally
- For bulk orders ask for organisation name and delivery address
- For complaints apologise sincerely and offer a clear solution
- For orders over R10,000 escalate to a human consultant
- When customers ask for contact details share all of the above
- Always be warm, professional and solution-focused

FINANCIAL ANALYSIS:
When customers ask about VAT or cost calculations:
- Calculate VAT at {CONFIG['VAT_RATE']*100:.0f}% showing subtotal, VAT amount and total
- For bulk orders calculate the full total cost
- Always show amounts in South African Rand (R)
- Give clear itemised breakdowns

QUOTE GENERATION:
When a customer asks for a quote or invoice:
1. Ask for their name and company name if not provided
2. Confirm the products and quantities
3. Respond with EXACTLY this format:

GENERATE_QUOTE
NAME: [customer name]
COMPANY: [company name]
ITEMS:
[product name], [quantity]
[product name], [quantity]
END_QUOTE

HUMAN ESCALATION:
Include ESCALATE_TO_HUMAN when:
- Customer requests a human agent
- Order likely exceeds R10,000
- Customer is very angry or mentions legal action
- Issue is too complex to resolve
"""

# ========== PAGE CONFIGURATION ==========
st.set_page_config(
    page_title=CONFIG["APP_TITLE"],
    page_icon="🟢",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Hide streamlit menu and footer
hide_menu_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """
st.markdown(hide_menu_style, unsafe_allow_html=True)

# ========== API CONNECTION ==========
@st.cache_resource
def initialize_anthropic_client():
    """Initialize Anthropic client with error handling."""
    try:
        api_key = st.secrets.get("ANTHROPIC_API_KEY")
        if not api_key:
            st.error("❌ Missing ANTHROPIC_API_KEY in secrets. Configure in Streamlit Cloud settings.")
            st.stop()
        
        client = anthropic.Anthropic(api_key=api_key)
        logger.info("Anthropic client initialized successfully")
        return client
    
    except Exception as e:
        logger.error(f"Error initializing Anthropic client: {str(e)}")
        st.error(f"❌ Failed to initialize API connection: {str(e)}")
        st.stop()


client = initialize_anthropic_client()

# ========== UTILITY FUNCTIONS ==========
def parse_quote_response(reply: str) -> dict | None:
    """
    Extract quote details from Claude's response.
    
    Args:
        reply: Claude's response text
        
    Returns:
        Dictionary with quote details or None if parsing fails
    """
    try:
        name_match = re.search(r"NAME:\s*(.+)", reply)
        company_match = re.search(r"COMPANY:\s*(.+)", reply)
        items_match = re.search(r"ITEMS:\n(.*?)END_QUOTE", reply, re.DOTALL)
        
        if all([name_match, company_match, items_match]):
            return {
                "name": name_match.group(1).strip(),
                "company": company_match.group(1).strip(),
                "items": items_match.group(1).strip()
            }
    except Exception as e:
        logger.error(f"Error parsing quote response: {str(e)}")
    
    return None


def parse_items(items_text: str) -> list:
    """
    Parse item text into list of [product, qty, price, total].
    
    Args:
        items_text: Items string in format "product, qty\nproduct, qty"
        
    Returns:
        List of parsed items
    """
    line_items = []
    
    for line in items_text.strip().split("\n"):
        if not line.strip() or "," not in line:
            continue
        
        try:
            parts = line.split(",")
            product = parts[0].strip()
            
            try:
                qty = int(parts[1].strip())
            except (ValueError, IndexError):
                qty = 1
            
            # Find matching price
            price = None
            for key, item_price in PRICE_LIST.items():
                if key in product.lower():
                    price = item_price
                    break
            
            if price is None:
                logger.warning(f"Product not found: {product}")
                price = 0.00
            
            line_items.append([product, qty, price, price * qty])
        
        except Exception as e:
            logger.warning(f"Error parsing line '{line}': {str(e)}")
            continue
    
    return line_items


def get_pdf_styles():
    """Create and return PDF paragraph styles."""
    styles = getSampleStyleSheet()
    
    header_style = ParagraphStyle(
        "Header",
        parent=styles["Normal"],
        fontSize=24,
        textColor=colors.HexColor(CONFIG["PRIMARY_COLOR"]),
        spaceAfter=2 * mm,
        fontName="Helvetica-Bold"
    )
    
    sub_style = ParagraphStyle(
        "Sub",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor(CONFIG["ACCENT_COLOR"]),
        spaceAfter=1 * mm
    )
    
    normal_style = ParagraphStyle(
        "Normal2",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#2C2C2C"),
        spaceAfter=1 * mm
    )
    
    footer_style = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.HexColor("#888888")
    )
    
    return {
        "header": header_style,
        "sub": sub_style,
        "normal": normal_style,
        "footer": footer_style,
        "base": styles
    }


def generate_quote(customer_name: str, company_name: str, items_text: str) -> tuple:
    """
    Generate a professional PDF quote in memory.
    
    Args:
        customer_name: Customer's name
        company_name: Company name
        items_text: Items in format "product, qty\nproduct, qty"
        
    Returns:
        Tuple of (pdf_bytes, quote_number) or (None, None) on failure
    """
    try:
        line_items = parse_items(items_text)
        
        if not line_items:
            logger.warning("No valid items found for quote")
            return None, None
        
        # Calculate totals
        subtotal = sum(item[3] for item in line_items)
        vat = subtotal * CONFIG["VAT_RATE"]
        total = subtotal + vat
        
        # Generate quote number and dates
        quote_num = f"SND-{random.randint(1000, 9999)}-{datetime.datetime.now().year}"
        today = datetime.datetime.now().strftime("%d %B %Y")
        valid_until = (datetime.datetime.now() + datetime.timedelta(days=CONFIG["QUOTE_VALIDITY_DAYS"])).strftime("%d %B %Y")
        
        # Create PDF in memory (better for cloud environments)
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=A4,
            rightMargin=20 * mm,
            leftMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=20 * mm
        )
        
        styles = get_pdf_styles()
        elements = []
        
        # Header
        elements.append(Paragraph(CONFIG["COMPANY_NAME"], styles["header"]))
        elements.append(Paragraph(
            "Stationery · PPE · Office Equipment · Household Consumables",
            styles["sub"]
        ))
        elements.append(Spacer(1, 3 * mm))
        
        # Divider
        divider = Table([[""]]], colWidths=[170 * mm])
        divider.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(CONFIG["ACCENT_COLOR"])),
            ("ROWHEIGHTS", (0, 0), (-1, -1), 2),
        ]))
        elements.append(divider)
        elements.append(Spacer(1, 5 * mm))
        
        # Quote info
        info_data = [
            [Paragraph("<b>QUOTATION</b>", styles["base"]["Normal"]),
             Paragraph("<b>Bill To:</b>", styles["base"]["Normal"])],
            [Paragraph(f"Quote No: {quote_num}", styles["normal"]),
             Paragraph(customer_name, styles["normal"])],
            [Paragraph(f"Date: {today}", styles["normal"]),
             Paragraph(company_name, styles["normal"])],
            [Paragraph(f"Valid Until: {valid_until}", styles["normal"]),
             Paragraph("", styles["normal"])]
        ]
        
        info_table = Table(info_data, colWidths=[85 * mm, 85 * mm])
        info_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP")
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 8 * mm))
        
        # Items table
        table_data = [["DESCRIPTION", "QTY", "UNIT PRICE", "TOTAL"]]
        
        for item in line_items:
            table_data.append([
                item[0],
                str(item[1]),
                f"R {item[2]:,.2f}",
                f"R {item[3]:,.2f}"
            ])
        
        table_data.append(["", "", "Subtotal:", f"R {subtotal:,.2f}"])
        table_data.append(["", "", f"VAT ({CONFIG['VAT_RATE']*100:.0f}%):", f"R {vat:,.2f}"])
        table_data.append(["", "", "TOTAL DUE:", f"R {total:,.2f}"])
        
        items_table = Table(
            table_data,
            colWidths=[90 * mm, 20 * mm, 30 * mm, 30 * mm]
        )
        
        items_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(CONFIG["PRIMARY_COLOR"])),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -4), [colors.HexColor("#FAFAF8"), colors.white]),
            ("FONTNAME", (2, -1), (-1, -1), "Helvetica-Bold"),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor(CONFIG["PRIMARY_COLOR"])),
            ("TEXTCOLOR", (0, -1), (-1, -1), colors.white),
            ("GRID", (0, 0), (-1, -4), 0.25, colors.HexColor("#E8E0D0")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(items_table)
        elements.append(Spacer(1, 10 * mm))
        
        # Footer
        footer_data = [[Paragraph(
            f"{CONFIG['COMPANY_NAME']} | {CONFIG['COMPANY_ADDRESS']}<br/>"
            f"Tel: {CONFIG['COMPANY_PHONE']} | Email: {CONFIG['COMPANY_EMAIL']} | {CONFIG['COMPANY_WEBSITE']}",
            styles["footer"]
        )]]
        
        footer_table = Table(footer_data, colWidths=[170 * mm])
        footer_table.setStyle(TableStyle([
            ("LINEABOVE", (0, 0), (-1, 0), 0.5, colors.HexColor(CONFIG["ACCENT_COLOR"])),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
        ]))
        
        elements.append(footer_table)
        
        # Build PDF
        doc.build(elements)
        pdf_buffer.seek(0)
        
        logger.info(f"Quote generated successfully: {quote_num}")
        return pdf_buffer.getvalue(), quote_num
    
    except Exception as e:
        logger.error(f"Error generating quote: {str(e)}")
        return None, None


def get_whatsapp_link(summary: str) -> str:
    """
    Create WhatsApp link with message.
    
    Args:
        summary: Message summary
        
    Returns:
        WhatsApp URL
    """
    message = f"Hello {CONFIG['COMPANY_NAME']}, I need assistance. {summary}"
    return f"https://wa.me/{CONFIG['WHATSAPP_NUMBER']}?text={quote(message)}"


@st.cache_data(ttl=3600)
def get_product_context(message: str) -> str:
    """
    Get product context from knowledge base (cached).
    
    Args:
        message: User message
        
    Returns:
        Product context string
    """
    try:
        results = knowledge_base.query(
            query_texts=[message],
            n_results=1
        )
        
        if results and results.get("documents") and results["documents"][0]:
            return results["documents"][0][0]
    except Exception as e:
        logger.warning(f"Error retrieving product context: {str(e)}")
    
    return ""


def chat_with_clarix(message: str) -> str:
    """
    Send message to Claude and get response.
    
    Args:
        message: User message
        
    Returns:
        Claude's response
    """
    try:
        product_context = get_product_context(message)
        
        enhanced_message = f"""Customer query: {message}
ShaNeal product information: {product_context}"""
        
        # Build conversation history
        conversation = []
        for item in st.session_state.messages:
            if item.get("role") in ["user", "assistant"]:
                conversation.append({
                    "role": item["role"],
                    "content": item["content"]
                })
        
        conversation.append({
            "role": "user",
            "content": enhanced_message
        })
        
        # Get response from Claude
        response = client.messages.create(
            model=CONFIG["API_MODEL"],
            max_tokens=CONFIG["MAX_TOKENS"],
            system=SYSTEM_PROMPT,
            messages=conversation
        )
        
        reply = response.content[0].text
        logger.info("Response generated successfully")
        
        # Handle quote generation
        if "GENERATE_QUOTE" in reply:
            quote_data = parse_quote_response(reply)
            
            if quote_data:
                pdf_bytes, quote_num = generate_quote(
                    quote_data["name"],
                    quote_data["company"],
                    quote_data["items"]
                )
                
                if pdf_bytes and quote_num:
                    st.session_state.latest_quote = {
                        "pdf": pdf_bytes,
                        "filename": f"CLARIX_Quote_{quote_num}.pdf",
                        "quote_num": quote_num
                    }
                    
                    reply = f"""✅ Quote {quote_num} generated!

**Customer:** {quote_data['name']} — {quote_data['company']}

📄 Your quote is ready. Use the **Download Latest Quote** button below to save your PDF.

Valid for {CONFIG['QUOTE_VALIDITY_DAYS']} days. Is there anything else I can help you with?"""
        
        # Handle human escalation
        if "ESCALATE_TO_HUMAN" in reply:
            summary = f"Customer issue: {message}"
            whatsapp_link = get_whatsapp_link(summary)
            clean_reply = reply.replace("ESCALATE_TO_HUMAN", "").strip()
            
            reply = f"""{clean_reply}

---
🔴 **This issue requires a human agent.**

👉 WhatsApp us: {whatsapp_link}

{CONFIG['BUSINESS_HOURS']}
📞 {CONFIG['COMPANY_PHONE']}"""
        
        return reply
    
    except anthropic.APIError as e:
        logger.error(f"Anthropic API error: {str(e)}")
        return f"❌ API Error: {str(e)}"
    
    except Exception as e:
        logger.error(f"Unexpected error in chat_with_clarix: {str(e)}")
        return f"❌ Error: {str(e)}"

# ========== SESSION STATE ==========
if "messages" not in st.session_state:
    st.session_state.messages = []

if "latest_quote" not in st.session_state:
    st.session_state.latest_quote = None

# ========== UI LAYOUT ==========
# Header
st.title(CONFIG["APP_TITLE"])
st.caption("Ask about products, request a quote, or get support.")

# Quick Actions
st.subheader("Quick Actions")

quick_actions = [
    "Can I get a quote for 10 reams of A4 paper?",
    "Calculate VAT on an invoice of R5,500.",
    "What is the total cost of PPE for 50 staff?",
    "I need PPE for 20 staff members.",
    "What stationery products do you stock?",
    "Help me set up a new office for 10 staff.",
    "My order arrived damaged, I need a refund urgently.",
    "I need to speak to a human agent.",
    "What are your business hours?",
    "How can I contact ShaNeal Distributors?",
]

selected_action = st.selectbox(
    "Choose an example question",
    [""] + quick_actions,
    label_visibility="collapsed"
)

if selected_action:
    st.session_state.pending_question = selected_action

# Chat display
st.subheader("Chat")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
user_input = st.chat_input("Type your message here...", key="chat_input")

if "pending_question" in st.session_state:
    user_input = st.session_state.pending_question
    del st.session_state.pending_question

if user_input:
    # Add user message to chat
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })
    
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # Get and display assistant response
    with st.chat_message("assistant"):
        with st.spinner("CLARIX is thinking..."):
            assistant_reply = chat_with_clarix(user_input)
            st.markdown(assistant_reply)
    
    st.session_state.messages.append({
        "role": "assistant",
        "content": assistant_reply
    })
    
    st.rerun()

# Download quote button
if st.session_state.latest_quote:
    st.divider()
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.download_button(
            label="📄 Download Latest Quote",
            data=st.session_state.latest_quote["pdf"],
            file_name=st.session_state.latest_quote["filename"],
            mime="application/pdf",
            key="download_quote"
        )
    
    with col2:
        if st.button("Clear Quote", key="clear_quote"):
            st.session_state.latest_quote = None
            st.rerun()

# Footer
st.divider()

footer_html = f"""
<div style="text-align:center; font-size:11px; color:#888;">
    POWERED BY CLARIX AI · {CONFIG['COMPANY_NAME']} · PRETORIA<br>
    <a href="https://{CONFIG['COMPANY_WEBSITE']}" style="color:{CONFIG['PRIMARY_COLOR']}; text-decoration:none;">
    {CONFIG['COMPANY_WEBSITE'].upper()}
    </a>
    <br><br>
    <span style="font-size:10px; color:#aaa;">
    CLARIX is a product of <strong style="color:{CONFIG['PRIMARY_COLOR']}">Nikhil Dante Mooloo</strong>
    · AI Business Operations Specialist · Pretoria
    </span>
</div>
"""

st.markdown(footer_html, unsafe_allow_html=True)
