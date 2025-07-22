# Research to Podcast

Transform academic or technical documents (PDF/Markdown/HTML) into engaging 5-minute conversational podcasts using AI.

## Overview

This project converts research papers, technical documents, and other written content into audio podcasts featuring natural conversations between AI-generated hosts. Choose from solo narration, dual-host discussions, or multi-agent conversations with fact-checking.

## Features

- **Multiple podcast modes**: Solo, dual-host, or multi-agent conversations
- **Flexible input formats**: PDF, Markdown, HTML documents
- **AI-powered script generation**: Uses OpenRouter/OpenAI models for natural dialogue
- **High-quality text-to-speech**: Google Cloud TTS with multiple voice options
- **CLI and web interface**: Command-line tool and React-based dashboard
- **Configurable duration**: Target 5-minute episodes with automatic pacing
- **Cost tracking**: Monitor LLM and TTS usage costs

## Quick Start

### Prerequisites

- Python 3.11+
- uv package manager
- API keys for OpenRouter/OpenAI and Google Cloud TTS

### Installation

```bash
git clone https://github.com/yourusername/researchtopodcast.git
cd researchtopodcast
uv sync
```

### Environment Setup

```bash
export OPENROUTER_API_KEY="your-openrouter-key"
export GOOGLE_TTS_KEY="your-google-tts-key"
```

### Basic Usage

Generate a podcast from a PDF:

```bash
research2podcast generate --input document.pdf --duration 300 --out ./output
```

List available voices:

```bash
research2podcast list-voices
```

Start the web interface:

```bash
research2podcast serve
```

## Podcast Modes

- **Solo**: Single narrator, news-reader style
- **Single-LLM Multi-Speaker**: Two hosts (expert + curious layperson) from one model
- **Multi-Agent Multi-Speaker**: Multiple specialized agents for richer conversations

## Project Structure

```
researchtopodcast/
├── llm_client/          # LLM integration (OpenRouter, OpenAI)
├── script_engine/       # Script generation and personas
├── speech/              # Text-to-speech synthesis
├── cli/                 # Command-line interface
├── api/                 # FastAPI web service
├── frontend/            # React dashboard
└── tests/               # Unit, integration, and E2E tests
```

## Configuration

All settings can be configured via environment variables:

- `OPENROUTER_API_KEY`: OpenRouter API token
- `OPENROUTER_BASE_URL`: Custom endpoint (default: https://openrouter.ai/api/v1)
- `OPENAI_API_KEY`: OpenAI API token (fallback)
- `GOOGLE_TTS_KEY`: Google Cloud TTS credentials
- `PODGEN_MAX_TOKENS`: Token limit per LLM call (default: 4096)
- `PODGEN_TEMP_DIR`: Output directory (default: ./output)

## Development

### Running Tests

```bash
# Unit tests
uv run pytest tests/unit/

# Integration tests
uv run pytest tests/integration/

# All tests
uv run pytest
```

### Code Quality

```bash
# Format code
uv run black .
uv run ruff --fix .

# Type checking
uv run mypy .
```

### Docker Development

```bash
docker compose up
```

Access the web interface at http://localhost:8080

## API Reference

### Generate Podcast

```bash
POST /v1/podcast
{
  "input_url": "path/to/document.pdf",
  "mode": "multi-agent",
  "duration": 300,
  "voices": ["en-US-Standard-A", "en-US-Standard-B"]
}
```

### Check Status

```bash
GET /v1/podcast/{id}
```

### List Voices

```bash
GET /v1/voices
```

## License

Apache 2.0 - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass and code quality checks pass
5. Submit a pull request

## Roadmap

- [x] Phase 0: Project bootstrap
- [ ] Phase 1: LLM integration
- [ ] Phase 2: Script generation
- [ ] Phase 3: TTS integration
- [ ] Phase 4: CLI interface
- [ ] Phase 5: FastAPI service
- [ ] Phase 6: React dashboard
- [ ] Phase 7: End-to-end testing
- [ ] Phase 8: Packaging and release

See `specs/base-app.md` for detailed specifications and development phases.
