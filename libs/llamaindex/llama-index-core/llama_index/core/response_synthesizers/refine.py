import logging
from typing import (
    Any,
    Callable,
    Generator,
    Optional,
    Sequence,
    Type,
    cast,
    AsyncGenerator,
)

from llama_index.core.bridge.pydantic import BaseModel, Field, ValidationError
from llama_index.core.callbacks.base import CallbackManager
from llama_index.core.indices.prompt_helper import PromptHelper
from llama_index.core.llms import LLM
from llama_index.core.prompts.base import BasePromptTemplate
from llama_index.core.prompts.default_prompt_selectors import (
    DEFAULT_REFINE_PROMPT_SEL,
    DEFAULT_TEXT_QA_PROMPT_SEL,
)
from llama_index.core.prompts.mixin import PromptDictType
from llama_index.core.response_synthesizers.base import BaseSynthesizer
from llama_index.core.types import RESPONSE_TEXT_TYPE, BasePydanticProgram
from llama_index.core.instrumentation.events.synthesis import (
    GetResponseEndEvent,
    GetResponseStartEvent,
)
import llama_index.core.instrumentation as instrument
from llama_index.core.base.response.schema import (
    refine_program_loop,
    arefine_program_loop,
)

dispatcher = instrument.get_dispatcher(__name__)

logger = logging.getLogger(__name__)


class StructuredRefineResponse(BaseModel):
    """
    Used to answer a given query based on the provided context.

    Also indicates if the query was satisfied with the provided answer.
    """

    answer: str = Field(
        description="The answer for the given query, based on the context and not "
        "prior knowledge."
    )
    query_satisfied: bool = Field(
        description="True if there was enough context given to provide an answer "
        "that satisfies the query."
    )


class DefaultRefineProgram(BasePydanticProgram):
    """
    Runs the query on the LLM as normal and always returns the answer with
    query_satisfied=True. In effect, doesn't do any answer filtering.
    """

    def __init__(
        self,
        prompt: BasePromptTemplate,
        llm: LLM,
        output_cls: Optional[Type[BaseModel]] = None,
    ):
        self._prompt = prompt
        self._llm = llm
        self._output_cls = output_cls

    @property
    def output_cls(self) -> Type[BaseModel]:
        return StructuredRefineResponse

    def __call__(self, *args: Any, **kwds: Any) -> StructuredRefineResponse:
        if self._output_cls is not None:
            answer = self._llm.structured_predict(
                self._output_cls,
                self._prompt,
                **kwds,
            )
            if isinstance(answer, BaseModel):
                answer = answer.model_dump_json()
        else:
            answer = self._llm.predict(
                self._prompt,
                **kwds,
            )
        return StructuredRefineResponse(answer=answer, query_satisfied=True)

    async def acall(self, *args: Any, **kwds: Any) -> StructuredRefineResponse:
        if self._output_cls is not None:
            answer = await self._llm.astructured_predict(  # type: ignore
                self._output_cls,
                self._prompt,
                **kwds,
            )
            if isinstance(answer, BaseModel):
                answer = answer.model_dump_json()
        else:
            answer = await self._llm.apredict(
                self._prompt,
                **kwds,
            )
        return StructuredRefineResponse(answer=answer, query_satisfied=True)


