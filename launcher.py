#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PyInstaller 打包入口。

不能用 __main__.py 直接打包: 它的相对导入在 exe(无包上下文)下会 ImportError。
本文件使用绝对导入, 兼顾 python -m 与 exe 两种启动方式。
"""

import sys

from campus_proxy_guard.cli import main

if __name__ == "__main__":
    sys.exit(main())
