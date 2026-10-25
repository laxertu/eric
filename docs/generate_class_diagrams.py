"""
Generates draw.io UML class diagrams of eric_sse.

Class members are read from the code, so diagrams only need regenerating when classes change.
Layout and relations other than inheritance are declared below, one entry per diagram.

Usage: python docs/generate_class_diagrams.py
"""
import ast
import html
import inspect
import re
import sys
import textwrap
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from eric_sse import connection, entities, facade, interfaces, listener, message, prefabs, queues, repository

OUTPUT_DIR = Path(__file__).resolve().parent

MODULE_COLORS = {
    'eric_sse.entities': ('#dae8fc', '#6c8ebf'),
    'eric_sse.prefabs': ('#d5e8d4', '#82b366'),
    'eric_sse.listener': ('#fff2cc', '#d6b656'),
    'eric_sse.message': ('#f8cecc', '#b85450'),
    'eric_sse.queues': ('#e1d5e7', '#9673a6'),
    'eric_sse.connection': ('#ffe6cc', '#d79b00'),
    'eric_sse.interfaces': ('#f5f5f5', '#666666'),
    'eric_sse.repository': ('#d0e0e3', '#45818e'),
    'eric_sse.facade': ('#fad9d5', '#ae4132'),
}

EDGE_STYLES = {
    'extends': 'endArrow=block;endFill=0;endSize=12;',
    'implements': 'endArrow=block;endFill=0;endSize=12;dashed=1;',
    'composition': 'startArrow=diamondThin;startFill=1;startSize=14;endArrow=none;',
    'aggregation': 'startArrow=diamondThin;startFill=0;startSize=14;endArrow=none;',
    'create': 'endArrow=open;endSize=10;dashed=1;',
    'uses': 'endArrow=open;endSize=10;dashed=1;',
}

ROW_HEIGHT = 20
TITLE_HEIGHT = 52
CHAR_WIDTH = 6.6
MIN_WIDTH = 180
H_GAP = 80
V_GAP = 90


@dataclass
class Diagram:
    file_name: str
    title: str
    # Rows of cells; a cell is a class, None for an empty slot. Columns are aligned across rows.
    layout: list[list[type | None]]
    # (source, target, kind, label). For composition / aggregation, source is the whole.
    relations: list[tuple[type, type, str, str]]
    # Classes drawn without members, as they are detailed in another diagram
    stubs: dict[type, str] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


def clean_annotation(annotation) -> str:
    text = inspect.formatannotation(annotation)
    text = re.sub(r'\b(?:[a-z_]+\.)+([A-Za-z_]\w*)', r'\1', text)
    text = text.replace('~', '').replace('NoneType', 'None')
    text = re.sub(r'\bOptional\[([^\[\]]+)]', r'\1 | None', text)
    return text


def format_signature(func) -> str:
    sig = inspect.signature(func)
    params = []
    for name, param in sig.parameters.items():
        if name in ('self', 'cls'):
            continue
        prefix = '**' if param.kind is param.VAR_KEYWORD else '*' if param.kind is param.VAR_POSITIONAL else ''
        if param.annotation is param.empty:
            params.append(f'{prefix}{name}')
        else:
            params.append(f'{prefix}{name}: {clean_annotation(param.annotation)}')
    result = f'({", ".join(params)})'
    if sig.return_annotation is not sig.empty and sig.return_annotation is not None:
        result += f': {clean_annotation(sig.return_annotation)}'
    return result


def visibility(name: str) -> str:
    return '-' if name.startswith('_') else '+'


def class_attributes(cls) -> list[str]:
    """Instance attributes assigned in __init__ and annotated class attributes, read from source."""
    tree = ast.parse(textwrap.dedent(inspect.getsource(cls)))
    class_node = tree.body[0]
    found: dict[str, str] = {}

    for node in class_node.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            found.setdefault(node.target.id, ast.unparse(node.annotation))

    init = next((n for n in class_node.body if isinstance(n, ast.FunctionDef) and n.name == '__init__'), None)
    if init:
        init_annotations = {a.arg: ast.unparse(a.annotation) for a in init.args.args if a.annotation}
        for node in ast.walk(init):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target] if isinstance(node, ast.AnnAssign) else []
            for target in targets:
                if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == 'self':
                    annotation = ast.unparse(node.annotation) if isinstance(node, ast.AnnAssign) else ''
                    if not annotation and isinstance(node.value, ast.Name):
                        annotation = init_annotations.get(node.value.id, '')
                    found.setdefault(target.attr, annotation)

    return [f'{visibility(n)} {n}: {a}' if a else f'{visibility(n)} {n}' for n, a in found.items()]


