"""
RAG 检索效果对比测试脚本
运行方式：python evaluate_rag.py
"""
import time
from agents.document_processor import DocumentProcessor

# 初始化文档处理器，加载测试文档
doc_proc = DocumentProcessor()
result = doc_proc.save_document(
    "test.txt",
    "人工智能是计算机科学的一个分支。它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。该领域的研究包括机器人、语言识别、图像识别、自然语言处理和专家系统等。"
)
print(f"保存结果: {result}")

query = "什么是人工智能"

# 1. 基础检索（粗筛）
start = time.perf_counter()
basic_results = doc_proc.search_documents(query, k=3)
basic_time = (time.perf_counter() - start) * 1000  # 毫秒

# 2. 带Rerank的检索
start = time.perf_counter()
rerank_results = doc_proc.search_and_rerank(query, k=3)
rerank_time = (time.perf_counter() - start) * 1000  # 毫秒

print(f"\n查询: {query}")
print(f"基础检索耗时: {basic_time:.3f}ms, 结果数: {len(basic_results)}")
print(f"Rerank检索耗时: {rerank_time:.3f}ms, 结果数: {len(rerank_results)}")

if rerank_results:
    print(f"\nRerank后首位结果: {rerank_results[0][:100]}...")