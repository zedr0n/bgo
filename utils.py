import html
import re

try:
    from .lib import fusion360utils as futil
except:
    futil = None

def remove_html_tags(html_content):
    if html_content == '':
        return html_content

    # Unescape HTML entities
    unescaped_content = html.unescape(html_content)
    
    # Remove HTML tags
    clean_text = re.sub(r'<[^>]+>', '', unescaped_content)
    
    return clean_text