# backend/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from transpiler import transpile_solidity_to_tact
import subprocess
import os
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TranspileRequest(BaseModel):
    code: str

class CompileRequest(BaseModel):
    code: str

@app.post("/compile")
async def compile_tact(request: CompileRequest):
    try:
        # Ensure directories exist
        os.makedirs("contracts", exist_ok=True)

        # Write the contract
        with open("contracts/storage.tact", "w") as f:
            f.write(request.code)

        # Run npm run build
        result = subprocess.run(
            ["npm", "run", "build"],
            capture_output=True,
            text=True
        )

        # If compilation failed, return the error
        if result.returncode != 0:
            raise Exception(result.stderr or result.stdout)

        return {
            "success": True,
            "compiler_output": result.stdout
        }

    except Exception as e:
        print(f"Compilation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/transpile")
async def transpile_code(request: TranspileRequest):
    try:
        tact_code = transpile_solidity_to_tact(request.code)
        return {"success": True, "tact_code": tact_code}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))