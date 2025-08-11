import pytest
from llama_index.core.llms.mock import MockLLM
from llama_index.core.node_parser.relational.unstructured_element import (
    UnstructuredElementNodeParser,
)
from llama_index.core.schema import Document, IndexNode, TextNode

try:
    from unstructured.partition.html import partition_html
except ImportError:
    partition_html = None  # type: ignore

try:
    from lxml import html
except ImportError:
    html = None  # type: ignore


@pytest.mark.skipif(partition_html is None, reason="unstructured not installed")
@pytest.mark.skipif(html is None, reason="lxml not installed")
def test_html_table_extraction() -> None:
    test_data = Document(
        text="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Page</title>
    </head>
    <body>
        <table>
            <tr>
                <td>My title center</td>
            </tr>
            <tr>
                <td>Design Website like its 2000</td>
                <td>Yeah!</td>
            </tr>
        </table>
        <p>
            Test paragraph
        </p>
        <table>
            <tr>
                <td>Year</td>
                <td>Benefits</td>
            </tr>
            <tr>
               <td>2020</td>
                <td>12,000</td>
            </tr>
            <tr>
               <td>2021</td>
                <td>10,000</td>
            </tr>
            <tr>
               <td>2022</td>
                <td>130,000</td>
            </tr>
        </table>
        <table>
            <tr>
                <td>Year</td>
                <td>Benefits</td>
            </tr>
            <tr>
               <td>2020</td>
                <td>12,000</td>
            </tr>
            <tr>
               <td>2021</td>
                <td>10,000</td>
                <td>2021</td>
                <td>10,000</td>
            </tr>
            <tr>
               <td>2022</td>
                <td>130,000</td>
            </tr>
        </table>
         <table>
            <tr>
                <td>age</td>
                <td>group</td>
            </tr>
            <tr>
               <td>yellow</td>
                <td></td>
            </tr>
        </table>
    </body>
    </html>
        """
    )

    node_parser = UnstructuredElementNodeParser(llm=MockLLM())

    nodes = node_parser.get_nodes_from_documents([test_data])

    assert len(nodes) == 6
    assert isinstance(nodes[0], TextNode)
    assert isinstance(nodes[1], IndexNode)
    assert isinstance(nodes[2], TextNode)
    assert isinstance(nodes[3], TextNode)
    assert isinstance(nodes[4], IndexNode)
    assert isinstance(nodes[5], TextNode)
