from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from django.conf import settings
import os
from datetime import datetime


def generate_application_pdf(application):
    """Генерация PDF-уведомления по заявке"""

    # Регистрируем русский шрифт
    pdfmetrics.registerFont(TTFont('DejaVu', 'DejaVuSans.ttf'))

    # Создаем PDF
    filename = f"application_{application.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join(settings.MEDIA_ROOT, 'pdfs', filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    doc = SimpleDocTemplate(filepath, pagesize=A4,
                            topMargin=20 * mm, bottomMargin=20 * mm,
                            leftMargin=20 * mm, rightMargin=20 * mm)

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Russian', fontName='DejaVu', fontSize=10, leading=14))
    styles.add(
        ParagraphStyle(name='Title', fontName='DejaVu', fontSize=16, leading=20, textColor=colors.HexColor('#667eea')))
    styles.add(ParagraphStyle(name='Header', fontName='DejaVu', fontSize=12, leading=16, textColor=colors.white))

    story = []

    # Заголовок
    title = Paragraph("СОЦИАЛЬНЫЙ ФОНД РОССИИ", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 10))

    title2 = Paragraph(f"Уведомление о статусе заявки №{application.id}", styles['Title'])
    story.append(title2)
    story.append(Spacer(1, 20))

    # Данные заявителя
    data = [
        ['Параметр', 'Значение'],
        ['ФИО', f"{application.last_name} {application.first_name} {application.patronymic}"],
        ['СНИЛС', application.snils],
        ['Тип услуги', application.service_type],
        ['Статус', application.get_status_display()],
        ['Дата создания', application.created_at.strftime('%d.%m.%Y %H:%M')],
        ['Дата обновления', application.updated_at.strftime('%d.%m.%Y %H:%M')],
    ]

    if application.employee_comment:
        data.append(['Комментарий сотрудника', application.employee_comment])

    table = Table(data, colWidths=[80 * mm, 100 * mm])
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'DejaVu'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))

    story.append(table)
    story.append(Spacer(1, 20))

    # Подпись
    story.append(Paragraph("С уважением,", styles['Russian']))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Социальный фонд России", styles['Russian']))

    # Генерируем PDF
    doc.build(story)

    return filepath