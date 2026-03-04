"""
并发控制和资源管理
"""
import asyncio
from typing import List, Callable, Any
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
import signal
import threading


class ConcurrencyManager:
    """并发控制管理器"""
    
    def __init__(self, max_concurrent: int = 8, timeout_seconds: int = 30):
        self.max_concurrent = max_concurrent
        self.timeout_seconds = timeout_seconds
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent)
    
    async def run_with_concurrency(self, func: Callable, *args, **kwargs) -> Any:
        """使用并发控制运行"""
        async with self.semaphore:
            return await asyncio.wait_for(
                asyncio.to_thread(func, *args, **kwargs),
                timeout=self.timeout_seconds
            )
    
    def run_with_timeout(self, func: Callable, *args, **kwargs) -> Any:
        """使用超时运行"""
        future = self.executor.submit(func, *args, **kwargs)
        try:
            return future.result(timeout=self.timeout_seconds)
        except FuturesTimeoutError:
            raise TimeoutError(f"Function {func.__name__} timed out after {self.timeout_seconds}s")
    
    def shutdown(self):
        """关闭线程池"""
        self.executor.shutdown(wait=True)


class ResourceMonitor:
    """资源监控"""
    
    def __init__(self, memory_limit_mb: int = 512):
        self.memory_limit_mb = memory_limit_mb
        self.start_memory = self.get_memory_usage()
    
    def get_memory_usage(self) -> int:
        """获取当前内存使用(MB)"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return 0
    
    def check_memory(self) -> bool:
        """检查内存是否超限"""
        current = self.get_memory_usage()
        if current > self.start_memory + self.memory_limit_mb:
            return False
        return True
    
    def get_memory_info(self) -> dict:
        """获取内存信息"""
        current = self.get_memory_usage()
        return {
            "current_mb": current,
            "limit_mb": self.start_memory + self.memory_limit_mb,
            "used_mb": current - self.start_memory,
            "safe": current < self.start_memory + self.memory_limit_mb
        }


class AutoGradeManager:
    """自动降级管理器"""
    
    def __init__(self):
        self.current_grade = "high"  # high, medium, low
        self.grades = {
            "high": {
                "max_concurrent": 8,
                "timeout": 60,
                "model": "gpt-4"
            },
            "medium": {
                "max_concurrent": 4,
                "timeout": 45,
                "model": "gpt-3.5-turbo"
            },
            "low": {
                "max_concurrent": 2,
                "timeout": 30,
                "model": "gpt-3.5-turbo"
            }
        }
    
    def should_downgrade(self, error: Exception, memory_safe: bool) -> bool:
        """判断是否应该降级"""
        if isinstance(error, (TimeoutError, asyncio.TimeoutError)):
            return True
        if not memory_safe:
            return True
        return False
    
    def downgrade(self):
        """降低等级"""
        if self.current_grade == "high":
            self.current_grade = "medium"
        elif self.current_grade == "medium":
            self.current_grade = "low"
        return self.get_current_config()
    
    def get_current_config(self) -> dict:
        """获取当前配置"""
        return self.grades[self.current_grade]


class ExceptionHandler:
    """异常处理器"""
    
    # 异常级别
    P0_CRITICAL = "P0"  # 系统崩溃
    P1_ERROR = "P1"      # 严重错误
    P2_WARNING = "P2"     # 警告
    P3_INFO = "P3"        # 信息
    
    def __init__(self):
        self.exception_log = []
    
    def classify_exception(self, error: Exception) -> str:
        """分类异常"""
        error_msg = str(error).lower()
        
        if "memory" in error_msg or "memoryerror" in error_msg:
            return self.P0_CRITICAL
        if "timeout" in error_msg:
            return self.P1_ERROR
        if "api" in error_msg or "rate limit" in error_msg:
            return self.P2_WARNING
        return self.P3_INFO
    
    def handle(self, error: Exception, context: dict) -> dict:
        """处理异常"""
        level = self.classify_exception(error)
        
        log_entry = {
            "level": level,
            "error": str(error),
            "context": context
        }
        self.exception_log.append(log_entry)
        
        return {
            "level": level,
            "should_retry": level in [self.P2_WARNING, self.P3_INFO],
            "should_rollback": level == self.P0_CRITICAL,
            "needs_human": level == self.P0_CRITICAL,
            "log_entry": log_entry
        }


class RetryManager:
    """重试管理器"""
    
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
    
    def should_retry(self, attempt: int, error: Exception) -> bool:
        """判断是否应该重试"""
        if attempt >= self.max_retries:
            return False
        
        error_msg = str(error).lower()
        
        # 可重试的错误
        retryable = [
            "timeout",
            "connection",
            "network",
            "rate limit",
            "temporary"
        ]
        
        return any(e in error_msg for e in retryable)
    
    def get_retry_delay(self, attempt: int) -> float:
        """计算重试延迟（指数退避）"""
        return min(2 ** attempt, 30)  # 最多30秒


# 全局实例
concurrency_manager = ConcurrencyManager()
resource_monitor = ResourceMonitor()
auto_grade_manager = AutoGradeManager()
exception_handler = ExceptionHandler()
retry_manager = RetryManager()
