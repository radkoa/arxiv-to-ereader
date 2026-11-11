"""Tests for the parser module."""

from arxiv_to_ereader.parser import parse_paper


class TestParsePaper:
    """Tests for parse_paper function."""

    def test_parse_title(self, sample_html: str, sample_paper_id: str) -> None:
        """Test extracting paper title."""
        paper = parse_paper(sample_html, sample_paper_id)
        assert paper.title == "A Sample Paper on Machine Learning"

    def test_parse_authors(self, sample_html: str, sample_paper_id: str) -> None:
        """Test extracting authors."""
        paper = parse_paper(sample_html, sample_paper_id)
        assert len(paper.authors) == 2
        assert "John Doe" in paper.authors
        assert "Jane Smith" in paper.authors

    def test_parse_abstract(self, sample_html: str, sample_paper_id: str) -> None:
        """Test extracting abstract."""
        paper = parse_paper(sample_html, sample_paper_id)
        assert "main contributions" in paper.abstract

    def test_parse_date(self, sample_html: str, sample_paper_id: str) -> None:
        """Test extracting date."""
        paper = parse_paper(sample_html, sample_paper_id)
        assert paper.date == "2024-02-15"

    def test_parse_sections(self, sample_html: str, sample_paper_id: str) -> None:
        """Test extracting sections."""
        paper = parse_paper(sample_html, sample_paper_id)

        # Should have main sections
        section_titles = [s.title for s in paper.sections]
        assert any("Introduction" in t for t in section_titles)
        assert any("Methods" in t for t in section_titles)
        assert any("Results" in t for t in section_titles)

    def test_parse_subsections(self, sample_html: str, sample_paper_id: str) -> None:
        """Test extracting subsections with correct levels."""
        paper = parse_paper(sample_html, sample_paper_id)

        # Find the subsection
        subsections = [s for s in paper.sections if s.level == 2]
        assert len(subsections) > 0
        assert any("Data Collection" in s.title for s in subsections)

    def test_parse_figures(self, sample_html: str, sample_paper_id: str) -> None:
        """Test extracting figures."""
        paper = parse_paper(sample_html, sample_paper_id)

        assert len(paper.figures) == 1
        fig = paper.figures[0]
        assert fig.id == "fig1"
        assert "Results comparison" in fig.caption
        assert fig.image_url is not None

    def test_parse_references(self, sample_html: str, sample_paper_id: str) -> None:
        """Test extracting references section."""
        paper = parse_paper(sample_html, sample_paper_id)

        assert paper.references_html is not None
        assert "Author A" in paper.references_html

    def test_paper_id_preserved(self, sample_html: str, sample_paper_id: str) -> None:
        """Test that paper ID is preserved."""
        paper = parse_paper(sample_html, sample_paper_id)
        assert paper.id == sample_paper_id

    def test_base_url_set(self, sample_html: str, sample_paper_id: str) -> None:
        """Test that base URL is set correctly."""
        paper = parse_paper(sample_html, sample_paper_id)
        assert paper.base_url == f"https://arxiv.org/html/{sample_paper_id}"

    def test_relative_image_url_resolved_like_browser(self) -> None:
        """Test that arXiv's version-prefixed relative srcs resolve against /html/."""
        html = '''<html><body><article class="ltx_document">
        <figure class="ltx_figure"><img src="2402.08954v1/x1.png" class="ltx_graphics"/>
        <figcaption>Figure 1</figcaption></figure></article></body></html>'''
        paper = parse_paper(html, "2402.08954")
        assert paper.all_images["2402.08954v1/x1.png"] == (
            "https://arxiv.org/html/2402.08954v1/x1.png"
        )

    def test_minimal_html(self, minimal_html: str) -> None:
        """Test parsing minimal HTML without LaTeXML structure."""
        paper = parse_paper(minimal_html, "0000.00000")

        # Should fall back to basic extraction
        assert "Minimal Paper" in paper.title
        assert paper.id == "0000.00000"


