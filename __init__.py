import os
import json
import folder_paths
import comfy.sd
from contextlib import redirect_stdout, redirect_stderr

class LoraLoaderWithTriggers:
    def __init__(self):
        self.json_data = self.load_trigger_words()

    @classmethod
    def load_trigger_words(cls):
        """JSONファイルを読み込むためのヘルパーメソッド"""
        p = os.path.dirname(os.path.realpath(__file__))
        file_path = os.path.join(p, "lora_triggers.json")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                print(f"[LoraLoaderWithTriggers] Loading trigger words from: {file_path}")
                return json.load(f)
        except Exception as e:
            print(f"[LoraLoaderWithTriggers] ERROR: Could not load or parse lora_triggers.json: {e}")
            return {}

    @classmethod
    def INPUT_TYPES(s):
        s.variation_options = ["None", "Variation 1", "Variation 2", "Variation 3"]
        
        return {
            "required": {
                "model": ("MODEL",),
                "clip": ("CLIP",),
                "lora_name": (folder_paths.get_filename_list("loras"),),
                "strength_model": ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01}),
                "strength_clip": ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01}),
                "variation_choice": (s.variation_options, ),
            }
        }

    RETURN_TYPES = ("MODEL", "CLIP", "STRING")
    RETURN_NAMES = ("MODEL", "CLIP", "TRIGGERS")
    FUNCTION = "load_lora_with_triggers"
    CATEGORY = "loaders/Lora Triggers"
    
    variation_key_map = {
        "Variation 1": "variation1",
        "Variation 2": "variation2",
        "Variation 3": "variation3",
    }

    def load_lora_with_triggers(self, model, clip, lora_name, strength_model, strength_clip, variation_choice):
        lora_path = folder_paths.get_full_path("loras", lora_name)
        lora = None
        if lora_path:
            lora = comfy.utils.load_torch_file(lora_path, safe_load=True)

        if lora is None:
             return (model, clip, "")
        
        # ※注意：この部分の警告抑制コードも削除しました。
        # 起動オプションで全体を抑制するため、個別対応は不要です。
        model_lora, clip_lora = comfy.sd.load_lora_for_models(model, clip, lora, strength_model, strength_clip)
        
        base_words = ""
        variation_words = ""
        
        if self.json_data and lora_name in self.json_data:
            lora_info = self.json_data[lora_name]
            base_words = lora_info.get("base", "").strip()
            
            if variation_choice != "None":
                json_key = self.variation_key_map.get(variation_choice)
                if json_key:
                    variations_dict = lora_info.get("variations", {})
                    variation_words = variations_dict.get(json_key, "").strip()
        else:
            print(f"[LoraLoaderWithTriggers] WARNING: No trigger word entry found for '{lora_name}' in lora_triggers.json")

        final_triggers = []
        if base_words:
            final_triggers.append(base_words)
        if variation_words:
            final_triggers.append(variation_words)
            
        output_text = ", ".join(filter(None, final_triggers))

        return (model_lora, clip_lora, output_text)

NODE_CLASS_MAPPINGS = {
    "LoraLoaderWithTriggers": LoraLoaderWithTriggers
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LoraLoaderWithTriggers": "Lora Loader with Triggers"
}