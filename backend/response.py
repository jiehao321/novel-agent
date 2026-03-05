"""
API 标准化响应模块
统一所有API的响应格式、错误处理和字段命名
"""
from datetime import datetime
from typing import Any, Optional, Dict
from fastapi import HTTPException
from fastapi.responses import JSONResponse


# API版本
API_VERSION = "1.0.0"


def success_response(data: Any, message: str = "成功") -> Dict[str, Any]:
    """成功响应格式"""
    return {
        "success": True,
        "message": message,
        "data": data,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": API_VERSION
    }


def error_response(
    code: str,
    message: str,
    details: Optional[Any] = None,
    status_code: int = 400
) -> Dict[str, Any]:
    """错误响应格式"""
    error = {
        "code": code,
        "message": message
    }
    if details:
        error["details"] = details
    
    return {
        "success": False,
        "error": error,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": API_VERSION
    }


def paginated_response(
    items: list,
    page: int = 1,
    page_size: int = 20,
    total: int = 0
) -> Dict[str, Any]:
    """分页响应格式"""
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    
    return success_response({
        "items": items,
        "pagination": {
            "page": page,
            "pageSize": page_size,
            "total": total,
            "totalPages": total_pages
        }
    })


def raise_api_error(code: str, message: str, status_code: int = 400, details: Any = None):
    """抛出标准化API错误"""
    response = error_response(code, message, details, status_code)
    raise HTTPException(status_code=status_code, detail=response)


# 错误码定义
class ErrorCode:
    # 通用错误
    BAD_REQUEST = "BAD_REQUEST"
    NOT_FOUND = "NOT_FOUND"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    
    # 业务错误
    NOVEL_NOT_FOUND = "NOVEL_NOT_FOUND"
    CHAPTER_NOT_FOUND = "CHAPTER_NOT_FOUND"
    NOVEL_NOT_PLANNED = "NOVEL_NOT_PLANNED"
    NOVEL_ALREADY_PLANNED = "NOVEL_ALREADY_PLANNED"
    REVIEW_NOT_FOUND = "REVIEW_NOT_FOUND"
    VOLUME_NOT_FOUND = "VOLUME_NOT_FOUND"


# 字段映射：后端snake_case -> 前端camelCase
def to_camel_case(data: Dict[str, Any]) -> Dict[str, Any]:
    """将snake_case转换为camelCase"""
    if not isinstance(data, dict):
        return data
    
    result = {}
    for key, value in data.items():
        # 转换键名
        camel_key = ''.join(
            word.capitalize() if i > 0 else word 
            for i, word in enumerate(key.split('_'))
        )
        
        # 递归处理嵌套字典和列表
        if isinstance(value, dict):
            result[camel_key] = to_camel_case(value)
        elif isinstance(value, list):
            result[camel_key] = [
                to_camel_case(item) if isinstance(item, dict) else item 
                for item in value
            ]
        else:
            result[camel_key] = value
    
    return result


def from_camel_case(data: Dict[str, Any]) -> Dict[str, Any]:
    """将camelCase转换为snake_case"""
    if not isinstance(data, dict):
        return data
    
    result = {}
    for key, value in data.items():
        # 转换键名
        snake_key = ''
        for i, char in enumerate(key):
            if char.isupper() and i > 0:
                snake_key += '_'
            snake_key += char.lower()
        
        # 递归处理嵌套字典和列表
        if isinstance(value, dict):
            result[snake_key] = from_camel_case(value)
        elif isinstance(value, list):
            result[snake_key] = [
                from_camel_case(item) if isinstance(item, dict) else item 
                for item in value
            ]
        else:
            result[snake_key] = value
    
    return result
