# -*- coding: utf-8 -*-
"""데일리 브리핑 차트 생성기 (재사용 가능 / 스케줄 작업 전용)

사용법:
    python3 tools/generate_charts.py <data.json> <YYYY-MM-DD> <output_dir>

data.json 형식 (각 종목의 dates/prices 는 최근 약 6개월치 '일별 종가', 길이 동일):
{
  "headline": "커버에 넣을 한 줄 요약 문장",
  "holdings":      {"ORCL": {"name":"오라클","dates":["2025-11-21",...],"prices":[...]},
                    "MSFT": {"name":"마이크로소프트","dates":[...],"prices":[...]}},
  "bigtech_focus": {"NVDA": {"name":"엔비디아","dates":[...],"prices":[...]}},
  "space":         {"RKLB": {"name":"로켓랩","dates":[...],"prices":[...]},
                    "LUNR": {"name":"인튜이티브 머신스","dates":[...],"prices":[...]},
                    "ASTS": {"name":"AST 스페이스모바일","dates":[...],"prices":[...]}}
}

산출물: <output_dir>/<DATE>_holdings.png, _bigtech.png, _space.png, _cover.png
누락되었거나 데이터가 비어 있는 섹션은 조용히 건너뛴다(전체 작업은 계속).
"""
import sys, json, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.colors as mcolors
from datetime import datetime
try:
    import koreanize_matplotlib  # noqa: F401  (한글 폰트 등록)
except Exception:
    print("warn: koreanize_matplotlib 미설치 — 한글이 깨질 수 있습니다. "
          "pip install koreanize-matplotlib --break-system-packages")

INK, GRID, MUTE = "#1f2430", "#e7e9ef", "#8b909c"
PALETTE = ["#d64545", "#2f6fb3", "#e07b39", "#7a5cc7", "#159a8c", "#c2410c"]
plt.rcParams.update({"axes.edgecolor": "#d4d7de", "axes.labelcolor": INK,
                     "text.color": INK, "xtick.color": MUTE, "ytick.color": MUTE,
                     "font.size": 11})


def to_dates(strs):
    return [datetime.strptime(s[:10], "%Y-%m-%d") for s in strs]


def style_ax(ax):
    ax.grid(True, color=GRID, lw=0.9)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%y.%m"))
    ax.margins(x=0.02)


def heading(ax, title, sub):
    ax.text(0, 1.135, title, transform=ax.transAxes, fontsize=16, fontweight="bold")
    ax.text(0, 1.045, sub, transform=ax.transAxes, fontsize=10.3, color=MUTE)


def valid(sec):
    """{ticker: {...}} 중 dates/prices 가 정상인 항목만 반환."""
    out = {}
    for tk, v in (sec or {}).items():
        try:
            p = [float(x) for x in v.get("prices", [])]
            d = list(v.get("dates", []))
            if len(p) >= 2 and len(p) == len(d):
                out[tk] = {"name": v.get("name", tk), "dates": to_dates(d), "prices": np.array(p)}
        except Exception:
            continue
    return out


