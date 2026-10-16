"""Targeted security checks for the intentionally restricted SVG subset."""
import unittest
from svg_avatar import validate_svg


def svg(body='', attrs=''):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" {attrs}>{body}</svg>'.encode()


class SVGTests(unittest.TestCase):
    def test_static_artwork(self):
        validate_svg(svg('<defs><linearGradient id="g"><stop offset="0%" stop-color="#fff"/></linearGradient></defs><path d="M0 0L256 256" stroke="url(#g)"/>'))
        validate_svg(b'<?xml version="1.0" encoding="UTF-8"?>' + svg('<circle cx="128" cy="128" r="100" fill="#abc"/>'))

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
