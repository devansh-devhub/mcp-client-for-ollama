# Config.json Guide

This guide explains each field in the `config.json` file and what values you should use for your setup.

## Quick Start - Essential Fields Only

For most use cases, you only need to configure these 3 fields:

### 1. `host` - Ollama Server URL
```json
"host": "http://localhost:11434"
```
- **Default**: `http://localhost:11434`
- **What to fill**: Your Ollama server URL
- **How to find**: 
  - If running Ollama locally: keep as-is
  - If using remote server: `http://your-server-host:port`
  - If using Ollama Cloud: `https://api.ollama.com`

### 2. `model` - Ollama Model
```json
"model": "qwen2.5:7b"
```
- **Default**: `qwen2.5:7b`
- **What to fill**: The model you want to use
- **How to find available models**: Run `ollama list` in your terminal
- **Recommended models for tool use**:
  - `qwen2.5:7b` - Good balance of speed and capability
  - `llama3.2:3b` - Faster, smaller, good for simple tasks
  - `gemma4:9b` - More capable, slower
  - `deepseek-r1:7b` - Good for reasoning tasks

### 3. MCP Server Configuration (choose ONE method)

#### Option A: Auto-discovery (Easiest)
```json
"auto_discovery": true,
"server_paths": [],
"server_urls": [],
"servers_json": null
```
- **When to use**: If you already have Claude Desktop installed with MCP servers configured
- **What happens**: Automatically finds servers from Claude's config file
- **Location**: 
  - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
  - Linux: `~/.config/Claude/claude_desktop_config.json`

#### Option B: Server JSON File
```json
"auto_discovery": false,
"servers_json": "/path/to/your-servers.json",
"server_paths": [],
"server_urls": []
```
- **When to use**: If you have a JSON file with MCP server configurations
- **What to fill**: Full path to your servers JSON file
- **Example servers.json format**:
```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/directory"]
    },
    "github": {
      "type": "streamable_http",
      "url": "https://api.githubcopilot.com/mcp/",
      "headers": {
        "Authorization": "Bearer YOUR_GITHUB_TOKEN"
      }
    }
  }
}
```

#### Option C: Direct Server Paths
```json
"auto_discovery": false,
"server_paths": ["/path/to/server1.py", "/path/to/server2.js"],
"server_urls": [],
"servers_json": null
```
- **When to use**: If you have local MCP server scripts
- **What to fill**: Array of file paths to your server scripts (.py or .js)

#### Option D: Server URLs
```json
"auto_discovery": false,
"server_paths": [],
"server_urls": ["http://localhost:8000/sse", "https://api.example.com/mcp"],
"servers_json": null
```
- **When to use**: If you have HTTP/SSE MCP servers
- **What to fill**: Array of URLs to your MCP servers
- **Common endpoints**: `/sse`, `/mcp`, or `/sse/mcp`

---

## Advanced Configuration

### 4. `systemPrompt` - Model Behavior
```json
"systemPrompt": "You are a helpful assistant that processes alerts and provides concise summaries."
```
- **What to fill**: Instructions for how the model should behave
- **Examples**:
  - Alert summarization: "You are an alert summarization assistant. Provide concise, actionable summaries of alerts."
  - Code analysis: "You are a code review assistant. Focus on security vulnerabilities and best practices."
  - General purpose: "You are a helpful assistant."

### 5. `temperature` - Response Creativity
```json
"temperature": 0.7
```
- **Range**: 0.0 to 1.0
- **What to fill**:
  - `0.0-0.3`: Deterministic, factual responses (good for data extraction)
  - `0.5-0.7`: Balanced creativity (good for most tasks)
  - `0.8-1.0`: Creative, diverse responses (good for brainstorming)

### 6. `top_p` - Sampling Diversity
```json
"top_p": 0.9
```
- **Range**: 0.0 to 1.0
- **What to fill**:
  - `0.1`: Very conservative, focused responses
  - `0.9`: Good default, balanced
  - `1.0`: Maximum diversity

### 7. `num_ctx` - Context Window
```json
"num_ctx": 4096
```
- **What to fill**: Maximum number of tokens the model can consider
- **Recommendations**:
  - `2048`: Simple queries, less memory
  - `4096`: Good default for most tasks
  - `8192+`: Long conversations, complex tasks
- **Note**: Larger values use more memory

### 8. `loopLimit` - Agent Mode Iterations
```json
"loopLimit": 3
```
- **What to fill**: Maximum number of tool calls per query
- **Recommendations**:
  - `1`: Disable agent mode (single tool call only)
  - `3`: Good default for most tasks
  - `5-10`: Complex multi-step tasks
