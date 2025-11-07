from parsers.python_parser import parse_python_file
from parsers.javascript_parser import parse_javascript_file


def test_parse_python_file_extracts_routes_and_classes():
    content = """
from fastapi import APIRouter

router = APIRouter()

@router.get("/items")
def list_items():
    pass

class ItemModel(Base):
    ...
"""
    summary = parse_python_file("app/api.py", content)
    assert "list_items" in summary.functions
    assert any("router.get" in route for route in summary.routes)
    assert "ItemModel" in summary.orm_models


def test_parse_javascript_file_detects_routes():
    content = """
import express from 'express';
const app = express();
app.get('/status', (req, res) => res.send('ok'));
"""
    summary = parse_javascript_file("src/server.js", content)
    assert summary.functions == []
    assert any("app.get" in route for route in summary.routes)
