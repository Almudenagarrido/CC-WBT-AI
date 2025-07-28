from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import config as c
import shutil
import os
import stat


app = FastAPI()


# Countries (GET, POST, COPY, DELETE)
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

@app.post("/countries/{country}")
def create_templates_for_country(country: str):
    dst = os.path.join(c.BASE_DIR, country)
    if os.path.exists(dst):
        return {"message": f"Templates for '{country}' already exist."}
    
    try:
        shutil.copytree(c.TEMPLATES_DIR, dst)
        return {"message": f"Templates for '{country}' created."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error copying templates: {e}")

def remove_readonly(func, path, excinfo):
    os.chmod(path, stat.S_IWRITE)
    func(path)

@app.delete("/countries")
def delete_country(request: CountryRequest):
    country = request.name.strip()
    if country not in c.COUNTRIES:
        raise HTTPException(status_code=404, detail="Country not found")

    c.COUNTRIES.remove(country)

    folder = os.path.join(c.BASE_DIR, country)
    if os.path.exists(folder) and os.path.isdir(folder):
        try:
            shutil.rmtree(folder, onerror=remove_readonly)
        except Exception as e:
            print(f"Error deleting folder '{folder}': {e}")
            raise HTTPException(status_code=500, detail=f"Error deleting folder: {e}")
        
    return {"message": f"Country '{country}' deleted."}