class Refine(BaseSynthesizer):
    """Refine a response to a query across text chunks."""

    def __init__(
        self,
        llm: Optional[LLM] = None,
        callback_manager: Optional[CallbackManager] = None,
        prompt_helper: Optional[PromptHelper] = None,
        text_qa_template: Optional[BasePromptTemplate] = None,
        refine_template: Optional[BasePromptTemplate] = None,
        output_cls: Optional[Type[BaseModel]] = None,
        streaming: bool = False,
        verbose: bool = False,
        structured_answer_filtering: bool = False,
        program_factory: Optional[
            Callable[[BasePromptTemplate], BasePydanticProgram]
        ] = None,
    ) -> None:
        super().__init__(
            llm=llm,
            callback_manager=callback_manager,
            prompt_helper=prompt_helper,
            streaming=streaming,
        )
        self._text_qa_template = text_qa_template or DEFAULT_TEXT_QA_PROMPT_SEL
        self._refine_template = refine_template or DEFAULT_REFINE_PROMPT_SEL
        self._verbose = verbose
        self._structured_answer_filtering = structured_answer_filtering
        self._output_cls = output_cls

        if self._streaming and self._structured_answer_filtering:
            raise ValueError(
                "Streaming not supported with structured answer filtering."
            )
        if not self._structured_answer_filtering and program_factory is not None:
            raise ValueError(
                "Program factory not supported without structured answer filtering."
            )
        self._program_factory = program_factory or self._default_program_factory

    def _get_prompts(self) -> PromptDictType:
        """Get prompts."""
        return {
            "text_qa_template": self._text_qa_template,
            "refine_template": self._refine_template,
        }

    def _update_prompts(self, prompts: PromptDictType) -> None:
        """Update prompts."""
        if "text_qa_template" in prompts:
            self._text_qa_template = prompts["text_qa_template"]
        if "refine_template" in prompts:
            self._refine_template = prompts["refine_template"]

    @dispatcher.span
    def get_response(
        self,
        query_str: str,
        text_chunks: Sequence[str],
        prev_response: Optional[RESPONSE_TEXT_TYPE] = None,
        **response_kwargs: Any,
    ) -> RESPONSE_TEXT_TYPE:
        """Give response over chunks."""
        dispatcher.event(
            GetResponseStartEvent(query_str=query_str, text_chunks=text_chunks)
        )
        response: Optional[RESPONSE_TEXT_TYPE] = None
        for text_chunk in text_chunks:
            if prev_response is None:
                # if this is the first chunk, and text chunk already
                # is an answer, then return it
                response = self._give_response_single(
                    query_str, text_chunk, **response_kwargs
                )
            else:
                # refine response if possible
                response = self._refine_response_single(
                    prev_response, query_str, text_chunk, **response_kwargs
                )
            prev_response = response
        if isinstance(response, str):
            if self._output_cls is not None:
                try:
                    response = self._output_cls.model_validate_json(response)
                except ValidationError:
                    pass
            else:
                response = response or "Empty Response"
        else:
            response = cast(Generator, response)
        dispatcher.event(GetResponseEndEvent())
        return response

    def _default_program_factory(
        self, prompt: BasePromptTemplate
    ) -> BasePydanticProgram:
        if self._structured_answer_filtering:
            from llama_index.core.program.utils import get_program_for_llm

            return get_program_for_llm(
                StructuredRefineResponse,
                prompt,
                self._llm,
                verbose=self._verbose,
            )
        else:
            return DefaultRefineProgram(
                prompt=prompt,
                llm=self._llm,
                output_cls=self._output_cls,
            )

    def _give_response_single(
        self,
        query_str: str,
        text_chunk: str,
        **response_kwargs: Any,
    ) -> RESPONSE_TEXT_TYPE:
        """Give response given a query and a corresponding text chunk."""
        text_qa_template = self._text_qa_template.partial_format(query_str=query_str)
        text_chunks = self._prompt_helper.repack(
            text_qa_template, [text_chunk], llm=self._llm
        )

        response: Optional[RESPONSE_TEXT_TYPE] = None
        program = self._program_factory(text_qa_template)
        # TODO: consolidate with loop in get_response_default
        for cur_text_chunk in text_chunks:
            query_satisfied = False
            if response is None and not self._streaming:
                try:
                    structured_response = cast(
                        StructuredRefineResponse,
                        program(
                            context_str=cur_text_chunk,
                            **response_kwargs,
                        ),
                    )
                    query_satisfied = structured_response.query_satisfied
                    if query_satisfied:
                        response = structured_response.answer
                except ValidationError as e:
                    logger.warning(
                        f"Validation error on structured response: {e}", exc_info=True
                    )
            elif response is None and self._streaming:
                response = self._llm.stream(
                    text_qa_template,
                    context_str=cur_text_chunk,
                    **response_kwargs,
                )
                query_satisfied = True
            else:
                response = self._refine_response_single(
                    cast(RESPONSE_TEXT_TYPE, response),
                    query_str,
                    cur_text_chunk,
                    **response_kwargs,
                )
        if response is None:
            response = "Empty Response"
        if isinstance(response, str):
            response = response or "Empty Response"
        else:
            response = cast(Generator, response)
        return response

    def _refine_response_single(
        self,
        response: RESPONSE_TEXT_TYPE,
        query_str: str,
        text_chunk: str,
        **response_kwargs: Any,
    ) -> Optional[RESPONSE_TEXT_TYPE]:
        """Refine response."""

        async def stream_fn(
            template: BasePromptTemplate, chunk: str, **kwargs: Any
        ) -> RESPONSE_TEXT_TYPE:
            return self._llm.stream(template, context_msg=chunk, **kwargs)

        return refine_program_loop(
            response,
            query_str,
            text_chunk,
            program_factory=self._program_factory,
            stream_fn=stream_fn,
            base_refine_template=self._refine_template,
            prompt_helper=self._prompt_helper,
            llm=self._llm,
            streaming=self._streaming,
            verbose=self._verbose,
            response_kwargs=response_kwargs,
        )

    @dispatcher.span
    async def aget_response(
        self,
        query_str: str,
        text_chunks: Sequence[str],
        prev_response: Optional[RESPONSE_TEXT_TYPE] = None,
        **response_kwargs: Any,
    ) -> RESPONSE_TEXT_TYPE:
        dispatcher.event(
            GetResponseStartEvent(query_str=query_str, text_chunks=text_chunks)
        )
        response: Optional[RESPONSE_TEXT_TYPE] = None
        for text_chunk in text_chunks:
            if prev_response is None:
                # if this is the first chunk, and text chunk already
                # is an answer, then return it
                response = await self._agive_response_single(
                    query_str, text_chunk, **response_kwargs
                )
            else:
                response = await self._arefine_response_single(
                    prev_response, query_str, text_chunk, **response_kwargs
                )
            prev_response = response
        if response is None:
            response = "Empty Response"
        if isinstance(response, str):
            if self._output_cls is not None:
                response = self._output_cls.model_validate_json(response)
            else:
                response = response or "Empty Response"
        else:
            response = cast(AsyncGenerator, response)
        dispatcher.event(GetResponseEndEvent())
        return response

    async def _arefine_response_single(
        self,
        response: RESPONSE_TEXT_TYPE,
        query_str: str,
        text_chunk: str,
        **response_kwargs: Any,
    ) -> Optional[RESPONSE_TEXT_TYPE]:
        """Refine response."""

        async def stream_fn(
            template: BasePromptTemplate, chunk: str, **kwargs: Any
        ) -> RESPONSE_TEXT_TYPE:
            return await self._llm.astream(template, context_msg=chunk, **kwargs)

        return await arefine_program_loop(
            response,
            query_str,
            text_chunk,
            program_factory=self._program_factory,
            stream_fn=stream_fn,
            base_refine_template=self._refine_template,
            prompt_helper=self._prompt_helper,
            llm=self._llm,
            streaming=self._streaming,
            verbose=self._verbose,
            response_kwargs=response_kwargs,
        )

    async def _agive_response_single(
        self,
        query_str: str,
        text_chunk: str,
        **response_kwargs: Any,
    ) -> RESPONSE_TEXT_TYPE:
        """Give response given a query and a corresponding text chunk."""
        text_qa_template = self._text_qa_template.partial_format(query_str=query_str)
        text_chunks = self._prompt_helper.repack(
            text_qa_template, [text_chunk], llm=self._llm
        )

        response: Optional[RESPONSE_TEXT_TYPE] = None
        program = self._program_factory(text_qa_template)
        # TODO: consolidate with loop in get_response_default
        for cur_text_chunk in text_chunks:
            if response is None and not self._streaming:
                try:
                    structured_response = await program.acall(
                        context_str=cur_text_chunk,
                        **response_kwargs,
                    )
                    structured_response = cast(
                        StructuredRefineResponse, structured_response
                    )
                    query_satisfied = structured_response.query_satisfied
                    if query_satisfied:
                        response = structured_response.answer
                except ValidationError as e:
                    logger.warning(
                        f"Validation error on structured response: {e}", exc_info=True
                    )
            elif response is None and self._streaming:
                response = await self._llm.astream(
                    text_qa_template,
                    context_str=cur_text_chunk,
                    **response_kwargs,
                )
                query_satisfied = True
            else:
                response = await self._arefine_response_single(
                    cast(RESPONSE_TEXT_TYPE, response),
                    query_str,
                    cur_text_chunk,
                    **response_kwargs,
                )
        if response is None:
            response = "Empty Response"
        if isinstance(response, str):
            response = response or "Empty Response"
        else:
            response = cast(AsyncGenerator, response)
        return response
