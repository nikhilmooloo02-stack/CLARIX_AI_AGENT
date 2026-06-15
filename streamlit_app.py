# streamlit_app.py

# ChromaDB SQLite fix for Streamlit Cloud
try:
    __import__("pysqlite3")
    import sys
    sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")
except Exception:
    pass

import streamlit as st
import anthropic
import chromadb
import re
import datetime
import random
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm


# -----------------------------
# PAGE SETUP
# -----------------------------

st.set_page_config(
    page_title="CLARIX — ShaNeal Distributors",
    page_icon="🟢",
    layout="centered"
)

st.title("CLARIX — ShaNeal Distributors AI Assistant")
st.caption("Ask about products, request a quote, or get support.")


# -----------------------------
# API CONNECTION
# -----------------------------

client = anthropic.Anthropic(
    api_key=st.secrets["ANTHROPIC_API_KEY"]
)


# -----------------------------
# PRODUCT KNOWLEDGE BASE
# -----------------------------

@st.cache_resource
def load_knowledge_base():
    chroma_client = chromadb.Client()

    try:
        chroma_client.delete_collection("shaneal_products")
    except Exception:
        pass

    knowledge_base = chroma_client.create_collection(
        name="shaneal_products"
    )

    products = """
PAPER:
- Butterfly A4 Paper 80gsm 500 sheets - R89.00
- Rotatrim A4 Paper 75gsm 500 sheets - R75.00
- A3 Paper 80gsm 500 sheets - R165.00
- Letterhead Paper A4 100 sheets - R45.00

PENS AND WRITING:
- Bic Ballpoint Pens Blue Box of 50 - R120.00
- Pilot G2 Gel Pens Black Pack of 12 - R95.00
- Staedtler Permanent Markers Pack of 10 - R85.00
- Highlighters Assorted Pack of 5 - R55.00

PPE:
- Surgical Face Masks Box of 50 - R95.00
- Nitrile Gloves Box of 100 - R180.00
- Safety Goggles - R45.00
- Reflective Safety Vest - R120.00

OFFICE EQUIPMENT:
- Bantex A4 Lever Arch File - R45.00
- Stapler Heavy Duty - R135.00
- Calculator Scientific - R250.00
- Whiteboard A1 - R850.00
- Shredder 10 Sheet - R1200.00

HOUSEHOLD CONSUMABLES:
- Refuse Bags Black Roll of 20 - R35.00
- Hand Sanitiser 500ml - R65.00
- Multipurpose Cleaning Spray 750ml - R45.00
- Toilet Paper 9 Roll Pack - R55.00
"""

    knowledge_base.add(
        documents=[products],
        ids=["shaneal_product_list"]
    )

    return knowledge_base


knowledge_base = load_knowledge_base()


# -----------------------------
# SYSTEM PROMPT
# -----------------------------

