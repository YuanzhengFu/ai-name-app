from __future__ import annotations

import textwrap
from datetime import datetime
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from core.name_compare import build_project_recommendations
from models.name_history import NameHistory
from models.naming_project import NamingProject


REPORT_FORMATS = {"pdf", "image", "txt"}


def build_report_filename(item: NameHistory, report_format: str) -> str:
    suffix = {"pdf": "pdf", "image": "png", "txt": "txt"}[report_format]
    safe_name = "".join(char for char in item.name if char not in r'\/:*?"<>|').strip() or "naming-report"
    return f"{safe_name}-起名方案.{suffix}"


def build_report_bytes(item: NameHistory, report_format: str) -> tuple[bytes, str]:
    if report_format == "pdf":
        return _build_pdf_report(item), "application/pdf"
    if report_format == "image":
        return _build_image_report(item), "image/png"
    if report_format == "txt":
        return _build_text_report(item).encode("utf-8"), "text/plain; charset=utf-8"
    raise ValueError("不支持的导出格式")


def build_project_report_filename(project: NamingProject, report_format: str) -> str:
    suffix = {"pdf": "pdf", "image": "png", "txt": "txt"}[report_format]
    safe_name = "".join(char for char in project.title if char not in r'\/:*?"<>|').strip() or "naming-project"
    return f"{safe_name}-项目命名方案.{suffix}"


def build_project_report_bytes(
    project: NamingProject,
    histories: list[NameHistory],
    report_format: str,
) -> tuple[bytes, str]:
    if report_format == "pdf":
        return _build_project_pdf_report(project, histories), "application/pdf"
    if report_format == "image":
        return _build_project_image_report(project, histories), "image/png"
    if report_format == "txt":
        return _build_project_text_report(project, histories).encode("utf-8"), "text/plain; charset=utf-8"
    raise ValueError("不支持的导出格式")


def _format_time(value: datetime | None) -> str:
    return value.strftime("%Y-%m-%d %H:%M:%S") if value else ""


def _report_rows(item: NameHistory) -> list[tuple[str, str]]:
    rows = [
        ("名字", item.name),
        ("分类", item.category),
        ("出处", item.reference),
        ("寓意", item.moral),
    ]
    if item.domain:
        domain = f"{item.domain}（{item.domain_status}）" if item.domain_status else item.domain
        rows.append(("域名", domain))
    if item.surname:
        rows.append(("姓氏", item.surname))
    if item.gender:
        rows.append(("性别倾向", item.gender))
    if item.length:
        rows.append(("字数要求", item.length))
    if item.other:
        rows.append(("起名诉求", item.other))
    rows.extend(
        [
            ("收藏状态", "已收藏" if item.is_favorite else "未收藏"),
            ("生成时间", _format_time(item.created_time)),
            ("会话ID", item.thread_id),
        ]
    )
    return rows


def _score_summary(item: NameHistory) -> str:
    parts = [
        f"综合 {item.score_total or 0}",
        f"音律 {item.rhythm_score or 0}",
        f"寓意 {item.meaning_score or 0}",
        f"传播 {item.spread_score or 0}",
    ]
    if item.category == "企业名" or item.domain:
        parts.append(f"域名 {item.domain_score or 0}")
    return " / ".join(parts)


def _project_summary_rows(project: NamingProject, histories: list[NameHistory]) -> list[tuple[str, str]]:
    favorites = sum(1 for item in histories if item.is_favorite)
    threads = {item.thread_id for item in histories if item.thread_id}
    rows = [
        ("项目名称", project.title),
        ("分类", project.category),
        ("项目描述", project.description or "未填写"),
        ("项目状态", "已归档" if project.status == "archived" else "进行中"),
        ("候选名数量", str(len(histories))),
        ("收藏数量", str(favorites)),
        ("迭代轮次", str(len(threads))),
        ("创建时间", _format_time(project.created_time)),
        ("更新时间", _format_time(project.updated_time)),
        ("导出时间", _format_time(datetime.now())),
    ]
    return rows


def _project_recommendation_lines(histories: list[NameHistory]) -> list[str]:
    if not histories:
        return ["暂无候选名，无法生成推荐。"]
    recommendations = build_project_recommendations(histories, limit=min(3, len(histories)))
    return [
        f"No.{item.rank} {item.name}：对比得分 {item.compare_score}，{item.reason}"
        for item in recommendations
    ]


