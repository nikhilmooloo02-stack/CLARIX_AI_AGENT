import streamlit as st
from groq import Groq
import re
import datetime
import random
import os

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm


# ---------------- PAGE SETUP ----------------

st.set_page_config(
    page_title="CLARIX — ShaNeal Distributors",
    page_icon="🟢",
    layout="centered"
)

st.title("CLARIX — ShaNeal Distributors AI Assistant")
st.caption("Ask about products, request a quote, or get support.")


# ---------------- PRODUCTS ----------------

PRODUCTS_TEXT = """
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

PRICE_LIST = {
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


# ---------------- SYSTEM PROMPT ----------------

SYSTEM_PROMPT = f"""
You are CLARIX, the professional AI assistant for ShaNeal Distributors.

ShaNeal Distributors sells stationery, PPE, office equipment and household consumables in Pretoria, South Africa.

PRODUCTS AND PRICING:
{PRODUCTS_TEXT}

CONTACT INFORMATION:
- Phone: 070 070 0770
- Email: ShaNeal@lantic.co.za
- Address: 332 Paul Kruger Street, Corner Van Heerden Street, Capital Park, Pretoria 0084
- Website: www.ShaNealonline.co.za
- Business Hours: Monday to Friday, 8am to 6pm

BEHAVIOUR:
- Recommend specific products with prices.
- Cross-sell related products naturally.
- Calculate VAT at 15% when asked.
- Always show amounts in South African Rand.
- For bulk orders ask for organisation name and delivery address.
- For orders over R10,000, recommend speaking to a human consultant.
- For complaints, apologise and offer a clear next step.

QUOTE GENERATION:
When a customer asks for a quote and gives their name, company and items, respond with EXACTLY this format:

GENERATE_QUOTE
NAME: [customer name]
COMPANY: [company name]
ITEMS:
[product name], [quantity]
[product name], [quantity]
END_QUOTE

If name/company/items are missing, ask for the missing information.
"""


# ---------------- API CONNECTION ----------------

client = Groq(api_key=st.secrets["GROQ_API_KEY"])


# ---------------- PDF QUOTE FUNCTION ----------------

def generate_quote(customer_name, company_name, items_text):
    line_items = []

    for line in items_text.strip().split("\n"):
        if "," not in line:
            continue

        product, qty_text = line.split(",", 1)
        product = product.strip()

        try:
            qty = int(qty_text.strip())
        except:
            qty = 1

        price = 0.00
        for key, value in PRICE_LIST.items():
            if key in product.lower():
                price = value
                break

        line_items.append([product, qty, price, price * qty])

    if not line_items:
        return None, None

    subtotal = sum(item[3] for item in line_items)
    vat = subtotal * 0.15
    total = subtotal + vat

    quote_num = f"SND-{random.randint(1000,9999)}-{datetime.datetime.now().year}"
    filename = f"CLARIX_Quote_{quote_num}.pdf"

    doc = SimpleDocTemplate(filename, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    title_style = ParagraphStyle(
        "Title",
        parent=styles["Normal"],
        fontSize=22,
        textColor=colors.HexColor("#2D6A2D"),
        fontName="Helvetica-Bold"
    )

    elements.append(Paragraph("SHANEAL DISTRIBUTORS", title_style))
    elements.append(Paragraph("Official Quotation", styles["Normal"]))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph(f"<b>Quote Number:</b> {quote_num}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Customer:</b> {customer_name}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Company:</b> {company_name}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    table_data = [["Description", "Qty", "Unit Price", "Total"]]

    for item in line_items:
        table_data.append([
            item[0],
            str(item[1]),
            f"R {item[2]:,.2f}",
            f"R {item[3]:,.2f}"
        ])

    table_data.append(["", "", "Subtotal", f"R {subtotal:,.2f}"])
    table_data.append(["", "", "VAT 15%", f"R {vat:,.2f}"])
    table_data.append(["", "", "Total", f"R {total:,.2f}"])

    table = Table(table_data)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2D6A2D")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (2, -1), (-1, -1), "Helvetica-Bold"),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 20))

    elements.append(Paragraph(
        "ShaNeal Distributors | 070 070 0770 | ShaNeal@lantic.co.za | www.ShaNealonline.co.za",
        styles["Normal"]
    ))

    doc.build(elements)

    return filename, quote_num


# ---------------- CHAT FUNCTION ----------------

def ask_clarix(user_message):
    conversation = [{"role": "system", "content": SYSTEM_PROMPT}]

    for msg in st.session_state.messages:
        conversation.append({
            "role": msg["role"],
            "content": msg["content"]
        })

    enhanced_message = f"""
Customer message:
{user_message}

Product information:
{PRODUCTS_TEXT}
"""

    conversation.append({
        "role": "user",
        "content": enhanced_message
    })

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=1000,
        messages=conversation
    )

    reply = response.choices[0].message.content

    if "GENERATE_QUOTE" in reply:
        name_match = re.search(r"NAME:\s*(.+)", reply)
        company_match = re.search(r"COMPANY:\s*(.+)", reply)
        items_match = re.search(r"ITEMS:\n(.*?)END_QUOTE", reply, re.DOTALL)

        if name_match and company_match and items_match:
            name = name_match.group(1).strip()
            company = company_match.group(1).strip()
            items = items_match.group(1).strip()

            filename, quote_num = generate_quote(name, company, items)

            if filename:
                st.session_state.latest_quote = filename
                reply = f"""
✅ Quote {quote_num} generated successfully.

Customer: **{name}**  
Company: **{company}**

Your PDF quote is ready. Use the download button below.
"""

    return reply


# ---------------- SESSION STATE ----------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "latest_quote" not in st.session_state:
    st.session_state.latest_quote = None


# ---------------- UI ----------------

with st.sidebar:
    st.header("Quick Actions")

    quick_questions = [
        "What stationery products do you stock?",
        "Can I get a quote for 10 Butterfly A4 Paper reams?",
        "Calculate VAT on R5,500.",
        "I need PPE for 20 staff members.",
        "Help me set up a new office for 10 staff.",
        "How can I contact ShaNeal Distributors?"
    ]

    for question in quick_questions:
        if st.button(question):
            st.session_state.pending_question = question

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

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
            reply = ask_clarix(user_input)
            st.markdown(reply)

    st.session_state.messages.append({
        "role": "assistant",
        "content": reply
    })

if st.session_state.latest_quote:
    with open(st.session_state.latest_quote, "rb") as file:
        st.download_button(
            label="📄 Download Latest Quote",
            data=file,
            file_name=os.path.basename(st.session_state.latest_quote),
            mime="application/pdf"
        )

st.markdown("---")
st.caption("CLARIX AI · Powered and Developed by Nikhil Dante Mooloo · ShaNeal Distributors · Pretoria")
