"""Tests for batch mode functionality. Copyright 2026 ITTH GmbH & Co. KG"""

import json
import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from rich.console import Console

from mcp_client_for_ollama.client import MCPClient, async_batch_main


@pytest.fixture
def temp_config_file():
    """Create a temporary batch configuration file."""
    config = {
        "host": "http://localhost:11434",
        "model": "qwen2.5:7b",
        "server_paths": [],
        "server_urls": [],
        "servers_json": None,
        "auto_discovery": False,
        "enabledTools": {},
        "modelConfig": {
            "systemPrompt": "Test prompt",
            "temperature": 0.7
        },
        "agentSettings": {
            "loopLimit": 3
        },
        "hilSettings": {
            "enabled": False
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config, f)
        temp_path = f.name
    
    yield temp_path
    
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def temp_output_file():
    """Create a temporary output file path."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name
    
    yield temp_path
    
    if os.path.exists(temp_path):
        os.unlink(temp_path)


def test_batch_command_requires_config():
    """Test that batch command requires a config file."""
    from typer.testing import CliRunner
    from mcp_client_for_ollama.client import app
    
    runner = CliRunner()
    result = runner.invoke(app, ["batch", "--config", "nonexistent.json", "--output-file", "output.json"])
    
    # Should fail because config file doesn't exist
    assert result.exit_code != 0


def test_batch_command_requires_output_file():
    """Test that batch command requires an output file."""
    from typer.testing import CliRunner
    from mcp_client_for_ollama.client import app
    
    runner = CliRunner()
    result = runner.invoke(app, ["batch", "--config", "config.json"])
    
    # Should fail because output file is missing
    assert result.exit_code != 0


def test_batch_config_file_not_found(temp_output_file, monkeypatch):
    """Test that batch mode handles missing config file correctly."""
    import sys
    from io import StringIO
    
    # Mock stdin with a query
    monkeypatch.setattr(sys, 'stdin', StringIO("test query\n"))
    
    with patch('sys.exit') as mock_exit:
        with patch('builtins.print') as mock_print:
            import asyncio
            asyncio.run(async_batch_main(
                "nonexistent_config.json",
                temp_output_file,
                "lines",
                3
            ))
            
            # Should have called sys.exit(1)
            mock_exit.assert_called_once_with(1)
            
            # Should have printed error to stderr
            error_calls = [call for call in mock_print.call_args_list 
                          if 'file' in call.kwargs and call.kwargs['file'] == sys.stderr]
            assert len(error_calls) > 0
            assert "Config file not found" in str(error_calls)


def test_batch_config_invalid_json(temp_config_file, temp_output_file, monkeypatch):
    """Test that batch mode handles invalid JSON in config file."""
    import sys
    from io import StringIO
    
    # Write invalid JSON to config file
    with open(temp_config_file, 'w') as f:
        f.write("{ invalid json")
    
    # Mock stdin with a query
    monkeypatch.setattr(sys, 'stdin', StringIO("test query\n"))
    
    with patch('sys.exit') as mock_exit:
        with patch('builtins.print') as mock_print:
            import asyncio
            asyncio.run(async_batch_main(
                temp_config_file,
                temp_output_file,
                "lines",
                3
            ))
            
            # Should have called sys.exit(1)
            mock_exit.assert_called_once_with(1)
            
            # Should have printed error about invalid JSON
            error_calls = [call for call in mock_print.call_args_list 
                          if 'file' in call.kwargs and call.kwargs['file'] == sys.stderr]
            assert len(error_calls) > 0
            assert "Invalid JSON" in str(error_calls)


def test_batch_no_queries_provided(temp_config_file, temp_output_file, monkeypatch):
    """Test that batch mode handles no queries correctly."""
    import sys
    from io import StringIO
    
    # Mock empty stdin
    monkeypatch.setattr(sys, 'stdin', StringIO(""))
    
    with patch('mcp_client_for_ollama.client.preflight_ollama', return_value=True):
        with patch('mcp_client_for_ollama.client.MCPClient.connect_to_servers', new_callable=AsyncMock):
            with patch('sys.exit') as mock_exit:
                with patch('builtins.print') as mock_print:
                    import asyncio
                    asyncio.run(async_batch_main(
                        temp_config_file,
                        temp_output_file,
                        "lines",
                        3
                    ))
                    
                    # Should have called sys.exit(1)
                    mock_exit.assert_called_once_with(1)
                    
                    # Should have printed error about no queries
                    error_calls = [call for call in mock_print.call_args_list 
                                  if 'file' in call.kwargs and call.kwargs['file'] == sys.stderr]
                    assert len(error_calls) > 0
                    assert "No queries provided" in str(error_calls)


def test_batch_lines_format(temp_config_file, temp_output_file, monkeypatch):
    """Test batch mode with lines input format."""
    import sys
    from io import StringIO
    
    # Mock stdin with multiple queries
    queries = "query 1\nquery 2\nquery 3\n"
    monkeypatch.setattr(sys, 'stdin', StringIO(queries))
    
    with patch('mcp_client_for_ollama.client.preflight_ollama', return_value=True):
        with patch('mcp_client_for_ollama.client.MCPClient.connect_to_servers', new_callable=AsyncMock):
            with patch('mcp_client_for_ollama.client.MCPClient.process_query', new_callable=AsyncMock) as mock_process:
                mock_process.return_value = "response"
                
                with patch('sys.exit') as mock_exit:
                    import asyncio
                    asyncio.run(async_batch_main(
                        temp_config_file,
                        temp_output_file,
                        "lines",
                        3
                    ))
                    
                    # Should have processed 3 queries
                    assert mock_process.call_count == 3
                    
                    # Should not have exited with error
                    mock_exit.assert_not_called()
                    
                    # Check output file was created
                    assert os.path.exists(temp_output_file)
                    
                    # Check output format
                    with open(temp_output_file, 'r') as f:
                        results = json.load(f)
                    assert len(results) == 3
                    assert all('query' in r for r in results)
                    assert all('response' in r for r in results)
                    assert all('success' in r for r in results)


def test_batch_jsonl_format(temp_config_file, temp_output_file, monkeypatch):
    """Test batch mode with JSONL input format."""
    import sys
    from io import StringIO
    
    # Mock stdin with JSONL data
    jsonl_data = '{"query": "query 1", "severity": "critical"}\n{"query": "query 2"}\n'
    monkeypatch.setattr(sys, 'stdin', StringIO(jsonl_data))
    
    with patch('mcp_client_for_ollama.client.preflight_ollama', return_value=True):
        with patch('mcp_client_for_ollama.client.MCPClient.connect_to_servers', new_callable=AsyncMock):
            with patch('mcp_client_for_ollama.client.MCPClient.process_query', new_callable=AsyncMock) as mock_process:
                mock_process.return_value = "response"
                
                with patch('sys.exit') as mock_exit:
                    import asyncio
                    asyncio.run(async_batch_main(
                        temp_config_file,
                        temp_output_file,
                        "jsonl",
                        3
                    ))
                    
                    # Should have processed 2 queries
                    assert mock_process.call_count == 2
                    
                    # Check output file was created
                    assert os.path.exists(temp_output_file)
                    
                    # Check output format
                    with open(temp_output_file, 'r') as f:
                        results = json.load(f)
                    assert len(results) == 2
                    assert results[0]['query'] == "query 1"
                    assert results[1]['query'] == "query 2"


def test_batch_hil_disabled(temp_config_file, temp_output_file, monkeypatch):
    """Test that HIL is disabled in batch mode."""
    import sys
    from io import StringIO
    
    # Mock stdin with a query
    monkeypatch.setattr(sys, 'stdin', StringIO("test query\n"))
    
    with patch('mcp_client_for_ollama.client.preflight_ollama', return_value=True):
        with patch('mcp_client_for_ollama.client.MCPClient.connect_to_servers', new_callable=AsyncMock):
            with patch('mcp_client_for_ollama.client.MCPClient.process_query', new_callable=AsyncMock) as mock_process:
                mock_process.return_value = "response"
                
                # Create a mock client to check HIL state
                with patch('mcp_client_for_ollama.client.MCPClient') as MockClient:
                    mock_client_instance = MagicMock()
                    MockClient.return_value = mock_client_instance
                    mock_client_instance.model_manager.get_current_model.return_value = "test-model"
                    mock_client_instance.tool_manager.get_enabled_tool_objects.return_value = []
                    mock_client_instance.process_query = AsyncMock(return_value="response")
                    
                    with patch('sys.exit'):
                        import asyncio
                        asyncio.run(async_batch_main(
                            temp_config_file,
                            temp_output_file,
                            "lines",
                            3
                        ))
                        
                        # HIL should have been disabled
                        mock_client_instance.hil_manager.set_enabled.assert_called_with(False)


def test_batch_silent_mode_enabled(temp_config_file, temp_output_file, monkeypatch):
    """Test that silent mode is enabled in batch mode."""
    import sys
    from io import StringIO
    
    # Mock stdin with a query
    monkeypatch.setattr(sys, 'stdin', StringIO("test query\n"))
    
    with patch('mcp_client_for_ollama.client.preflight_ollama', return_value=True):
        with patch('mcp_client_for_ollama.client.MCPClient.connect_to_servers', new_callable=AsyncMock):
            with patch('mcp_client_for_ollama.client.MCPClient.process_query', new_callable=AsyncMock) as mock_process:
                mock_process.return_value = "response"
                
                with patch('sys.exit'):
                    import asyncio
                    asyncio.run(async_batch_main(
                        temp_config_file,
                        temp_output_file,
                        "lines",
                        3
                    ))
                    
                    # process_query should have been called with silent_mode=True
                    assert mock_process.call_count == 1
                    call_kwargs = mock_process.call_args.kwargs
                    assert 'silent_mode' in call_kwargs
                    assert call_kwargs['silent_mode'] is True


def test_batch_loop_limit_override(temp_config_file, temp_output_file, monkeypatch):
    """Test that loop limit can be overridden via command line."""
    import sys
    from io import StringIO
    
    # Mock stdin with a query
    monkeypatch.setattr(sys, 'stdin', StringIO("test query\n"))
    
    with patch('mcp_client_for_ollama.client.preflight_ollama', return_value=True):
        with patch('mcp_client_for_ollama.client.MCPClient.connect_to_servers', new_callable=AsyncMock):
            with patch('mcp_client_for_ollama.client.MCPClient.process_query', new_callable=AsyncMock) as mock_process:
                mock_process.return_value = "response"
                
                with patch('mcp_client_for_ollama.client.MCPClient') as MockClient:
                    mock_client_instance = MagicMock()
                    MockClient.return_value = mock_client_instance
                    mock_client_instance.model_manager.get_current_model.return_value = "test-model"
                    mock_client_instance.tool_manager.get_enabled_tool_objects.return_value = []
                    mock_client_instance.process_query = AsyncMock(return_value="response")
                    
                    with patch('sys.exit'):
                        import asyncio
                        # Override loop limit to 5
                        asyncio.run(async_batch_main(
                            temp_config_file,
                            temp_output_file,
                            "lines",
                            5
                        ))
                        
                        # Loop limit should have been set to 5
                        assert mock_client_instance.loop_limit == 5


def test_batch_error_handling(temp_config_file, temp_output_file, monkeypatch):
    """Test that batch mode handles query errors correctly."""
    import sys
    from io import StringIO
    
    # Mock stdin with multiple queries
    queries = "query 1\nquery 2\nquery 3\n"
    monkeypatch.setattr(sys, 'stdin', StringIO(queries))
    
    with patch('mcp_client_for_ollama.client.preflight_ollama', return_value=True):
        with patch('mcp_client_for_ollama.client.MCPClient.connect_to_servers', new_callable=AsyncMock):
            with patch('mcp_client_for_ollama.client.MCPClient.process_query', new_callable=AsyncMock) as mock_process:
                # First query succeeds, second fails, third succeeds
                mock_process.side_effect = ["response 1", Exception("Test error"), "response 3"]
                
                with patch('sys.exit') as mock_exit:
                    import asyncio
                    asyncio.run(async_batch_main(
                        temp_config_file,
                        temp_output_file,
                        "lines",
                        3
                    ))
                    
                    # Should have called sys.exit(1) because of error
                    mock_exit.assert_called_once_with(1)
                    
                    # Check output file contains error details
                    with open(temp_output_file, 'r') as f:
                        results = json.load(f)
                    assert len(results) == 3
                    assert results[0]['success'] is True
                    assert results[1]['success'] is False
                    assert results[1]['error'] == "Test error"
                    assert results[2]['success'] is True


def test_batch_context_retention_disabled(temp_config_file, temp_output_file, monkeypatch):
    """Test that context retention is disabled in batch mode."""
    import sys
    from io import StringIO
    
    # Mock stdin with a query
    monkeypatch.setattr(sys, 'stdin', StringIO("test query\n"))
    
    with patch('mcp_client_for_ollama.client.preflight_ollama', return_value=True):
        with patch('mcp_client_for_ollama.client.MCPClient.connect_to_servers', new_callable=AsyncMock):
            with patch('mcp_client_for_ollama.client.MCPClient.process_query', new_callable=AsyncMock) as mock_process:
                mock_process.return_value = "response"
                
                with patch('mcp_client_for_ollama.client.MCPClient') as MockClient:
                    mock_client_instance = MagicMock()
                    MockClient.return_value = mock_client_instance
                    mock_client_instance.model_manager.get_current_model.return_value = "test-model"
                    mock_client_instance.tool_manager.get_enabled_tool_objects.return_value = []
                    mock_client_instance.process_query = AsyncMock(return_value="response")
                    
                    with patch('sys.exit'):
                        import asyncio
                        asyncio.run(async_batch_main(
                            temp_config_file,
                            temp_output_file,
                            "lines",
                            3
                        ))
                        
                        # Context retention should be disabled
                        assert mock_client_instance.retain_context is False
