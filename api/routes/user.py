from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from pydantic import BaseModel, Field
from typing import List, Optional
from bson import ObjectId

from db import mongo_collection
from auth.security import create_access_token, verify_password, hash_password

router = APIRouter(prefix="/users", tags=["Users"])

class Token(BaseModel):
    access_token: str
    token_type: str
    user_info: dict

class UserBase(BaseModel):
    username: str
    fullName: str
    email: str
    role: str

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    fullName: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    password: Optional[str] = None

class UserInDB(UserBase):
    id: str = Field(..., alias="_id")
    class Config:
        from_attributes = True
        # Mapea _id de MongoDB a un campo que no comience con guion bajo
        populate_by_name = True
        json_encoders = {
            'ObjectId': str,
        }

@router.post("/login", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Autentica un usuario y devuelve un token JWT.
    FastAPI espera un form-data con 'username' y 'password'.
    El frontend puede enviar el email en el campo 'username'.
    """
    # Buscar usuario por email (que viene en el campo 'username' del form)
    user = mongo_collection.find_one({"email": form_data.username})

    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Verificar la contraseña
    if not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Contraseña incorrecta")

    # Crear el token JWT
    access_token = create_access_token(data={"sub": user["username"], "role": user["role"]})

    # Devolver el token y la información del usuario
    user_info = {"fullName": user["fullName"], "email": user["email"], "role": user["role"]}
    
    return {"access_token": access_token, "token_type": "bearer", "user_info": user_info}

# Esquema de seguridad para obtener el token de la cabecera
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/users/login")


@router.get("", response_model=List[UserInDB])
def read_users(token: str = Depends(oauth2_scheme)):
    """
    Obtiene una lista de todos los usuarios del sistema.
    Ruta protegida que requiere autenticación.
    """
    # La dependencia oauth2_scheme ya valida que el token exista.
    # Aquí podrías añadir una validación más profunda del token si quisieras.
    
    users = []
    for user in mongo_collection.find():
        # Asegurarse de que el _id se pueda serializar
        user['_id'] = str(user['_id'])
        users.append(UserInDB(**user))
    return users

@router.post("", response_model=UserInDB)
def create_user(user: UserCreate, token: str = Depends(oauth2_scheme)):
    """
    Crea un nuevo usuario en el sistema.
    """
    # Verificar si el username o email ya existen
    if mongo_collection.find_one({"username": user.username}):
        raise HTTPException(status_code=400, detail="El nombre de usuario ya está en uso.")
    if mongo_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="El correo electrónico ya está en uso.")

    hashed_pass = hash_password(user.password)
    user_doc = user.model_dump()
    del user_doc["password"]
    user_doc["password_hash"] = hashed_pass

    result = mongo_collection.insert_one(user_doc)
    created_user = mongo_collection.find_one({"_id": result.inserted_id})
    
    # Convertir el ObjectId a string antes de pasarlo al modelo Pydantic
    created_user['_id'] = str(created_user['_id'])

    return UserInDB(**created_user)

@router.put("/{user_id}", response_model=UserInDB)
def update_user(user_id: str, user_update: UserUpdate, token: str = Depends(oauth2_scheme)):
    """
    Actualiza la información de un usuario.
    """
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="ID de usuario inválido.")

    update_data = user_update.model_dump(exclude_unset=True)

    # Si se proporciona una nueva contraseña, hashearla
    if "password" in update_data and update_data["password"]:
        update_data["password_hash"] = hash_password(update_data["password"])
        del update_data["password"]
    elif "password" in update_data:
        del update_data["password"] # No actualizar si está vacía

    updated_user = mongo_collection.find_one_and_update(
        {"_id": ObjectId(user_id)},
        {"$set": update_data},
        return_document=True
    )

    if not updated_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    # Convertir el ObjectId a string antes de pasarlo al modelo Pydantic
    updated_user['_id'] = str(updated_user['_id'])

    return UserInDB(**updated_user)

@router.delete("/{user_id}", status_code=204)
def delete_user(user_id: str, token: str = Depends(oauth2_scheme)):
    """
    Elimina un usuario del sistema.
    """
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="ID de usuario inválido.")

    delete_result = mongo_collection.delete_one({"_id": ObjectId(user_id)})

    if delete_result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    
    return None
