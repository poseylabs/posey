# OLLAMA

## Running Ollama
By default ollama will run an app in the background when installed on Mac that automatically serves any available models. If you don't want to do this (or want to run from terminal to tail logs) you can easily quite this application and run ollama from the command line:

### Starting Ollama serving any available models
```bash
ollama serve
```

### Starting Ollama serving a specific model
```bash
ollama run llama3.2:latest
```

## Managing Models

### Adding Models
```bash
docker ollama pull llama3.2
```

### Running Models

```bash
ollama run llama3.2:latest
```

### Listing Models

```bash
ollama list
```

### Removing Models

```bash
ollama rm llama3.2
```