def class_members(cls) -> tuple[list[tuple[str, int]], list[tuple[str, int]]]:
    """Returns (attributes, methods) as (text, fontStyle) tuples. fontStyle 2 = italic (abstract), 4 = underline (static)."""
    attributes = [(a, 0) for a in class_attributes(cls)]
    methods = []
    for name, obj in cls.__dict__.items():
        if name.startswith('__') and name.endswith('__'):
            continue
        if isinstance(obj, property):
            style = 2 if getattr(obj.fget, '__isabstractmethod__', False) else 0
            returns = inspect.signature(obj.fget).return_annotation
            type_text = '' if returns is inspect.Signature.empty else f': {clean_annotation(returns)}'
            attributes.append((f'+ {name}{type_text} {{readOnly}}', style))
            continue
        static = isinstance(obj, (staticmethod, classmethod))
        func = obj.__func__ if static else obj
        if not inspect.isfunction(func):
            continue
        style = 4 if static else 0
        if getattr(func, '__isabstractmethod__', False):
            style |= 2
        suffix = ' {async}' if inspect.iscoroutinefunction(func) or inspect.isasyncgenfunction(func) else ''
        methods.append((f'{visibility(name)} {name}{format_signature(func)}{suffix}', style))
    return attributes, methods


def class_title(cls) -> tuple[str, list[str]]:
    """Returns (html title, plain text lines used for width estimation)."""
    name = cls.__name__
    params = getattr(cls, '__parameters__', ())
    if params:
        name += f'<{", ".join(p.__name__ for p in params)}>'
    stereotype = ''
    if name.endswith('Interface') or cls.__name__.endswith('Interface'):
        stereotype = '«interface»'
    elif inspect.isabstract(cls) or any(b.__name__ == 'ABC' for b in cls.__bases__):
        stereotype = '«abstract»'

    name_html = html.escape(name)
    if stereotype:
        name_html = f'<i>{name_html}</i>'
    parts = [stereotype] if stereotype else []
    parts.append(name_html)
    parts.append(f'<font style="font-size:9px;font-weight:normal">{cls.__module__}</font>')
    return '<br>'.join(parts), [stereotype, name, cls.__module__]


