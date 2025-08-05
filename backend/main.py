import os
import stat
import copy
import shutil
import tempfile
import openpyxl
import config as c
import pandas as pd
from shutil import copyfile
from pydantic import BaseModel
from typing import List, Dict, Any
from fastapi.responses import FileResponse, JSONResponse
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

@app.get("/download-country")
def download_country_files(country: str, background_tasks: BackgroundTasks):
    temp_dir = tempfile.mkdtemp()
    try:
        folder_path = os.path.join(c.BASE_DIR, country)        
        internal_folder = os.path.join(temp_dir, country)
        os.makedirs(internal_folder, exist_ok=True)

        files_to_include = [
            f for f in os.listdir(folder_path)
            if os.path.isfile(os.path.join(folder_path, f)) and "{model}" not in f and "{template}" not in f
        ]

        for filename in files_to_include:
            src = os.path.join(folder_path, filename)
            dst = os.path.join(internal_folder, filename)
            shutil.copy(src, dst)

        zip_base = os.path.join(tempfile.gettempdir(), f"{country}_files")
        zip_path = shutil.make_archive(zip_base, 'zip', internal_folder)

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

def sort_fuels(fuels):
    return sorted(fuels, key=lambda x: (x not in c.ELECTRICITY_VARIANTS, x))

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
    
    return {"fuels": sort_fuels(c.FUELS[country][key])}

@app.post("/add-fuels")
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

@app.delete("/delete-fuels")
def delete_fuel(request: FuelRequest):
    fuel = request.fuel.strip()
    country = request.country.strip()

    if not fuel:
        raise HTTPException(status_code=400, detail="Fuel keyword is empty")
    
    if country not in c.FUELS:
        raise HTTPException(status_code=404, detail=f"Country '{country}' not found in fuels.")

    if fuel.lower().startswith("electricity"):
        to_delete = c.ELECTRICITY_VARIANTS
    else:
        to_delete = {fuel}

    deleted = []
    for key in c.FUELS[country]:
        original = c.FUELS[country][key]
        filtered = [f for f in original if f not in to_delete]
        removed = set(original) - set(filtered)
        c.FUELS[country][key] = filtered
        deleted.extend(removed)

    if not deleted:
        raise HTTPException(status_code=404, detail="No matching fuel entries found")

    return {"message": f"Removed entries: {sorted(set(deleted))}"}


# Models (GET, POST, DOWNLOAD, DELETE)
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

    return {"message": f"Model '{model}' created successfully for country '{country}'."}

@app.get("/download-model")
def download_model_files(country:str, model: str, background_tasks: BackgroundTasks):
    temp_dir = tempfile.mkdtemp()
    try:
        folder_path = os.path.join(c.BASE_DIR, country)
        files_to_copy = []

        if model.lower() != "bau":
            for route in c.ROUTES:
                filename = route.format(model=model)
                full_path = os.path.join(folder_path, filename)
                if not os.path.exists(full_path):
                    shutil.rmtree(temp_dir)
                files_to_copy.append(full_path)

        for shared_route in c.SHARED_ROUTES:
            full_path = os.path.join(folder_path, shared_route)
            if os.path.exists(full_path):
                files_to_copy.append(full_path)

        for path in files_to_copy:
            shutil.copy(path, os.path.join(temp_dir, os.path.basename(path)))

        zip_base = os.path.join(tempfile.gettempdir(), f"{country}_{model}_files")
        zip_path = shutil.make_archive(zip_base, 'zip', temp_dir)

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
    
    
# Excel Sheet (Abstract Class) (GET)
class SheetUpdate(BaseModel):
    country: str
    route: str
    template_route: str
    sheet_name: str
    data: List[Dict[str, Any]]
    key_fuels: str

