from flask import Flask, request, Response, make_response, render_template, stream_with_context
import json, ollama
app = Flask(__name__)

validTokens = ["custom-key"]

def validateApiToken(token:str):
    if token in validTokens:
        return True
    return False

@app.route("/", methods=['GET'])
def availableModels():
    aModels = []
    for i in ollama.list()['models']:
        aModels.append(i.model)
    return render_template('index.html', models=', '.join(aModels))

@app.route("/chat/completions", methods=['POST', 'OPTIONS'])
def chatCompletions():
    if request.method == 'OPTIONS':
        resp = Response()
        resp.access_control_allow_origin = "*"
        resp.access_control_allow_headers = "*"
        resp.access_control_allow_methods = "*"
        return resp
    else:
        if validateApiToken(request.authorization.token):
            print(f"Validated {request.remote_addr} with token({request.authorization.token})...")
            info = request.get_json()
            if not 'max_tokens' in info.values():
                info['max_tokens'] = -1
                
            try:
                modelChat = ollama.chat(
                    model=info['model'],
                    messages=info['messages'],
                    stream=info['stream'],
                    options={'temperature':info['temperature'], "num_predict": info['max_tokens']}
                )
                print(f"Initialized chat for {request.remote_addr}...")
            except ollama.ResponseError:
                return "Whoops. Unsupported model..."
            except Exception as e:
                return f"Internal server error..."
            if info['stream']:
                print(f"Started streaming for {request.remote_addr}...")
                def stream():
                    for part in modelChat:
                        formatedOutput = {
                            "object":"chat.completion.chunk",
                            "created": "fakeid",
                            "model": part.model,
                            "choices":
                            [
                                {
                                    "index": 0,
                                    "delta":{"content":part.message.content},
                                    "logprobs":None,
                                    "finish_reason": part.done_reason
                                }
                            ],
                        }
                        if part.done_reason == None:
                            yield f"data: {json.dumps(formatedOutput)}\n\n"
                        else:
                            yield f"data: {json.dumps(formatedOutput)}\n\n"
                    yield "data: [DONE]\n\n"
                    print(f"Ended streaming for client({request.remote_addr})...")
                return Response(
                    stream_with_context(stream()),
                    content_type='text/event-stream',
                    headers={
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Headers": "*",
                        "Access-Control-Allow-Methods": "*"
                    }
                )
            else:
                print(f"Started generation for {request.remote_addr}...")
                formatedOutput = {
                    "id": "fakeid",
                    "model": info['model'],
                    "object": "chat.completion",
                    "created": "fakeid",
                    "choices": 
                    [
                        {
                            "logprobs": None,
                            "finish_reason": modelChat.done_reason,
                            "native_finish_reason": modelChat.done_reason,
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": modelChat.message.content,
                                "refusal": None,
                                "reasoning": None
                            }
                        }
                    ]
                }
                resp = make_response(formatedOutput)
                resp.content_type = 'application/json'
                resp.access_control_allow_origin = "*"
                resp.access_control_allow_headers = "*"
                resp.access_control_allow_methods = "*"
                return resp
        else:
            raise RuntimeError("Invalid API token")
