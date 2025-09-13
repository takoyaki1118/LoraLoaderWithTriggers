import { app } from "/scripts/app.js";

app.registerExtension({
    name: "LoraLoaderWithTriggers",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "LoraLoaderWithTriggers") {
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                onNodeCreated?.apply(this, arguments);

                const loraNameWidget = this.widgets.find(w => w.name === "lora_name");
                const variationWidget = this.widgets.find(w => w.name === "variation");
                
                const updateVariations = async () => {
                    const lora_name = loraNameWidget.value;
                    if (!lora_name) {
                        variationWidget.options.values = ["Select a LoRA"];
                        variationWidget.value = "Select a LoRA";
                        return;
                    }
                    
                    try {
                        const res = await api.fetchApi(`/lora_variations?lora_name=${encodeURIComponent(lora_name)}`);
                        if (res.status !== 200) {
                             console.error("Failed to fetch LoRA variations:", res.statusText);
                             return;
                        }

                        const data = await res.json();
                        
                        variationWidget.options.values = data.variations;
                        // 新しいリストに現在の値がなければ、先頭の値にリセット
                        if (!data.variations.includes(variationWidget.value)) {
                            variationWidget.value = data.variations[0];
                        }
                        this.setDirtyCanvas(true);
                    } catch (error) {
                        console.error("Error updating LoRA variations:", error);
                    }
                };

                loraNameWidget.callback = updateVariations;
                
                // 初期ロード時に一度実行
                setTimeout(updateVariations, 100);
            };
        }
    },
});