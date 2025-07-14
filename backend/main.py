from fastapi import FastAPI,Path,HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel,Field,computed_field
from typing import Annotated,Literal,Optional
import json
app=FastAPI()
class Patient(BaseModel):
    id:Annotated[str,Field(...,description="Id of the patient",example="P001")]
    name:Annotated[str,Field(...,description="Name of the patient")]
    city:Annotated[str,Field(...,description="City of the patient",example="Noida")]
    age:Annotated[int,Field(...,gt=0,lt=120,description="Age of the patient")]
    gender:Annotated[Literal["male","female","others"],Field(...,description="Gender of the patient from male , female,others")]
    height:Annotated[float,Field(...,gt=0,description="Height of the patient in meters")]
    weight:Annotated[float,Field(...,gt=0,description="Weight of the patient in kg")]

    @computed_field(return_type=float)
    @property
    def bmi(self)->float:
        bmi=round(self.weight/(self.height**2),2)
        return bmi
    @computed_field(return_type=str)
    @property
    def verdict(self)->str:
        if self.bmi<18.5:
            return "Underweight"
        elif self.bmi<25:
            return "Normal"
        elif self.bmi<30:
            return "Overweight"
        else:
            return "Obese"
class PatientUpdate(BaseModel):
    name:Annotated[Optional[str],Field(default=None)]
    city:Annotated[Optional[str],Field(default=None)]
    age:Annotated[Optional[int],Field(default=None,gt=0)]
    gender:Annotated[Optional[Literal["male","female","others"]],Field(default=None)]
    height:Annotated[Optional[float],Field(gt=0,default=None)]
    weight:Annotated[Optional[float],Field(gt=0,default=None)]

def load_data():
    with open("patients.json","r") as file:
        data=json.load(file)
        return data
def save_data(data):
    with open("patients.json","w") as file:
        json.dump(data,file)
@app.get("/")
def hello():
    return {"message":"Patient Management System"}
@app.get("/about")
def about():
    return {"message":"A fully functional API for managing your patient records."}
@app.get("/view")
def view():
    data=load_data()
    return data
@app.get("/patient/{id}")
def view_patient(id:str=Path(...,description="ID of the patient in the database",example="P001")):
    data=load_data()
    if id in data:
        return data[id]
    raise HTTPException(status_code=404,detail="Patient not found")
@app.get("/sort")
def sort_patients(sort_by: str=Query(...,description="Sort on the basis Weight, Height or BMI"),order: str=Query("asc",description="sort in asc and desc order.")):
    valid_fields=["height","weight","bmi"]
    if(sort_by not in valid_fields):
        raise HTTPException(status_code=400,detail=f"Invalid field select from {valid_fields}")
    if(order not in ["asc","desc"]):
        raise HTTPException(status_code=400,detail="Invalid order select from asc or desc.")
    data=load_data()
    sort_order=False if order=="asc" else True
    sorted_data=sorted(data.values(),key=lambda x:x.get(sort_by,0),reverse=sort_order)
    return sorted_data
@app.post("/create")
def create_patient(patient:Patient):
    data=load_data()
    if(patient.id in data):
        raise HTTPException(status_code=400,detail="Patient already exist")
    data[patient.id]=patient.model_dump(exclude={"id"})
    save_data(data)
    return JSONResponse(status_code=201,content={"message":"patient created successfully"})

@app.put("/edit/{patient_id}")
def update_patient(patient_id:str,patient_update:PatientUpdate):
    data=load_data()
    if patient_id not in data:
        raise HTTPException(status_code=404,detail="Invalid Patient id")
    existing_patient_info=data[patient_id]
    updated_patient_info=patient_update.model_dump(exclude_unset=True)
    for key,value in updated_patient_info.items():
        existing_patient_info[key]=value
    existing_patient_info["id"]=patient_id
    patient_pydantic_obj=Patient(**existing_patient_info)
    existing_patient_info=patient_pydantic_obj.model_dump(exclude="id")
    data[patient_id]=existing_patient_info
    save_data(data)
    return JSONResponse(status_code=200,content="Patient updated")

@app.delete("/delete/{patient_id}")
def delete_patient(patient_id):
    data=load_data()
    if patient_id not in data:
        raise HTTPException(status_code=404,detail="Invalid patient id")
    del data[patient_id]
    save_data(data)
    return JSONResponse(status_code=200,content="Patient deleted")