class DrawioBuilder:
    def __init__(self, diagram: Diagram):
        self.diagram = diagram
        self.root = ET.Element('root')
        ET.SubElement(self.root, 'mxCell', id='0')
        ET.SubElement(self.root, 'mxCell', id='1', parent='0')
        self.ids: dict[type, str] = {}
        self.boxes: dict[str, tuple[float, float, float, float]] = {}

    @staticmethod
    def _text_width(lines: list[str]) -> float:
        return max(MIN_WIDTH, max(len(line) for line in lines) * CHAR_WIDTH + 16)

    def _class_content(self, cls):
        title_html, title_lines = class_title(cls)
        if cls in self.diagram.stubs:
            attributes, methods = [(self.diagram.stubs[cls], 2)], []
        else:
            attributes, methods = class_members(cls)
        lines = title_lines + [t for t, _ in attributes + methods]
        return title_html, attributes, methods, self._text_width(lines)

    @staticmethod
    def _class_height(attributes, methods) -> float:
        return TITLE_HEIGHT + ROW_HEIGHT * max(1, len(attributes)) + 8 + ROW_HEIGHT * max(1, len(methods))

    def _add_text_row(self, parent_id: str, row_id: str, text: str, style: int, y: float, width: float):
        cell = ET.SubElement(self.root, 'mxCell', id=row_id, value=html.escape(text), vertex='1', parent=parent_id, style=(
            'text;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;spacingLeft=4;spacingRight=4;'
            f'overflow=hidden;rotatable=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;fontSize=11;html=1;fontStyle={style};'
        ))
        ET.SubElement(cell, 'mxGeometry', y=str(y), width=str(width), height=str(ROW_HEIGHT), attrib={'as': 'geometry'})

    def _add_class(self, cls, x: float, y: float, width: float):
        cell_id = f'c{len(self.ids)}'
        self.ids[cls] = cell_id
        title_html, attributes, methods, _ = self._class_content(cls)
        height = self._class_height(attributes, methods)
        fill, stroke = MODULE_COLORS.get(cls.__module__, ('#ffffff', '#000000'))
        dashed = 'dashed=1;' if cls in self.diagram.stubs else ''
        cell = ET.SubElement(self.root, 'mxCell', id=cell_id, value=title_html, vertex='1', parent='1', style=(
            f'swimlane;fontStyle=1;align=center;verticalAlign=top;childLayout=stackLayout;horizontal=1;startSize={TITLE_HEIGHT};'
            'horizontalStack=0;resizeParent=1;resizeParentMax=0;resizeLast=0;collapsible=1;marginBottom=0;whiteSpace=wrap;html=1;'
            f'fillColor={fill};strokeColor={stroke};swimlaneFillColor=#ffffff;{dashed}'
        ))
        ET.SubElement(cell, 'mxGeometry', x=str(x), y=str(y), width=str(width), height=str(height), attrib={'as': 'geometry'})
        self.boxes[cell_id] = (x, y, width, height)

        row_y = TITLE_HEIGHT
        for i, (text, style) in enumerate(attributes or [('', 0)]):
            self._add_text_row(cell_id, f'{cell_id}a{i}', text, style, row_y, width)
            row_y += ROW_HEIGHT
        separator = ET.SubElement(self.root, 'mxCell', id=f'{cell_id}s', value='', vertex='1', parent=cell_id, style=(
            'line;strokeWidth=1;fillColor=none;align=left;verticalAlign=middle;spacingTop=-1;spacingLeft=3;spacingRight=3;'
            'rotatable=0;labelPosition=right;points=[];portConstraint=eastwest;strokeColor=inherit;'
        ))
        ET.SubElement(separator, 'mxGeometry', y=str(row_y), width=str(width), height='8', attrib={'as': 'geometry'})
        row_y += 8
        for i, (text, style) in enumerate(methods or [('', 0)]):
            self._add_text_row(cell_id, f'{cell_id}m{i}', text, style, row_y, width)
            row_y += ROW_HEIGHT

    def _add_edge(self, index: int, source: str, target: str, kind: str, label: str):
        edge = ET.SubElement(self.root, 'mxCell', id=f'e{index}', value=html.escape(label), edge='1', parent='1',
                             source=source, target=target, style=(
                'edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;fontSize=10;labelBackgroundColor=#ffffff;' + EDGE_STYLES[kind]
            ))
        ET.SubElement(edge, 'mxGeometry', relative='1', attrib={'as': 'geometry'})

    def _add_legend(self, x: float, y: float):
        modules = sorted({cls.__module__ for cls in self.ids})
        lines = [f'<span style="background-color:{MODULE_COLORS[m][0]};border:1px solid {MODULE_COLORS[m][1]}">&nbsp;&nbsp;&nbsp;&nbsp;</span> {m}' for m in modules]
        lines += [
            '',
            '<b>Arrows</b>',
            'solid, hollow triangle: extends',
            'dashed, hollow triangle: implements an interface',
            'filled diamond: composition (diamond on the owner)',
            'hollow diamond: aggregation (diamond on the owner)',
            'dashed, open arrow: «create» / uses',
            '',
            '<i>italic</i>: abstract, <u>underlined</u>: static',
            'dashed border: detailed in the other diagram',
        ] + self.diagram.notes
        value = f'<b>{html.escape(self.diagram.title)}</b><br><br>' + '<br>'.join(lines)
        height = 40 + 16 * len(lines)
        legend = ET.SubElement(self.root, 'mxCell', id='legend', value=value, vertex='1', parent='1', style=(
            'text;html=1;align=left;verticalAlign=top;whiteSpace=wrap;spacing=8;fontSize=11;strokeColor=#999999;fillColor=#ffffff;'
        ))
        ET.SubElement(legend, 'mxGeometry', x=str(x), y=str(y), width='360', height=str(height), attrib={'as': 'geometry'})
        self.boxes['legend'] = (x, y, 360, height)

    def build(self) -> ET.Element:
        diagram = self.diagram
        columns = max(len(row) for row in diagram.layout)
        sizes = {}
        for row in diagram.layout:
            for cls in row:
                if cls is not None:
                    _, attributes, methods, width = self._class_content(cls)
                    sizes[cls] = (width, self._class_height(attributes, methods))

        column_widths = [
            max([sizes[row[c]][0] for row in diagram.layout if c < len(row) and row[c] is not None] or [MIN_WIDTH])
            for c in range(columns)
        ]
        y = 40.0
        for row in diagram.layout:
            x = 40.0
            for c, cls in enumerate(row):
                if cls is not None:
                    self._add_class(cls, x, y, column_widths[c])
                x += column_widths[c] + H_GAP
            y += max([sizes[cls][1] for cls in row if cls is not None] or [0]) + V_GAP

        relations = list(diagram.relations)
        for cls in self.ids:
            for base in cls.__bases__:
                if base in self.ids:
                    kind = 'implements' if base.__name__.endswith('Interface') else 'extends'
                    relations.append((cls, base, kind, ''))
        for i, (source, target, kind, label) in enumerate(relations):
            self._add_edge(i, self.ids[source], self.ids[target], kind, label)

        self._add_legend(40.0, y)

        mxfile = ET.Element('mxfile', host='app.diagrams.net', type='device')
        page = ET.SubElement(mxfile, 'diagram', id=diagram.file_name, name=diagram.title)
        model = ET.SubElement(page, 'mxGraphModel', dx='2000', dy='1200', grid='1', gridSize='10', guides='1', tooltips='1',
                              connect='1', arrows='1', fold='1', page='0', pageScale='1', math='0', shadow='0')
        model.append(self.root)
        return mxfile


