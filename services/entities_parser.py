# services/entities_parser.py

from html.parser import HTMLParser
from typing import List, Tuple
from aiogram.types import MessageEntity

class HTMLToEntitiesParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = ""
        self.entities = []
        self.current_position = 0
        self.open_tags = []

    def handle_starttag(self, tag, attrs):
        if tag == 'b' or tag == 'strong':
            self.open_tags.append(('bold', self.current_position))
        elif tag == 'i' or tag == 'em':
            self.open_tags.append(('italic', self.current_position))
        elif tag == 'u':
            self.open_tags.append(('underline', self.current_position))
        elif tag == 's':
            self.open_tags.append(('strikethrough', self.current_position))
        elif tag == 'a':
            href = next((v for k, v in attrs if k == 'href'), None)
            if href:
                self.open_tags.append(('text_link', self.current_position, href))

    def handle_endtag(self, tag):
        if self.open_tags:
            start_tag, start_pos, *extra = self.open_tags.pop()
            if (tag == 'b' and start_tag == 'bold') or \
               (tag == 'i' and start_tag == 'italic') or \
               (tag == 'u' and start_tag == 'underline') or \
               (tag == 's' and start_tag == 'strikethrough') or \
               (tag == 'a' and start_tag == 'text_link'):
                self.entities.append(
                    MessageEntity(
                        type=start_tag,
                        offset=start_pos,
                        length=self.current_position - start_pos,
                        url=extra[0] if extra else None
                    )
                )

    def handle_data(self, data):
        self.text += data
        self.current_position += len(data)

    def handle_entityref(self, name):
        self.text += self.unescape(f'&{name};')
        self.current_position += 1

    def handle_charref(self, name):
        self.text += self.unescape(f'&#{name};')
        self.current_position += 1

def html_to_entities(html_text: str) -> Tuple[str, List[MessageEntity]]:
    parser = HTMLToEntitiesParser()
    parser.feed(html_text)
    return parser.text, parser.entities

# Example usage:
# text, entities = html_to_entities("<b>Bold</b> and <i>italic</i> text with <a href='https://example.com'>link</a>")
