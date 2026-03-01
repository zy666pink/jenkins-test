#!/bin/bash
echo "===== 1. 环境检查 ====="
python3 --version  # 检查Python版本
echo "主机名：$(hostname)"

echo -e "\n===== 2. 代码测试 ====="
python3 test_hello.py  # 执行单元测试

echo -e "\n===== 3. 构建完成 ====="
echo "构建成功: hello, jenkins"
