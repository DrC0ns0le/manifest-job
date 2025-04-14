import aiohttp
import json


class LLM:
    def __init__(self, config):
        """
        Initialize the LLM with the given configuration

        Args:
            config (dict): The configuration dictionary

        If the configuration contains the key "ollama", the LLM will be
        initialized with an Ollama model. Otherwise, a ValueError will be
        raised.
        """
        self.model = None

        if "ollama" in config:
            self.model = Ollama(
                model=config["ollama"]["model"],
                base_url=config["ollama"].get("endpoint", "http://localhost:11434"),
                temperature=config["ollama"].get("temperature", 1.0),
                top_k=config["ollama"].get("top_k", 64),
                top_p=config["ollama"].get("top_p", 0.95),
                timeout=config["ollama"].get("timeout_seconds", 180),
            )

    def get_model(self):
        """
        Get the initialized LLM model

        Returns:
            LLM: The initialized LLM model

        Raises:
            ValueError: If the LLM is not initialized
        """
        if self.model is None:
            raise ValueError("LLM not initialized")
        return self.model


class Ollama:
    def __init__(self, model, base_url, temperature, top_k, top_p, timeout):
        """
        Initialize an Ollama LLM

        Args:
            model (str): The name of the Ollama model to use
            base_url (str): The base URL of the Ollama API
            temperature (float): The temperature to use for generation
            top_k (int): The number of top tokens to consider at each step
            top_p (float): The probability of considering all tokens at each step
        """
        self.model = model
        self.base_url = base_url
        self.temperature = temperature
        self.top_k = top_k
        self.top_p = top_p
        self.timeout = timeout

    async def ainvoke(self, prompt, stream=False):
        """
        Asynchronously generate a response from Ollama API.

        Args:
            prompt (str): The prompt to send to the model
            model (str): The model to use
            stream (bool): Whether to stream the response, defaults to False

        Returns:
            str: The generated response text
        """
        url = f"{self.base_url}/api/generate"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": self.temperature,
                "top_k": self.top_k,
                "top_p": self.top_p,
                "num_predict": 8192,
                "num_ctx": 6144,
            },
            "format": "json",
        }

        timeout = aiohttp.ClientTimeout(total=self.timeout)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=payload) as response:
                if stream:
                    # Handle streaming response
                    result = ""
                    async for line in response.content:
                        if line:
                            data = json.loads(line)
                            if "response" in data:
                                result += data["response"]
                                # print(data["response"], end="")
                    return result
                else:
                    # Handle non-streaming response
                    data = await response.json()
                    # print(data)
                    return data["response"]
