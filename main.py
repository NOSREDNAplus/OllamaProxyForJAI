from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import json, ollama
app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def validateApiToken(token:str) -> bool:
    if token == 'custom-key':
        return True
    return False

@app.post('/v1/chat/completions')
async def postchatCompletions(request:Request):
    token = request.headers["authorization"].split(" ")[1]
    if await validateApiToken(token):
        info = await request.json()
        if not 'max_tokens' in info.values():
            info['max_tokens'] = -1    
        try:
            modelChat = ollama.chat(
                model=info['model'],
                messages=info['messages'],
                stream=info['stream'],
                options={'temperature':info['temperature'], "num_predict": info['max_tokens']}
            )
        except ollama.ResponseError:
            return "Whoops. Unsupported model..."
        except Exception:
            return f"Internal server error..."
        if info['stream']:
            def stream():
                for part in modelChat:
                    formatedOutput = {
                        "object":"chat.completion.chunk",
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
            return StreamingResponse(stream(), media_type='text/event-stream')
        else:
            formatedOutput = {
                    "model": info['model'],
                    "object": "chat.completion",
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
            return Response(formatedOutput, media_type='application/json')
    else:
        raise RuntimeError('Invalid auth token...')
