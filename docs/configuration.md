# Configuration reference

The public `.env.example` contains only blank placeholders:

| Name | Role |
|---|---|
| `LLM_MODEL` | Model identifier used by the model client. |
| `LLM_BASE_URL` | Model-provider endpoint. |
| `LLM_API_KEY` | Provider credential. Keep the real value private. |
| `COMMERCE_API_BASE_URL` | Mock commerce service address. |
| `DATABASE_URL` | Database connection setting. |
| `APP_HOST` | Listening interface. |
| `APP_PORT` | Listening port. |

The supplied project configuration identified DeepSeek, but the actual API key and database credentials are intentionally withheld. This repository should never contain a real `.env`, API key, password, token, cookie or private path.

The complete course application startup instructions are also intentionally not republished here because the full source is withheld and its redistribution permission was not established from the supplied materials.