def _history_iteration_groups(histories: list[NameHistory]) -> list[tuple[str, list[NameHistory]]]:
    grouped: dict[str, list[NameHistory]] = {}
    for item in sorted(histories, key=lambda entry: (entry.created_time, entry.id)):
        grouped.setdefault(item.thread_id or "未记录会话", []).append(item)
    return list(grouped.items())


def _build_text_report(item: NameHistory) -> str:
    lines = ["AI 智能起名方案", "=" * 18]
    lines.extend(f"{label}：{value}" for label, value in _report_rows(item))
    return "\n".join(lines) + "\n"


def _build_project_text_report(project: NamingProject, histories: list[NameHistory]) -> str:
    lines = [f"{project.title} 项目命名方案", "=" * 24, ""]
    lines.append("一、项目概览")
    lines.extend(f"{label}：{value}" for label, value in _project_summary_rows(project, histories))

    lines.extend(["", "二、对比推荐"])
    lines.extend(_project_recommendation_lines(histories))

    lines.extend(["", "三、候选名清单"])
    if not histories:
        lines.append("暂无候选名。")
    for index, item in enumerate(sorted(histories, key=lambda entry: (-int(entry.score_total or 0), entry.id)), start=1):
        favorite = "已收藏" if item.is_favorite else "未收藏"
        domain = f"；域名：{item.domain}（{item.domain_status}）" if item.domain else ""
        lines.append(f"{index}. {item.name}（{favorite}；{_score_summary(item)}{domain}）")
        lines.append(f"   出处：{item.reference}")
        lines.append(f"   寓意：{item.moral}")
        if item.score_explanation:
            lines.append(f"   评分说明：{item.score_explanation}")
        if item.other:
            lines.append(f"   需求摘要：{item.other}")

    lines.extend(["", "四、反馈迭代记录"])
    for group_index, (thread_id, group_items) in enumerate(_history_iteration_groups(histories), start=1):
        first_time = _format_time(group_items[0].created_time) if group_items else ""
        lines.append(f"第 {group_index} 轮 / 会话 {thread_id} / {first_time}")
        names = "、".join(item.name for item in group_items)
        lines.append(f"   产出候选：{names}")
        requirement = next((item.other for item in group_items if item.other), "")
        if requirement:
            lines.append(f"   记录需求：{requirement}")

    return "\n".join(lines) + "\n"


def _build_pdf_report(item: NameHistory) -> bytes:
    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=f"{item.name} 起名方案",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontName="STSong-Light",
        fontSize=22,
        leading=30,
        textColor=colors.HexColor("#1f2937"),
        spaceAfter=12,
    )
    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["BodyText"],
        fontName="STSong-Light",
        fontSize=11,
        leading=18,
        textColor=colors.HexColor("#374151"),
    )

    table_data = [
        [
            Paragraph(f"<b>{label}</b>", body_style),
            Paragraph(_escape_pdf_text(value), body_style),
        ]
        for label, value in _report_rows(item)
    ]
    table = Table(table_data, colWidths=[28 * mm, 132 * mm])
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), "STSong-Light"),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f3f4f6")),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#374151")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d1d5db")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )

    doc.build([Paragraph("AI 智能起名方案", title_style), Spacer(1, 6 * mm), table])
    return buffer.getvalue()


