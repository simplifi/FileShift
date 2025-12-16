"""
Pytest configuration and shared fixtures for JSON/CSV Converter tests.
"""
import pytest
import json
import csv
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_json_array_file(temp_dir):
    """Create a sample JSON array file."""
    data = [
        {"id": 1, "name": "Alice", "age": 30, "city": "New York"},
        {"id": 2, "name": "Bob", "age": 25, "city": "Los Angeles"},
        {"id": 3, "name": "Charlie", "age": 35, "city": "Chicago"}
    ]
    file_path = temp_dir / "sample_array.json"
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    return file_path


@pytest.fixture
def sample_jsonl_file(temp_dir):
    """Create a sample JSONL (newline-delimited JSON) file."""
    data = [
        {"id": 1, "name": "Alice", "age": 30, "city": "New York"},
        {"id": 2, "name": "Bob", "age": 25, "city": "Los Angeles"},
        {"id": 3, "name": "Charlie", "age": 35, "city": "Chicago"}
    ]
    file_path = temp_dir / "sample.jsonl"
    with open(file_path, 'w', encoding='utf-8') as f:
        for record in data:
            f.write(json.dumps(record) + '\n')
    return file_path


@pytest.fixture
def sample_nested_json_file(temp_dir):
    """Create a JSON file with nested structures."""
    data = [
        {
            "id": 1,
            "user": {
                "name": "Alice",
                "contact": {
                    "email": "alice@example.com",
                    "phone": "123-456-7890"
                }
            },
            "tags": ["python", "data", "analysis"]
        },
        {
            "id": 2,
            "user": {
                "name": "Bob",
                "contact": {
                    "email": "bob@example.com",
                    "phone": "098-765-4321"
                }
            },
            "tags": ["javascript", "web"]
        }
    ]
    file_path = temp_dir / "nested.json"
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    return file_path


@pytest.fixture
def sample_csv_file(temp_dir):
    """Create a sample CSV file."""
    file_path = temp_dir / "sample.csv"
    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['id', 'name', 'age', 'city'])
        writer.writeheader()
        writer.writerow({'id': '1', 'name': 'Alice', 'age': '30', 'city': 'New York'})
        writer.writerow({'id': '2', 'name': 'Bob', 'age': '25', 'city': 'Los Angeles'})
        writer.writerow({'id': '3', 'name': 'Charlie', 'age': '35', 'city': 'Chicago'})
    return file_path


@pytest.fixture
def sample_csv_with_nested_file(temp_dir):
    """Create a CSV file with dot notation for nested fields."""
    file_path = temp_dir / "nested.csv"
    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['id', 'user.name', 'user.contact.email', 'user.contact.phone'])
        writer.writeheader()
        writer.writerow({
            'id': '1',
            'user.name': 'Alice',
            'user.contact.email': 'alice@example.com',
            'user.contact.phone': '123-456-7890'
        })
        writer.writerow({
            'id': '2',
            'user.name': 'Bob',
            'user.contact.email': 'bob@example.com',
            'user.contact.phone': '098-765-4321'
        })
    return file_path


@pytest.fixture
def malformed_json_file(temp_dir):
    """Create a malformed JSON file for error handling tests."""
    file_path = temp_dir / "malformed.json"
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('{"id": 1, "name": "Alice"}\n')
        f.write('{"id": 2, "name": "Bob", invalid json here\n')
        f.write('{"id": 3, "name": "Charlie"}\n')
    return file_path


@pytest.fixture
def mixed_encoding_file(temp_dir):
    """Create a file with non-UTF8 encoding."""
    file_path = temp_dir / "latin1.json"
    data = {"name": "José", "city": "São Paulo"}
    with open(file_path, 'w', encoding='latin-1') as f:
        json.dump(data, f)
    return file_path


@pytest.fixture
def large_jsonl_file(temp_dir):
    """Create a large JSONL file for performance testing."""
    file_path = temp_dir / "large.jsonl"
    with open(file_path, 'w', encoding='utf-8') as f:
        for i in range(10000):
            record = {
                "id": i,
                "name": f"User{i}",
                "email": f"user{i}@example.com",
                "age": 20 + (i % 50),
                "score": i * 1.5,
                "active": i % 2 == 0
            }
            f.write(json.dumps(record) + '\n')
    return file_path