def check(builder: DrawioBuilder):
    """Structural checks: edge ends exist, top level boxes do not overlap."""
    ids = {cell.get('id') for cell in builder.root}
    for cell in builder.root:
        if cell.get('edge'):
            assert cell.get('source') in ids and cell.get('target') in ids, cell.get('id')
    boxes = list(builder.boxes.items())
    for i, (a, (ax, ay, aw, ah)) in enumerate(boxes):
        for b, (bx, by, bw, bh) in boxes[i + 1:]:
            assert ax + aw <= bx or bx + bw <= ax or ay + ah <= by or by + bh <= ay, f'{a} overlaps {b}'


AbstractChannel = entities.AbstractChannel
ConnectionManager = entities._ConnectionManager
MessageQueueListener = listener.MessageQueueListener
Queue = queues.Queue
Connection = connection.Connection
ConnectionsFactory = connection.ConnectionsFactory
DefaultConnectionsFactory = connection.DefaultConnectionsFactory
InMemoryConnectionsFactory = connection.InMemoryConnectionsFactory

PUBSUB = Diagram(
    file_name='eric_sse_pubsub_diagram.drawio',
    title='eric_sse: publish-subscribe',
    layout=[
        [None, prefabs.SimpleDistributedApplicationChannel, prefabs.SSEChannel, prefabs.DataProcessingChannel],
        [ConnectionManager, None, AbstractChannel, None, ConnectionsFactory],
        [Connection, None, None, None, DefaultConnectionsFactory],
        [MessageQueueListener, prefabs.SimpleDistributedApplicationListener, Queue, queues.InMemoryQueue, InMemoryConnectionsFactory],
        [message.MessageContract, message.Message, message.SignedMessage, message.UniqueMessage],
    ],
    relations=[
        (AbstractChannel, ConnectionManager, 'composition', ''),
        (AbstractChannel, ConnectionsFactory, 'aggregation', 'connections_factory'),
        (ConnectionManager, Connection, 'aggregation', '0..*'),
        (Connection, MessageQueueListener, 'aggregation', 'listener'),
        (Connection, Queue, 'aggregation', 'queue'),
        (ConnectionsFactory, Connection, 'create', '«create»'),
        (Queue, message.MessageContract, 'uses', 'push / pop'),
        (MessageQueueListener, message.MessageContract, 'uses', 'on_message'),
        (AbstractChannel, message.MessageContract, 'uses', 'dispatch / adapt'),
        (message.UniqueMessage, message.MessageContract, 'aggregation', 'wraps'),
        (prefabs.SimpleDistributedApplicationListener, AbstractChannel, 'aggregation', 'channel'),
        (prefabs.SimpleDistributedApplicationListener, message.SignedMessage, 'create', '«create»'),
        (prefabs.SimpleDistributedApplicationChannel, prefabs.SimpleDistributedApplicationListener, 'uses', 'set_channel'),
    ],
    notes=[
        '',
        'Reserved message types (eric_sse.entities):',
        'MESSAGE_TYPE_CLOSED, MESSAGE_TYPE_END_OF_STREAM, MESSAGE_TYPE_INTERNAL_ERROR',
    ],
)

