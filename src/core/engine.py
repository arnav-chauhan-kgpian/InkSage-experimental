"""
InkSage Engine - LOGIC FIXED
"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, StoppingCriteria, StoppingCriteriaList
import logging
import hashlib
import time
from threading import Lock
from typing import Optional, Dict, List
from ..utils.config import config

# --- 1. Custom Stop Logic (Stops AI from rambling) ---
class StopOnTokens(StoppingCriteria):
    def __init__(self, stop_ids):
        self.stop_ids = stop_ids
    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs) -> bool:
        # Check if the last generated token is in our stop list
        return input_ids[0][-1] in self.stop_ids

# --- 2. Cache (Unchanged) ---
class LLMCache:
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self.cache: Dict[str, tuple] = {}
        self.access_order: List[str] = []
        self.lock = Lock()
    
    def _generate_key(self, prompt: str, **kwargs) -> str:
        content = f"{prompt}|{kwargs.get('temperature', 0)}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, prompt: str, **kwargs) -> Optional[str]:
        key = self._generate_key(prompt, **kwargs)
        with self.lock:
            if key in self.cache:
                response, timestamp = self.cache[key]
                if time.time() - timestamp < 3600:
                    return response
        return None
    
    def set(self, prompt: str, response: str, **kwargs) -> None:
        key = self._generate_key(prompt, **kwargs)
        with self.lock:
            self.cache[key] = (response, time.time())

# --- 3. The Engine ---
class Engine:
    def __init__(self):
        self.logger = logging.getLogger("InkSage.Engine")
        self.model = None
        self.tokenizer = None
        self.lock = Lock()
        self.cache = LLMCache()
        
        self.model_id = config.get('engine.model_path', "Qwen/Qwen2.5-1.5B-Instruct")
        self._load_model()

    def _load_model(self):
        print(f"⏳ Loading PyTorch Engine: {self.model_id}...")
        try:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            print(f"   Device: {self.device.upper()}")

            self.tokenizer = AutoTokenizer.from_pretrained(self.model_id)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_id,
                torch_dtype="auto",
                device_map=self.device,
                low_cpu_mem_usage=True
            )
            print("✅ Engine Loaded")
        except Exception as e:
            print(f"❌ Failed to load model: {e}")

    def generate(self, prompt: str, system_prompt: str = None, **kwargs) -> str:
        if not self.model or not self.tokenizer: return ""

        # Cache Check
        cached = self.cache.get(prompt, **kwargs)
        if cached: return cached

        # 🚨 LOGIC FIX: Detect Mode based on System Prompt availability
        # If NO system prompt is passed, it's a Quick Suggestion.
        is_suggestion = system_prompt is None or "sentence completer" in system_prompt
        
        try:
            with self.lock:
                with torch.no_grad():
                    if is_suggestion:
                        # === SUGGESTION MODE (Strict) ===
                        # 1. Feed Raw Text (No Chat Template)
                        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
                        
                        # 2. Define Stop Tokens (Newline, Dot)
                        stop_token_ids = [self.tokenizer.eos_token_id]
                        if self.tokenizer.convert_tokens_to_ids("\n"):
                            stop_token_ids.append(self.tokenizer.convert_tokens_to_ids("\n"))
                        
                        stopping_criteria = StoppingCriteriaList([StopOnTokens(stop_token_ids)])

                        outputs = self.model.generate(
                            **inputs,
                            max_new_tokens=16,   # Very short (1-5 words max)
                            temperature=0.1,     # Very precise (No "Wwwhoooo")
                            do_sample=True,      # Still sample, but strictly
                            top_p=0.8,
                            repetition_penalty=1.3, # Strong penalty for repeats
                            stopping_criteria=stopping_criteria,
                            pad_token_id=self.tokenizer.eos_token_id
                        )
                        
                        # Decode ONLY new tokens
                        input_len = inputs.input_ids.shape[1]
                        generated_ids = outputs[0][input_len:]
                        response = self.tokenizer.decode(generated_ids, skip_special_tokens=True)
                        
                        # 🚨 Cleanup: Don't return just punctuation
                        if response.strip() in [".", ",", "!", "?"]:
                            return ""
                        
                    else:
                        # === AUTO-WRITE MODE (Creative) ===
                        messages = [{"role": "user", "content": prompt}]
                        if system_prompt:
                            messages.insert(0, {"role": "system", "content": system_prompt})
                            
                        text_input = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
                        inputs = self.tokenizer(text_input, return_tensors="pt").to(self.device)
                        
                        outputs = self.model.generate(
                            **inputs,
                            max_new_tokens=kwargs.get('max_tokens', 256),
                            temperature=0.7,
                            do_sample=True,
                            pad_token_id=self.tokenizer.eos_token_id
                        )
                        input_len = inputs.input_ids.shape[1]
                        generated_ids = outputs[0][input_len:]
                        response = self.tokenizer.decode(generated_ids, skip_special_tokens=True)

            clean_response = response.strip()
            
            # Only cache if we actually got something
            if clean_response:
                self.cache.set(prompt, clean_response, **kwargs)
                
            return clean_response

        except Exception as e:
            self.logger.error(f"Inference error: {e}")
            return ""

    def is_available(self) -> bool:
        return self.model is not None

    def cleanup(self):
        if self.model: del self.model
        if self.tokenizer: del self.tokenizer
        if torch.cuda.is_available(): torch.cuda.empty_cache()