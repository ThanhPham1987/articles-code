import logging
import traceback
from pathlib import Path
from typing import Optional, Union

import numpy as np
from sentence_transformers.cross_encoder import CrossEncoder
from transformers import AutoModel, AutoTokenizer

from src import settings
from src.base import SingletonMeta

logger = logging.getLogger(__name__)


class EmbeddingModelSingleton(metaclass=SingletonMeta):
    """
    A singleton class that provides a pre-trained transformer model for generating embeddings of input text.

    Args:
        model_id (str): The identifier of the pre-trained transformer model to use.
        max_input_length (int): The maximum length of input text to tokenize.
        device (str): The device to use for running the model (e.g. "cpu", "cuda").
        cache_dir (Optional[Path]): The directory to cache the pre-trained model files.
            If None, the default cache directory is used.

    Attributes:
        max_input_length (int): The maximum length of input text to tokenize.
        tokenizer (AutoTokenizer): The tokenizer used to tokenize input text.
    """

    def __init__(
        self,
        model_id: str = settings.EMBEDDING_MODEL_ID,
        embedding_size: int = settings.EMBEDDING_SIZE,
        max_input_length: int = settings.EMBEDDING_MODEL_MAX_INPUT_LENGTH,
        device: str = settings.EMBEDDING_MODEL_DEVICE,
        cache_dir: Optional[Path] = None,
    ):
        """
        Initializes the EmbeddingModelSingleton instance.

        Args:
            model_id (str): The identifier of the pre-trained transformer model to use.
            max_input_length (int): The maximum length of input text to tokenize.
            device (str): The device to use for running the model (e.g. "cpu", "cuda").
            cache_dir (Optional[Path]): The directory to cache the pre-trained model files.
                If None, the default cache directory is used.
        """

        self._model_id = model_id
        self._embedding_size = embedding_size
        self._device = device
        self._max_input_length = max_input_length

        self._tokenizer = AutoTokenizer.from_pretrained(model_id)
        self._model = AutoModel.from_pretrained(
            model_id,
            cache_dir=str(cache_dir) if cache_dir else None,
        ).to(self._device)
        self._model.eval()

    @property
    def model_id(self) -> str:
        """
        Returns the identifier of the pre-trained transformer model to use.

        Returns:
            str: The identifier of the pre-trained transformer model to use.
        """

        return self._model_id

    @property
    def embedding_size(self) -> int:
        """
        Returns the size of the embeddings generated by the pre-trained transformer model.

        Returns:
            int: The size of the embeddings generated by the pre-trained transformer model.
        """

        return self._embedding_size

    @property
    def max_input_length(self) -> int:
        """
        Returns the maximum length of input text to tokenize.

        Returns:
            int: The maximum length of input text to tokenize.
        """

        return self._max_input_length

    @property
    def tokenizer(self) -> AutoTokenizer:
        """
        Returns the tokenizer used to tokenize input text.

        Returns:
            AutoTokenizer: The tokenizer used to tokenize input text.
        """

        return self._tokenizer

    def __call__(
        self, input_text: str, to_list: bool = True
    ) -> Union[np.ndarray, list]:
        """
        Generates embeddings for the input text using the pre-trained transformer model.

        Args:
            input_text (str): The input text to generate embeddings for.
            to_list (bool): Whether to return the embeddings as a list or numpy array. Defaults to True.

        Returns:
            Union[np.ndarray, list]: The embeddings generated for the input text.
        """

        try:
            tokenized_text = self._tokenizer(
                input_text,
                padding=True,
                truncation=True,
                return_tensors="pt",
                max_length=self._max_input_length,
            ).to(self._device)
        except Exception:
            logger.error(traceback.format_exc())
            logger.error(f"Error tokenizing the following input text: {input_text}")

            return [] if to_list else np.array([])

        try:
            result = self._model(**tokenized_text)
        except Exception:
            logger.error(traceback.format_exc())
            logger.error(
                f"Error generating embeddings for the following model_id: {self._model_id} and input text: {input_text}"
            )

            return [] if to_list else np.array([])

        embeddings = result.last_hidden_state[:, 0, :].cpu().detach().numpy()
        if to_list:
            embeddings = embeddings.flatten().tolist()

        return embeddings


class CrossEncoderModelSingleton(metaclass=SingletonMeta):
    def __init__(
        self,
        model_id: str = settings.CROSS_ENCODER_MODEL_ID,
        device: str = settings.EMBEDDING_MODEL_DEVICE,
    ):
        """
        Initializes the EmbeddingModelSingleton instance.

        Args:
            model_id (str): The identifier of the pre-trained transformer model to use.
            device (str): The device to use for running the model (e.g. "cpu", "cuda").
        """

        self._model_id = model_id
        self._device = device

        self._model = CrossEncoder(model_name=self._model_id, device=self._device)

    def __call__(self, pairs: list[tuple[str, str]]) -> list[float]:
        scores = self._model.predict(pairs)

        return scores.tolist()