PERSISTENCE = Diagram(
    file_name='eric_sse_persistence_diagram.drawio',
    title='eric_sse: persistence layer',
    layout=[
        [None, facade.Facade, None, None, prefabs.SSEChannelRepository],
        [interfaces.ChannelRepositoryInterface, interfaces.ConnectionRepositoryInterface,
         interfaces.ListenerRepositoryInterface, interfaces.QueueRepositoryInterface, repository.AbstractChannelRepository],
        [ConnectionsFactory, repository.ConnectionRepository, repository.KvListenerRepository, repository.KvQueueRepository],
        [DefaultConnectionsFactory, repository.InMemoryStorage, repository.KvStorage, repository.PrefixedStorage],
        [InMemoryConnectionsFactory, Connection, MessageQueueListener, Queue, AbstractChannel],
    ],
    relations=[
        (facade.Facade, repository.AbstractChannelRepository, 'composition', 'repository'),
        (facade.Facade, repository.PrefixedStorage, 'create', '«create» one per namespace'),
        (facade.Facade, DefaultConnectionsFactory, 'create', '«create»'),
        (interfaces.ChannelRepositoryInterface, interfaces.ConnectionRepositoryInterface, 'aggregation', 'connections_repository'),
        (interfaces.ChannelRepositoryInterface, ConnectionsFactory, 'aggregation', 'connections_factory'),
        (interfaces.ConnectionRepositoryInterface, interfaces.ListenerRepositoryInterface, 'aggregation', 'listeners_repository'),
        (interfaces.ConnectionRepositoryInterface, interfaces.QueueRepositoryInterface, 'aggregation', 'queues_repository'),
        (repository.AbstractChannelRepository, repository.KvStorage, 'aggregation', 'storage'),
        (repository.ConnectionRepository, repository.KvStorage, 'aggregation', 'storage'),
        (repository.KvListenerRepository, repository.KvStorage, 'aggregation', 'storage'),
        (repository.KvQueueRepository, repository.KvStorage, 'aggregation', 'storage'),
        (repository.PrefixedStorage, repository.KvStorage, 'aggregation', 'wraps'),
        (interfaces.ChannelRepositoryInterface, AbstractChannel, 'uses', 'load / persist'),
        (interfaces.ConnectionRepositoryInterface, Connection, 'uses', 'load / persist'),
        (interfaces.ListenerRepositoryInterface, MessageQueueListener, 'uses', 'load / persist'),
        (interfaces.QueueRepositoryInterface, Queue, 'uses', 'load / persist'),
        (ConnectionsFactory, Connection, 'create', '«create»'),
    ],
    stubs={
        AbstractChannel: 'see publish-subscribe diagram',
        MessageQueueListener: 'see publish-subscribe diagram',
        Queue: 'see publish-subscribe diagram',
    },
)


def main():
    for diagram in (PUBSUB, PERSISTENCE):
        builder = DrawioBuilder(diagram)
        mxfile = builder.build()
        check(builder)
        ET.indent(mxfile)
        path = OUTPUT_DIR / diagram.file_name
        ET.ElementTree(mxfile).write(path, encoding='utf-8', xml_declaration=False)
        print(f'{path}: {len(builder.ids)} classes, {sum(1 for c in builder.root if c.get("edge"))} relations')


if __name__ == '__main__':
    main()