def _build_project_pdf_report(project: NamingProject, histories: list[NameHistory]) -> bytes:
    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=f"{project.title} 项目命名方案",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ProjectReportTitle",
        parent=styles["Title"],
        fontName="STSong-Light",
        fontSize=22,
        leading=30,
        textColor=colors.HexColor("#1f2937"),
        spaceAfter=10,
    )
    section_style = ParagraphStyle(
        "ProjectReportSection",
        parent=styles["Heading2"],
        fontName="STSong-Light",
        fontSize=15,
        leading=22,
        textColor=colors.HexColor("#111827"),
        spaceBefore=12,
        spaceAfter=8,
    )
    body_style = ParagraphStyle(
        "ProjectReportBody",
        parent=styles["BodyText"],
        fontName="STSong-Light",
        fontSize=10.5,
        leading=17,
        textColor=colors.HexColor("#374151"),
    )

    story: list = [Paragraph(f"{project.title} 项目命名方案", title_style)]
    story.append(Paragraph("一、项目概览", section_style))
    story.append(_build_pdf_table(_project_summary_rows(project, histories), body_style, [30 * mm, 128 * mm]))

    story.append(Paragraph("二、对比推荐", section_style))
    story.extend(Paragraph(_escape_pdf_text(line), body_style) for line in _project_recommendation_lines(histories))

    story.append(Paragraph("三、候选名清单", section_style))
    if histories:
        candidate_rows = [
            (
                item.name,
                "已收藏" if item.is_favorite else "未收藏",
                _score_summary(item),
                f"{item.domain}（{item.domain_status}）" if item.domain and item.domain_status else (item.domain or "-"),
                item.moral,
            )
            for item in sorted(histories, key=lambda entry: (-int(entry.score_total or 0), entry.id))
        ]
        story.append(
            _build_pdf_table(
                [("候选名", "收藏", "评分", "域名", "寓意"), *candidate_rows],
                body_style,
                [24 * mm, 18 * mm, 38 * mm, 34 * mm, 44 * mm],
                header=True,
            )
        )
    else:
        story.append(Paragraph("暂无候选名。", body_style))

    story.append(PageBreak())
    story.append(Paragraph("四、候选名详情", section_style))
    for item in sorted(histories, key=lambda entry: (entry.created_time, entry.id)):
        detail_rows = [
            ("候选名", item.name),
            ("收藏状态", "已收藏" if item.is_favorite else "未收藏"),
            ("评分", _score_summary(item)),
            ("出处", item.reference),
            ("寓意", item.moral),
            ("评分说明", item.score_explanation or ""),
            ("需求摘要", item.other or ""),
            ("生成时间", _format_time(item.created_time)),
        ]
        if item.domain:
            detail_rows.insert(3, ("域名", f"{item.domain}（{item.domain_status}）" if item.domain_status else item.domain))
        story.append(Paragraph(_escape_pdf_text(item.name), section_style))
        story.append(_build_pdf_table(detail_rows, body_style, [28 * mm, 130 * mm]))

    story.append(Paragraph("五、反馈迭代记录", section_style))
    for group_index, (thread_id, group_items) in enumerate(_history_iteration_groups(histories), start=1):
        first_time = _format_time(group_items[0].created_time) if group_items else ""
        story.append(Paragraph(f"第 {group_index} 轮 / 会话 {thread_id} / {first_time}", body_style))
        names = "、".join(item.name for item in group_items)
        story.append(Paragraph(_escape_pdf_text(f"产出候选：{names}"), body_style))
        requirement = next((item.other for item in group_items if item.other), "")
        if requirement:
            story.append(Paragraph(_escape_pdf_text(f"记录需求：{requirement}"), body_style))
        story.append(Spacer(1, 4 * mm))

    doc.build(story)
    return buffer.getvalue()


def _build_pdf_table(
    rows: list[tuple[str, ...]],
    body_style: ParagraphStyle,
    col_widths: list[float],
    header: bool = False,
) -> Table:
    table_data = [
        [Paragraph(f"<b>{_escape_pdf_text(cell)}</b>" if header and row_index == 0 else _escape_pdf_text(cell), body_style) for cell in row]
        for row_index, row in enumerate(rows)
    ]
    table = Table(table_data, colWidths=col_widths, repeatRows=1 if header else 0)
    commands = [
        ("FONTNAME", (0, 0), (-1, -1), "STSong-Light"),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#374151")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d1d5db")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]
    if header:
        commands.append(("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eaf4ff")))
    else:
        commands.append(("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f3f4f6")))
    table.setStyle(TableStyle(commands))
    return table


def _escape_pdf_text(value: str) -> str:
    return (
        str(value or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "<br/>")
    )


