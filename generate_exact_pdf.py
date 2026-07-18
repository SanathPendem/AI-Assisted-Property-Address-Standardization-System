import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
from reportlab.lib.enums import TA_LEFT

def build_pdf():
    pdf_filename = r"C:\Users\sanat\Desktop\5_Minute_Loom_Video_Recording_Blueprint.pdf"
    
    doc = SimpleDocTemplate(
        pdf_filename,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Title'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0F172A'),
        alignment=TA_LEFT,
        spaceAfter=10
    )

    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#1E293B'),
        spaceBefore=14,
        spaceAfter=6
    )

    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#2563EB'),
        spaceBefore=10,
        spaceAfter=4
    )

    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#334155'),
        spaceAfter=4
    )

    script_style = ParagraphStyle(
        'ScriptText',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9,
        leading=13.5,
        textColor=colors.HexColor('#0F766E'),
        spaceBefore=4,
        spaceAfter=6
    )

    visual_style = ParagraphStyle(
        'VisualText',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#D97706'),
        spaceAfter=4
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white
    )

    table_body_style = ParagraphStyle(
        'TableBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#1E293B')
    )

    elements = []

    # Title Banner
    elements.append(Paragraph("🎬 5-Minute Loom Video Recording Blueprint", title_style))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2563EB'), spaceAfter=10))

    # TIP Box
    tip_text = (
        "<b>TIP — Pre-recording Setup:</b><br/>"
        "• Set VS Code font size to 130%–150% (Ctrl + + twice).<br/>"
        "• Open the project root folder: <b>Adress project</b>.<br/>"
        "• Collapse all folders in the file explorer before hitting Record."
    )
    tip_table = Table([[Paragraph(tip_text, body_style)]], colWidths=[540])
    tip_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#EFF6FF')),
        ('BORDER', (0,0), (-1,-1), 1, colors.HexColor('#BFDBFE')),
        ('PADDING', (0,0), (-1,-1), 8),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    elements.append(tip_table)
    elements.append(Spacer(1, 10))

    # Timeline Matrix
    elements.append(Paragraph("⏱️ Video Timeline & Screen Actions Summary", h1_style))
    
    matrix_data = [
        [
            Paragraph("Time", table_header_style),
            Paragraph("Section", table_header_style),
            Paragraph("File(s) to Open / Show", table_header_style),
            Paragraph("Key Focus", table_header_style)
        ],
        [
            Paragraph("0:00–0:30", table_body_style),
            Paragraph("1. Introduction", table_body_style),
            Paragraph("File Explorer / Root Directory", table_body_style),
            Paragraph("Problem Statement & System Purpose", table_body_style)
        ],
        [
            Paragraph("0:30–1:10", table_body_style),
            Paragraph("2. Project Structure", table_body_style),
            Paragraph("docker-compose.yml & Top-level Folders", table_body_style),
            Paragraph("Service Separation & Architecture", table_body_style)
        ],
        [
            Paragraph("1:10–2:10", table_body_style),
            Paragraph("3. Backend Architecture", table_body_style),
            Paragraph("addresses.controller.ts, addresses.service.ts, review/, audit/", table_body_style),
            Paragraph("Request flow, Audit trail logging", table_body_style)
        ],
        [
            Paragraph("2:10–3:40", table_body_style),
            Paragraph("4. ML Service & Decision Logic", table_body_style),
            Paragraph("main.py, parser.py, features.py, model.py", table_body_style),
            Paragraph("libpostal, feature engineering & LightGBM", table_body_style)
        ],
        [
            Paragraph("3:40–4:20", table_body_style),
            Paragraph("5. Decision Logic & System Flow", table_body_style),
            Paragraph("addresses.service.ts#L44-L52 & README.md", table_body_style),
            Paragraph("Threshold routing matrix", table_body_style)
        ],
        [
            Paragraph("4:20–5:00", table_body_style),
            Paragraph("6. Closing", table_body_style),
            Paragraph("Entire VS Code Window", table_body_style),
            Paragraph("Architectural summary & wrap up", table_body_style)
        ]
    ]

    matrix_table = Table(matrix_data, colWidths=[65, 110, 195, 170])
    matrix_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E293B')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('PADDING', (0,0), (-1,-1), 5),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')])
    ]))
    elements.append(matrix_table)
    elements.append(Spacer(1, 10))

    # Detailed Script Section
    elements.append(Paragraph("📜 Detailed Word-for-Word Script & Visual Walkthrough", h1_style))

    sections = [
        {
            "title": "📍 Section 1: Introduction (0:00–0:30)",
            "visual": "Visual On Screen:<br/>VS Code open with root folder <b>Adress project</b>.",
            "script": "\"Hi, I'm Sanath. This project is an AI-Assisted Property Address Standardization System.<br/><br/>In real-world data pipelines, property address records from various source systems are notoriously messy, duplicated, and unformatted. The goal of this system is to ingest raw, unstructured property addresses, parse and standardize them into a canonical format, predict a machine learning confidence score, and automatically decide whether to auto-accept the match or route it for human review.\""
        },
        {
            "title": "📍 Section 2: Project Structure (0:30–1:10)",
            "visual": "Visual On Screen:<br/>Collapse all subfolders in VS Code explorer so only top-level directories are visible:<br/>📁 backend/<br/>📁 database/<br/>📁 ml-service/<br/>📄 docker-compose.yml<br/>📄 README.md",
            "script": "\"I deliberately separated the system into multiple independent services to maintain clear boundaries of responsibility:<br/><br/>• <b>backend/</b>: Built with NestJS, this service coordinates the pipeline. It exposes REST APIs, manages PostgreSQL transactions, routes records into review queues, and handles audit logging.<br/>• <b>ml-service/</b>: Built with Python FastAPI, dedicated to address parsing using libpostal, feature extraction, LightGBM model inference, and vector embeddings.<br/>• <b>database/</b>: Contains PostgreSQL migration scripts and schemas with pgvector enabled for spatial vector similarity search.<br/>• <b>docker-compose.yml</b>: Containerizes and orchestrates all microservices alongside PostgreSQL and Redis.\""
        },
        {
            "title": "📍 Section 3: Backend Architecture (1:10–2:10)",
            "visual": "Visual On Screen:<br/>Expand backend/src/addresses -> Open <b>addresses.controller.ts</b> (Highlight @Post('standardize') at line 13).<br/>Open <b>addresses.service.ts</b> (Highlight lines 39–53).<br/>Briefly collapse addresses and highlight review/ and audit/ folders in the sidebar.",
            "script": "\"Looking at the NestJS backend, inside addresses.controller.ts, the @Post('standardize') endpoint receives raw property addresses.<br/><br/>Delegating to addresses.service.ts, the service forwards the raw string to the Python ML service to retrieve the standardized output and predicted confidence score.<br/><br/>Notice how we handle routing logic right here: high-confidence predictions update or create master canonical records, whereas mid and low-confidence predictions are placed in the review/ queue for manual human-in-the-loop validation.<br/><br/>Crucially, every single prediction and human correction logs an event to the audit/ module. Maintaining an immutable audit trail ensures complete traceability and accountability across all address transformations.\""
        },
        {
            "title": "📍 Section 4: ML Service & Decision Logic (2:10–3:40)",
            "visual": "Visual On Screen:<br/>Open <b>ml-service/app/main.py</b> (Point to POST /standardize at line 49).<br/>Open <b>ml-service/app/parser.py</b> (Show libpostal parse_address() call at line 12).<br/>Open <b>ml-service/app/features.py</b> (Scroll through Jaccard, Levenshtein, directional/suffix expansion flags at lines 23–68).<br/>Open <b>ml-service/app/model.py</b> (Highlight predict_confidence() and LightGBM model invocation at line 41).",
            "script": "\"Now let's look at the ML Service. Inside FastAPI's main.py, the POST /standardize endpoint orchestrates the ML pipeline.<br/><br/>First, parser.py utilizes libpostal, an C library trained on open street data, to decompose unstructured addresses into discrete fields like house number, street name, city, state, and zip code.<br/><br/>Next, features.py extracts a rich set of numerical and text features for model scoring. This includes token-level Jaccard similarity, character-level Levenshtein ratios, component presence flags, and expansion checks like expanding 'W' to 'West' or 'St' to 'Street'.<br/><br/>Finally, in model.py, a LightGBM Classifier evaluates these features to output a calibrated confidence score between 0 and 1. Rather than forcing a binary decision, predicting a confidence score allows the overall system to make nuanced, threshold-driven decisions.\""
        },
        {
            "title": "📍 Section 5: Decision Logic & System Flow (3:40–4:20)",
            "visual": "Visual On Screen:<br/>Open <b>README.md</b> and highlight the Confidence Routing Matrix table (Lines 34–40), or show <b>addresses.service.ts#L44-L52</b>.",
            "script": "\"The decision architecture relies on three explicit confidence thresholds:<br/><br/>• <b>Score &ge; 0.80 (auto_accepted)</b>: Straight-through processing. Automatically linked or merged with canonical master address records.<br/>• <b>0.50 to 0.79 (pending_review)</b>: Sent to the human-in-the-loop review queue. We prioritize items near the decision boundary using uncertainty sampling to maximize human review efficiency.<br/>• <b>Score &lt; 0.50 (flagged)</b>: Escalate immediately to manual review with low-confidence warning tags.<br/><br/>This human feedback is stored and used to trigger automated model retraining once enough corrections are collected, closing the active learning loop.\""
        },
        {
            "title": "📍 Section 6: Closing (4:20–5:00)",
            "visual": "Visual On Screen:<br/>Switch back to full VS Code view showing top-level files.",
            "script": "\"To summarize, this system demonstrates robust separation of concerns between backend coordination and specialized ML services, robust audit logging, and a pragmatic ML design where confidence scores drive automated vs. human decision-making.<br/><br/>One architectural decision I'm particularly proud of is using confidence-based review queues with active learning—it prevents corrupt address data from touching production databases while continuously improving model performance over time.<br/><br/>Thank you for watching!\""
        }
    ]

    for sec in sections:
        sec_elements = []
        sec_elements.append(Paragraph(sec["title"], h2_style))
        sec_elements.append(Paragraph(sec["visual"], visual_style))
        sec_elements.append(Paragraph(f"🗣️ <b>Spoken Script:</b><br/>{sec['script']}", script_style))
        sec_elements.append(Spacer(1, 4))
        elements.append(KeepTogether(sec_elements))

    doc.build(elements)
    print(f"PDF built successfully at: {pdf_filename}")

if __name__ == "__main__":
    build_pdf()
