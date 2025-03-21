import numpy as np
from scipy.io import wavfile
import os

# フォルダの作成
os.makedirs("physics_simulation", exist_ok=True)

def generate_collision_sound():
    """衝突音を生成する関数"""
    sample_rate = 44100
    duration = 0.2  # 0.2秒
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    
    # 単純な減衰するサイン波
    frequency = 440.0  # A4音
    note = np.sin(2 * np.pi * frequency * t) * np.exp(-t * 10)
    
    # 音量調整
    note = note * 0.3
    
    # 整数値に変換
    note = (note * 32767).astype(np.int16)
    
    # ファイル保存
    wavfile.write("physics_simulation/collision.wav", sample_rate, note)
    print("衝突音を生成しました: physics_simulation/collision.wav")

def generate_goal_sound():
    """ゴール音を生成する関数"""
    sample_rate = 44100
    duration = 1.0  # 1秒
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    
    # 上昇するチャープ音
    frequencies = np.linspace(220, 880, int(sample_rate * duration))
    note = np.sin(2 * np.pi * frequencies * t / sample_rate)
    
    # 音量調整と包絡線の適用
    envelope = np.exp(-t * 2)
    note = note * envelope * 0.5
    
    # 整数値に変換
    note = (note * 32767).astype(np.int16)
    
    # ファイル保存
    wavfile.write("physics_simulation/goal.wav", sample_rate, note)
    print("ゴール音を生成しました: physics_simulation/goal.wav")

def generate_bgm():
    """簡単なBGMを生成する関数"""
    sample_rate = 44100
    duration = 5.0  # 5秒間のループ
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    
    # 複数の周波数を合成
    notes = []
    
    # ベース音
    base_freq = 110  # A2音
    base_note = 0.3 * np.sin(2 * np.pi * base_freq * t)
    notes.append(base_note)
    
    # メロディー
    for i in range(5):
        freq = 220 * (1 + 0.33 * i)  # 倍音を使用
        amp = 0.2 / (i + 1)  # 振幅を徐々に小さく
        note = amp * np.sin(2 * np.pi * freq * t)
        # パルス関数で音にリズムを付ける
        rhythm = 0.5 + 0.5 * np.sin(2 * np.pi * 0.5 * t)  # 0.5Hzのリズム
        rhythm = (rhythm > 0).astype(float)
        note = note * rhythm
        notes.append(note)
    
    # 全ての音を合成
    audio = np.zeros_like(t)
    for note in notes:
        audio += note
    
    # クリッピングを防ぐためにスケーリング
    audio = audio / np.max(np.abs(audio)) * 0.8
    
    # 整数値に変換
    audio = (audio * 32767).astype(np.int16)
    
    # ファイル保存（WAV形式）
    wavfile.write("physics_simulation/bgm.wav", sample_rate, audio)
    print("BGMを生成しました: physics_simulation/bgm.wav")
    print("注意: MP3形式に変換するには追加のライブラリが必要です。現在はWAV形式で保存しています。")
    print("main.pyを編集して、BGMのファイル名を'bgm.wav'に変更してください。")

if __name__ == "__main__":
    generate_collision_sound()
    generate_goal_sound()
    generate_bgm()
    
    print("\n全てのサウンドファイルの生成が完了しました。")
    print("プログラムを実行するには、次のコマンドを実行してください:")
    print("python physics_simulation/main.py")