def chart_holdings(sec, date, out):
    items = list(valid(sec).items())
    if not items:
        return None
    n = len(items)
    fig, axes = plt.subplots(1, n, figsize=(6.3 * n, 5.3), squeeze=False)
    fig.patch.set_facecolor("white")
    fig.subplots_adjust(left=0.07, right=0.95, top=0.70, bottom=0.13, wspace=0.26)
    fig.text(0.07, 0.92, "내 보유 종목 · 최근 6개월 주가 흐름", fontsize=17, fontweight="bold")
    fig.text(0.07, 0.855, "보유 종목의 6개월 주가 흐름입니다 — 단위: USD", fontsize=10.8, color=MUTE)
    for i, (tk, v) in enumerate(items):
        ax = axes[0][i]
        c = PALETTE[i % len(PALETTE)]
        s, dts = v["prices"], v["dates"]
        ax.plot(dts, s, color=c, lw=2.3, zorder=5)
        ax.fill_between(dts, s, s.min() * 0.965, color=c, alpha=0.10, zorder=1)
        style_ax(ax)
        lo = int(np.argmin(s))
        ax.scatter([dts[lo]], [s[lo]], s=44, color=c, zorder=6, edgecolor="white", lw=1.4)
        ax.annotate(f"저점 ${s[lo]:,.0f}", (dts[lo], s[lo]), textcoords="offset points",
                    xytext=(8, -15), fontsize=9.5, color=MUTE)
        ax.scatter([dts[-1]], [s[-1]], s=72, color=c, zorder=7, edgecolor="white", lw=1.6)
        ax.annotate(f"  ${s[-1]:,.2f}", (dts[-1], s[-1]), textcoords="offset points",
                    xytext=(8, -3), fontsize=12, fontweight="bold", color=c)
        ax.text(0, 1.07, f"{v['name']}  {tk}", transform=ax.transAxes,
                fontsize=13.5, fontweight="bold", color=c)
    path = os.path.join(out, f"{date}_holdings.png")
    fig.savefig(path, dpi=170, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def chart_bigtech(sec, date, out):
    items = list(valid(sec).items())
    if not items:
        return None
    tk, v = items[0]
    s, dts = v["prices"], v["dates"]
    fig, ax = plt.subplots(figsize=(12.6, 5.5))
    fig.patch.set_facecolor("white")
    fig.subplots_adjust(left=0.07, right=0.93, top=0.80, bottom=0.12)
    NV = "#76b900"
    ax.plot(dts, s, color=NV, lw=2.6, zorder=5, label=f"{tk} 종가")
    ax.fill_between(dts, s, s.min() * 0.95, color=NV, alpha=0.12, zorder=1)
    if len(s) >= 50:
        ma = np.convolve(np.pad(s, (49, 0), mode="edge"), np.ones(50) / 50, mode="valid")
        ax.plot(dts, ma, color="#9aa0ac", lw=1.6, ls="--", zorder=4, label="50일 이동평균")
    style_ax(ax)
    hi = int(np.argmax(s))
    ax.scatter([dts[hi]], [s[hi]], s=56, color=NV, zorder=6, edgecolor="white", lw=1.5)
    ax.annotate(f"고점권 ${s[hi]:,.0f}", (dts[hi], s[hi]), textcoords="offset points",
                xytext=(-95, -4), fontsize=9.5, color=MUTE)
    ax.scatter([dts[-1]], [s[-1]], s=78, color=NV, zorder=7, edgecolor="white", lw=1.7)
    ax.annotate(f"  ${s[-1]:,.2f}", (dts[-1], s[-1]), textcoords="offset points",
                xytext=(8, -4), fontsize=12.5, fontweight="bold", color="#5c8f00")
    ax.legend(frameon=False, loc="upper left", fontsize=10, bbox_to_anchor=(0, 0.97))
    heading(ax, f"{v['name']} ({tk}) · 최근 6개월 주가 흐름", "빅테크 대표주의 6개월 주가 흐름 — 단위: USD")
    path = os.path.join(out, f"{date}_bigtech.png")
    fig.savefig(path, dpi=170, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def chart_space(sec, date, out):
    items = list(valid(sec).items())
    if not items:
        return None
    fig, ax = plt.subplots(figsize=(12.6, 5.6))
    fig.patch.set_facecolor("white")
    fig.subplots_adjust(left=0.07, right=0.93, top=0.80, bottom=0.12)
    ax.axhline(100, color="#c4c8d0", lw=1.2, ls=(0, (4, 3)), zorder=1)
    cols = ["#e07b39", "#7a5cc7", "#159a8c", "#d64545", "#2f6fb3"]
    for i, (tk, v) in enumerate(items):
        s, dts = v["prices"], v["dates"]
        norm = s / s[0] * 100
        c = cols[i % len(cols)]
        ax.plot(dts, norm, color=c, lw=2.5, zorder=5, label=f"{tk}  {v['name']}")
        ax.scatter([dts[-1]], [norm[-1]], s=62, color=c, zorder=7, edgecolor="white", lw=1.6)
        ax.annotate(f" {norm[-1]:,.0f}", (dts[-1], norm[-1]), textcoords="offset points",
                    xytext=(8, -3), fontsize=11.5, fontweight="bold", color=c)
    style_ax(ax)
    ax.set_ylabel("환산 지수")
    ax.legend(frameon=False, loc="upper left", fontsize=10.5, bbox_to_anchor=(0, 0.99))
    heading(ax, "우주 섹터 · 최근 6개월 수익률 비교",
            "6개월 전 투자금을 100으로 환산 (점선 = 원금 100)")
    path = os.path.join(out, f"{date}_space.png")
    fig.savefig(path, dpi=170, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def chart_cover(headline, date, out):
    fig = plt.figure(figsize=(15, 6))
    ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off")
    grad = np.linspace(0, 1, 400).reshape(-1, 1)
    ax.imshow(grad, extent=[0, 1, 0, 1], aspect="auto", origin="lower", zorder=0,
              cmap=mcolors.LinearSegmentedColormap.from_list("bg", ["#10172b", "#1d2b4d", "#24407a"]))
    rng = np.random.default_rng(7)
    gx = np.linspace(0, 1, 160)
    for base, alpha in [(0.20, 0.20), (0.34, 0.13), (0.10, 0.11)]:
        gy = base + np.cumsum(rng.normal(0, 1, 160)) * 0.0026
        ax.plot(gx, gy, color="#5b8bd0", lw=1.6, alpha=alpha, zorder=1)
    disp = date.replace("-", ". ")
    ax.add_patch(plt.Rectangle((0.062, 0.605), 0.072, 0.013, color="#5da9ff", zorder=3))
    ax.text(0.062, 0.70, "DAILY MARKET BRIEFING", color="#7fb0e8", fontsize=15,
            fontweight="bold", zorder=3)
    ax.text(0.06, 0.40, f"{disp}  데일리 브리핑", color="white", fontsize=43,
            fontweight="bold", zorder=3)
    ax.text(0.063, 0.255, "프리미엄 포맷  ·  빅테크 + 매크로 + 우주 섹터", color="#c5d4ec",
            fontsize=18, zorder=3)
    hl = (headline or "").strip()
    if len(hl) > 60:
        hl = hl[:58] + "…"
    ax.text(0.063, 0.115, hl, color="#8ea6c8", fontsize=12.5, style="italic", zorder=3)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    path = os.path.join(out, f"{date}_cover.png")
    fig.savefig(path, dpi=150, facecolor="#10172b")
    plt.close(fig)
    return path


def main():
    if len(sys.argv) < 4:
        print("usage: python3 generate_charts.py <data.json> <YYYY-MM-DD> <output_dir>")
        sys.exit(1)
    data = json.load(open(sys.argv[1], encoding="utf-8"))
    date, out = sys.argv[2], sys.argv[3]
    os.makedirs(out, exist_ok=True)
    made = []
    for fn, args in [(chart_holdings, data.get("holdings")),
                     (chart_bigtech, data.get("bigtech_focus")),
                     (chart_space, data.get("space"))]:
        try:
            p = fn(args, date, out)
            if p:
                made.append(p)
        except Exception as e:
            print(f"warn: {fn.__name__} 실패 — {e}")
    try:
        made.append(chart_cover(data.get("headline", ""), date, out))
    except Exception as e:
        print(f"warn: chart_cover 실패 — {e}")
    print("생성된 차트:")
    for p in made:
        print("  ", p, os.path.getsize(p), "bytes")


if __name__ == "__main__":
    main()
