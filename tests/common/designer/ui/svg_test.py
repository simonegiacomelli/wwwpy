import xml.etree.ElementTree as ET

from wwwpy.common.designer.ui.svg import build_document, add_rounded_background2

# language=html
_svg1 = """
<!-- Copyright © 2000–2024 JetBrains s.r.o. -->
<svg width="20" height="20" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
  <path fill="none" stroke="#CED0D6" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M10 18.15v-15c0-.69-.56-1.25-1.25-1.25H3.12c-.69 0-1.25.56-1.25 1.25V16.9c0 .69.56 1.25 1.25 1.25h13.75c.69 0 1.25-.56 1.25-1.25v-5.62c0-.69-.56-1.25-1.25-1.25H1.88"/>
  <path fill="none" stroke="#CED0D6" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M18.96 4.58c.19.19.29.45.29.7s-.1.51-.29.7l-3.51 3.51a.984.984 0 0 1-1.4 0l-3.51-3.51a.984.984 0 0 1 0-1.4l3.51-3.51c.97-.97 1.69.28 4.91 3.51"/>
</svg>
"""


def test_namespace_ok():
    svg_str = add_rounded_background2(_svg1, '#00FF00')
    assert 'ns0:' not in svg_str
    assert 'xmlns="http://www.w3.org/2000/svg"' in svg_str


def test_change_stroke_color():
    def mutator(attrs):
        if 'stroke' in attrs:
            attrs['stroke'] = '#000000'

    result = build_document(_svg1, mutator)
    root = ET.fromstring(result)
    for elem in root.iter():
        if elem.tag.endswith('path'):
            assert elem.attrib['stroke'] == '#000000'

    assert 'ns0:' not in result
    assert 'xmlns="http://www.w3.org/2000/svg"' in result


def test_add_data_test_attribute():
    def mutator(attrs):
        attrs['data-test'] = '1'

    result = build_document(_svg1, mutator)
    root = ET.fromstring(result)
    for elem in root.iter():
        assert elem.attrib.get('data-test') == '1'

    assert 'ns0:' not in result
    assert 'xmlns="http://www.w3.org/2000/svg"' in result
