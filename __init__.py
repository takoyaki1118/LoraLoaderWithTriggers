import os
import json
import folder_paths
import comfy.sd

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
        # プルダウンメニューに表示する選択肢のリスト
        s.variation_options = ["None", "Variation 1", "Variation 2", "Variation 3"]
        
        return {
            "required": {
                "model": ("MODEL",),
                "clip": ("CLIP",),
                "lora_name": (folder_paths.get_filename_list("loras"),),
                "strength_model": ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01}),
                "strength_clip": ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01}),
                # バリエーション選択をプルダウンメニューに変更
                "variation_choice": (s.variation_options, ),
            }
        }

    # 出力ピンを簡略化
    RETURN_TYPES = ("MODEL", "CLIP", "STRING")
    RETURN_NAMES = ("MODEL", "CLIP", "TRIGGERS")
    FUNCTION = "load_lora_with_triggers"
    CATEGORY = "loaders/Lora Triggers"
    
    # UIの選択肢とJSONのキーを対応付ける辞書
    variation_key_map = {
        "Variation 1": "variation1",
        "Variation 2": "variation2",
        "Variation 3": "variation3",
    }

    def load_lora_with_triggers(self, model, clip, lora_name, strength_model, strength_clip, variation_choice):
        # 1. LoRAの読み込み処理 (変更なし)
        lora_path = folder_paths.get_full_path("loras", lora_name)
        lora = None
        if lora_path:
            lora = comfy.utils.load_torch_file(lora_path, safe_load=True)

        if lora is None:
             return (model, clip, "")
        
        model_lora, clip_lora = comfy.sd.load_lora_for_models(model, clip, lora, strength_model, strength_clip)
        
        # 2. トリガーワードの処理 (ロジック更新)
        base_words = ""
        variation_words = ""
        
        # JSONにLoRAのエントリがあるか確認
        if self.json_data and lora_name in self.json_data:
            lora_info = self.json_data[lora_name]
            
            # baseのトリガーワードを取得
            base_words = lora_info.get("base", "").strip()
            
            # プルダウンで "None" 以外が選択されているか確認
            if variation_choice != "None":
                # UIの選択肢名 (例: "Variation 1") をJSONのキー (例: "variation1") に変換
                json_key = self.variation_key_map.get(variation_choice)
                
                if json_key:
                    variations_dict = lora_info.get("variations", {})
                    # 対応するキーのトリガーワードを取得 (キーがなければ空文字が返る)
                    variation_words = variations_dict.get(json_key, "").strip()
        else:
            print(f"[LoraLoaderWithTriggers] WARNING: No trigger word entry found for '{lora_name}' in lora_triggers.json")

        # 3. テキストの結合
        final_triggers = []
        if base_words:
            final_triggers.append(base_words)
        if variation_words:
            final_triggers.append(variation_words)
            
        output_text = ", ".join(filter(None, final_triggers)) # filter(None, ...) で空文字の要素を除外

        # 最終的な結果を返す
        return (model_lora, clip_lora, output_text)

# ComfyUIへの登録 (変更なし)
NODE_CLASS_MAPPINGS = {
    "LoraLoaderWithTriggers": LoraLoaderWithTriggers
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LoraLoaderWithTriggers": "Lora Loader with Triggers"
}