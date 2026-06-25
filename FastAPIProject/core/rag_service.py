import os
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from settings import CHROMA_RAG_DB_PATH


# 初始化嵌入模型 (复用之前配置好的 nomic-embed-text)
embedding_model = OllamaEmbeddings(model="nomic-embed-text")
DB_PATH = str(CHROMA_RAG_DB_PATH)


# 把数据存储到语义数据库
def process_and_stor_file(file_path, user_id, task_id=None, project_id=None):
     """ 后台任务：解析文件并存入该用户的专属向量库"""

     suffix = Path(file_path).suffix.lower()
     if suffix == ".pdf":
         doc = PyPDFLoader(file_path).load()
     elif suffix == ".txt":
         doc = TextLoader(file_path,encoding="utf-8").load()
     else:
         raise ValueError("Unsupported knowledge file format")

     collection_name = f"user_{user_id}_docs"
     doc_spliter = RecursiveCharacterTextSplitter(
         chunk_size=300,
         chunk_overlap=50,
         add_start_index=True
     )
     all_docs = doc_spliter.split_documents(doc)
     if not all_docs:
         raise ValueError("No readable content found in uploaded file")
     for item in all_docs:
         item.metadata.update({
             "user_id": int(user_id),
             "task_id": int(task_id) if task_id is not None else 0,
             "project_id": int(project_id) if project_id is not None else 0,
             "source": os.path.abspath(file_path),
         })



     my_company_collection = Chroma(
         collection_name=collection_name,
         embedding_function=embedding_model,
         persist_directory=DB_PATH
     )

     if task_id is not None:
         try:
             my_company_collection.delete(where={"task_id": int(task_id)})
         except Exception:
             pass

     ids = None
     if task_id is not None:
         ids = [f"user_{user_id}_task_{task_id}_chunk_{index}" for index, _ in enumerate(all_docs)]
     my_company_collection.add_documents(all_docs, ids=ids)
     return {
         "chunk_count": len(all_docs),
         "parse_log": f"Parsed {len(doc)} document page(s) into {len(all_docs)} chunk(s).",
     }


def delete_task_vectors(user_id, task_id):
    collection_name = f"user_{user_id}_docs"
    my_company_collection = Chroma(
        collection_name=collection_name,
        embedding_function=embedding_model,
        persist_directory=DB_PATH
    )
    try:
        my_company_collection.delete(where={"task_id": int(task_id)})
    except Exception:
        return False
    return True


def retrive_user_from_knowledge(user_id,search_query, active_task_ids=None, project_id=None):
    """
    供智能体调用的检索工具：只查当前用户的专属知识库
    """
    # 指定白哦名称
    collection_name = f"user_{user_id}_docs"

    my_company_collection = Chroma(
        collection_name=collection_name,
        embedding_function=embedding_model,
        persist_directory=DB_PATH
    )

    if active_task_ids is not None and not active_task_ids:
        return "当前没有启用且解析完成的知识库文件。"

    search_kwargs = {"k": 2}
    if active_task_ids:
        active_task_ids = [int(task_id) for task_id in active_task_ids]
        task_filter = (
            {"task_id": active_task_ids[0]}
            if len(active_task_ids) == 1
            else {"task_id": {"$in": active_task_ids}}
        )
        if project_id is not None:
            search_kwargs["filter"] = {"$and": [task_filter, {"project_id": int(project_id)}]}
        else:
            search_kwargs["filter"] = task_filter

    result_docs = my_company_collection.similarity_search(search_query, **search_kwargs)
    if not result_docs:
        return "未在您的知识库中检索到相关信息。"

    context = "\n\n".join(
        f"【您的专属参考资料】:\n{doc.page_content}" for doc in result_docs
    )
    return context
