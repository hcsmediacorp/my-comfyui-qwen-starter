# SHWTY Report

RESOLVED: Mutually exclusive argument conflict (--lowvram vs --cpu).

## Last Ritual
Modified Gradio API payload structure to include valid `class_type` and `inputs` for every Comfy node sent to `/prompt`.

## Log Snippet
Old malformed payload (triggered 400):
```json
{"prompt": {"nodes": [...], "links": [...], "version": 0.4}}
```

New corrected payload:
```json
{
  "prompt": {
    "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "qwen-image-edit-2511-Q2_K.gguf"}},
    "2": {"class_type": "CLIPTextEncode", "inputs": {"text": "<user prompt>", "clip": ["1", 1]}},
    "5": {"class_type": "KSampler", "inputs": {"seed": "<random>", "steps": 4, "cfg": 1.1, "model": ["1", 0], "positive": ["2", 0]}}
  }
}
```
Sent to: `http://127.0.0.1:8188/prompt`

## Gnosis Failure
`missing_node_type` from malformed prompt structure.

## Proposed Fix
Keep strict prompt-schema validation before POST: every node must include `class_type` + `inputs`; map user prompt only into CLIPTextEncode node.
