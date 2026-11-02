import unittest
from unittest.mock import patch
from poligon import providers

class ProviderAdapterTests(unittest.TestCase):
    def test_openai_message_conversion_preserves_tool_calls(self):
        messages = [
            {"role":"system","content":"system"},
            {"role":"user","content":"hello"},
            {"role":"assistant","content":"","tool_calls":[
                {"id":"call_1","type":"function","function":{"name":"system_info","arguments":"{}"}}
            ]},
            {"role":"tool","tool_call_id":"call_1","content":"{\"os\":\"Windows\"}"}
        ]
        converted = providers._openai_messages(messages)
        self.assertEqual(converted[2]["tool_calls"][0]["function"]["name"], "system_info")
        self.assertEqual(converted[3]["tool_call_id"], "call_1")

    def test_gemini_message_conversion_maps_function_response(self):
        messages = [
            {"role":"system","content":"system prompt"},
            {"role":"user","content":"check pc"},
            {"role":"assistant","content":"","tool_calls":[
                {"id":"call_1","type":"function","function":{"name":"system_info","arguments":"{}"}}
            ]},
            {"role":"tool","tool_call_id":"call_1","content":"{\"ok\":true}"}
        ]
        contents, system = providers._gemini_messages(messages)
        self.assertEqual(system, "system prompt")
        self.assertEqual(contents[1]["role"], "model")
        self.assertEqual(contents[2]["parts"][0]["functionResponse"]["name"], "system_info")

    def test_gemini_schema_removes_unsupported_json_schema_fields(self):
        schema = {"function":{"name":"test","parameters":{
            "type":"object","additionalProperties":False,
            "properties":{"x":{"type":"string","default":"abc"}}
        }}}
        converted = providers._gemini_schema(schema)
        self.assertNotIn("additionalProperties", converted["parameters"])
        self.assertNotIn("default", converted["parameters"]["properties"]["x"])

    def test_auto_mode_falls_back_to_local_when_no_free_provider_is_connected(self):
        with patch.object(providers, "credential", return_value=None):
            self.assertIsNone(providers.auto_chat([{"role":"user","content":"hello"}]))

    def test_auto_mode_prefers_openrouter_free_router(self):
        expected = {"role":"assistant","content":"ok"}
        with patch.object(providers, "credential", side_effect=lambda p: "secret" if p == "openrouter" else None), patch.object(providers, "chat", return_value=expected) as call:
            result = providers.auto_chat([{"role":"user","content":"hello"}])
        self.assertEqual(result, expected)
        self.assertEqual(call.call_args.kwargs["provider_override"], "openrouter")
        self.assertEqual(call.call_args.kwargs["model_override"], "openrouter/free")

    def test_auto_mode_falls_back_when_free_provider_is_unavailable(self):
        with patch.object(providers, "credential", side_effect=lambda p: "secret" if p == "openrouter" else None), patch.object(providers, "chat", side_effect=RuntimeError("rate limit")):
            self.assertIsNone(providers.auto_chat([{"role":"user","content":"hello"}]))

    def test_openrouter_only_exposes_free_variants(self):
        response = {"data":[
            {"id":"provider/model:free","name":"Free","pricing":{"prompt":"0","completion":"0"}},
            {"id":"provider/model-paid","name":"Paid","pricing":{"prompt":"0.1","completion":"0.2"}},
            {"id":"provider/model:free-paid","name":"Bad free","pricing":{"prompt":"0.1","completion":"0"}}
        ]}
        with patch.object(providers, "credential", return_value="secret"), patch.object(providers, "_request", return_value=response):
            models = providers.list_models("openrouter")
        ids = {item["id"] for item in models}
        self.assertIn("openrouter/free", ids)
        self.assertIn("provider/model:free", ids)
        self.assertNotIn("provider/model-paid", ids)
        self.assertNotIn("provider/model:free-paid", ids)

    def test_gemini_model_catalog_uses_live_supported_generation_methods(self):
        response = {"models":[
            {"name":"models/gemini-3.8-flash","displayName":"Gemini 3.8 Flash","supportedGenerationMethods":["generateContent"]},
            {"name":"models/gemini-4-argon","displayName":"Gemini 4 Argon","supportedGenerationMethods":["generateContent"]},
            {"name":"models/gemini-embed","supportedGenerationMethods":["embedContent"]}
        ]}
        with patch.object(providers, "credential", return_value="secret"), patch.object(providers, "_request", return_value=response):
            models = providers.list_models("gemini")
        self.assertEqual([item["id"] for item in models], ["gemini-3.8-flash"])

if __name__ == "__main__":
    unittest.main()
