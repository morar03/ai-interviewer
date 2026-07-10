from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

from django.conf import settings
BASE_DIR = settings.BASE_DIR

FONT_DIR = BASE_DIR / 'static' / 'fonts'
pdfmetrics.registerFont(TTFont('DejaVu', str(FONT_DIR / 'DejaVuSans.ttf')))
pdfmetrics.registerFont(TTFont('DejaVu-Bold', str(FONT_DIR / 'DejaVuSans-Bold.ttf')))

from .models import Interview, Question, Answer
from .prompts import generate_first_question, generate_next_question, generate_summary


def login_view(request):
    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            error = 'Invalid username or password.'
    return render(request, 'login.html', {'error': error})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def home(request):
    if request.method == 'POST':
        topic = request.POST.get('topic', '').strip()
        level = request.POST.get('level', 'mid')
        if topic:
            interview = Interview.objects.create(topic=topic, level=level)
            first_question = generate_first_question(topic, level)
            Question.objects.create(
                interview=interview,
                text=first_question,
                order=1
            )
            return redirect('interview', interview_id=interview.id)
    suggestions = [
        'AI in the workplace',
        'Productivity tools',
        'Remote work culture',
        'Future of education',
        'Climate technology',
    ]
    return render(request, 'home.html', {'suggestions': suggestions})


@login_required
def interview_view(request, interview_id):
    interview = get_object_or_404(Interview, id=interview_id)
    questions = interview.questions.order_by('order')
    last_question = interview.questions.filter(answer__isnull=True).order_by('order').first()

    if request.method == 'POST':
        answer_text = request.POST.get('answer', '').strip()
        if answer_text and last_question:
            Answer.objects.create(
                question=last_question,
                text=answer_text
            )

            qa_pairs = []
            for q in questions:
                if hasattr(q, 'answer'):
                    qa_pairs.append((q.text, q.answer.text))

            next_q = generate_next_question(interview.topic, interview.level, qa_pairs)

            if next_q["continue"] and next_q["question"]:
                Question.objects.create(
                    interview=interview,
                    text=next_q["question"],
                    order=last_question.order + 1
                )
                return redirect('interview', interview_id=interview.id)
            else:
                result = generate_summary(interview.topic, interview.level, qa_pairs)
                interview.summary = result["summary"]
                interview.sentiment = result["sentiment"]
                interview.keywords = result["keywords"]
                interview.save()
                return redirect('summary', interview_id=interview.id)

    answered_count = sum(1 for q in questions if hasattr(q, 'answer'))
    context = {
        'interview': interview,
        'current_question': last_question,
        'question_number': last_question.order if last_question else 1,
        'answered_count': answered_count,
    }
    return render(request, 'interview.html', context)

@login_required
def summary_view(request, interview_id):
    interview = get_object_or_404(Interview, id=interview_id)
    questions = interview.questions.order_by('order')
    context = {
        'interview': interview,
        'questions': questions,
    }
    return render(request, 'summary.html', context)


@login_required
def history_view(request):
    interviews = Interview.objects.order_by('-created_at')
    return render(request, 'history.html', {'interviews': interviews})


