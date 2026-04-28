from bs4 import BeautifulSoup
import re


def extract(html):
    if not html:
        return "", ""

    try:
        soup = BeautifulSoup(html, "html.parser")

        # remove unwanted tags
        for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "aside"]):
            tag.decompose()

        # Remove PHP error messages and debug output
        for comment in soup.find_all(string=re.compile(r'PHP Error|Notice:|Warning:|Fatal Error')):
            if comment.parent:
                comment.parent.decompose()
        
        for pre in soup.find_all("pre"):
            pre.decompose()

        # Get text with better structure preservation
        text = soup.get_text(separator="\n")

        # Clean up the text
        lines = []
        for line in text.split("\n"):
            # Skip PHP errors, warnings, notices and stack traces
            if re.search(r'PHP Error|Notice:|Warning:|Fatal Error|Undefined variable|Backtrace:|Severity:|Filename:|Line Number:|Function:|Message:', line, re.IGNORECASE):
                continue
            # Skip stack trace lines
            if re.search(r'^/home/|application/controllers|application/views', line):
                continue
            line = line.strip()
            if len(line) > 10:
                lines.append(line)

        text = "\n".join(lines)
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)

        return text.strip(), ""

    except Exception:
        return "", ""


def extract_with_footer(html):
    """
    Extract main content and footer separately.
    Returns: (main_content, footer_content)
    """
    if not html:
        return "", ""

    try:
        soup = BeautifulSoup(html, "html.parser")

        # Find footer - try multiple approaches
        footer_content = ""
        main_content = ""
        
        # Method 1: Find footer by tag
        footer_tag = soup.find("footer")
        if footer_tag:
            # Remove footer from soup to get main content
            footer_text = footer_tag.get_text(separator="\n")
            footer_tag.decompose()
            footer_content = clean_text(footer_text)
        
        # Also check for common footer class/id patterns
        for selector in [".footer", "#footer", ".site-footer", ".copyright"]:
            footer_elem = soup.select_one(selector)
            if footer_elem and not footer_content:
                footer_text = footer_elem.get_text(separator="\n")
                footer_elem.decompose()
                footer_content = clean_text(footer_text)

        # Get remaining text as main content
        main_text = soup.get_text(separator="\n")
        main_content = clean_text(main_text)

        return main_content, footer_content

    except Exception as e:
        return "", ""


def clean_text(text):
    """Clean extracted text by removing noise and formatting"""
    lines = []
    for line in text.split("\n"):
        # Skip PHP errors, warnings, notices and stack traces
        if re.search(r'PHP Error|Notice:|Warning:|Fatal Error|Undefined variable|Backtrace:|Severity:|Filename:|Line Number:|Function:|Message:', line, re.IGNORECASE):
            continue
        # Skip stack trace lines
        if re.search(r'^/home/|application/controllers|application/views', line):
            continue
        line = line.strip()
        if len(line) > 10:
            lines.append(line)
    
    text = "\n".join(lines)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()