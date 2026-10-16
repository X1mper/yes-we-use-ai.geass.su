"""Targeted security checks for the intentionally restricted SVG subset."""
import unittest
from svg_avatar import normalize_svg, validate_svg
import xml.etree.ElementTree as ET


def svg(body='', attrs=''):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" {attrs}>{body}</svg>'.encode()


class SVGTests(unittest.TestCase):
    def test_static_artwork(self):
        validate_svg(svg('<defs><linearGradient id="g"><stop offset="0%" stop-color="#fff"/></linearGradient></defs><path d="M0 0L256 256" stroke="url(#g)"/>'))
        validate_svg(b'<?xml version="1.0" encoding="UTF-8"?>' + svg('<circle cx="128" cy="128" r="100" fill="#abc"/>'))

    def test_editor_export_normalized(self):
        source = b'<?xml version="1.0" encoding="UTF-8" standalone="no"?><svg viewBox="0 0 10 10"><path fill="red" style="fill:none;stroke:#ff006b;stroke-width:12" d="M0 0L10 10"/></svg>'
        normalized = normalize_svg(source)
        validate_svg(normalized)
        path = list(ET.fromstring(normalized))[0]
        self.assertEqual(path.attrib['fill'], 'none')
        self.assertEqual(path.attrib['stroke'], '#ff006b')
        self.assertEqual(path.attrib['stroke-width'], '12')
        self.assertNotIn('style', path.attrib)
        self.assertEqual(normalize_svg(normalized), normalized)

    def test_unsafe_styles_not_normalized(self):
        for style in ['fill:url(https://example.com/x)', 'fill:url(&#104;ttps://example.com/x)',
                      'fill:red!important', 'fill:/*x*/red', 'behavior:url(x)',
                      'stroke-width:expression(alert(1))', 'fill:red;unknown:1', 'fill']:
            with self.subTest(style=style), self.assertRaises(ValueError):
                normalize_svg(svg(f'<path style="{style}"/>'))
        for body in ['<script/>', '<foreignObject/>', '<image href="https://example.com"/>']:
            with self.assertRaises(ValueError):
                normalize_svg(svg(body))

    def test_active_and_external_content_rejected(self):
        cases = [svg('<script>alert(1)</script>'), svg(attrs='onload="alert(1)"'),
                 svg('<foreignObject/>'), svg('<style/>'), svg(attrs='style="fill:red"'),
                 svg('<animate attributeName="fill"/>'), svg('<image href="https://example.com/x"/>'),
                 svg('<use href="#x"/>'), svg('<a href="javascript:alert(1)"/>'),
                 svg('<path fill="url(https://example.com/x)"/>'),
                 svg('<path fill="url(&#104;ttps://example.com/x)"/>'),
                 svg('<path xmlns="http://www.w3.org/1999/xhtml"/>'),
                 svg('<path xml:base="https://example.com/"/>'),
                 b'<!DOCTYPE svg [<!ENTITY x "test">]>' + svg(),
                 b'<?xml-stylesheet href="https://example.com/x"?>' + svg(),
                 svg().decode().encode('utf-16'), b'<svg/>', b'<svg',
                 svg('<g/>' * 4096), svg() + b' ' * (1024 * 1024)]
        for payload in cases:
            with self.subTest(payload=payload[:100]), self.assertRaises(ValueError):
                validate_svg(payload)


if __name__ == '__main__':
    unittest.main()
