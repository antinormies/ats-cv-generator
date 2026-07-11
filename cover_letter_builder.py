from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import os


class CoverLetterBuilder:
    def __init__(self, info: dict):
        self.info = info

    def _normalize_url(self, url: str) -> str:
        if url.startswith("mailto:"):
            return url
        if not url.startswith(("http://", "https://")):
            return f"https://{url}"
        return url

    def _add_hyperlink(self, paragraph, text: str, url: str, font_size=9):
        url = self._normalize_url(url)
        part = paragraph.part
        r_id = part.relate_to(url, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink", is_external=True)
        hyperlink = OxmlElement("w:hyperlink")
        hyperlink.set(qn("r:id"), r_id)
        new_run = OxmlElement("w:r")
        rPr = OxmlElement("w:rPr")
        c = OxmlElement("w:color")
        c.set(qn("w:val"), "2255CC")
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

    def build(self, output_path: str, body: str, company: str = "", recipient: str = "") -> str:
        doc = Document()
        section = doc.sections[0]
        section.top_margin = Inches(0.5)
        section.bottom_margin = Inches(0.5)
        section.left_margin = Inches(0.7)
        section.right_margin = Inches(0.7)

        style = doc.styles["Normal"]
        font = style.font
        font.name = "Calibri"
        font.size = Pt(10.5)
        font.color.rgb = RGBColor(0x33, 0x33, 0x33)
        style.paragraph_format.space_after = Pt(3)
        style.paragraph_format.space_before = Pt(0)
        style.paragraph_format.line_spacing = 1.08

        # --- HEADER (same as CV) ---
        name_p = doc.add_paragraph()
        name_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        name_run = name_p.add_run(self.info["name"])
        name_run.bold = True
        name_run.font.size = Pt(20)
        name_run.font.color.rgb = RGBColor(0x1A, 0x1A, 0x2E)

        title_p = doc.add_paragraph()
        title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title_run = title_p.add_run(self.info["title"])
        title_run.font.size = Pt(11)
        title_run.font.color.rgb = RGBColor(0x55, 0x55, 0x55)

        contact_p = doc.add_paragraph()
        contact_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        contact_items = []
        if self.info["location"]:
            r = contact_p.add_run(self.info["location"])
            r.font.size = Pt(9)
            r.font.color.rgb = RGBColor(0x66, 0x66, 0x66)
            contact_items.append(True)
        if self.info["linkedin"]:
            if contact_items:
                r = contact_p.add_run("  \u2022  ")
                r.font.size = Pt(9)
                r.font.color.rgb = RGBColor(0x66, 0x66, 0x66)
            self._add_hyperlink(contact_p, "LinkedIn", self.info["linkedin"], font_size=9)
            contact_items.append(True)
        if self.info["github"]:
            if contact_items:
                r = contact_p.add_run("  \u2022  ")
                r.font.size = Pt(9)
                r.font.color.rgb = RGBColor(0x66, 0x66, 0x66)
            self._add_hyperlink(contact_p, "GitHub", self.info["github"], font_size=9)
            contact_items.append(True)
        if self.info["email"]:
            if contact_items:
                r = contact_p.add_run("  \u2022  ")
                r.font.size = Pt(9)
                r.font.color.rgb = RGBColor(0x66, 0x66, 0x66)
            self._add_hyperlink(contact_p, self.info["email"], f"mailto:{self.info['email']}", font_size=9)
            contact_items.append(True)
        if self.info["website"]:
            if contact_items:
                r = contact_p.add_run("  \u2022  ")
                r.font.size = Pt(9)
                r.font.color.rgb = RGBColor(0x66, 0x66, 0x66)
            self._add_hyperlink(contact_p, self.info["website"], self.info["website"], font_size=9)
            contact_items.append(True)

        self._add_hr(doc)

        # --- DATE ---
        from datetime import date
        date_p = doc.add_paragraph()
        date_p.paragraph_format.space_before = Pt(8)
        date_p.paragraph_format.space_after = Pt(6)
        date_run = date_p.add_run(date.today().strftime("%B %d, %Y"))
        date_run.font.size = Pt(10)

        # --- RECIPIENT ---
        if recipient:
            rp = doc.add_paragraph()
            rp.paragraph_format.space_after = Pt(1)
            rr = rp.add_run(recipient)
            rr.font.size = Pt(10)
        if company:
            cp = doc.add_paragraph()
            cp.paragraph_format.space_after = Pt(6)
            cr = cp.add_run(company)
            cr.font.size = Pt(10)

        # --- SUBJECT ---
        subj_p = doc.add_paragraph()
        subj_p.paragraph_format.space_after = Pt(6)
        subj_r = subj_p.add_run(f"Re: Application for {self.info['title']} Position")
        subj_r.bold = True
        subj_r.font.size = Pt(10.5)

        # --- SALUTATION ---
        sal_p = doc.add_paragraph()
        sal_p.paragraph_format.space_after = Pt(6)
        sal_r = sal_p.add_run("Dear Hiring Manager,")
        sal_r.font.size = Pt(10.5)

        # --- BODY ---
        paragraphs = [p.strip() for p in body.split("\n") if p.strip()]
        for para_text in paragraphs:
            bp = doc.add_paragraph()
            bp.paragraph_format.space_after = Pt(6)
            bp.paragraph_format.line_spacing = 1.15
            br = bp.add_run(para_text)
            br.font.size = Pt(10.5)

        # --- CLOSING ---
        close_p = doc.add_paragraph()
        close_p.paragraph_format.space_before = Pt(6)
        close_p.paragraph_format.space_after = Pt(2)
        close_r = close_p.add_run("Best regards,")
        close_r.font.size = Pt(10.5)

        name_close = doc.add_paragraph()
        name_close.paragraph_format.space_after = Pt(1)
        ncr = name_close.add_run(self.info["name"])
        ncr.bold = True
        ncr.font.size = Pt(10.5)

        if self.info.get("phone"):
            phone_p = doc.add_paragraph()
            phone_p.paragraph_format.space_after = Pt(1)
            ph = phone_p.add_run(self.info["phone"])
            ph.font.size = Pt(9.5)
            ph.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

        if self.info.get("email"):
            email_p = doc.add_paragraph()
            email_p.paragraph_format.space_after = Pt(1)
            em = email_p.add_run(self.info["email"])
            em.font.size = Pt(9.5)
            em.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

        doc.save(output_path)
        return output_path
