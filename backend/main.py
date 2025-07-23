from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import shutil
import os
import config as c

app = FastAPI()

# Countries (GET, POST, COPY)
class CountryRequest(BaseModel):
    name: str

@app.get("/countries")
def get_countries():
    return {"countries": c.COUNTRIES}

@app.post("/countries")
def add_country(request: CountryRequest):
    new_country = request.name.strip()
    if not new_country:
        raise HTTPException(status_code=400, detail="Country name empty")
    if new_country in c.COUNTRIES:
        raise HTTPException(status_code=400, detail="Country already exists")

    c.COUNTRIES.append(new_country)
    return {"message": f"Country '{new_country}' added."}

@app.delete("/countries")
def delete_country(request: CountryRequest):
    country = request.name.strip()
    if country not in c.COUNTRIES:
        raise HTTPException(status_code=404, detail="Country not found")

    c.COUNTRIES.remove(country)

    # Eliminar carpeta si existe
    return {"message": f"Country '{country}' deleted."}