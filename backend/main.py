import os
import stat
import copy
import shutil
import tempfile
import config as c
from pydantic import BaseModel
from fastapi.responses import FileResponse
from fastapi import FastAPI, HTTPException, BackgroundTasks


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
            raise HTTPException(status_code=500, detail=f"Error deleting folder: {e}")
        
    return {"message": f"Country '{country}' deleted."}


# Fuels (GET, POST, DELETE)
class FuelRequest(BaseModel):
    fuel: str
    country: str

@app.get("/fuels")
def get_fuels(key, country):
    key = key.strip()
    country = country.strip()

    if country not in c.FUELS:
        if "template" not in c.FUELS:
            raise HTTPException(status_code=500, detail="Template country not available.")
        c.FUELS[country] = copy.deepcopy(c.FUELS["template"])

    if key not in c.FUELS[country]:
        raise HTTPException(status_code=404, detail=f"Key '{key}' not found in country '{country}'.")
    
    return {"fuels": c.FUELS[country][key]}

@app.post("/fuels")
def add_fuel(request: FuelRequest):
    fuel = request.fuel.strip()
    country = request.country.strip()

    if not fuel:
        raise HTTPException(status_code=400, detail="Fuel name is empty")

    if country not in c.FUELS:
        raise HTTPException(status_code=404, detail=f"Country '{country}' not found in fuels.")

    added_to = []
    for key in c.FUELS[country]:
        if fuel == "Electricity":
            if key == "expanded":
                values = ["Electricity & E-Cooking", "Electricity (Just access)"]
            elif key == "more_expanded":
                values = ["Electricity (Only E-Cooking)", "Electricity & E-Cooking", "Electricity (Just access)"]
            else:
                values = ["Electricity"]
        else:
            values = [fuel]

        for v in values:
            if v not in c.FUELS[country][key]:
                c.FUELS[country][key].append(v)
                added_to.append((key, v))

    if not added_to:
        return {"message": f"Fuel already present in all lists for {country}."}
    return {"message": f"Fuel added to {country}: {added_to}"}

@app.delete("/fuels")
def delete_fuel(request: FuelRequest):
    fuel = request.fuel.strip()
    country = request.country.strip()

    if not fuel:
        raise HTTPException(status_code=400, detail="Fuel keyword is empty")
    
    if country not in c.FUELS:
        raise HTTPException(status_code=404, detail=f"Country '{country}' not found in fuels.")

    deleted = []
    for key in c.FUELS[country]:
        original = c.FUELS[country][key]
        filtered = [f for f in original if fuel.lower() not in f.lower()]
        removed = set(original) - set(filtered)
        c.FUELS[country][key] = filtered
        deleted.extend(removed)

    if not deleted:
        raise HTTPException(status_code=404, detail="No matching fuel entries found")

    return {"message": f"Removed entries: {sorted(set(deleted))}"}


# Models (GET)
class ModelRequest(BaseModel):
    country: str
    model: str

@app.get("/models")
def get_models(country):
    country = country.strip()
    if country not in c.MODELS:
        c.MODELS[country] = []
    
    return {"models": c.MODELS[country]}

@app.post("/model")
async def create_model(country: str, model: str, start_year: int, end_year: int):
    country = country.strip()
    model = model.strip()

    if model.lower() == "bau":
        if country not in c.COUNTRY_YEAR_RANGES:
            c.COUNTRY_YEAR_RANGES[country] = {
                "start": start_year,
                "end": end_year
            }
            c.MODELS[country] = ["BAU"]

    else:
        expected_range = c.COUNTRY_YEAR_RANGES[country]
        if start_year != expected_range["start"] or end_year != expected_range["end"]:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Year range mismatch. Expected "
                    f"{expected_range['start']}–{expected_range['end']}, "
                    f"got {start_year}–{end_year}."
                )
            )
        
        for route in c.ROUTES:
            src_path = os.path.join(c.BASE_DIR, country, route)
            dst_path = os.path.join(c.BASE_DIR, country, route.format(model=model))

            if os.path.exists(src_path):
                shutil.copy(src_path, dst_path)
            else:
                raise HTTPException(status_code=404, detail=f"Template file not found: {src_path}")
                
        c.MODELS[country].append(model)

    for route in c.SHARED_ROUTES:
        # Aqui va la logica de añadir lineas
        pass

    return {"message": f"Model '{model}' created successfully for country '{country}'."}

@app.get("/download-model")
def download_model_files(country:str, model: str, background_tasks: BackgroundTasks):
    temp_dir = tempfile.mkdtemp()
    try:
        paths = []
        if model.lower() != "bau":
            for route in c.ROUTES:
                filename = route.format(model=model)
                full_path = os.path.join(c.BASE_DIR, country, filename)
                paths.append(full_path)

        for route in c.SHARED_ROUTES:
            full_path = os.path.join(c.BASE_DIR, country, route)
            paths.append(full_path)

        for path in paths:
            if not os.path.exists(path):
                shutil.rmtree(temp_dir)
                raise HTTPException(status_code=404, detail=f"Missing file: {path}")
            shutil.copy(path, os.path.join(temp_dir, os.path.basename(path)))

        zip_path = os.path.join(tempfile.gettempdir(), f"{country}_{model}_files.zip")
        shutil.make_archive(zip_path.replace(".zip", ""), 'zip', temp_dir)

        background_tasks.add_task(os.remove, zip_path)
        shutil.rmtree(temp_dir)

        return FileResponse(
            zip_path,
            media_type="application/zip",
            filename=os.path.basename(zip_path)
        )

    except Exception as e:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/model")
def delete_model(request: ModelRequest):
    country = request.country.strip()
    model = request.model.strip()

    if model.lower() == "bau":
        c.MODELS.pop(country, None)
        c.COUNTRY_YEAR_RANGES.pop(country, None)
    else:
        for route in c.ROUTES:
            file_path = os.path.join(c.BASE_DIR, country, route.format(model=model))
            if os.path.exists(file_path):
                os.remove(file_path)

        c.MODELS[country].remove(model)

        # Aquí iría la gestión de archivos en c.SHARED_ROUTES

    return {"message": f"Model '{model}' deleted successfully for country '{country}'."}
    
    
