from __future__ import annotations

import torch
from typing import List, Optional
from transformers import AutoModelForCausalLM, AutoTokenizer, GenerationConfig
from peft import PeftModel, PeftConfig

from ..config import model_config


class LocalQwen:
    def __init__(self) -> None:
        base_dir = model_config.base_model_dir
        lora_dir = model_config.lora_adapter_dir

        self.tokenizer = AutoTokenizer.from_pretrained(base_dir, trust_remote_code=True)
        base_model = AutoModelForCausalLM.from_pretrained(
            base_dir,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto",
            trust_remote_code=True,
        )
        if lora_dir:
            try:
                peft_cfg = PeftConfig.from_pretrained(lora_dir)
                self.model = PeftModel.from_pretrained(base_model, lora_dir)
            except Exception:
                # 允许无 LoRA 或加载失败时退回基础模型
                self.model = base_model
        else:
            self.model = base_model

        self.model.eval()
        self.gen_cfg = GenerationConfig(
            max_new_tokens=model_config.max_new_tokens,
            temperature=model_config.temperature,
            do_sample=True if model_config.temperature > 0 else False,
            top_p=0.95,
            repetition_penalty=1.05,
        )

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        prompt = f"<|system|>\n{system_prompt}\n<|user|>\n{user_prompt}\n<|assistant|>"
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        with torch.no_grad():
            output_ids = self.model.generate(**inputs, generation_config=self.gen_cfg)
        text = self.tokenizer.decode(output_ids[0], skip_special_tokens=True)
        # 简单截断：取assistant之后的内容
        if "<|assistant|>" in text:
            text = text.split("<|assistant|>", 1)[-1].strip()
        return text 