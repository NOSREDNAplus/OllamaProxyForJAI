# OllamaProxyForJAI
A solution for self hosting LLMs using Ollama and using it as a proxy through Janitorai, re-routes traffic through local host to support generation. Supports text streaming.

## Setup
Once downloading and unzipping the file open a terminal in the current folder and run `python -r requirements.txt` to install the requirements.

Now that the requirements are installed in the same terminal run `python -m fastapi run main.py`, make sure Ollama is running with `ollama -v`.

In order to set it up in Janitorai go to API setting and add a proxy configuration:

Configuration Name: `Custom Proxy` (Can be anything)

Model name: `<insert model name>` (Has to be a model you've pulled using Ollama, find models on the ollama website and pull using `ollama pull <model name>`, if you don't know the models you've pulled use `ollama list`)

Proxy URL: `http://localhost:8000/v1/chat/completions` (Or what ever port it says the fastapi server is running on.)

API Key: `custom-key` (Can be changed in code, but doesn't matter when self hosting.)

After proxy configuration, save changes and settings then refresh the page, the proxy should be working.

NOTE: Only the model `temperature` and `max tokens` can be changed from the `generation settings` menu.
