# Qwen

- `custom.qwen` connects Muse to Qwen through the Alibaba DashScope OpenAI-compatible API. It authenticates with the registered `api_key` credential and calls only `dashscope-intl.aliyuncs.com`.

- Helpers live in `~/workspace/custom-connectors/custom.qwen/bin/`. `qwen.py` lists models and runs chat completions against the DashScope compatible-mode endpoint.

## Connect

- The connection was registered with `credentials.request_api_access` and these details. Reuse them to reconnect:

```json
{
  "provider": "qwen",
  "auth_scheme": "api_key",
  "placement": "bearer_header",
  "api_hosts": ["dashscope-intl.aliyuncs.com"]
}
```

- The key is read from the registered connection only, never from a file. Helpers get a surrogate from `dynamic_credentials.py`, which places it in the `Authorization: Bearer` header. Muse swaps in the real credential only on an approved request to a registered host.

- A DashScope API key is created in the Alibaba Cloud Model Studio console, in API key management. A ModelScope token is a different credential and does not work here. A key created on the China console does not work on the international endpoint used here.

## Helpers

- Run `qwen.py` from `~/workspace/custom-connectors/custom.qwen/bin/`. It takes `list-models` and `generate --model <model> --prompt <text>`. The default model is `qwen-plus`.

```bash
~/workspace/custom-connectors/custom.qwen/bin/qwen.py list-models
~/workspace/custom-connectors/custom.qwen/bin/qwen.py generate --model qwen-plus --prompt "Hello"
```

- The helper uses `urllib` with redirects disabled and a 60 second timeout. It prints the completion text for `generate` and the JSON model list for `list-models`. It prints `error: ...` to stderr and exits 1 on failure.

## Verified operations

- `list-models` was run on 2026-11-25. The request reached DashScope and came back `HTTP Error 401: Unauthorized`.

- `generate` with model `qwen-plus` was run on 2026-11-25, twice. The first call timed out at 60 seconds. The retry came back `HTTP Error 401: Unauthorized` in under 3 seconds.

- The request was confirmed to carry the `Authorization: Bearer` surrogate, the host is registered, and the placement is `bearer_header`. The 401 means DashScope rejects the stored key value itself. The key submitted on 2026-11-25 is most likely a ModelScope token or a China-region DashScope key, not an international DashScope API key.

- No successful Qwen call has been made with this connector yet. A successful call is still untested.

## Recovery

- On a 401, do not resend the same request unchanged. Ask the user to create a fresh DashScope API key in the Model Studio console on the international side and re-submit it through `credentials.request_api_access` with `reconnect: true`, reusing the details above. Then run `list-models` again as the harmless proof before any real task.

## Related skills

- The Da Qalam AI app (`~/workspace/daqalam/`) uses the same endpoint, model and bearer auth in its own `qwen_client.py`, reading `QWEN_API_KEY` from the environment. The PashtoVoice project (`~/workspace/pashtovoice/`) uses the same DashScope pattern.

- Use `muse.skill_search` to find other skills and `muse.connector_search` to find other connectors.
