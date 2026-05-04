from bs4 import BeautifulSoup
import re


def extract(html):
    """
    Extract main content ONLY - footer removed from each page.
    Footer will be extracted once per job, not per URL.
    Returns: (main_content, "")
    """
    if not html:
        return "", ""

    try:
        soup = BeautifulSoup(html, "html.parser")

        # Remove footer content FIRST (before getting text)
        # Method 1: Remove <footer> tag
        for tag in soup(["footer", "script", "style", "noscript", "header", "nav", "aside"]):
            tag.decompose()
        
        # Method 2: Remove common footer class/id patterns
        footer_selectors = [".footer", "#footer", ".site-footer", ".copyright", 
                          "[class*='footer']", "[id*='footer']", ".site-info"]
        for selector in footer_selectors:
            for elem in soup.select(selector):
                elem.decompose()

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
    Note: extract() now already removes footer, this function kept for backward compatibility.
    """
    return extract(html)


def extract_page_metadata(html, url):
    """
    Extract page metadata: title, description
    """
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Title from <title> or <h1>
        title = soup.find('title')
        if not title:
            title = soup.find('h1')
        title_text = title.get_text().strip()[:200] if title else url.rsplit('/', 1)[-1].replace('-', ' ').title()
        
        # Meta description
        desc_tag = soup.find('meta', attrs={'name': 'description'})
        desc = desc_tag.get('content', '')[:500] if desc_tag else ''
        
        return {
            'title': title_text,
            'description': desc,
            'url': url
        }
    except Exception:
        return {'title': url.rsplit('/', 1)[-1], 'description': '', 'url': url}


def extract_clean_main_content(html, url):
    """
    Extract ONLY main content - aggressive cleanup for RAG
    """
    if not html:
        return {'content': '', 'metadata': extract_page_metadata(html, url)}
    
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove navigation, ads, footer, noise aggressively
        for tag in soup(['nav', 'header', 'footer', 'aside', 'script', 'style', 'noscript']):
            tag.decompose()
        
        # Remove common footer patterns
        for selector in [".footer", "#footer", ".site-footer", ".copyright", "[class*='footer']", "[id*='footer']"]:
            for elem in soup.select(selector):
                elem.decompose()
        
        # Remove social/share widgets
        for div in soup.find_all('div', class_=re.compile(r'share|social|widget|advert')):
            div.decompose()
        
        # Get structured text
        text = soup.get_text(separator='\n', strip=True)
        clean_content = clean_text(text)
        
        metadata = extract_page_metadata(html, url)
        
        return {
            'content': clean_content,
            'metadata': metadata
        }
    except Exception as e:
        metadata = extract_page_metadata(html, url)
        return {'content': '', 'metadata': metadata}


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
