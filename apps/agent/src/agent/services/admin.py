from connectrpc.request import RequestContext
from sqlalchemy import select, func
from google.protobuf.timestamp_pb2 import Timestamp

import os
from pathlib import Path

import agent.gen.admin.v1.admin_pb2 as admin_pb2
from agent.gen.admin.v1.admin_connect import AdminService as AdminServiceProtocol
from agent.infrastructure.database import DocumentModel, async_session
from agent.config.settings import settings
from agent.memory.store import delete_source
from agent.retrieval.hybrid import get_bm25_index

class AdminService(AdminServiceProtocol):
    async def list_documents(
        self, 
        request: admin_pb2.ListDocumentsRequest, 
        ctx: RequestContext
    ) -> admin_pb2.ListDocumentsResponse:
        async with async_session() as session:
            # Query
            stmt = select(DocumentModel).order_by(DocumentModel.created_at.desc())
            
            # Pagination
            page_size = request.page_size or 10
            page = request.page or 1
            stmt = stmt.offset((page - 1) * page_size).limit(page_size)
            
            result = await session.execute(stmt)
            docs = result.scalars().all()
            
            # Total count
            count_stmt = select(func.count()).select_from(DocumentModel)
            count_result = await session.execute(count_stmt)
            total_count = count_result.scalar()
            
            response_docs = []
            for d in docs:
                created_at = Timestamp()
                created_at.FromDatetime(d.created_at)
                updated_at = Timestamp()
                updated_at.FromDatetime(d.updated_at)
                
                response_docs.append(admin_pb2.Document(
                    id=str(d.id),
                    filename=d.filename,
                    status=d.status,
                    created_at=created_at,
                    updated_at=updated_at,
                    metadata={} # TODO: map metadata_json if needed
                ))
                
            return admin_pb2.ListDocumentsResponse(
                documents=response_docs,
                total_count=total_count
            )

    async def upload_document(
        self, 
        request: admin_pb2.UploadDocumentRequest, 
        ctx: RequestContext
    ) -> admin_pb2.UploadDocumentResponse:
        try:
            # Create upload directory
            upload_path = Path(settings.upload_dir)
            upload_path.mkdir(parents=True, exist_ok=True)
            
            # Sanitize filename (basic)
            filename = os.path.basename(request.filename)
            file_path = upload_path / filename
            
            # Write file
            with open(file_path, "wb") as f:
                f.write(request.content)
            
            async with async_session() as session:
                new_doc = DocumentModel(
                    filename=request.filename,
                    status="PROCESSING",
                )
                session.add(new_doc)
                await session.commit()
                await session.refresh(new_doc)
                
                # Ingest (Now using async versions)
                try:
                    is_pdf = filename.lower().endswith(".pdf") or request.content_type == "application/pdf"
                    
                    from agent.loaders import aingest_pdf, aingest_text
                    
                    if is_pdf:
                        await aingest_pdf(str(file_path))
                    else:
                        await aingest_text(str(file_path))
                        
                    new_doc.status = "COMPLETED"
                except Exception as e:
                    print(f"Ingestion failed: {e}")
                    new_doc.status = "FAILED"
                    # Capture error in metadata if model supported it
                
                await session.commit()
                
                return admin_pb2.UploadDocumentResponse(
                    id=str(new_doc.id),
                    status=new_doc.status
                )
        except Exception as e:
            print(f"Upload failed: {e}")
            raise e

    async def delete_document(
        self, 
        request: admin_pb2.DeleteDocumentRequest, 
        ctx: RequestContext
    ) -> admin_pb2.DeleteDocumentResponse:
        async with async_session() as session:
            doc = await session.get(DocumentModel, request.id)
            if doc:
                source_name = doc.filename
                await session.delete(doc)
                await session.commit()
                # Clean up vector stores
                delete_source(source_name)
                get_bm25_index().delete_by_source(source_name)
                return admin_pb2.DeleteDocumentResponse(success=True)
            return admin_pb2.DeleteDocumentResponse(success=False)

    async def get_ingestion_status(
        self, 
        request: admin_pb2.GetIngestionStatusRequest, 
        ctx: RequestContext
    ) -> admin_pb2.GetIngestionStatusResponse:
        async with async_session() as session:
            doc = await session.get(DocumentModel, request.id)
            if doc:
                return admin_pb2.GetIngestionStatusResponse(
                    id=str(doc.id),
                    status=doc.status
                )
            return admin_pb2.GetIngestionStatusResponse(
                id=request.id,
                status="NOT_FOUND"
            )
