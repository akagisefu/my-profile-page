# 物理演算シミュレーション

Pygameを使用した物理ベースのブロック反射シミュレーション

## 主な機能

- 複数のカラーブロックの物理運動シミュレーション
- 3種類の動的障害物（移動壁/振動壁/巡回壁）
- ゴール到達判定システム
- マルチビデオ生成機能
- BGMと効果音の再生
- OpenCVを使った動画出力

## 動作要件

- Python 3.8+
- Pygame 2.0+
- OpenCV 4.2+（動画出力機能使用時）
- FFmpeg（音声付き動画出力使用時）

## 関数設計書

### 主要関数一覧

| 関数名 | 引数 | 戻り値 | 概要 |
|--------|------|--------|------|
| `initialize_pygame` | なし | なし | Pygameの初期化と音声設定 |
| `create_obstacles` | margin | obstaclesリスト | 障害物設定の生成 |
| `setup_map` | なし | (margin, box_rect, goal_rect) | マップ基本要素の初期化 |
| `Block.update` | box_rect, goal_rect, blocks, moving_wall_y | bool（ゴール到達時True） | ブロックの位置・衝突判定更新 |
| `main` | record, block_count | video_filename | メインゲームループ実行 |
| `run_multiple_simulations` | count, record | video_filesリスト | 複数シミュレーション実行 |

### 障害物タイプ仕様

```python
{
    'type': 'horizontal_moving',  # 水平移動壁
    'position': (x, y),           # 初期位置
    'color': (R, G, B),           # 表示色
    'velocity': (dx, dy),         # 移動速度
    'move_range': (min, max),     # 移動範囲
    'thickness': int,             # 壁の太さ
    'sound': 'filepath'           # 衝突音
}
```

## 使用方法

```bash
# 基本実行（1動画生成）
python main.py

# 複数動画生成（例：3個）
python main.py --count 3

# 動画出力無効
python main.py --no-video
```

## ファイル構成

```
physics_simulation/
├── main.py            # メインプログラム
├── config.py          # 設定パラメータ
├── assets/            # リソースファイル
│   ├── sounds/        # 効果音
│   └── bgm/           # BGM
└── videos/            # 生成動画保存先
```