class TestParserEdgeCases:
    """Edge case tests for the parser."""

    def test_empty_authors(self) -> None:
        """Test handling HTML with no authors."""
        html = """
        <html>
        <head><title>No Authors Paper</title></head>
        <body>
            <h1 class="ltx_title ltx_title_document">Paper Without Authors</h1>
        </body>
        </html>
        """
        paper = parse_paper(html, "0000.00000")
        assert paper.authors == []

    def test_authors_with_email(self) -> None:
        """Test extracting authors when email is embedded in personname."""
        html = """
        <html>
        <head><title>Test</title></head>
        <body>
            <div class="ltx_authors">
                <span class="ltx_personname">Test Team
                    <br/><span class="ltx_text">team@example.com</span>
                </span>
            </div>
        </body>
        </html>
        """
        paper = parse_paper(html, "0000.00000")
        assert len(paper.authors) == 1
        assert paper.authors[0] == "Test Team"
        assert "@" not in paper.authors[0]

    def test_empty_abstract(self) -> None:
        """Test handling HTML with no abstract."""
        html = """
        <html>
        <head><title>No Abstract</title></head>
        <body>
            <h1 class="ltx_title ltx_title_document">Paper Without Abstract</h1>
        </body>
        </html>
        """
        paper = parse_paper(html, "0000.00000")
        assert paper.abstract == ""

    def test_no_sections(self) -> None:
        """Test handling HTML with no sections."""
        html = """
        <html>
        <head><title>No Sections</title></head>
        <body>
            <article class="ltx_document">
                <h1>Title</h1>
                <p>Just a paragraph.</p>
            </article>
        </body>
        </html>
        """
        paper = parse_paper(html, "0000.00000")
        # Should either have no sections or a main content section
        assert isinstance(paper.sections, list)


class TestInfoBoxes:
    """Tests for converting LaTeXML tcolorbox SVGs to HTML."""

    BOX_HTML = """<html><body><article class="ltx_document">
<section class="ltx_section" id="S1"><h2 class="ltx_title">Intro</h2>
<div class="ltx_para"><span class="ltx_inline-block">
<svg class="ltx_picture" viewBox="0 0 680 100">
<g fill="#000000"><g fill="#994D00" fill-opacity="1.0"><path d="M 0 0"></path></g>
<g fill="#FFF9F2" fill-opacity="1.0"><path d="M 1 1"></path></g>
<g fill-opacity="1.0"><foreignobject width="575" height="12">
<span class="ltx_foreignobject_container"><span class="ltx_foreignobject_content">
<span class="ltx_inline-block ltx_minipage" style="width:41em;">
<span class="ltx_p"><span class="ltx_text ltx_font_bold">Box Title</span></span>
</span></span></span>
</foreignobject></g>
<g fill-opacity="1.0"><foreignobject width="662" height="40">
<span class="ltx_foreignobject_container"><span class="ltx_foreignobject_content">
<span class="ltx_inline-block ltx_minipage" style="width:47em;">
<span class="ltx_p">Box body text.</span></span></span></span></foreignobject></g>
</g></svg></span></div></section></article></body></html>"""

    def test_box_svg_becomes_html(self) -> None:
        """Test that the SVG box is replaced by a titled HTML block with its colors."""
        from bs4 import BeautifulSoup

        paper = parse_paper(self.BOX_HTML, "2402.08954")
        soup = BeautifulSoup(paper.sections[0].content, "lxml")

        assert soup.find("svg") is None
        box = soup.select_one(".info-box")
        assert box is not None
        assert "#FFF9F2" in box["style"]
        title = box.select_one(".info-box-title")
        assert title.get_text(strip=True) == "Box Title"
        assert "#994D00" in title["style"]
        assert box.select_one(".info-box-body").get_text(strip=True) == "Box body text."

    def test_box_with_minipage_foreignobject(self) -> None:
        """Test a box whose body foreignobject is itself the minipage (e.g. holding a table)."""
        from bs4 import BeautifulSoup

        html = self.BOX_HTML.replace(
            '<foreignobject width="662" height="40">',
            '<foreignobject class="ltx_minipage" width="662" height="40">',
        ).replace(
            '<span class="ltx_inline-block ltx_minipage" style="width:47em;">\n'
            '<span class="ltx_p">Box body text.</span></span>',
            '<table class="ltx_tabular"><tr><td>Box body text.</td></tr></table>',
        )
        assert "ltx_tabular" in html

        paper = parse_paper(html, "2402.08954")
        soup = BeautifulSoup(paper.sections[0].content, "lxml")

        assert soup.find("svg") is None
        assert soup.select_one(".info-box-body table") is not None