SYSTEM_PROMPT = """You are CLARIX, the professional AI assistant for
ShaNeal Distributors — a stationery, PPE, office equipment and household
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
- Phone: 070 070 0770
- Email: ShaNeal@lantic.co.za
- Address: 332 Paul Kruger Street, Corner Van Heerden Street,
Capital Park, Pretoria 0084
- Website: www.ShaNealonline.co.za
- Business Hours: Monday to Friday, 8am to 6pm

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
- Calculate VAT at 15% showing subtotal, VAT amount and total
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


# -----------------------------
# QUOTE GENERATION
# -----------------------------

WHATSAPP_NUMBER = "27723304651"

price_list = {
    "butterfly a4 paper": 89.00,
    "rotatrim a4 paper": 75.00,
    "a3 paper": 165.00,
    "letterhead paper": 45.00,
    "bic ballpoint pens": 120.00,
    "pilot g2 gel pens": 95.00,
    "staedtler permanent markers": 85.00,
    "highlighters": 55.00,
    "surgical face masks": 95.00,
    "nitrile gloves": 180.00,
    "safety goggles": 45.00,
    "reflective safety vest": 120.00,
    "bantex a4 lever arch file": 45.00,
    "stapler heavy duty": 135.00,
    "calculator scientific": 250.00,
    "whiteboard a1": 850.00,
    "shredder 10 sheet": 1200.00,
    "refuse bags": 35.00,
    "hand sanitiser": 65.00,
    "multipurpose cleaning spray": 45.00,
    "toilet paper": 55.00,
}


def generate_quote(customer_name, company_name, items_text):
    line_items = []

    for line in items_text.strip().split("\n"):
        if "," in line:
            parts = line.split(",")
            product = parts[0].strip()

            try:
                qty = int(parts[1].strip())
            except Exception:
                qty = 1

            price = None
            for key in price_list:
                if key in product.lower():
                    price = price_list[key]
                    break

            if price is None:
                price = 0.00

            line_items.append([product, qty, price, price * qty])

    if not line_items:
        return None, None

    subtotal = sum(item[3] for item in line_items)
    vat = subtotal * 0.15
    total = subtotal + vat

    quote_num = f"SND-{random.randint(1000, 9999)}-{datetime.datetime.now().year}"
    today = datetime.datetime.now().strftime("%d %B %Y")
    valid_until = (datetime.datetime.now() + datetime.timedelta(days=30)).strftime("%d %B %Y")

    filename = f"CLARIX_Quote_{quote_num}.pdf"

    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm
    )

    styles = getSampleStyleSheet()
    elements = []

    header_style = ParagraphStyle(
        "Header",
        parent=styles["Normal"],
        fontSize=24,
        textColor=colors.HexColor("#2D6A2D"),
        spaceAfter=2 * mm,
        fontName="Helvetica-Bold"
    )

    sub_style = ParagraphStyle(
        "Sub",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#D4A017"),
        spaceAfter=1 * mm
    )

    normal_style = ParagraphStyle(
        "Normal2",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#2C2C2C"),
        spaceAfter=1 * mm
    )

    elements.append(Paragraph("SHANEAL DISTRIBUTORS", header_style))
    elements.append(Paragraph(
        "Stationery · PPE · Office Equipment · Household Consumables",
        sub_style
    ))
    elements.append(Spacer(1, 3 * mm))

    divider = Table([[""]], colWidths=[170 * mm])
    divider.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#D4A017")),
        ("ROWHEIGHTS", (0, 0), (-1, -1), 2),
    ]))
    elements.append(divider)
    elements.append(Spacer(1, 5 * mm))

    info_data = [
        [Paragraph("<b>QUOTATION</b>", styles["Normal"]),
         Paragraph("<b>Bill To:</b>", styles["Normal"])],
        [Paragraph(f"Quote No: {quote_num}", normal_style),
         Paragraph(customer_name, normal_style)],
        [Paragraph(f"Date: {today}", normal_style),
         Paragraph(company_name, normal_style)],
        [Paragraph(f"Valid Until: {valid_until}", normal_style),
         Paragraph("", normal_style)]
    ]

    info_table = Table(info_data, colWidths=[85 * mm, 85 * mm])
    info_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP")
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 8 * mm))

    table_data = [["DESCRIPTION", "QTY", "UNIT PRICE", "TOTAL"]]

    for item in line_items:
        table_data.append([
            item[0],
            str(item[1]),
            f"R {item[2]:,.2f}",
            f"R {item[3]:,.2f}"
        ])

    table_data.append(["", "", "Subtotal:", f"R {subtotal:,.2f}"])
    table_data.append(["", "", "VAT (15%):", f"R {vat:,.2f}"])
    table_data.append(["", "", "TOTAL DUE:", f"R {total:,.2f}"])

    items_table = Table(
        table_data,
        colWidths=[90 * mm, 20 * mm, 30 * mm, 30 * mm]
    )

    items_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2D6A2D")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -4), [colors.HexColor("#FAFAF8"), colors.white]),
        ("FONTNAME", (2, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#2D6A2D")),
        ("TEXTCOLOR", (0, -1), (-1, -1), colors.white),
        ("GRID", (0, 0), (-1, -4), 0.25, colors.HexColor("#E8E0D0")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))

    elements.append(items_table)
    elements.append(Spacer(1, 10 * mm))

    footer_data = [[Paragraph(
        "ShaNeal Distributors | 332 Paul Kruger Street, Capital Park, Pretoria 0084<br/>"
        "Tel: 070 070 0770 | Email: ShaNeal@lantic.co.za | www.ShaNealonline.co.za",
        ParagraphStyle(
            "Footer",
            parent=styles["Normal"],
            fontSize=8,
            textColor=colors.HexColor("#888888")
        )
    )]]

    footer_table = Table(footer_data, colWidths=[170 * mm])
    footer_table.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 0.5, colors.HexColor("#D4A017")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))

    elements.append(footer_table)
    doc.build(elements)

    return filename, quote_num


def get_whatsapp_link(summary):
    message = f"Hello ShaNeal Distributors, I need assistance. {summary}"
    encoded = message.replace(" ", "%20").replace("\n", "%0A")
    return f"https://wa.me/{WHATSAPP_NUMBER}?text={encoded}"


# -----------------------------
# CHAT FUNCTION
# -----------------------------

def chat_with_clarix(message):
    results = knowledge_base.query(
        query_texts=[message],
        n_results=1
    )

    product_context = ""

    try:
        if results["documents"][0]:
            product_context = results["documents"][0][0]
    except Exception:
        product_context = ""

    enhanced_message = f"""Customer query: {message}
