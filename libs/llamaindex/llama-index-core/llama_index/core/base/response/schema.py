# libs/llamaindex/llama-index-core/llama_index/core/base/response/schema.py

"""Response schema."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Union,
    Callable,
    Awaitable,
    Generator,
    AsyncGenerator,
)

from typing import TYPE_CHECKING
from llama_index.core.async_utils import asyncio_run
from llama_index.core.bridge.pydantic import BaseModel, Field, ValidationError
from llama_index.core.schema import NodeWithScore
from llama_index.core.types import (
    TokenGen,
    TokenAsyncGen,
    RESPONSE_TEXT_TYPE,
    BasePydanticProgram,
)
from llama_index.core.utils import truncate_text

if TYPE_CHECKING:  # pragma: no cover
    from llama_index.core.prompts.base import BasePromptTemplate
    from llama_index.core.indices.prompt_helper import PromptHelper
    from llama_index.core.llms import LLM

logger = logging.getLogger(__name__)


class StructuredRefineResponse(BaseModel):
    """Response schema used for structured refining."""
    answer: str = Field(
        description="The answer for the given query, based on the context and not prior knowledge."
    )
    query_satisfied: bool = Field(
        description="True if there was enough context given to provide an answer that satisfies the query."
    )


@dataclass
class Response:
    """Response object. Returned if streaming=False."""
    response: Optional[str]
    source_nodes: List[NodeWithScore] = field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None

    def __str__(self) -> str:
        return self.response or "None"

    def get_formatted_sources(self, length: int = 100) -> str:
        texts = []
        for source_node in self.source_nodes:
            fmt_text_chunk = truncate_text(source_node.node.get_content(), length)
            node_id = source_node.node.node_id or "None"
            source_text = f"> Source (Node id: {node_id}): {fmt_text_chunk}"
            texts.append(source_text)
        return "\n\n".join(texts)


@dataclass
class PydanticResponse:
    """PydanticResponse object. Returned if streaming=False."""
    response: Optional[BaseModel]
    source_nodes: List[NodeWithScore] = field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None

    def __str__(self) -> str:
        return self.response.model_dump_json() if self.response else "None"

    def __getattr__(self, name: str) -> Any:
        if self.response is not None and name in self.response.model_dump():
            return getattr(self.response, name)
        return None

    def __post_init_post_parse__(self) -> None:
        return

    def get_formatted_sources(self, length: int = 100) -> str:
        texts = []
        for source_node in self.source_nodes:
            fmt_text_chunk = truncate_text(source_node.node.get_content(), length)
            node_id = source_node.node.node_id or "None"
            source_text = f"> Source (Node id: {node_id}): {fmt_text_chunk}"
            texts.append(source_text)
        return "\n\n".join(texts)

    def get_response(self) -> Response:
        response_txt = self.response.model_dump_json() if self.response else "None"
        return Response(response_txt, self.source_nodes, self.metadata)


@dataclass
class StreamingResponse:
    """StreamingResponse object. Returned if streaming=True."""
    response_gen: TokenGen
    source_nodes: List[NodeWithScore] = field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None
    response_txt: Optional[str] = None

    def __str__(self) -> str:
        if self.response_txt is None and self.response_gen is not None:
            response_txt = ""
            for text in self.response_gen:
                response_txt += text
            self.response_txt = response_txt
        return self.response_txt or "None"

    def get_response(self) -> Response:
        if self.response_txt is None and self.response_gen is not None:
            response_txt = ""
            for text in self.response_gen:
                response_txt += text
            self.response_txt = response_txt
        return Response(self.response_txt, self.source_nodes, self.metadata)

    def print_response_stream(self) -> None:
        if self.response_txt is None and self.response_gen is not None:
            response_txt = ""
            for text in self.response_gen:
                print(text, end="", flush=True)
                response_txt += text
            self.response_txt = response_txt
        else:
            print(self.response_txt)

    def get_formatted_sources(self, length: int = 100, trim_text: bool = True) -> str:
        texts = []
        for source_node in self.source_nodes:
            fmt_text_chunk = source_node.node.get_content()
            if trim_text:
                fmt_text_chunk = truncate_text(fmt_text_chunk, length)
            node_id = source_node.node.node_id or "None"
            source_text = f"> Source (Node id: {node_id}): {fmt_text_chunk}"
            texts.append(source_text)
        return "\n\n".join(texts)


@dataclass
class AsyncStreamingResponse:
    """AsyncStreamingResponse object. Returned if streaming=True while using async."""
    response_gen: TokenAsyncGen
    source_nodes: List[NodeWithScore] = field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None
    response_txt: Optional[str] = None

    def __post_init__(self) -> None:
        self._lock = asyncio.Lock()

    def __str__(self) -> str:
        return asyncio_run(self._async_str())

    async def _async_str(self) -> str:
        async for _ in self._yield_response():
            ...
        return self.response_txt or "None"

    async def _yield_response(self) -> TokenAsyncGen:
        async with self._lock:
            if self.response_txt is None and self.response_gen is not None:
                self.response_txt = ""
                async for text in self.response_gen:
                    self.response_txt += text
                    yield text
            else:
                yield self.response_txt

    async def async_response_gen(self) -> TokenAsyncGen:
        async for text in self._yield_response():
            yield text

    async def get_response(self) -> Response:
        async for _ in self._yield_response():
            ...
        return Response(self.response_txt, self.source_nodes, self.metadata)

    async def print_response_stream(self) -> None:
        async for text in self._yield_response():
            print(text, end="", flush=True)
        print()

    def get_formatted_sources(self, length: int = 100, trim_text: bool = True) -> str:
        texts = []
        for source_node in self.source_nodes:
            fmt_text_chunk = source_node.node.get_content()
            if trim_text:
                fmt_text_chunk = truncate_text(fmt_text_chunk, length)
            node_id = source_node.node.node_id or "None"
            source_text = f"> Source (Node id: {node_id}): {fmt_text_chunk}"
            texts.append(source_text)
        return "\n\n".join(texts)


async def _refinement_loop(
    response: RESPONSE_TEXT_TYPE,
    query_str: str,
    text_chunk: str,
    *,
    program_factory: Callable[[BasePromptTemplate], BasePydanticProgram],
    stream_fn: Callable[[BasePromptTemplate, str, Any], Awaitable[RESPONSE_TEXT_TYPE]],
    base_refine_template: BasePromptTemplate,
    prompt_helper: PromptHelper,
    llm: LLM,
    streaming: bool,
    verbose: bool,
    response_kwargs: Dict[str, Any],
) -> RESPONSE_TEXT_TYPE:
    """Shared refinement loop used by Refine synthesizers."""
    from llama_index.core.response.utils import get_response_text, aget_response_text

    if isinstance(response, Generator):
        response = get_response_text(response)
    if isinstance(response, AsyncGenerator):
        response = await aget_response_text(response)

    fmt_text_chunk = truncate_text(text_chunk, 50)
    logger.debug(f"> Refine context: {fmt_text_chunk}")
    if verbose:
        print(f"> Refine context: {fmt_text_chunk}")

    refine_template = base_refine_template.partial_format(
        query_str=query_str, existing_answer=response
    )

    avail_chunk_size = prompt_helper._get_available_chunk_size(refine_template)
    if avail_chunk_size < 0:
        return response

    text_chunks = prompt_helper.repack(
        refine_template, text_chunks=[text_chunk], llm=llm
    )

    program = program_factory(refine_template)
    for cur_text_chunk in text_chunks:
        query_satisfied = False
        if not streaming:
            try:
                structured_response = await program.acall(
                    context_msg=cur_text_chunk, **response_kwargs
                )
                query_satisfied = getattr(structured_response, "query_satisfied", False)
                if query_satisfied:
                    response = getattr(structured_response, "answer", response)
            except ValidationError as e:
                logger.warning(
                    f"Validation error on structured response: {e}", exc_info=True
                )
        else:
            if isinstance(response, Generator):
                from llama_index.core.response.utils import get_response_text as _grt
                response = _grt(response)
            if isinstance(response, AsyncGenerator):
                from llama_index.core.response.utils import aget_response_text as _gart
                response = await _gart(response)
            refine_template = base_refine_template.partial_format(
                query_str=query_str, existing_answer=response
            )
            response = await stream_fn(
                refine_template, cur_text_chunk, **response_kwargs
            )
        if query_satisfied:
            refine_template = base_refine_template.partial_format(
                query_str=query_str, existing_answer=response
            )
    return response


def refine_program_loop(
    response: RESPONSE_TEXT_TYPE,
    query_str: str,
    text_chunk: str,
    *,
    program_factory: Callable[[BasePromptTemplate], BasePydanticProgram],
    stream_fn: Callable[[BasePromptTemplate, str, Any], Awaitable[RESPONSE_TEXT_TYPE]],
    base_refine_template: BasePromptTemplate,
    prompt_helper: PromptHelper,
    llm: LLM,
    streaming: bool,
    verbose: bool,
    response_kwargs: Dict[str, Any],
) -> RESPONSE_TEXT_TYPE:
    """Synchronous wrapper for _refinement_loop."""
    return asyncio_run(
        _refinement_loop(
            response,
            query_str,
            text_chunk,
            program_factory=program_factory,
            stream_fn=stream_fn,
            base_refine_template=base_refine_template,
            prompt_helper=prompt_helper,
            llm=llm,
            streaming=streaming,
            verbose=verbose,
            response_kwargs=response_kwargs,
        )
    )


async def arefine_program_loop(
    response: RESPONSE_TEXT_TYPE,
    query_str: str,
    text_chunk: str,
    *,
    program_factory: Callable[[BasePromptTemplate], BasePydanticProgram],
    stream_fn: Callable[[BasePromptTemplate, str, Any], Awaitable[RESPONSE_TEXT_TYPE]],
    base_refine_template: BasePromptTemplate,
    prompt_helper: PromptHelper,
    llm: LLM,
    streaming: bool,
    verbose: bool,
    response_kwargs: Dict[str, Any],
) -> RESPONSE_TEXT_TYPE:
    """Async wrapper for _refinement_loop."""
    return await _refinement_loop(
        response,
        query_str,
        text_chunk,
        program_factory=program_factory,
        stream_fn=stream_fn,
        base_refine_template=base_refine_template,
        prompt_helper=prompt_helper,
        llm=llm,
        streaming=streaming,
        verbose=verbose,
        response_kwargs=response_kwargs,
    )


RESPONSE_TYPE = Union[
    Response, StreamingResponse, AsyncStreamingResponse, PydanticResponse
]
