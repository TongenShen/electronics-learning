# -*- coding: utf-8 -*-
"""
01 课：电阻与欧姆定律 —— 分压器

生成 5 张图：
  divider.asc             空载分压器（V1=12V，R1=R2=10k，中点应为 6V）+ .dc 扫描看线性
  divider_load_1k.asc     带载 RL=1k
  divider_load_10k.asc    带载 RL=10k
  divider_load_100k.asc   带载 RL=100k
  divider_load_step.asc   同一张图用 .step 扫三个负载值（在 GUI 里一次看三条曲线）

布局按约定：元件留白、引脚之间一律经过导线。
"""
import os
import sys

SCRIPTS = os.environ.get(
    "LTSPICE_BUILDER",
    os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "..", "..", "ltspice-schematic", "scripts")),
)
sys.path.insert(0, SCRIPTS)
from ltspice_builder import Schematic, SymbolLib  # noqa: E402

OUT_DIR = os.path.dirname(os.path.abspath(__file__))


def base_circuit(lib, sch):
    """公共部分：V1=12V、R1/R2=10k 串联分压、地轨"""
    v1 = sch.symbol(lib, "voltage", 160, 320, "R0", inst="V1", value="12")
    r1 = sch.symbol(lib, "res", 240, 160, "R0", inst="R1", value="10k")
    r2 = sch.symbol(lib, "res", 240, 320, "R0", inst="R2", value="10k")

    sch.wire(160, 336, 160, 176)      # V1+ 上引 -> 顶部横线
    sch.wire(160, 176, 256, 176)      # 顶部横线 -> R1 上端(A)
    sch.wire(256, 256, 256, 336)      # R1 下端(B) -> R2 上端(A)，中点即 out 节点

    sch.wire(160, 416, 160, 496)      # V1- 下引
    sch.wire(256, 416, 256, 496)      # R2 下端(B) 下引
    return v1, r1, r2


def build_divider():
    lib, sch = SymbolLib(), Schematic(1000, 800)
    base_circuit(lib, sch)

    sch.wire(256, 296, 400, 296)      # 中点引出去
    sch.label(400, 296, "out")

    sch.wire(160, 496, 256, 496)      # 地轨
    sch.ground(208, 496)

    sch.comment(448, 192, "no load: Vout = Vin * R2/(R1+R2)")
    sch.comment(448, 224, "            = 12 * 10k/20k = 6 V")
    sch.spice_text(448, 400, ".op")
    sch.spice_text(448, 436, ".meas op Vout FIND V(out)")
    sch.spice_text(448, 472, ".meas op I_V1 FIND I(V1)")
    return sch


def build_divider_dc():
    """同一张分压器，改用 .dc 扫描 Vin：在 GUI 里能看到 V(out) 随 Vin 线性变化"""
    lib, sch = SymbolLib(), Schematic(1000, 800)
    base_circuit(lib, sch)

    sch.wire(256, 296, 400, 296)
    sch.label(400, 296, "out")

    sch.wire(160, 496, 256, 496)
    sch.ground(208, 496)

    sch.comment(448, 192, "sweep Vin from 0 to 12V")
    sch.comment(448, 224, "V(out) is always Vin/2 (no load)")
    sch.spice_text(448, 400, ".dc V1 0 12 1")
    return sch


def build_load(rl, name_note):
    """带固定负载的分压器"""
    lib, sch = SymbolLib(), Schematic(1000, 800)
    base_circuit(lib, sch)

    rl = sch.symbol(lib, "res", 400, 336, "R0", inst="RL", value=rl)

    sch.wire(256, 296, 480, 296)      # 中点横线（同时引到 out 标签）
    sch.wire(416, 296, 416, 352)      # 分叉下去接 RL 上端(A)
    sch.label(480, 296, "out")

    sch.wire(416, 416, 416, 496)      # RL 下端(B) 下引
    sch.wire(160, 496, 416, 496)      # 地轨（三个接地点共用）
    sch.ground(208, 496)

    sch.comment(496, 192, "with load: Vout = Vin * (R2//RL)/(R1+R2//RL)")
    sch.comment(496, 224, name_note)
    sch.spice_text(496, 448, ".op")
    sch.spice_text(496, 484, ".meas op Vout FIND V(out)")
    return sch


def build_load_step():
    lib, sch = SymbolLib(), Schematic(1000, 800)
    base_circuit(lib, sch)

    sch.symbol(lib, "res", 400, 336, "R0", inst="RL", value="{RL}")

    sch.wire(256, 296, 480, 296)
    sch.wire(416, 296, 416, 352)
    sch.label(480, 296, "out")

    sch.wire(416, 416, 416, 496)
    sch.wire(160, 496, 416, 496)
    sch.ground(208, 496)

    sch.comment(496, 192, "sweep the load: one run, three curves")
    sch.comment(496, 224, "run this in the GUI and plot V(out)")
    sch.spice_text(496, 448, ".step param RL list 1k 10k 100k")
    sch.spice_text(496, 484, ".op")
    return sch


def main():
    jobs = [
        ("divider.asc", build_divider),
        ("divider_dc.asc", build_divider_dc),
        ("divider_load_1k.asc", lambda: build_load("1k", "RL = 1k  -> expect about 1.0 V")),
        ("divider_load_10k.asc", lambda: build_load("10k", "RL = 10k -> expect about 4.0 V")),
        ("divider_load_100k.asc", lambda: build_load("100k", "RL = 100k -> expect about 5.7 V")),
        ("divider_load_step.asc", build_load_step),
    ]
    for name, fn in jobs:
        path = os.path.join(OUT_DIR, name)
        fn().save(path)
        print("written :", name)


if __name__ == "__main__":
    main()