- **What it does**: Controls how many times the model can call tools in a loop

### 9. `hilSettings.enabled` - Human-in-the-Loop
```json
"hilSettings": {
  "enabled": false
}
```
- **CRITICAL for batch mode**: MUST be `false`
- **What it does**: When `false`, tools execute automatically without confirmation
- **When to use**:
  - Batch mode: Always `false`
  - Interactive mode: `true` for safety, `false` for automation

### 10. `contextSettings.retainContext` - Conversation Memory
```json
"contextSettings": {
  "retainContext": false
}
```
- **CRITICAL for batch mode**: Should be `false`
- **What it does**: When `false`, each query is processed independently
- **When to use**:
  - Batch mode: Always `false` (each query is independent)
  - Interactive mode: `true` for multi-turn conversations

---

## Other Model Parameters (Usually Keep Defaults)

These parameters control fine-grained model behavior. For most use cases, keep the defaults:

- `seed`: Random seed (-1 = random, specific number = reproducible)
- `top_k`: Top-k sampling (-1 = disabled)
- `min_p`: Minimum probability threshold (0.0 = disabled)
- `typical_p`: Typical sampling (1.0 = disabled)
- `repeat_last_n`: Repetition check window (0 = disabled)
- `repeat_penalty`: Repetition penalty (1.0 = no penalty)
- `presence_penalty`: New topic penalty (0.0 = no penalty)
- `frequency_penalty`: Frequency penalty (0.0 = no penalty)
- `tfs_z`: Tail free sampling (1.0 = disabled)
- `mirostat`: Mirostat algorithm (0 = disabled)
- `num_batch`: Batch size (2048 = good default)
- `num_gpu`: GPU layers (-1 = all, 0 = CPU only)
- `stop`: Custom stop sequences ([] = none)

---

## Settings Ignored in Batch Mode

These settings are saved in the config file but ignored during batch processing:

- `displaySettings.showToolExecution` - Tool execution display
- `displaySettings.showMetrics` - Performance metrics
- `displaySettings.answerRenderMode` - Answer display mode
- `inputSettings.inputMode` - Chat input mode
- `modelSettings.showThinking` - Thinking text visibility

---

## Example Configurations

### Minimal Config (Alert Summarization)
```json
{
  "host": "http://localhost:11434",
  "model": "qwen2.5:7b",
  "auto_discovery": true,
  "modelConfig": {
    "systemPrompt": "You are an alert summarization assistant. Provide concise, actionable summaries.",
    "temperature": 0.5
  },
  "hilSettings": {
    "enabled": false
  },
  "contextSettings": {
    "retainContext": false
  }
}
```

### Config with Custom MCP Server
```json
{
  "host": "http://localhost:11434",
  "model": "llama3.2:3b",
  "auto_discovery": false,
  "servers_json": "/home/user/mcp-servers.json",
  "modelConfig": {
    "systemPrompt": "You are a helpful assistant.",
    "temperature": 0.7
  },
  "agentSettings": {
    "loopLimit": 5
  },
  "hilSettings": {
    "enabled": false
  },
  "contextSettings": {
    "retainContext": false
  }
}
```

### Config with HTTP Server
```json
{
  "host": "http://localhost:11434",
  "model": "gemma4:9b",
  "auto_discovery": false,
  "server_urls": ["http://localhost:8000/sse"],
  "modelConfig": {
    "systemPrompt": "You are a code analysis assistant.",
    "temperature": 0.3
  },
  "hilSettings": {
    "enabled": false
  },
  "contextSettings": {
    "retainContext": false
  }
}
```

---

## Testing Your Config

After creating your config, test it:

```bash
# Test with a simple query
echo "Hello" | ollmcp batch --config config.json --output-file test.json

# Check the output
cat test.json
```

If it works, you should see a JSON file with the model's response.

---

## Troubleshooting

### "Config file not found"
- Ensure the path to your config file is correct
- Use absolute paths: `/home/user/config.json` not `config.json`

### "Cannot connect to Ollama server"
- Ensure Ollama is running: `ollama serve`
- Check your `host` setting matches your Ollama server

### "No tools are enabled"
- Check your MCP server configuration
- Ensure `auto_discovery` is set correctly
- Verify your servers are running

### "Tool calls skipped by user"
- Ensure `hilSettings.enabled` is `false` in your config

---

## Getting Help

For more information:
- Check the main README.md
- See `misc/batch-config-example.json` for another example
- Run `ollmcp batch --help` for command-line options
