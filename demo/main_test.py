from pytest import register_assert_rewrite
register_assert_rewrite(__name__)
print('hello?')

def not_a_test():
    print("broken")

def test_a():
    assert 5==5

def test_b():
    assert 6==5

copy_dict = dict(locals())
for func in copy_dict.values():
    try:
        if not func.__name__.startswith("test_"):
            continue
    except:
        continue

    print("running test:", func.__name__)
    func()
