from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml.ns import qn, nsdecls
from docx.oxml import OxmlElement, parse_xml
from fpdf import FPDF
import os
import re

from data.personal_info import PERSONAL_INFO


BLACK = RGBColor(0x00, 0x00, 0x00)


class CVBuilder:
    ATS_KEYWORDS = [
        "Android", "Kotlin", "Java", "Jetpack Compose", "Android SDK",
        "Clean Architecture", "MVVM", "MAD", "Coroutines", "Flow",
        "Hilt", "Dagger", "Koin", "Retrofit", "OkHttp", "REST API",
        "Room", "Firebase", "Firebase Auth", "Firestore", "Crashlytics",
        "CI/CD", "Fastlane", "GitHub Actions", "Google Play",
        "Material Design 3", "Material Design", "JNI", "NDK",
        "llama.cpp", "whisper.cpp", "TFLite", "LiteRT", "ONNX",
        "Machine Learning", "AI", "LLM", "CNN",
        "WorkManager", "Navigation Component", "Paging 3",
        "CameraX", "WebSocket", "Git",
        "Performance Optimization", "Code Review",
        "Agile", "Scrum", "Unit Test", "JUnit", "MockK",
        "SQLite", "DataStore", "StateFlow",
        "Google Play Console", "Play Store",
        "Adaptive Layout", "Jetpack",
        "Deep Learning", "On-Device", "Inference",
        "Live2D", "sherpa-onnx", "Vulkan", "GGUF", "MMPROJ",
        "Qwen", "MiniCPM", "CameraX", "LiteRT",
    ]

    def __init__(self, info: dict = None, links: dict = None):
        self.info = info or PERSONAL_INFO
        self.links = links or {}

    def _set_cell_border(self, cell, **kwargs):
        tc = cell._tc
        tcPr = tc.get_or_add_tcPr()
        tcBorders = OxmlElement("w:tcBorders")
        for edge, val in kwargs.items():
            element = OxmlElement(f"w:{edge}")
            for attr, value in val.items():
                element.set(qn(f"w:{attr}"), str(value))
            tcBorders.append(element)
        tcPr.append(tcBorders)

    def _normalize_url(self, url: str) -> str:
        if url.startswith(("mailto:", "http://", "https://")):
            return url
        return f"https://{url}"

    def _add_hyperlink(self, paragraph, text: str, url: str, font_size=9):
        url = self._normalize_url(url)
        part = paragraph.part
        r_id = part.relate_to(url, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink", is_external=True)
        hyperlink = OxmlElement("w:hyperlink")
        hyperlink.set(qn("r:id"), r_id)
        new_run = OxmlElement("w:r")
        rPr = OxmlElement("w:rPr")
        c = OxmlElement("w:color")
        c.set(qn("w:val"), "000000")
        rPr.append(c)
        u = OxmlElement("w:u")
        u.set(qn("w:val"), "single")
        rPr.append(u)
        sz = OxmlElement("w:sz")
        sz.set(qn("w:val"), str(int(font_size * 2)))
        rPr.append(sz)
        new_run.append(rPr)
        t = OxmlElement("w:t")
        t.text = text
        new_run.append(t)
        hyperlink.append(new_run)
        paragraph._p.append(hyperlink)
        return hyperlink

    def _add_hr(self, doc):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        pPr = p._p.get_or_add_pPr()
        pBdr = OxmlElement("w:pBdr")
        bottom = OxmlElement("w:bottom")
        bottom.set(qn("w:val"), "single")
        bottom.set(qn("w:sz"), "4")
        bottom.set(qn("w:space"), "1")
        bottom.set(qn("w:color"), "333333")
        pBdr.append(bottom)
        pPr.append(pBdr)

    def build_docx(self, output_path: str) -> str:
        doc = Document()
        section = doc.sections[0]
        section.top_margin = Inches(0.4)
        section.bottom_margin = Inches(0.4)
        section.left_margin = Inches(0.6)
        section.right_margin = Inches(0.6)

        style = doc.styles["Normal"]
        font = style.font
        font.name = "Calibri"
        font.size = Pt(10)
        font.color.rgb = RGBColor(0x3C, 0x31, 0x32)
        style.paragraph_format.space_after = Pt(2)
        style.paragraph_format.space_before = Pt(0)
        style.paragraph_format.line_spacing = 1.05

        TITLE_COLOR = RGBColor(0xA4, 0x9F, 0x9F)
        SEC_COLOR = RGBColor(0x70, 0x68, 0x69)
        BODY_COLOR = RGBColor(0x3C, 0x31, 0x32)

        # --- HEADER ---
        name_p = doc.add_paragraph()
        name_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        name_p.paragraph_format.space_after = Pt(0)
        name_run = name_p.add_run(self.info["name"].upper())
        name_run.bold = True
        name_run.font.size = Pt(18)
        name_run.font.color.rgb = RGBColor(0x3C, 0x31, 0x32)

        title_p = doc.add_paragraph()
        title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title_p.paragraph_format.space_before = Pt(0)
        title_p.paragraph_format.space_after = Pt(2)
        title_run = title_p.add_run(self.info["title"])
        title_run.bold = True
        title_run.font.size = Pt(11)
        title_run.font.color.rgb = TITLE_COLOR

        contact_p = doc.add_paragraph()
        contact_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        contact_p.paragraph_format.space_after = Pt(2)
        loc_r = contact_p.add_run(self.info["location"])
        loc_r.font.size = Pt(8.5)
        loc_r.font.color.rgb = BODY_COLOR
        sep_r = contact_p.add_run("  -  ")
        sep_r.font.size = Pt(8.5)
        sep_r.font.color.rgb = BODY_COLOR
        self._add_hyperlink(contact_p, "LinkedIn", self.info["linkedin"], font_size=8.5)
        sep_r2 = contact_p.add_run("  -  ")
        sep_r2.font.size = Pt(8.5)
        sep_r2.font.color.rgb = BODY_COLOR
        self._add_hyperlink(contact_p, "GitHub", self.info["github"], font_size=8.5)
        sep_r3 = contact_p.add_run("  -  ")
        sep_r3.font.size = Pt(8.5)
        sep_r3.font.color.rgb = BODY_COLOR
        self._add_hyperlink(contact_p, self.info["email"], f"mailto:{self.info['email']}", font_size=8.5)
        sep_r4 = contact_p.add_run("  -  ")
        sep_r4.font.size = Pt(8.5)
        sep_r4.font.color.rgb = BODY_COLOR
        self._add_hyperlink(contact_p, self.info["website"], self.info["website"], font_size=8.5)

        self._add_hr(doc)

        def add_section(title):
            heading = doc.add_paragraph()
            heading.paragraph_format.space_before = Pt(8)
            heading.paragraph_format.space_after = Pt(2)
            run = heading.add_run(title.upper())
            run.bold = True
            run.font.size = Pt(11)
            run.font.color.rgb = SEC_COLOR
            self._add_hr(doc)

        add_section("About")
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(4)
        r = p.add_run(self.info["summary"])
        r.font.size = Pt(9.5)
        r.font.color.rgb = BODY_COLOR

        if self.info.get("company_projects"):
            add_section("Company Projects")
            self._build_company_projects_section_docx(doc)

        add_section("Work Experience")
        self._build_experience_section_docx(doc)

        add_section("Personal Portfolio")
        self._build_portfolio_section_docx(doc)

        add_section("Skills")
        self._build_skills_section_docx(doc)

        add_section("Education")
        self._build_education_section_docx(doc)

        doc.save(output_path)
        return output_path

    def _add_bullet_docx(self, doc, text):
        bp = doc.add_paragraph()
        bp.paragraph_format.space_before = Pt(0)
        bp.paragraph_format.space_after = Pt(1)
        bp.paragraph_format.left_indent = Inches(0.25)
        bp.paragraph_format.first_line_indent = Inches(-0.15)
        bullet = bp.add_run("•")
        bullet.font.size = Pt(9)
        bullet.font.color.rgb = RGBColor(0x3C, 0x31, 0x32)
        text_run = bp.add_run(text)
        text_run.font.size = Pt(9)
        text_run.font.color.rgb = RGBColor(0x3C, 0x31, 0x32)

    def _build_portfolio_section_docx(self, doc):
        for item in self.info.get("portfolio", []):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(1)
            url = self.links.get(item.get("url", ""), "")
            platform = item.get("platform", "")
            title = item["title"]
            if platform and url:
                p.add_run(title).bold = True
                p.runs[-1].font.size = Pt(10)
                p.runs[-1].font.color.rgb = BLACK
                p.add_run("  (").font.size = Pt(9)
                self._add_hyperlink(p, platform, url, font_size=9)
                p.add_run(")").font.size = Pt(9)
            else:
                t = p.add_run(title)
                t.bold = True
                t.font.size = Pt(10)
                t.font.color.rgb = BLACK

            if item.get("description"):
                dp = doc.add_paragraph()
                dp.paragraph_format.space_after = Pt(2)
                dr = dp.add_run(item["description"])
                dr.font.size = Pt(9)
                dr.font.color.rgb = RGBColor(0x3C, 0x31, 0x32)

            doi_url = item.get("doi_url")
            for i, h in enumerate(item.get("highlights", [])):
                text = h[2:].lstrip() if h and h[0] in '«»' else h
                if i == 0 and doi_url:
                    bp = doc.add_paragraph()
                    bp.paragraph_format.space_before = Pt(0)
                    bp.paragraph_format.space_after = Pt(1)
                    bp.paragraph_format.left_indent = Inches(0.25)
                    bp.paragraph_format.first_line_indent = Inches(-0.15)
                    bullet = bp.add_run("• ")
                    bullet.font.size = Pt(9)
                    bullet.font.color.rgb = RGBColor(0x3C, 0x31, 0x32)
                    self._add_hyperlink(bp, text, doi_url, font_size=9)
                else:
                    self._add_bullet_docx(doc, text)

    def _build_experience_section_docx(self, doc):
        for exp in self.info["experience"]:
            right_stop = Inches(6.2)

            # Company | Location
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(5)
            p.paragraph_format.space_after = Pt(0)
            pPr = p._p.get_or_add_pPr()
            tabs = OxmlElement("w:tabs")
            tab = OxmlElement("w:tab")
            tab.set(qn("w:val"), "right")
            tab.set(qn("w:pos"), str(int(right_stop)))
            tabs.append(tab)
            pPr.append(tabs)
            cr = p.add_run(exp["company"])
            cr.bold = True
            cr.font.size = Pt(10)
            cr.font.color.rgb = BLACK
            tr = p.add_run("\t")
            tr.font.size = Pt(10)
            lr = p.add_run(exp["location"])
            lr.font.size = Pt(9)
            lr.font.color.rgb = RGBColor(0x3C, 0x31, 0x32)

            # Role | Period
            rp = doc.add_paragraph()
            rp.paragraph_format.space_before = Pt(0)
            rp.paragraph_format.space_after = Pt(3)
            rPr2 = rp._p.get_or_add_pPr()
            tabs2 = OxmlElement("w:tabs")
            tab2 = OxmlElement("w:tab")
            tab2.set(qn("w:val"), "right")
            tab2.set(qn("w:pos"), str(int(right_stop)))
            tabs2.append(tab2)
            rPr2.append(tabs2)
            rr = rp.add_run(exp["role"])
            rr.font.size = Pt(9)
            rr.font.color.rgb = RGBColor(0x3C, 0x31, 0x32)
            tr2 = rp.add_run("\t")
            tr2.font.size = Pt(9)
            dr = rp.add_run(exp["period"])
            dr.font.size = Pt(9)
            dr.font.color.rgb = RGBColor(0x3C, 0x31, 0x32)

            for h in exp["highlights"]:
                text = h[2:].lstrip() if h and h[0] in '«»' else h
                self._add_bullet_docx(doc, text)

    def _build_company_projects_section_docx(self, doc):
        for proj in self.info.get("company_projects", []):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(1)
            url = self.links.get(proj.get("url", ""), "")
            platform = proj.get("platform", "")
            title = proj["title"]
            tr = p.add_run(title)
            tr.bold = True
            tr.font.size = Pt(10)
            tr.font.color.rgb = BLACK
            if proj.get("company"):
                tr2 = p.add_run(f" - {proj['company']}")
                tr2.font.size = Pt(9)
                tr2.font.color.rgb = RGBColor(0x3C, 0x31, 0x32)
            if platform and url:
                sp = p.add_run("  (")
                sp.font.size = Pt(9)
                self._add_hyperlink(p, platform, url, font_size=9)
                ep = p.add_run(")")
                ep.font.size = Pt(9)

            for h in proj.get("highlights", []):
                text = h[2:].lstrip() if h and h[0] in '«»' else h
                self._add_bullet_docx(doc, text)

    def _build_skills_section_docx(self, doc):
        sections = self.info.get("skills_sections", [])
        if not sections:
            return

        for sec in sections:
            # Sub-section title
            sp = doc.add_paragraph()
            sp.paragraph_format.space_before = Pt(4)
            sp.paragraph_format.space_after = Pt(2)
            sr = sp.add_run(sec["title"])
            sr.bold = True
            sr.font.size = Pt(9)
            sr.font.color.rgb = BLACK

            if sec["type"] == "grid":
                items = sec["items"]
                cols = 3
                rows = (len(items) + cols - 1) // cols
                table = doc.add_table(rows=rows, cols=cols)
                table.autofit = True
                for i, s in enumerate(items):
                    row = i // cols
                    col = i % cols
                    cell = table.cell(row, col)
                    cell.text = ""
                    p = cell.paragraphs[0]
                    p.paragraph_format.space_before = Pt(1)
                    p.paragraph_format.space_after = Pt(1)
                    dot = p.add_run("• ")
                    dot.font.size = Pt(8.5)
                    dot.font.color.rgb = RGBColor(0x3C, 0x31, 0x32)
                    tr = p.add_run(s)
                    tr.font.size = Pt(8.5)
                    tr.font.color.rgb = RGBColor(0x3C, 0x31, 0x32)
                for row in table.rows:
                    for cell in row.cells:
                        for paragraph in cell.paragraphs:
                            paragraph.paragraph_format.space_before = Pt(0)
                            paragraph.paragraph_format.space_after = Pt(1)
                        tc = cell._tc
                        tcPr = tc.get_or_add_tcPr()
                        tcBorders = OxmlElement("w:tcBorders")
                        for edge in ["top", "left", "bottom", "right"]:
                            element = OxmlElement(f"w:{edge}")
                            element.set(qn("w:val"), "none")
                            element.set(qn("w:sz"), "0")
                            element.set(qn("w:space"), "0")
                            element.set(qn("w:color"), "auto")
                            tcBorders.append(element)
                        tcPr.append(tcBorders)
            elif sec["type"] == "bullets":
                for item in sec["items"]:
                    bp = doc.add_paragraph()
                    bp.paragraph_format.space_before = Pt(0)
                    bp.paragraph_format.space_after = Pt(1)
                    bp.paragraph_format.left_indent = Inches(0.25)
                    bp.paragraph_format.first_line_indent = Inches(-0.15)
                    dot = bp.add_run("•")
                    dot.font.size = Pt(8.5)
                    dot.font.color.rgb = RGBColor(0x3C, 0x31, 0x32)
                    tr = bp.add_run(item)
                    tr.font.size = Pt(8.5)
                    tr.font.color.rgb = RGBColor(0x3C, 0x31, 0x32)

    def _build_education_section_docx(self, doc):
        for edu in self.info["education"]:
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(3)
            pr = p.add_run(f"{edu['school']}")
            pr.bold = True
            pr.font.size = Pt(10)
            pr.font.color.rgb = BLACK

            dp = doc.add_paragraph()
            dp.paragraph_format.space_after = Pt(2)
            dr = dp.add_run(edu["degree"])
            dr.font.size = Pt(9)
            dr.font.color.rgb = RGBColor(0x3C, 0x31, 0x32)

    def _build_skills_section(self, doc):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(1)
        skills_display = []
        for s in self.info["skills"]:
            skills_display.append(s)
        label_run = p.add_run("Languages & Frameworks: ")
        label_run.bold = True
        label_run.font.size = Pt(9.5)
        val_run = p.add_run(", ".join(skills_display[:8]))
        val_run.font.size = Pt(9.5)

        p2 = doc.add_paragraph()
        label2 = p2.add_run("Architecture & Patterns: ")
        label2.bold = True
        label2.font.size = Pt(9.5)
        val2 = p2.add_run(", ".join(skills_display[8:16]))
        val2.font.size = Pt(9.5)

        p3 = doc.add_paragraph()
        label3 = p3.add_run("Tools & Platforms: ")
        label3.bold = True
        label3.font.size = Pt(9.5)
        val3 = p3.add_run(", ".join(skills_display[16:]))
        val3.font.size = Pt(9.5)

    def _build_portfolio_section(self, doc):
        for i, project in enumerate(self.info.get("latest_portfolio", [])):
            # Title with links
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(5)
            p.paragraph_format.space_after = Pt(1)
            title_run = p.add_run(project["title"])
            title_run.bold = True
            title_run.font.size = Pt(10.5)
            title_run.font.color.rgb = RGBColor(0x1A, 0x1A, 0x2E)

            # Links inline
            if project.get("links"):
                link_p = doc.add_paragraph()
                link_p.paragraph_format.space_after = Pt(1)
                link_idx = 0
                for platform, url in project["links"].items():
                    if link_idx > 0:
                        sep = link_p.add_run("  |  ")
                        sep.font.size = Pt(8.5)
                        sep.font.color.rgb = RGBColor(0x66, 0x66, 0x66)
                    self._add_hyperlink(link_p, platform, url, font_size=8.5)
                    link_idx += 1

            # Description
            if project.get("description"):
                desc_p = doc.add_paragraph()
                desc_p.paragraph_format.space_after = Pt(1)
                desc_run = desc_p.add_run(project["description"])
                desc_run.italic = True
                desc_run.font.size = Pt(9.5)

            # Highlights
            for h in project.get("highlights", []):
                bp = doc.add_paragraph()
                bp.paragraph_format.space_before = Pt(0)
                bp.paragraph_format.space_after = Pt(1)
                bp.paragraph_format.left_indent = Inches(0.2)
                bullet = bp.add_run("\u2022  ")
                bullet.font.size = Pt(9)
                bullet.font.color.rgb = RGBColor(0x66, 0x66, 0x66)
                text_run = bp.add_run(h)
                text_run.font.size = Pt(9.5)

    def _build_experience_section(self, doc):
        for exp in self.info["experience"]:
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(5)
            p.paragraph_format.space_after = Pt(1)
            role_run = p.add_run(f"{exp['role']}")
            role_run.bold = True
            role_run.font.size = Pt(10.5)
            role_run.font.color.rgb = RGBColor(0x1A, 0x1A, 0x2E)
            sep = p.add_run("  |  ")
            sep.font.size = Pt(9)
            comp_run = p.add_run(exp["company"])
            comp_run.font.size = Pt(10)
            comp_run.font.color.rgb = RGBColor(0x55, 0x55, 0x55)

            p2 = doc.add_paragraph()
            p2.paragraph_format.space_after = Pt(2)
            per_run = p2.add_run(f"{exp['period']}  |  {exp['location']}")
            per_run.font.size = Pt(9)
            per_run.font.color.rgb = RGBColor(0x77, 0x77, 0x77)
            per_run.italic = True

            for h in exp["highlights"]:
                bp = doc.add_paragraph()
                bp.paragraph_format.space_before = Pt(0)
                bp.paragraph_format.space_after = Pt(1)
                bp.paragraph_format.left_indent = Inches(0.2)
                bullet = bp.add_run("\u2022  ")
                bullet.font.size = Pt(9)
                bullet.font.color.rgb = RGBColor(0x66, 0x66, 0x66)
                text_run = bp.add_run(h)
                text_run.font.size = Pt(9.5)

    def _build_projects_section(self, doc):
        for project in self.info.get("projects", []):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(5)
            p.paragraph_format.space_after = Pt(1)
            title_run = p.add_run(project["title"])
            title_run.bold = True
            title_run.font.size = Pt(10.5)
            title_run.font.color.rgb = RGBColor(0x1A, 0x1A, 0x2E)
            if project.get("company"):
                sep_p = p.add_run("  -  ")
                comp_run = p.add_run(project["company"])
                comp_run.font.size = Pt(10)
                comp_run.font.color.rgb = RGBColor(0x55, 0x55, 0x55)

            if project.get("links"):
                link_p = doc.add_paragraph()
                link_p.paragraph_format.space_after = Pt(1)
                link_idx = 0
                for platform, url in project["links"].items():
                    if link_idx > 0:
                        sep = link_p.add_run("  |  ")
                        sep.font.size = Pt(8.5)
                        sep.font.color.rgb = RGBColor(0x66, 0x66, 0x66)
                    self._add_hyperlink(link_p, platform, url, font_size=8.5)
                    link_idx += 1

            for h in project.get("highlights", []):
                bp = doc.add_paragraph()
                bp.paragraph_format.space_before = Pt(0)
                bp.paragraph_format.space_after = Pt(1)
                bp.paragraph_format.left_indent = Inches(0.2)
                bullet = bp.add_run("\u2022  ")
                bullet.font.size = Pt(9)
                bullet.font.color.rgb = RGBColor(0x66, 0x66, 0x66)
                text_run = bp.add_run(h)
                text_run.font.size = Pt(9.5)

    def _build_education_section(self, doc):
        for edu in self.info["education"]:
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(3)
            deg_run = p.add_run(edu["degree"])
            deg_run.bold = True
            deg_run.font.size = Pt(10.5)
            if edu.get("school"):
                sep = p.add_run("  \u2014  ")
                sch_run = p.add_run(edu["school"])
                sch_run.font.size = Pt(10)
                sch_run.font.color.rgb = RGBColor(0x55, 0x55, 0x55)

            if edu.get("period") or edu.get("gpa"):
                p2 = doc.add_paragraph()
                p2.paragraph_format.space_after = Pt(1)
                parts = [x for x in [edu.get("period", ""), edu.get("gpa", "")] if x]
                if parts:
                    detail_run = p2.add_run("  |  ".join(parts))
                    detail_run.font.size = Pt(9)
                    detail_run.font.color.rgb = RGBColor(0x77, 0x77, 0x77)
                    detail_run.italic = True

    def build_pdf(self, output_path: str) -> str:
        class CVPDF(FPDF):
            def header(self):
                pass
            def footer(self):
                self.set_y(-15)
                self.set_font("Helvetica", "I", 7)
                self.set_text_color(150, 150, 150)
                self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

        TITLE_CLR = (164, 159, 159)
        SEC_CLR = (112, 104, 105)
        BODY_CLR = (60, 49, 50)

        pdf = CVPDF()
        pdf.alias_nb_pages()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_margins(14, 10, 14)
        pdf.add_font("Calibri", "", "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf")
        pdf.add_font("Calibri", "B", "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf")

        # --- NAME ---
        pdf.set_font("Calibri", "B", 18)
        pdf.set_text_color(*BODY_CLR)
        pdf.cell(0, 8, self.info["name"].upper(), align="C", new_x="LMARGIN", new_y="NEXT")

        # --- TITLE ---
        pdf.set_font("Calibri", "B", 11)
        pdf.set_text_color(*TITLE_CLR)
        pdf.cell(0, 5, self.info["title"], align="C", new_x="LMARGIN", new_y="NEXT")

        # --- CONTACT ---
        def pdf_link_cell(text, url, is_last=False):
            if url:
                pdf.set_text_color(0, 0, 0)
                pdf.set_draw_color(0, 0, 0)
                x0 = pdf.get_x()
                w = pdf.get_string_width(text)
                pdf.cell(w, 6, text, link=url)
                pdf.line(x0, pdf.get_y() + 4.5, x0 + w, pdf.get_y() + 4.5)
            else:
                pdf.set_text_color(*BODY_CLR)
                pdf.cell(pdf.get_string_width(text), 6, text)
            if not is_last:
                pdf.set_text_color(*BODY_CLR)
                sep_w = pdf.get_string_width("  -  ")
                pdf.cell(sep_w, 6, "  -  ")

        pdf.set_font("Calibri", "", 8.5)
        total_w = (pdf.get_string_width(self.info["location"]) +
                   pdf.get_string_width("  -  ") * 4 +
                   pdf.get_string_width("LinkedIn") +
                   pdf.get_string_width("GitHub") +
                   pdf.get_string_width(self.info["email"]) +
                   pdf.get_string_width(self.info["website"]))
        pdf.set_x((pdf.w - total_w) / 2)
        pdf_link_cell(self.info["location"], "")
        pdf_link_cell("LinkedIn", self._normalize_url(self.info["linkedin"]))
        pdf_link_cell("GitHub", self._normalize_url(self.info["github"]))
        pdf_link_cell(self.info["email"], f"mailto:{self.info['email']}")
        pdf_link_cell(self.info["website"], self._normalize_url(self.info["website"]), is_last=True)
        pdf.ln()

        self._pdf_hr(pdf)
        pdf.ln(1)

        def pdf_section(title):
            pdf.set_font("Calibri", "B", 11)
            pdf.set_text_color(*SEC_CLR)
            pdf.cell(0, 6, title.upper(), new_x="LMARGIN", new_y="NEXT")
            self._pdf_hr(pdf)
            pdf.ln(1)

        def pdf_bullet(sym, text):
            pdf.set_font("Calibri", "", 9)
            pdf.set_text_color(*BODY_CLR)
            x_start = pdf.l_margin + 3
            pdf.set_x(x_start)
            pdf.cell(5, 4.5, sym)
            pdf.multi_cell(pdf.w - pdf.l_margin - pdf.r_margin - x_start - 5, 4.5, text)
            pdf.set_x(x_start)

        # --- ABOUT ---
        pdf_section("About")
        pdf.set_font("Calibri", "", 9.5)
        pdf.set_text_color(*BODY_CLR)
        pdf.multi_cell(0, 4.8, self.info["summary"])
        pdf.ln(1)

        # --- COMPANY PROJECTS ---
        if self.info.get("company_projects"):
            pdf_section("Company Projects")
            for proj in self.info["company_projects"]:
                pdf.set_font("Calibri", "B", 10)
                pdf.set_text_color(0, 0, 0)
                title = proj["title"]
                extra = f" - {proj['company']}" if proj.get("company") else ""
                title_text = f"{title}{extra}"
                pdf.cell(pdf.get_string_width(title_text), 5, title_text)
                url = self.links.get(proj.get("url", ""), "")
                platform = proj.get("platform", "")
                if platform and url:
                    pdf.set_font("Calibri", "", 9)
                    sp_w = pdf.get_string_width(" ")
                    pdf.cell(sp_w, 5, " ")
                    plat_text = f"({platform})"
                    plat_w = pdf.get_string_width(plat_text)
                    x0 = pdf.get_x()
                    pdf.cell(plat_w, 5, plat_text, link=url)
                    pdf.set_draw_color(0, 0, 0)
                    pdf.line(x0, pdf.get_y() + 4, x0 + plat_w, pdf.get_y() + 4)
                pdf.ln()
                for h in proj.get("highlights", []):
                    text = h[2:].lstrip() if h and h[0] in '«»' else h
                    pdf_bullet("•", text)
                pdf.ln(2)

        # --- WORK EXPERIENCE ---
        pdf_section("Work Experience")
        for exp in self.info["experience"]:
            # Company | Location
            pdf.set_font("Calibri", "B", 10)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(pdf.w - pdf.l_margin - pdf.r_margin - 50, 5, exp["company"])
            pdf.set_font("Calibri", "", 9)
            pdf.set_text_color(*BODY_CLR)
            pdf.cell(50, 5, exp["location"], align="R", new_x="LMARGIN", new_y="NEXT")

            # Role | Period
            pdf.set_font("Calibri", "", 9)
            pdf.set_text_color(*BODY_CLR)
            pdf.cell(pdf.w - pdf.l_margin - pdf.r_margin - 50, 4.5, exp["role"])
            pdf.cell(50, 4.5, exp["period"], align="R", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)
            for h in exp["highlights"]:
                text = h[2:].lstrip() if h and h[0] in '«»' else h
                pdf_bullet("•", text)
            pdf.ln(2)

        # --- PERSONAL PORTFOLIO ---
        pdf_section("Personal Portfolio")
        for item in self.info.get("portfolio", []):
            pdf.set_font("Calibri", "B", 10)
            pdf.set_text_color(0, 0, 0)
            title_w = pdf.get_string_width(item["title"])
            pdf.cell(title_w, 5, item["title"])
            url = self.links.get(item.get("url", ""), "")
            platform = item.get("platform", "")
            if platform and url:
                pdf.set_font("Calibri", "", 9)
                sp_w = pdf.get_string_width(" ")
                pdf.cell(sp_w, 5, " ")
                plat_text = f"({platform})"
                plat_w = pdf.get_string_width(plat_text)
                x0 = pdf.get_x()
                pdf.cell(plat_w, 5, plat_text, link=url)
                pdf.set_draw_color(0, 0, 0)
                pdf.line(x0, pdf.get_y() + 4, x0 + plat_w, pdf.get_y() + 4)
            pdf.ln()
            if item.get("description"):
                pdf.set_font("Calibri", "", 9)
                pdf.set_text_color(*BODY_CLR)
                pdf.multi_cell(0, 4.5, item["description"])
            pdf.ln(1)
            doi_url = item.get("doi_url")
            for i, h in enumerate(item.get("highlights", [])):
                text = h[2:].lstrip() if h and h[0] in '«»' else h
                if i == 0 and doi_url:
                    pdf.set_font("Calibri", "", 9)
                    pdf.set_text_color(*BODY_CLR)
                    x_start = pdf.l_margin + 3
                    pdf.set_x(x_start)
                    pdf.cell(5, 4.5, "•")
                    pdf.multi_cell(pdf.w - pdf.l_margin - pdf.r_margin - x_start - 5, 4.5, text, link=doi_url)
                    pdf.set_x(x_start)
                else:
                    pdf_bullet("•", text)
            pdf.ln(4)

        # --- SKILLS ---
        pdf_section("Skills")
        sections = self.info.get("skills_sections", [])
        for sec in sections:
            pdf.set_font("Calibri", "B", 9)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 5, sec["title"], new_x="LMARGIN", new_y="NEXT")
            pdf.ln(1)

            if sec["type"] == "grid":
                pdf.set_font("Calibri", "", 8.5)
                pdf.set_text_color(*BODY_CLR)
                items = sec["items"]
                cols = 3
                col_w = (pdf.w - pdf.l_margin - pdf.r_margin) / cols
                for i, s in enumerate(items):
                    c = i % cols
                    if c == 0:
                        pdf.set_x(pdf.l_margin)
                    else:
                        pdf.set_x(pdf.l_margin + c * col_w)
                    pdf.cell(col_w, 4.5, f"• {s}")
                    if c == cols - 1:
                        pdf.ln(4.5)
                if len(items) % cols != 0:
                    pdf.ln(4.5)
            elif sec["type"] == "bullets":
                pdf.set_font("Calibri", "", 8.5)
                pdf.set_text_color(*BODY_CLR)
                for item in sec["items"]:
                    x_start = pdf.l_margin + 3
                    pdf.set_x(x_start)
                    pdf.cell(5, 4.5, "•")
                    pdf.multi_cell(pdf.w - pdf.l_margin - pdf.r_margin - x_start - 5, 4.5, item)
                    pdf.set_x(x_start)
            pdf.ln(2)

        # --- EDUCATION ---
        pdf_section("Education")
        for edu in self.info["education"]:
            pdf.set_font("Calibri", "B", 10)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 5, edu["school"], new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Calibri", "", 9)
            pdf.set_text_color(*BODY_CLR)
            pdf.cell(0, 4.5, edu["degree"], new_x="LMARGIN", new_y="NEXT")

        pdf.output(output_path)
        return output_path

    def _pdf_section_header(self, pdf, title):
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(26, 26, 46)
        pdf.cell(0, 7, title.upper(), new_x="LMARGIN", new_y="NEXT")
        self._pdf_hr(pdf)
        pdf.ln(2)

    def _pdf_hr(self, pdf):
        y = pdf.get_y()
        pdf.set_draw_color(51, 51, 51)
        pdf.set_line_width(0.3)
        pdf.line(15, y, pdf.w - 15, y)
        pdf.set_y(y + 1.5)

    def get_keyword_density(self) -> dict:
        text = self.info["summary"] + " "
        text += " ".join(self.info["skills"]) + " "
        text += " ".join(
            h for exp in self.info["experience"] for h in exp["highlights"]
        )
        text += " ".join(
            h for p in self.info.get("latest_portfolio", [])
            for h in p.get("highlights", [])
        )
        text += " ".join(
            h for p in self.info.get("projects", [])
            for h in p.get("highlights", [])
        )
        result = {}
        for kw in self.ATS_KEYWORDS:
            count = len(re.findall(re.escape(kw), text, re.IGNORECASE))
            result[kw] = count
        return result