def _build_image_report(item: NameHistory) -> bytes:
    width = 1080
    margin = 72
    label_width = 150
    line_gap = 14
    row_gap = 28
    title_font = _load_font(48)
    label_font = _load_font(30)
    body_font = _load_font(30)
    small_font = _load_font(24)

    rows = _report_rows(item)
    wrapped_rows: list[tuple[str, list[str]]] = []
    content_width = width - margin * 2 - label_width
    for label, value in rows:
        wrapped_rows.append((label, _wrap_for_image(str(value or ""), body_font, content_width)))

    height = margin * 2 + 76
    for _, lines in wrapped_rows:
        height += max(42, len(lines) * 42 + (len(lines) - 1) * line_gap) + row_gap
    height += 32

    image = Image.new("RGB", (width, height), "#f5f7fa")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((36, 36, width - 36, height - 36), radius=22, fill="#ffffff")
    draw.text((margin, margin), "AI 智能起名方案", fill="#1f2937", font=title_font)
    draw.text((margin, margin + 58), f"导出时间：{_format_time(datetime.now())}", fill="#6b7280", font=small_font)

    y = margin + 120
    for label, lines in wrapped_rows:
        draw.text((margin, y), f"{label}：", fill="#111827", font=label_font)
        text_x = margin + label_width
        line_y = y
        for line in lines:
            draw.text((text_x, line_y), line, fill="#374151", font=body_font)
            line_y += 42 + line_gap
        y += max(42, len(lines) * 42 + (len(lines) - 1) * line_gap) + row_gap

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _build_project_image_report(project: NamingProject, histories: list[NameHistory]) -> bytes:
    width = 1280
    margin = 72
    line_gap = 10
    block_gap = 26
    title_font = _load_font(48)
    section_font = _load_font(34)
    label_font = _load_font(28)
    body_font = _load_font(26)
    small_font = _load_font(22)
    content_width = width - margin * 2

    blocks: list[tuple[str, str, ImageFont.ImageFont]] = []
    blocks.append(("title", f"{project.title} 项目命名方案", title_font))
    blocks.append(("small", f"导出时间：{_format_time(datetime.now())}", small_font))

    blocks.append(("section", "一、项目概览", section_font))
    for label, value in _project_summary_rows(project, histories):
        blocks.append(("body", f"{label}：{value}", body_font))

    blocks.append(("section", "二、对比推荐", section_font))
    for line in _project_recommendation_lines(histories):
        blocks.append(("body", line, body_font))

    blocks.append(("section", "三、候选名清单", section_font))
    if histories:
        for index, item in enumerate(sorted(histories, key=lambda entry: (-int(entry.score_total or 0), entry.id)), start=1):
            favorite = "已收藏" if item.is_favorite else "未收藏"
            domain = f"；域名：{item.domain}（{item.domain_status}）" if item.domain else ""
            blocks.append(("body", f"{index}. {item.name}（{favorite}；{_score_summary(item)}{domain}）", label_font))
            blocks.append(("body", f"寓意：{item.moral}", body_font))
            blocks.append(("body", f"出处：{item.reference}", body_font))
    else:
        blocks.append(("body", "暂无候选名。", body_font))

    blocks.append(("section", "四、反馈迭代记录", section_font))
    for group_index, (thread_id, group_items) in enumerate(_history_iteration_groups(histories), start=1):
        first_time = _format_time(group_items[0].created_time) if group_items else ""
        names = "、".join(item.name for item in group_items)
        blocks.append(("body", f"第 {group_index} 轮 / 会话 {thread_id} / {first_time}", label_font))
        blocks.append(("body", f"产出候选：{names}", body_font))
        requirement = next((item.other for item in group_items if item.other), "")
        if requirement:
            blocks.append(("body", f"记录需求：{requirement}", body_font))

    measured: list[tuple[str, list[str], ImageFont.ImageFont]] = []
    height = margin * 2
    for kind, text, font in blocks:
        lines = _wrap_for_image(text, font, content_width)
        measured.append((kind, lines, font))
        line_height = max(30, font.size if hasattr(font, "size") else 28) + line_gap
        height += len(lines) * line_height
        height += 18 if kind == "section" else block_gap if kind == "title" else 8
    height += 60

    image = Image.new("RGB", (width, height), "#f5f7fa")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((36, 36, width - 36, height - 36), radius=22, fill="#ffffff")

    y = margin
    for kind, lines, font in measured:
        fill = "#1f2937"
        if kind == "section":
            fill = "#0f4f8f"
        elif kind == "small":
            fill = "#6b7280"
        line_height = max(30, font.size if hasattr(font, "size") else 28) + line_gap
        for line in lines:
            draw.text((margin, y), line, fill=fill, font=font)
            y += line_height
        y += 18 if kind == "section" else block_gap if kind == "title" else 8

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    font_paths = [
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simsun.ttc",
        "C:/Windows/Fonts/simhei.ttf",
    ]
    for path in font_paths:
        try:
            return ImageFont.truetype(path, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def _wrap_for_image(text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    if not text:
        return [""]
    lines: list[str] = []
    for raw_line in text.splitlines() or [""]:
        current = ""
        for char in raw_line:
            test = current + char
            bbox = font.getbbox(test)
            if bbox[2] - bbox[0] <= max_width:
                current = test
                continue
            if current:
                lines.append(current)
            current = char
        lines.append(current)

    normalized: list[str] = []
    for line in lines:
        if not line:
            normalized.append("")
        elif len(line) > 80:
            normalized.extend(textwrap.wrap(line, width=80))
        else:
            normalized.append(line)
    return normalized
