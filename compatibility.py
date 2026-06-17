import sys
import types
import importlib

def apply_patches():
    # 1. Исправляем imghdr
    try:
        import imghdr
    except ImportError:
        m = types.ModuleType('imghdr')
        m.what = lambda file, h=None: 'png'
        sys.modules['imghdr'] = m

    # 2. Исправляем audioop
    try:
        import audioop
    except ImportError:
        # Если модуля реально нет (Python 3.13+), создаем заглушку
        m = types.ModuleType('audioop')
        # Добавляем основные функции, чтобы библиотеки не падали сразу
        m.getsample = m.max = m.avg = m.cross = m.rms = lambda *args, **kwargs: 0
        m.mul = lambda *args: b''
        m.lin2lin = lambda *args: args[0] # Просто возвращает данные без изменений
        sys.modules['audioop'] = m
    
    # 3. Исправляем pkg_resources для pymorphy2
    if 'pkg_resources' not in sys.modules or not hasattr(sys.modules['pkg_resources'], 'WorkingSet'):
        try:
            import pkg_resources
        except ImportError:
            m = types.ModuleType('pkg_resources')
            m.iter_entry_points = lambda *args, **kwargs: []
            m.get_distribution = lambda *args: types.SimpleNamespace(version='0.0.0')
            class WorkingSet:
                def __init__(self, *args, **kwargs): pass
                def __iter__(self): return iter([])
                def find(self, *args, **kwargs): return None
                def require(self, *args, **kwargs): return []
                def iter_entry_points(self, *args, **kwargs): return iter([])
            m.WorkingSet = WorkingSet
            sys.modules['pkg_resources'] = m

    # 4. Фикс для urllib3
    if 'urllib3.contrib.appengine' not in sys.modules:
        sys.modules['urllib3.contrib.appengine'] = types.ModuleType('appengine')

apply_patches()
print("Система совместимости адаптирована под ваше окружение")
