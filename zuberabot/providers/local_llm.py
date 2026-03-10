"""Local LLM provider using LlamaCpp for cost-efficient inference."""

from pathlib import Path
from typing import Any, List, Dict, Optional
from asyncio import Semaphore
import torch
from loguru import logger

try:
    from llama_cpp import Llama
    LLAMACPP_AVAILABLE = True
except ImportError:
    LLAMACPP_AVAILABLE = False
    logger.warning("llama-cpp-python not installed. Install with: pip install llama-cpp-python")

from zuberabot.providers.base import LLMProvider, LLMResponse, ToolCall


class LocalLLMProvider(LLMProvider):
    """
    Local LLM provider using LlamaCpp for cost efficiency.
    
    Optimized for GTX 1650 (4GB VRAM) with:
    - Sequential request processing (prevents OOM)
    - GPU memory monitoring
    - 4-bit quantized model support
    """
    
    def __init__(
        self,
        model_path: str,
        n_gpu_layers: int = -1,  # Use all GPU layers
        n_ctx: int = 2048,  # Context window
        n_batch: int = 256,  # Smaller batch for 4GB VRAM
        temperature: float = 0.7,
        max_concurrent: int = 1,  # Only 1 concurrent request for 4GB VRAM
    ):
        """
        Initialize local LLM provider.
        
        Args:
            model_path: Path to GGUF model file
            n_gpu_layers: Number of layers to offload to GPU (-1 = all)
            n_ctx: Context window size (reduce if OOM)
            n_batch: Batch size for processing (reduce if OOM)
            temperature: Sampling temperature
            max_concurrent: Maximum concurrent requests (1 for 4GB VRAM)
        """
        if not LLAMACPP_AVAILABLE:
            raise ImportError(
                "llama-cpp-python is required for LocalLLMProvider. "
                "Install with: pip install llama-cpp-python"
            )
        
        self.model_path = Path(model_path)
        
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Model not found: {model_path}\n"
                f"Download models to: ./models/\n"
                f"See LOCAL_MODEL_SETUP.md for instructions."
            )
        
        logger.info(f"Loading local model: {self.model_path.name}")
        logger.info(f"GPU layers: {n_gpu_layers}, Context: {n_ctx}, Batch: {n_batch}")
        
        # Check GPU availability
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
            logger.info(f"GPU: {gpu_name} ({gpu_memory:.2f} GB VRAM)")
        else:
            logger.warning("CUDA not available! Model will run on CPU (very slow)")
        
        # Load model
        try:
            self.llm = Llama(
                model_path=str(self.model_path),
                n_gpu_layers=n_gpu_layers,
                n_ctx=n_ctx,
                n_batch=n_batch,
                verbose=False,
                # low_vram=True,  # Uncomment if you get OOM errors
            )
            logger.info(f"✅ Local model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
        
        self.temperature = temperature
        self.model_name = f"local/{self.model_path.stem}"
        
        # Semaphore to limit concurrent requests (prevent OOM)
        self._request_semaphore = Semaphore(max_concurrent)
        
        logger.info(f"Max concurrent requests: {max_concurrent}")
    
    def get_default_model(self) -> str:
        """Get default model name."""
        return self.model_name
    
    async def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]] | None = None,
        model: str | None = None,
        **kwargs: Any
    ) -> LLMResponse:
        """
        Generate chat completion.
        
        Args:
            messages: Conversation messages
            tools: Available tools (basic support)
            model: Model to use (ignored, uses loaded model)
            **kwargs: Additional generation parameters
        
        Returns:
            LLMResponse with generated text
        """
        async with self._request_semaphore:
            return await self._generate(messages, tools, **kwargs)
    
    async def _generate(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]],
        **kwargs: Any
    ) -> LLMResponse:
        """Internal generation method (handles one request at a time)."""
        
        # Format messages into prompt
        prompt = self._format_messages(messages, tools)
        
        # Log GPU memory before generation
        if torch.cuda.is_available():
            self._log_gpu_memory("Before generation")
        
        # Generate response
        try:
            max_tokens = kwargs.get("max_tokens", 500)
            temp = kwargs.get("temperature", self.temperature)
            
            result = self.llm(
                prompt,
                max_tokens=max_tokens,
                temperature=temp,
                stop=["User:", "Assistant:", "\n\n\n", "###"],
                echo=False
            )
            
            response_text = result["choices"][0]["text"].strip()
            
            # Log GPU memory after generation
            if torch.cuda.is_available():
                self._log_gpu_memory("After generation")
            
            # Parse tool calls if tools were provided
            tool_calls = []
            if tools:
                tool_calls = self._parse_tool_calls(response_text)
            
            # Remove tool call markers from response
            if tool_calls:
                response_text = self._clean_response_with_tools(response_text)
            
            return LLMResponse(
                content=response_text if response_text else None,
                model=self.model_name,
                tool_calls=tool_calls
            )
            
        except Exception as e:
            logger.error(f"Local LLM generation error: {e}")
            
            # Check if it's an OOM error
            if "out of memory" in str(e).lower():
                logger.error("GPU OOM! Try reducing n_ctx or n_batch in provider config")
            
            return LLMResponse(
                content="Sorry, I encountered an error processing your request.",
                model=self.model_name,
                tool_calls=[]
            )
    
    def _format_messages(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Format messages into prompt for local model.
        
        Args:
            messages: Conversation messages
            tools: Available tools (appended to system prompt)
            
        Returns:
            Formatted prompt string
        """
        prompt_parts = []
        
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            if role == "system":
                prompt_parts.append(f"System: {content}")
                
                # Add tools to system prompt if available
                if tools:
                    tools_desc = self._format_tools(tools)
                    prompt_parts.append(f"\nAvailable Tools:\n{tools_desc}")
                
            elif role == "user":
                prompt_parts.append(f"\nUser: {content}")
            elif role == "assistant":
                prompt_parts.append(f"\nAssistant: {content}")
        
        # Add assistant prefix for generation
        prompt_parts.append("\nAssistant:")
        
        return "".join(prompt_parts)
    
    def _format_tools(self, tools: List[Dict[str, Any]]) -> str:
        """Format tools for system prompt."""
        tool_descriptions = []
        for tool in tools:
            name = tool.get("function", {}).get("name", "unknown")
            desc = tool.get("function", {}).get("description", "")
            tool_descriptions.append(f"- {name}: {desc}")
        return "\n".join(tool_descriptions)
    
    def _parse_tool_calls(self, response: str) -> List[ToolCall]:
        """
        Parse tool calls from response (basic implementation).
        
        Looks for patterns like: TOOL[tool_name](arg1, arg2)
        """
        tool_calls = []
        # Simple pattern matching (can be improved)
        import re
        pattern = r'TOOL\[(\w+)\]\((.*?)\)'
        matches = re.findall(pattern, response)
        
        for i, (tool_name, args_str) in enumerate(matches):
            tool_calls.append(ToolCall(
                id=f"call_{i}",
                name=tool_name,
                arguments={"input": args_str}  # Simplified
            ))
        
        return tool_calls
    
    def _clean_response_with_tools(self, response: str) -> str:
        """Remove tool call markers from response."""
        import re
        return re.sub(r'TOOL\[.*?\]\(.*?\)', '', response).strip()
    
    def _log_gpu_memory(self, label: str = ""):
        """Log current GPU memory usage."""
        if not torch.cuda.is_available():
            return
        
        allocated = torch.cuda.memory_allocated(0) / 1024**3
        reserved = torch.cuda.memory_reserved(0) / 1024**3
        total = torch.cuda.get_device_properties(0).total_memory / 1024**3
        free = total - reserved
        
        logger.debug(
            f"GPU Memory [{label}]: "
            f"Allocated={allocated:.2f}GB, "
            f"Reserved={reserved:.2f}GB, "
            f"Free={free:.2f}GB, "
            f"Total={total:.2f}GB"
        )
