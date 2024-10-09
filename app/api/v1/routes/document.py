from datetime import datetime, UTC
from app.utils.logger import Logger
from fastapi import (
    APIRouter, Depends,
    status, HTTPException
)
from app.core.security import is_admin, is_authenticated
from app.api.v1.controllers.document import (
    add_document,
    retrieve_documents,
    retrieve_document_by_id,
    update_document,
    delete_document_by_id,
)
from app.schemas.document import (
    DocumentSchema,
    DocumentSchemaDB,
    UpdateDocumentSchema,
    UpdateDocumentSchemaDB
)
from app.schemas.response import (
    DictResponseModel,
    ListResponseModel
)
from app.utils.time import local_to_utc

router = APIRouter()
logger = Logger("routes/meeting", log_file="meeting.log")


@router.post("",
             dependencies=[Depends(is_admin)],
             tags=["Admin"],
             description="Add a new document")
async def create_document(document_data: DocumentSchema,
                          creator_id: str = Depends(is_authenticated)):
    document_db = DocumentSchemaDB(
        file_name=document_data.file_name,
        meeting_id=document_data.meeting_id,
        mask_url=document_data.mask_url,
        creator_id=creator_id,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )
    new_document = await add_document(document_db.model_dump())
    if isinstance(new_document, Exception):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Add document failed"
        )
    return DictResponseModel(
        data=new_document,
        message="Document added successfully",
        code=status.HTTP_201_CREATED
    )
    

@router.get("",
            dependencies=[Depends(is_authenticated)],
            description="Retrieve all documents")
async def get_documents():
    documents = await retrieve_documents()
    if isinstance(documents, Exception):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Retrieve documents failed"
        )
    return ListResponseModel(
        data=documents,
        message="Documents retrieved successfully",
        code=status.HTTP_200_OK
    )


@router.get("/{id}",
            dependencies=[Depends(is_authenticated)],
            description="Retrieve a document by id")
async def get_document_by_id(id: str):
    document = await retrieve_document_by_id(id)
    if isinstance(document, Exception):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Retrieve document failed"
        )
    return DictResponseModel(
        data=document,
        message="Document retrieved successfully",
        code=status.HTTP_200_OK
    )


@router.put("/{id}",
            dependencies=[Depends(is_admin)],
            description="Update a document by id")
async def update_document_data(id: str, 
                               document_data: UpdateDocumentSchema,
                               creator_id: str = Depends(is_authenticated)):
    
    new_document_data = UpdateDocumentSchemaDB(
        file_name=document_data.file_name,
        meeting_id=document_data.meeting_id,
        mask_url=document_data.mask_url,
        creator_id=creator_id,
        updated_at=datetime.now(UTC)
    ).model_dump()
    document = await update_document(id, new_document_data)
    if isinstance(document, Exception):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Update document failed"
        )
    return DictResponseModel(
        data=document,
        message="Document updated successfully",
        code=status.HTTP_200_OK
    )


@router.delete("/{id}",
                dependencies=[Depends(is_admin)],
                description="Delete a document by id")
async def delete_document(id: str):
    document = await delete_document_by_id(id)
    if isinstance(document, Exception):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Delete document failed"
        )
    return DictResponseModel(
        data=[],
        message="Document deleted successfully",
        code=status.HTTP_200_OK
    )

                         