ShaNeal product information: {product_context}"""

    conversation = []

    for item in st.session_state.messages:
        if item["role"] in ["user", "assistant"]:
            conversation.append({
                "role": item["role"],
                "content": item["content"]
            })

    conversation.append({
        "role": "user",
        "content": enhanced_message
    })

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=conversation
    )

    reply = response.content[0].text

    # Quote generation
    if "GENERATE_QUOTE" in reply:
        try:
            name_match = re.search(r"NAME:\s*(.+)", reply)
            company_match = re.search(r"COMPANY:\s*(.+)", reply)
            items_match = re.search(r"ITEMS:\n(.*?)END_QUOTE", reply, re.DOTALL)

            if all([name_match, company_match, items_match]):
                customer_name = name_match.group(1).strip()
                company_name = company_match.group(1).strip()
                items_text = items_match.group(1).strip()

                filename, quote_num = generate_quote(
                    customer_name,
                    company_name,
                    items_text
                )

                st.session_state.latest_quote_path = filename

                reply = f"""✅ Quote {quote_num} generated!

**Customer:** {customer_name} — {company_name}

📄 Your quote is ready. Use the **Download Latest Quote** button below to save your PDF.

Valid for 30 days. Is there anything else I can help you with?"""

        except Exception as e:
            reply = f"Error generating quote: {str(e)}"

    # Human escalation
    if "ESCALATE_TO_HUMAN" in reply:
        summary = f"Customer issue: {message}"
        whatsapp_link = get_whatsapp_link(summary)
        clean_reply = reply.replace("ESCALATE_TO_HUMAN", "").strip()

        reply = f"""{clean_reply}

---
🔴 **This issue requires a human agent.**

👉 WhatsApp us: {whatsapp_link}

Monday to Friday, 8am to 6pm  
📞 070 070 0770"""

    return reply


# -----------------------------
# SESSION STATE
# -----------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "latest_quote_path" not in st.session_state:
    st.session_state.latest_quote_path = None


# -----------------------------
# QUICK ACTIONS
# -----------------------------

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
    [""] + quick_actions
)

if selected_action:
    st.session_state.pending_question = selected_action


# -----------------------------
# DISPLAY CHAT HISTORY
# -----------------------------

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# -----------------------------
# CHAT INPUT
# -----------------------------

user_input = st.chat_input("Type your message here...")

if "pending_question" in st.session_state:
    user_input = st.session_state.pending_question
    del st.session_state.pending_question

if user_input:
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("CLARIX is thinking..."):
            assistant_reply = chat_with_clarix(user_input)
            st.markdown(assistant_reply)

    st.session_state.messages.append({
        "role": "assistant",
        "content": assistant_reply
    })


# -----------------------------
# DOWNLOAD QUOTE
# -----------------------------

if st.session_state.latest_quote_path:
    try:
        with open(st.session_state.latest_quote_path, "rb") as pdf_file:
            st.download_button(
                label="📄 Download Latest Quote",
                data=pdf_file,
                file_name=os.path.basename(st.session_state.latest_quote_path),
                mime="application/pdf"
            )
    except Exception:
        st.warning("Quote file could not be loaded. Please generate the quote again.")


# -----------------------------
# FOOTER
# -----------------------------

st.markdown("---")
st.markdown(
    """
    <div style="text-align:center; font-size:12px; color:#888;">
    POWERED BY CLARIX AI · SHANEAL DISTRIBUTORS · PRETORIA<br>
    <a href="https://www.shanealonline.co.za" style="color:#2D6A2D; text-decoration:none;">
    SHANEALONLINE.CO.ZA
    </a>
    <br><br>
    <span style="font-size:11px; color:#aaa;">
    CLARIX is a product of <strong style="color:#2D6A2D;">Nikhil Dante Mooloo</strong>
    · AI Business Operations Specialist · Pretoria
    </span>
    </div>
    """,
    unsafe_allow_html=True
)
