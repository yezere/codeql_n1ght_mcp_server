# CodeQL N1ght MCP Server

A Model Context Protocol (MCP) server for integrating CodeQL N1ght tool with AI assistants.

## Overview

This MCP server provides a standardized interface for AI assistants to interact with the CodeQL N1ght tool, enabling automated code analysis workflows including environment setup, database creation, and security scanning.

## Features

- **Environment Installation**: One-click setup of JDK, Ant, and CodeQL dependencies
- **Database Creation**: Create CodeQL databases from JAR/WAR/ZIP files with configurable decompilers
- **Security Scanning**: Execute security scans with customizable query packs
- **Parallel Processing**: Support for goroutines and multi-threading
- **Flexible Configuration**: Customizable paths, timeouts, and caching options

## Available Tools

### `version`
Get version or help information from the CodeQL N1ght executable.

### `install_environment`
Install required dependencies (JDK, Ant, CodeQL) with optional custom URLs.

### `create_database`
Create a CodeQL database from target files (JAR/WAR/ZIP) with options for:
- Decompiler selection (procyon/fernflower)
- Dependency handling (none/all)
- Parallel processing
- Cache management

### `scan_database`
Execute security scans on CodeQL databases with configurable:
- Database and query pack paths
- Parallel processing options
- Cache control

### `run_codeql_n1ght`
Generic interface for direct command execution with custom arguments.

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure the CodeQL N1ght executable is available at the configured path (default: `J:\mcp\codeql-n1ght.exe`)

## Usage

Run the MCP server in STDIO mode:

```bash
python codeql_n1ght_mcp_server.py
```

## Configuration

- **Default Executable Path**: `J:\mcp\codeql-n1ght.exe`
- **Path Compatibility**: Supports both Windows (`J:\path`) and Unix-style (`/j:/path`) path formats
- **Timeouts**: Configurable per operation (default: 10 minutes for general operations, 20 hours for database/scan operations)

## Response Format

All tools return a standardized response format:
```json
{
  "returncode": 0,
  "stdout": "command output",
  "stderr": "error output",
  "timeout": false
}
```

## Error Handling

- **Executable Not Found**: Returns error if CodeQL N1ght executable is missing
- **Invalid Parameters**: Validates decompiler and dependency options
- **Timeout Management**: Configurable timeouts with process termination
- **Path Resolution**: Automatic path normalization and validation

## License

This project is open source and available under the MIT License.