import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
from reportlab.lib.enums import TA_LEFT

def build_pdf():
    pdf_filename = r"C:\Users\sanat\Desktop\5_Minute_Loom_Video_Script_And_Execution_Blueprint.pdf"
    
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
        fontSize=17,
        leading=21,
        textColor=colors.HexColor('#0F172A'),
        alignment=TA_LEFT,
        spaceAfter=3
    )

    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#2563EB'),
        alignment=TA_LEFT,
        spaceAfter=10
    )

    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=colors.HexColor('#1E293B'),
        spaceBefore=12,
        spaceAfter=6
    )

    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13.5,
        textColor=colors.HexColor('#2563EB'),
        spaceBefore=8,
        spaceAfter=4
    )

    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#334155'),
        spaceAfter=4
    )

    script_style = ParagraphStyle(
        'ScriptText',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8.5,
        leading=12.5,
        textColor=colors.HexColor('#0F766E'),
        spaceBefore=3,
        spaceAfter=5
    )

    visual_style = ParagraphStyle(
        'VisualText',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=11.5,
        textColor=colors.HexColor('#D97706'),
        spaceAfter=3
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=11,
        textColor=colors.white
    )

    table_body_style = ParagraphStyle(
        'TableBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.8,
        leading=10.5,
        textColor=colors.HexColor('#1E293B')
    )

    elements = []

    # Title Banner
    elements.append(Paragraph("🎬 5-Minute Loom Video Script & Blueprint", title_style))
    elements.append(Paragraph("AI-Assisted Property Address Standardization System — Code Walkthrough & Live Execution", subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2563EB'), spaceAfter=8))

    # Setup Box
    setup_text = (
        "<b>Pre-Recording Setup & Execution Instructions:</b><br/>"
        "• <b>VS Code Font Size:</b> Set to 130%–150% (Ctrl + +) for maximum readability.<br/>"
        "• <b>Project Root:</b> Open <code>C:\\Users\\sanat\\Desktop\\Adress_project2\\Adress project</code>.<br/>"
        "• <b>GitHub Repository:</b> <code>https://github.com/SanathPendem/AI-Assisted-Property-Address-Standardization-System</code><br/>"
        "• <b>System Execution Command:</b> Run Docker stack before recording:<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;<code>docker compose up --build -d</code><br/>"
        "• <b>Live Endpoints:</b> Web UI (<code>http://localhost:3000</code>) | Swagger Docs (<code>http://localhost:3000/api/docs</code>)<br/>"
        "• <b>Initial View:</b> Collapse all folders in the file explorer before recording starts."
    )
    setup_table = Table([[Paragraph(setup_text, body_style)]], colWidths=[540])
    setup_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#EFF6FF')),
        ('BORDER', (0,0), (-1,-1), 1, colors.HexColor('#BFDBFE')),
        ('PADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    elements.append(setup_table)
    elements.append(Spacer(1, 8))

    # Timeline Matrix
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
            Paragraph("0:30–1:00", table_body_style),
            Paragraph("2. Project Structure", table_body_style),
            Paragraph("docker-compose.yml & top-level folders", table_body_style),
            Paragraph("Explain microservice separation of concerns", table_body_style)
        ],
        [
            Paragraph("1:00–1:50", table_body_style),
            Paragraph("3. Backend Architecture", table_body_style),
            Paragraph("addresses.controller.ts, addresses.service.ts", table_body_style),
            Paragraph("Walk through NestJS flow, queues & audit trail", table_body_style)
        ],
        [
            Paragraph("1:50–3:10", table_body_style),
            Paragraph("4. ML Service & Pipeline", table_body_style),
            Paragraph("main.py, parser.py, features.py, model.py", table_body_style),
            Paragraph("Show libpostal, feature engineering & LightGBM", table_body_style)
        ],
        [
            Paragraph("3:10–3:50", table_body_style),
            Paragraph("5. Decision Flow", table_body_style),
            Paragraph("README.md matrix / threshold logic", table_body_style),
            Paragraph("Confidence routing & active learning loop", table_body_style)
        ],
        [
            Paragraph("3:50–4:30", table_body_style),
            Paragraph("6. Execution & Demo", table_body_style),
            Paragraph("Terminal (docker compose ps) & Web/Swagger UI", table_body_style),
            Paragraph("Demonstrate live execution & container status", table_body_style)
        ],
        [
            Paragraph("4:30–5:00", table_body_style),
            Paragraph("7. Closing", table_body_style),
            Paragraph("Entire VS Code Window", table_body_style),
            Paragraph("Summarize architecture & thank interviewer", table_body_style)
        ]
    ]

    matrix_table = Table(matrix_data, colWidths=[65, 110, 195, 170])
    matrix_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E293B')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('PADDING', (0,0), (-1,-1), 4),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')])
    ]))
    elements.append(matrix_table)
    elements.append(Spacer(1, 8))

    # Detailed Script Section
    elements.append(Paragraph("2. Section-by-Section Script & Action Blueprint", h1_style))

    sections = [
        {
            "title": "📍 Section 1: Introduction (0:00–0:30)",
            "visual": "🎬 Visual: VS Code with root project folder open. Show clean workspace.",
            "script": "\"Hi, I'm Sanath. This project is an AI-Assisted Property Address Standardization System.<br/><br/>In real-world data pipelines, property address records from various source systems are notoriously messy, duplicated, and unformatted. The goal of this system is to ingest raw, unstructured property addresses, parse and standardize them into a canonical format, predict a machine learning confidence score, and automatically decide whether to auto-accept the match or route it for human review.\""
        },
        {
            "title": "📍 Section 2: Project Structure (0:30–1:00)",
            "visual": "🎬 Visual: Collapse all folders in VS Code explorer so only top-level directories are visible:<br/>📁 backend/ &nbsp;&nbsp; 📁 database/ &nbsp;&nbsp; 📁 ml-service/ &nbsp;&nbsp; 📄 docker-compose.yml &nbsp;&nbsp; 📄 README.md",
            "script": "\"I deliberately separated the system into independent services to maintain clear boundaries of responsibility:<br/><br/>• <b>backend/</b>: Built with NestJS. Exposes REST APIs, manages PostgreSQL records, coordinates queues, and maintains audit trails.<br/>• <b>ml-service/</b>: Built with Python FastAPI. Handles address parsing using libpostal, feature extraction, LightGBM scoring, and vector embeddings.<br/>• <b>database/</b>: Contains PostgreSQL migrations and schema with pgvector enabled.<br/>• <b>docker-compose.yml</b>: Containerizes and orchestrates all microservices alongside PostgreSQL and Redis.\""
        },
        {
            "title": "📍 Section 3: Backend Architecture (1:00–1:50)",
            "visual": "🎬 Visual: Expand backend/src/addresses -> Open addresses.controller.ts (lines 13-36) and addresses.service.ts (lines 39-53). Highlight review/ and audit/ folders.",
            "script": "\"In backend/src/addresses/addresses.controller.ts, the POST /standardize endpoint accepts raw input. In addresses.service.ts, the service sends raw text to the ML service and receives standardized components plus a confidence score. High confidence matches are saved directly to canonical records, while lower confidence items route into review/. Crucially, every operation logs an immutable record in audit/, giving interviewers complete visibility and auditability.\""
        },
        {
            "title": "📍 Section 4: ML Service & Decision Logic (1:50–3:10)",
            "visual": "🎬 Visual: Open ml-service/app/main.py -> parser.py -> features.py -> model.py.",
            "script": "\"In ml-service/app/main.py, POST /standardize drives the ML pipeline:<br/><br/>1. parser.py: Uses libpostal to parse raw text into house_number, road, city, state, zip.<br/>2. features.py: Computes Jaccard similarity, Levenshtein edit ratios, directional expansions (W to West), and suffix expansions (St to Street).<br/>3. model.py: A LightGBM Classifier evaluates these features to predict a confidence score between 0 and 1. Predicting confidence—rather than a binary output—gives us flexible control over automation thresholds.\""
        },
        {
            "title": "📍 Section 5: Decision Logic & System Flow (3:10–3:50)",
            "visual": "🎬 Visual: Show README.md routing matrix table or addresses.service.ts lines 44-52.",
            "script": "\"The decision architecture routes records dynamically:<br/><br/>• <b>Score &ge; 0.80 -> Auto Accepted</b>: Bypasses review and updates canonical records.<br/>• <b>0.50 - 0.79 -> Review Queue</b>: Routed to human reviewers, prioritized near the decision boundary using uncertainty sampling.<br/>• <b>Score &lt; 0.50 -> Flagged</b>: Immediately escalated for manual intervention.<br/><br/>When reviewers submit corrections, the system collects feedback to trigger automated model retraining.\""
        },
        {
            "title": "📍 Section 6: System Execution & Live Demo (3:50–4:30)",
            "visual": "🎬 Visual: Open VS Code terminal, run docker compose ps. Open Browser to http://localhost:3000 (Web UI) or http://localhost:3000/api/docs (Swagger UI) and execute POST /addresses/standardize live.",
            "script": "\"Here you can see the live system execution. Running docker compose ps, all four containerized microservices—NestJS backend, FastAPI ML engine, PostgreSQL pgvector database, and Redis queue—are active and healthy.<br/><br/>When we execute a sample raw address request like '45 W 34 St Apt 2, NY 12308', the pipeline returns the standardized canonical string '45 West 34th Street, Apartment 2, New York, NY 12308' alongside its 75.5% confidence score and parsed components in just 130 milliseconds.\""
        },
        {
            "title": "📍 Section 7: Closing (4:30–5:00)",
            "visual": "🎬 Visual: Switch back to top-level VS Code view.",
            "script": "\"To summarize, this project highlights clean service boundaries, asynchronous ML integration, and a pragmatic human-in-the-loop design. Using confidence scores with an active learning loop ensures we keep bad data out of production while continuously improving the model. Thank you for watching!\""
        }
    ]

    for sec in sections:
        sec_elements = []
        sec_elements.append(Paragraph(sec["title"], h2_style))
        sec_elements.append(Paragraph(sec["visual"], visual_style))
        sec_elements.append(Paragraph(f"🗣️ <b>Spoken Script:</b><br/>{sec['script']}", script_style))
        sec_elements.append(Spacer(1, 3))
        elements.append(KeepTogether(sec_elements))

    doc.build(elements)
    print(f"PDF built successfully at: {pdf_filename}")

if __name__ == "__main__":
    build_pdf()
