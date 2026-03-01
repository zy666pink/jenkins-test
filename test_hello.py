# test_hello.py - 单元测试示例
def test_say_hello():
    # 函数内的代码缩进4个空格
    assert "hello" in "hello, jenkins", "测试失败：未包含hello"

if __name__ == "__main__":
    # 这个代码块内的所有代码都缩进4个空格（层级一致）
    test_say_hello()
    print("✅ 单元测试全部通过！")  # 缩进4个空格，和上一行test_say_hello()一致
    print("测试自动触发成功2")     # 同样缩进4个空格，层级统一