@login_required
def export_pdf(request, interview_id):
    interview = get_object_or_404(Interview, id=interview_id)
    questions = interview.questions.order_by('order')

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="interview_{interview_id}.pdf"'

    doc = SimpleDocTemplate(response, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)

    from reportlab.lib import colors
    from reportlab.platypus import HRFlowable, Table, TableStyle

    BLUE = colors.HexColor('#2563eb')
    LIGHT_BLUE = colors.HexColor('#eff6ff')
    DARK = colors.HexColor('#111827')
    GREY = colors.HexColor('#6b7280')
    LIGHT_GREY = colors.HexColor('#f3f4f6')
    GREEN = colors.HexColor('#16a34a')
    RED = colors.HexColor('#dc2626')
    YELLOW = colors.HexColor('#ca8a04')

    title_style = ParagraphStyle('Title', fontName='DejaVu-Bold', fontSize=24,
                                  textColor=DARK, spaceAfter=8, alignment=TA_CENTER)
    subtitle_style = ParagraphStyle('Subtitle', fontName='DejaVu', fontSize=12,
                                     textColor=GREY, spaceAfter=16, alignment=TA_CENTER)
    section_style = ParagraphStyle('Section', fontName='DejaVu-Bold', fontSize=12,
                                    textColor=BLUE, spaceAfter=8, spaceBefore=16)
    body_style = ParagraphStyle('Body', fontName='DejaVu', fontSize=10,
                                 textColor=DARK, spaceAfter=8, leading=16)
    question_style = ParagraphStyle('Question', fontName='DejaVu-Bold', fontSize=10,
                                     textColor=DARK, spaceAfter=4, leading=14)
    answer_style = ParagraphStyle('Answer', fontName='DejaVu', fontSize=10,
                                   textColor=colors.HexColor('#374151'), spaceAfter=8,
                                   leading=14, leftIndent=12)
    meta_style = ParagraphStyle('Meta', fontName='DejaVu', fontSize=9, textColor=GREY)

    story = []

    # Header
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("AI Interviewer", title_style))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph("Interview Transcript", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=BLUE, spaceAfter=12))
    story.append(Spacer(1, 0.3*cm))

    # Meta info
    story.append(Paragraph(f"<b>Topic:</b> {interview.topic}", body_style))
    story.append(Paragraph(f"<b>Date:</b> {interview.created_at.strftime('%d %B %Y, %H:%M')}", meta_style))
    story.append(Paragraph(f"<b>Questions:</b> {questions.count()}", meta_style))
    story.append(Spacer(1, 0.4*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#e5e7eb')))

    # Summary section
    if interview.summary:
        story.append(Paragraph("Summary", section_style))
        story.append(Paragraph(interview.summary, body_style))
        story.append(Spacer(1, 0.2*cm))

    # Sentiment + Keywords in a table
    if interview.sentiment or interview.keywords:
        sentiment_color = GREEN if interview.sentiment == "Positive" else RED if interview.sentiment == "Negative" else YELLOW
        sentiment_text = f"<font color='#{sentiment_color.hexval()[1:] if hasattr(sentiment_color, 'hexval') else '000000'}'>{interview.sentiment}</font>"

        data = []
        if interview.sentiment:
            data.append([
                Paragraph("<b>Sentiment</b>", ParagraphStyle('th', fontName='DejaVu-Bold', fontSize=9, textColor=GREY)),
                Paragraph(interview.sentiment, ParagraphStyle('td', fontName='DejaVu-Bold', fontSize=10, textColor=sentiment_color))
            ])
        if interview.keywords:
            data.append([
                Paragraph("<b>Keywords</b>", ParagraphStyle('th', fontName='DejaVu-Bold', fontSize=9, textColor=GREY)),
                Paragraph(interview.keywords, ParagraphStyle('td', fontName='DejaVu', fontSize=10, textColor=DARK))
            ])

        table = Table(data, colWidths=[3*cm, 13*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), LIGHT_GREY),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [LIGHT_GREY, colors.white]),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('ROUNDEDCORNERS', [4]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
        ]))
        story.append(table)
        story.append(Spacer(1, 0.4*cm))

    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#e5e7eb')))

     # Transcript
    story.append(Paragraph("Full Transcript", section_style))
    story.append(Spacer(1, 0.2*cm))

    for q in questions:
        # Numar intrebare
        story.append(Paragraph(f"Question {q.order}", ParagraphStyle(
            'QNum', fontName='DejaVu-Bold', fontSize=9,
            textColor=BLUE, spaceAfter=4
        )))

        # Textul intrebarii
        q_data = [[Paragraph(q.text, question_style)]]
        q_table = Table(q_data, colWidths=[16*cm])
        q_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BLUE),
            ('PADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('ROUNDEDCORNERS', [4]),
        ]))
        story.append(q_table)
        story.append(Spacer(1, 0.15*cm))

        # Raspunsul userului
        if hasattr(q, 'answer'):
            answer_label = Paragraph("User answer", ParagraphStyle(
                'ALabel', fontName='DejaVu-Bold', fontSize=9,
                textColor=GREY, spaceAfter=3
            ))
            story.append(answer_label)

            a_data = [[Paragraph(q.answer.text, answer_style)]]
            a_table = Table(a_data, colWidths=[16*cm])
            a_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f9fafb')),
                ('PADDING', (0, 0), (-1, -1), 10),
                ('LEFTPADDING', (0, 0), (-1, -1), 12),
                ('LINEAFTER', (0, 0), (0, -1), 3, colors.HexColor('#e5e7eb')),
                ('LINEBEFORE', (0, 0), (0, -1), 3, colors.HexColor('#d1d5db')),
            ]))
            story.append(a_table)

        story.append(Spacer(1, 0.4*cm))

    # Footer
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#e5e7eb')))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph("Generated by AI Interviewer", meta_style))

    doc.build(story)
    return response