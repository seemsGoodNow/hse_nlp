import json
from typing import Dict

import uvicorn
from fastapi import FastAPI, Request, Depends
from contextlib import asynccontextmanager
import pymorphy3
from src.models import TextRequest, LinksResponse
import src.law_link_parser as parser


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    with open("data/law_alias_to_id.json", "r") as file:
        law_alias_to_id = json.load(file)
    morph = pymorphy3.MorphAnalyzer()
    app.state.law_alias_to_id = law_alias_to_id
    app.state.morph = morph
    print("🚀 Сервис запускается...")
    yield
    # Shutdown
    del law_alias_to_id
    del morph
    print("🛑 Сервис завершается...")


def get_law_alias_to_id(request: Request) -> Dict:
    return request.app.state.law_alias_to_id


def get_morph(request: Request) -> pymorphy3.MorphAnalyzer:
    return request.app.state.morph


app = FastAPI(
    title="Law Links Service",
    description="Cервис для выделения юридических ссылок из текста",
    version="1.0.0",
    lifespan=lifespan,
)


@app.post("/detect")
async def get_law_links(
    data: TextRequest,
    request: Request,
    law_alias_to_id: Dict = Depends(get_law_alias_to_id),
    morph: Dict = Depends(get_morph),
) -> LinksResponse:
    """
    Принимает текст и возвращает список юридических ссылок
    """
    # Место для алгоритма распознавания ссылок
    normalized_text = parser.normalize_input_text(
        morph=morph, input_text_corpus=data.text
    )
    raw_links = parser.extract_raw_links(normalized_text)
    processed_links = parser.process_raw_links(
        raw_links, law_alias_to_id=law_alias_to_id
    )

    processed_links = sorted(
        processed_links, key=lambda x: normalized_text.index(x.article or "")
    )

    return LinksResponse(links=processed_links)


@app.get("/health")
async def health_check():
    """
    Проверка состояния сервиса
    """
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8978)