def sync_sheets_with_fuels(country, route, template_route, key_fuels):
    allowed_sheets = c.FUELS.get(country, {}).get(key_fuels, [])
    full_path = os.path.join(c.BASE_DIR, route)
    template_path = os.path.join(c.BASE_DIR, template_route)

    if not os.path.isfile(full_path):
        if not os.path.isfile(template_path):
            raise FileNotFoundError("Template not found")
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        copyfile(template_path, full_path)

    wb = openpyxl.load_workbook(full_path)
    wb_template = openpyxl.load_workbook(template_path)
    changed = False

    for fuel_sheet in allowed_sheets:
        if fuel_sheet not in wb.sheetnames:
            template_sheet = wb_template[fuel_sheet] if fuel_sheet in wb_template.sheetnames else wb_template["Electricity"]
            new_sheet = wb.create_sheet(fuel_sheet)
            for row in template_sheet.iter_rows():
                for cell in row:
                    new_sheet[cell.coordinate].value = cell.value
                    if cell.has_style:
                        new_sheet[cell.coordinate]._style = cell._style

            for col_letter, dimension in template_sheet.column_dimensions.items():
                new_sheet.column_dimensions[col_letter].width = dimension.width
                new_sheet.column_dimensions[col_letter].hidden = dimension.hidden

            changed = True

    sheets_to_delete = [sheet for sheet in wb.sheetnames if sheet not in allowed_sheets]
    for sheet in sheets_to_delete:
        std = wb[sheet]
        wb.remove(std)
        changed = True

    if changed:
        wb.save(full_path)

    wb.close()
    wb_template.close()

    return changed

@app.get("/get-sheet")
def get_sheet(country, route, template_route, sheet_name, key_fuels):
    
    if sheet_name not in c.FUELS.get(country, {}).get(key_fuels, []):
        raise HTTPException(status_code=400, detail="Sheet name not allowed for this fuel and country")

    try:
        sync_sheets_with_fuels(country, route, template_route, key_fuels)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error syncing sheets: {str(e)}")

    full_path = os.path.join(c.BASE_DIR, route)
    df = pd.read_excel(full_path, sheet_name=sheet_name, engine="openpyxl")

    return JSONResponse({"sheet": df.to_dict(orient="records")})

@app.post("/save-sheet")
async def save_sheet(update: SheetUpdate):
    excel_path = os.path.join(c.BASE_DIR, update.route)
    
    if not os.path.isfile(excel_path):
        raise HTTPException(status_code=404, detail="File not found")

    wb = None
    original_sheet = None
    temp_sheet = None
    
    try:
        wb = openpyxl.load_workbook(excel_path)
        if update.sheet_name in wb.sheetnames:
            original_sheet = wb[update.sheet_name]
            
            temp_sheet = wb.create_sheet("temp_style_sheet")
            for row in original_sheet.iter_rows():
                for cell in row:
                    temp_cell = temp_sheet[cell.coordinate]
                    temp_cell.value = cell.value
                    if cell.has_style:
                        temp_cell._style = cell._style
            
            wb.remove(original_sheet)
        
        new_sheet = wb.create_sheet(update.sheet_name)
        df_data = pd.DataFrame(update.data)
        
        if original_sheet:
            for cell in original_sheet[1]:
                new_cell = new_sheet.cell(row=1, column=cell.column, value=cell.value)
                if cell.has_style:
                    new_cell._style = cell._style

        for r_idx, row in enumerate(df_data.itertuples(index=False), start=2):
            for c_idx, value in enumerate(row, start=1):
                cell = new_sheet.cell(row=r_idx, column=c_idx, value=value)
                
                if temp_sheet:
                    temp_cell = temp_sheet.cell(row=r_idx, column=c_idx)
                    if temp_cell.has_style:
                        cell._style = temp_cell._style
        
        if original_sheet:
            for col_letter, dimension in original_sheet.column_dimensions.items():
                new_sheet.column_dimensions[col_letter].width = dimension.width
                new_sheet.column_dimensions[col_letter].hidden = dimension.hidden
        
        if temp_sheet:
            wb.remove(temp_sheet)
        wb.save(excel_path)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving sheet: {str(e)}")
    finally:
        if wb:
            wb.close()
    
    return {"message": f"Sheet '{update.sheet_name}' updated with preserved styles."}

@app.post("/reset-sheet")
async def reset_sheet(update: SheetUpdate):
    excel_path = os.path.join(c.BASE_DIR, update.route)
    template_path = os.path.join(c.BASE_DIR, update.template_route)

    if not os.path.isfile(template_path):
        raise HTTPException(status_code=404, detail="Template file not found")

    if not os.path.isfile(excel_path):
        raise HTTPException(status_code=404, detail="Target file not found")

    try:
        df_new = pd.read_excel(template_path, sheet_name=update.sheet_name, engine="openpyxl")
    except ValueError:
        df_new = pd.read_excel(template_path, sheet_name="Electricity", engine="openpyxl")

    with pd.ExcelWriter(excel_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
        df_new.to_excel(writer, sheet_name=update.sheet_name, index=False)

    return {"message": f"Sheet '{update.sheet_name}' in '{update.route}' reset successfully."}
