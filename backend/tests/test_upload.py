import io

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield

def test_upload_and_list_csv():
    csv_content = "PD,LGD,EAD\n0.1,0.2,100\n0.05,0.15,200"
    response = client.post(
        "/upload",
        files={"file": ("test.csv", csv_content, "text/csv")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["inserted"] == 2

    response = client.get("/instruments")
    assert response.status_code == 200
    instruments = response.json()
    assert len(instruments) == 2
    assert instruments[0]["pd"] == 0.1
    assert instruments[1]["ead"] == 200.0

def test_upload_missing_columns():
    csv_content = "PD,LGD\n0.1,0.2"
    response = client.post(
        "/upload",
        files={"file": ("test.csv", csv_content, "text/csv")},
    )
    assert response.status_code == 400
    assert "Missing columns" in response.json()["detail"]

def test_upload_non_numeric():
    csv_content = "PD,LGD,EAD\nx,0.2,100"
    response = client.post(
        "/upload",
        files={"file": ("test.csv", csv_content, "text/csv")},
    )
    assert response.status_code == 400
    assert "must be numeric" in response.json()["detail"]

def test_upload_excel(tmp_path):
    df = pd.DataFrame({"PD": [0.3], "LGD": [0.4], "EAD": [300]})
    file_path = tmp_path / "test.xlsx"
    df.to_excel(file_path, index=False)
    with open(file_path, "rb") as f:
        response = client.post(
            "/upload",
            files={"file": ("test.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
    assert response.status_code == 200
    assert response.json()["inserted"] == 1

def test_upload_history_endpoint():
    # Upload a simple CSV
    csv_content = "PD,LGD,EAD\n0.2,0.3,150"
    client.post(
        "/upload",
        files={"file": ("hist.csv", csv_content, "text/csv")},
    )
    response = client.get("/upload-history")
    assert response.status_code == 200
    history = response.json()
    assert len(history) == 1
    assert history[0]["filename"] == "hist.csv"
    assert history[0]["inserted"] == 1

@pytest.mark.parametrize(
    "content, error_msg", [
        ("PD,LGD,EAD\n-0.1,0.2,100", "PD must be between 0 and 1"),
        ("PD,LGD,EAD\n0.2,1.1,100", "LGD must be between 0 and 1"),
        ("PD,LGD,EAD\n0.2,0.2,-5", "EAD must be non-negative"),
    ],
)
def test_upload_invalid_ranges(content, error_msg):
    response = client.post(
        "/upload",
        files={"file": ("test.csv", content, "text/csv")},
    )
    assert response.status_code == 400
    assert error_msg in response.json()["detail"]