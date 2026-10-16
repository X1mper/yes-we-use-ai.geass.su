"""Normalize plain editor exports, then enforce a strict static SVG subset."""
import re
import xml.etree.ElementTree as ET

NAMESPACE = 'http://www.w3.org/2000/svg'
ELEMENTS = set('svg g defs title desc path rect circle ellipse line polyline polygon linearGradient radialGradient stop clipPath'.split())
ATTRIBUTES = set('id viewBox width height x y x1 x2 y1 y2 cx cy r rx ry d points transform fill fill-opacity fill-rule stroke stroke-width stroke-opacity stroke-linecap stroke-linejoin stroke-miterlimit stroke-dasharray stroke-dashoffset opacity clip-path clip-rule gradientUnits gradientTransform spreadMethod offset stop-color stop-opacity fx fy fr preserveAspectRatio version'.split())
PAINT = re.compile(r'(?:#[0-9a-fA-F]{3,8}|[A-Za-z]+|(?:rgb|rgba|hsl|hsla)\([0-9.,% +\-]+\)|url\(#[A-Za-z_][A-Za-z0-9_.-]*\))')


STYLE_PROPERTIES = set('fill fill-opacity fill-rule stroke stroke-width stroke-opacity stroke-linecap stroke-linejoin stroke-miterlimit stroke-dasharray stroke-dashoffset opacity clip-path clip-rule stop-color stop-opacity'.split())


def parse_svg(data):
    if not 0 < len(data) <= 1024 * 1024:
        raise ValueError('SVG avatar: maximum size is 1 MiB')
    try:
        source = data.decode('utf-8-sig')
        # Reject DTD/entities and processing instructions before parsing. Only
        # an ordinary UTF-8 XML declaration is accepted (no alternate encoding).
        source = re.sub(r'^<\?xml\s+version=[\"\']1\.0[\"\'](?:\s+encoding=[\"\']UTF-8[\"\'])?(?:\s+standalone=[\"\'](?:yes|no)[\"\'])?\s*\?>', '', source, count=1, flags=re.I)
        if '<!' in source or '<?' in source:
            raise ValueError('SVG avatar: declarations, comments and processing instructions are unsupported')
        root = ET.fromstring(source)
    except (UnicodeError, ET.ParseError) as error:
        raise ValueError('SVG avatar: invalid UTF-8 XML') from error
    return root


def validate_svg(data):
    validate_tree(parse_svg(data))


def normalize_svg(data):
    root = parse_svg(data)
    implicit_namespace = root.tag == 'svg'
    for node in root.iter():
        if implicit_namespace and node.tag in ELEMENTS:
            node.tag = '{' + NAMESPACE + '}' + node.tag
        style = node.attrib.pop('style', None)
        if style is not None:
            # No general CSS parser: accept only literal presentation properties.
            # CSS escapes, comments, !important, functions other than validated
            # paints, and unknown properties fail closed rather than being dropped.
            for declaration in style.split(';'):
                if not declaration.strip():
                    continue
                key, separator, value = declaration.partition(':')
                key, value = key.strip(), value.strip()
                if not separator or key not in STYLE_PROPERTIES or not value:
                    raise ValueError('SVG avatar: unsupported inline style')
                if key not in {'fill', 'stroke', 'stop-color', 'clip-path'} and not re.fullmatch(r'[A-Za-z0-9_.,%+\- ]+', value):
                    raise ValueError('SVG avatar: unsupported style value')
                validate_tree(ET.Element('{' + NAMESPACE + '}svg', {key: value}))
                node.set(key, value)
    validate_tree(root)
    try:
        result = ET.tostring(root, encoding='utf-8')
    except RecursionError as error:
        raise ValueError('SVG avatar: excessive nesting') from error
    validate_svg(result)
    return result


def validate_tree(root):
    if root.tag != '{' + NAMESPACE + '}svg':
        raise ValueError('SVG avatar: expected SVG root with SVG namespace')
    nodes = list(root.iter())
    if len(nodes) > 4096:
        raise ValueError('SVG avatar: too many elements')
    for node in nodes:
        if node.tag not in {'{' + NAMESPACE + '}' + name for name in ELEMENTS}:
            raise ValueError(f'SVG avatar: unsupported element {node.tag}')
        for key, value in node.attrib.items():
            if key not in ATTRIBUTES:
                raise ValueError(f'SVG avatar: unsupported attribute {key}')
            if key in {'fill', 'stroke', 'stop-color', 'clip-path'}:
                if not PAINT.fullmatch(value):
                    raise ValueError('SVG avatar: unsupported paint or external reference')
            elif not re.fullmatch(r'[A-Za-z0-9_.,%+\-() #]*', value):
                raise ValueError(f'SVG avatar: unsupported value for {key}')
