import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

def build_pdf():
    pdf_filename = r"C:\Users\sanat\Desktop\Loom_Video_Script_Address_Standardization.pdf"
    
    doc = SimpleDocTemplate(
        pdf_filename,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Title'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#1E293B'),
        alignment=TA_LEFT,
        spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#2563EB'),
        alignment=TA_LEFT,
        spaceAfter=15
    )

    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#0F172A'),
        spaceBefore=14,
        spaceAfter=8
    )

    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor('#1E40AF'),
        spaceBefore=10,
        spaceAfter=4
    )

    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor('#334155'),
        spaceAfter=6
    )

    script_style = ParagraphStyle(
        'ScriptText',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor('#0F766E'),
        spaceBefore=4,
        spaceAfter=6
    )

    visual_style = ParagraphStyle(
        'VisualText',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#B45309'),
        spaceAfter=4
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.white
    )

    table_body_style = ParagraphStyle(
        'TableBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor('#1E293B')
    )

    elements = []

    # Title Banner
    elements.append(Paragraph("5-Minute Loom Video Script & Blueprint", title_style))
    elements.append(Paragraph("AI-Assisted Property Address Standardization System — Code Walkthrough", subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2563EB'), spaceAfter=12))

    # Setup Box
    setup_text = (
        "<b>Pre-Recording Checklist:</b><br/>"
        "• <b>VS Code Font Size:</b> Set to 130%–150% (Ctrl + +) for maximum readability.<br/>"
        "• <b>Project Root:</b> Open <code>C:\\Users\\sanat\\Desktop\\Adress_project2\\Adress project</code>.<br/>"
        "• <b>Initial View:</b> Collapse all folders in the file explorer before recording starts.<br/>"
        "• <b>Audio & Mic:</b> Speak at a natural, steady pace with quiet background surroundings."
    )
    setup_table = Table(
        [[Paragraph(setup_text, body_style)]],
        colWidths=[530]
    )
    setup_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#EFF6FF')),
        ('BORDER', (0,0), (-1,-1), 1, colors.HexColor('#BFDBFE')),
        ('PADDING', (0,0), (-1,-1), 8),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    elements.append(setup_table)
    elements.append(Spacer(1, 10))

    # Section: Timeline Matrix
    elements.append(Paragraph("1. Video Timeline & Screen Actions Matrix", h1_style))
    
    matrix_data = [
        [
            Paragraph("Time", table_header_style),
            Paragraph("Section", table_header_style),
            Paragraph("Files / Screen Focus", table_header_style),
            Paragraph("Key Objective", table_header_style)
        ],
        [
            Paragraph("0:00–0:30", table_body_style),
            Paragraph("1. Introduction", table_body_style),
            Paragraph("File Explorer (Root Directory)", table_body_style),
            Paragraph("Hook viewer with problem & system goal", table_body_style)
        ],
        [
            Paragraph("0:30–1:10", table_body_style),
            Paragraph("2. Project Structure", table_body_style),
            Paragraph("docker-compose.yml & top-level folders", table_body_style),
            Paragraph("Explain microservice separation of concerns", table_body_style)
        ],
        [
            Paragraph("1:10–2:10", table_body_style),
            Paragraph("3. Backend Architecture", table_body_style),
            Paragraph("addresses.controller.ts, addresses.service.ts", table_body_style),
            Paragraph("Walk through NestJS flow, queues & audit trail", table_body_style)
        ],
        [
            Paragraph("2:10–3:40", table_body_style),
            Paragraph("4. ML Service & Pipeline", table_body_style),
            Paragraph("main.py, parser.py, features.py, model.py", table_body_style),
            Paragraph("Show libpostal, feature engineering & LightGBM", table_body_style)
        ],
        [
            Paragraph("3:40–4:20", table_body_style),
            Paragraph("5. Decision Flow", table_body_style),
            Paragraph("README.md matrix / threshold logic", table_body_style),
            Paragraph("Confidence routing & active learning loop", table_body_style)
        ],
        [
            Paragraph("4:20–5:00", table_body_style),
            Paragraph("6. Closing", table_body_style),
            Paragraph("Entire VS Code Window", table_body_style),
            Paragraph("Summarize architecture & thank interviewer", table_body_style)
        ]
    ]

    matrix_table = Table(matrix_data, colWidths=[65, 110, 185, 170])
    matrix_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E293B')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('PADDING', (0,0), (-1,-1), 5),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')])
    ]))
    elements.append(matrix_table)
    elements.append(Spacer(1, 12))

    # Section: Walkthrough & Script
    elements.append(Paragraph("2. Section-by-Section Script & Action Blueprint", h1_style))

    sections = [
        {
            "title": "Section 1: Introduction (0:00–0:30)",
            "visual": "🎬 Visual: VS Code with root project folder open. Show clean workspace.",
            "script": "\"Hi, I'm Sanath. This project is an AI-Assisted Property Address Standardization System. In real-world property databases, raw address inputs are messy, inconsistently formatted, and full of abbreviations. The goal of this system is to ingest raw property addresses, standardize them into a canonical format, predict a machine learning confidence score, and automatically decide whether to accept the result or send it for human review.\""
        },
        {
            "title": "Section 2: Project Structure (0:30–1:10)",
            "visual": "🎬 Visual: Collapse all folders in VS Code. Point to backend/, ml-service/, database/, docker-compose.yml.",
            "script": "\"I separated the system into independent services to keep responsibilities clean and modular:\n• backend/: Built with NestJS. Exposes REST APIs, manages PostgreSQL records, coordinates queues, and maintains audit trails.\n• ml-service/: Built with Python FastAPI. Handles address parsing using libpostal, feature extraction, LightGBM scoring, and vector embeddings.\n• database/: Contains PostgreSQL migrations and schema with pgvector enabled.\n• docker-compose.yml: Orchestrates the entire containerized stack including Redis and PostgreSQL.\""
        },
        {
            "title": "Section 3: Backend Architecture (1:10–2:10)",
            "visual": "🎬 Visual: Expand backend/src/addresses -> Open addresses.controller.ts (lines 13-36) and addresses.service.ts (lines 39-53). Highlight review/ and audit/ folders.",
            "script": "\"In backend/src/addresses/addresses.controller.ts, the POST /standardize endpoint accepts raw input. In addresses.service.ts, the service sends raw text to the ML service and receives standardized components plus a confidence score. High confidence matches are saved directly to canonical records, while lower confidence items route into review/. Crucially, every operation logs an immutable record in audit/, giving interviewers complete visibility and auditability.\""
        },
        {
            "title": "Section 4: ML Service & Decision Logic (2:10–3:40)",
            "visual": "🎬 Visual: Open ml-service/app/main.py -> parser.py -> features.py -> model.py.",
            "script": "\"In ml-service/app/main.py, POST /standardize drives the ML pipeline:\n1. parser.py: Uses libpostal to parse raw text into house_number, road, city, state, zip.\n2. features.py: Computes Jaccard similarity, Levenshtein edit ratios, directional expansions (W to West), and suffix expansions (St to Street).\n3. model.py: A LightGBM Classifier evaluates these features to predict a confidence score between 0 and 1. Predicting confidence—rather than a binary output—gives us flexible control over automation thresholds.\""
        },
        {
            "title": "Section 5: Decision Logic & System Flow (3:40–4:20)",
            "visual": "🎬 Visual: Show README.md routing matrix table or addresses.service.ts lines 44-52.",
            "script": "\"The decision architecture routes records dynamically:\n• Score >= 0.80 -> Auto Accepted: Bypasses review and updates canonical records.\n• 0.50 - 0.79 -> Review Queue: Routed to human reviewers, prioritized near the decision boundary using uncertainty sampling.\n• Score < 0.50 -> Flagged: Immediately escalated for manual intervention.\nWhen reviewers submit corrections, the system collects feedback to trigger automated model retraining.\""
        },
        {
            "title": "Section 6: Closing (4:20–5:00)",
            "visual": "🎬 Visual: Switch back to top-level VS Code view.",
            "script": "\"To summarize, this project highlights clean service boundaries, asynchronous ML integration, and a pragmatic human-in-the-loop design. Using confidence scores with an active learning loop ensures we keep bad data out of production while continuously improving the model. Thank you for watching!\""
        }
    ]

    for sec in sections:
        sec_elements = []
        sec_elements.append(Paragraph(sec["title"], h2_style))
        sec_elements.append(Paragraph(sec["visual"], visual_style))
        formatted_script = sec["script"].replace('\n', '<br/>')
        sec_elements.append(Paragraph(f"🗣️ <b>Script:</b> {formatted_script}", script_style))
        sec_elements.append(Spacer(1, 4))
        elements.append(KeepTogether(sec_elements))

    # Build PDF
    doc.build(elements)
    print(f"PDF successfully generated at: {pdf_filename}")

if __name__ == "__main__":
    build_pdf()
