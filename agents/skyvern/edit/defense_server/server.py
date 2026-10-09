# inference_server.py
from fastapi import FastAPI
from pydantic import BaseModel
import torch
from transformers import AutoTokenizer
from infer_classifier import InjectionDetector  

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

app = FastAPI()


tokenizer_classifier = AutoTokenizer.from_pretrained("roberta-base")
model_classifier = InjectionDetector()
state = torch.load("/app/injection_detector.pt", map_location="cpu")
model_classifier.load_state_dict(state)
model_classifier = model_classifier.to(device)
model_classifier.half()   
model_classifier.eval()

##################################################################

class Request(BaseModel):
    texts: list[str]

class Response(BaseModel):
    scores: list[float]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/classify")
def classify(req: Request):
    texts = req.texts

    enc = tokenizer_classifier(
        texts,
        truncation=True,
        padding=True,
        return_tensors="pt"
    )
    with torch.no_grad():
        scores = model_classifier(
            input_ids=enc["input_ids"].to(device),
            attention_mask=enc["attention_mask"].to(device)
        ).cpu().numpy().tolist()

    return {"scores": scores}