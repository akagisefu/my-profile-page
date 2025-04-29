import pygame
import cv2
import numpy as np
import os
import time
from datetime import datetime
import config

# Check if OpenCV is available
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    print("警告: OpenCVが見つかりません。ビデオ出力が無効になっています。")
    print("OpenCVをインストールするには: pip install opencv-python")

class VideoExporter:
    """
    ビデオ出力を管理するクラス
    シミュレーションのフレームをキャプチャし、動画ファイルとして保存
    """
    def __init__(self, width=config.WIDTH, height=config.HEIGHT, fps=config.VIDEO_FPS,
                 filename_prefix=config.VIDEO_FILENAME_PREFIX, output_dir=config.VIDEO_DIR,
                 bitrate=config.VIDEO_BITRATE):
        """
        VideoExporterを初期化
        
        Args:
            width (int): ビデオの幅
            height (int): ビデオの高さ
            fps (int): フレームレート
            filename_prefix (str): 出力ファイル名のプレフィックス
            output_dir (str): 出力ディレクトリ
            bitrate (str): ビットレート（例: "8000k"）
        """
        if not OPENCV_AVAILABLE or not config.RECORD_VIDEO:
            self.video_writer = None
            self.enabled = False
            print("ビデオ出力は無効です（OpenCVが見つからないか、RECORD_VIDEO=False）。")
            return

        self.enabled = True
        self.width = width
        self.height = height
        self.fps = fps
        self.bitrate = bitrate
        
        # フレームカウンター（処理フレーム数）
        self.frame_count = 0
        
        # FPS計測用（実行時間計測）
        self.start_time = time.time()
        self.processing_fps = 0
        
        # 出力ディレクトリの作成（存在しなければ）
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.output_path = os.path.join(script_dir, output_dir)
        os.makedirs(self.output_path, exist_ok=True)

        # タイムスタンプ付きのファイル名を生成
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.filename = os.path.join(
            self.output_path, 
            f"{filename_prefix}_{timestamp}.mp4"
        )

        # コーデックの設定とVideoWriterの作成
        # 'mp4v'はMP4ファイル用のコーデック
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        try:
            self.video_writer = cv2.VideoWriter(
                self.filename, 
                fourcc, 
                self.fps, 
                (self.width, self.height)
            )
            
            if not self.video_writer.isOpened():
                raise IOError(f"'{self.filename}'のVideoWriterを開けませんでした")
            
            print(f"ビデオ録画有効。保存先: {self.filename}")
            print(f"解像度: {self.width}x{self.height}, FPS: {self.fps}, ビットレート: {self.bitrate}")
        except Exception as e:
            print(f"VideoWriter初期化エラー: {e}")
            self.video_writer = None
            self.enabled = False

    def capture_frame(self, surface):
        """
        Pygameサーフェスからフレームをキャプチャし、動画に書き込む
        
        Args:
            surface (pygame.Surface): キャプチャするPygameサーフェス
        """
        if not self.enabled or self.video_writer is None:
            return

        try:
            # Pygameサーフェスからピクセルデータを取得
            frame_data = pygame.surfarray.array3d(surface)
            
            # Pygameは(width, height, channels)、OpenCVは(height, width, channels)の順
            # PygameはRGB、OpenCVはBGRを使用
            frame_data = frame_data.swapaxes(0, 1)  # 幅と高さを入れ替え
            frame_data = cv2.cvtColor(frame_data, cv2.COLOR_RGB2BGR)  # RGBからBGRへ変換

            # 動画に書き込み
            self.video_writer.write(frame_data)
            
            # フレームカウンターをインクリメント
            self.frame_count += 1
            
            # 10フレームごとに実際のFPSを計算
            if self.frame_count % 10 == 0:
                elapsed_time = time.time() - self.start_time
                if elapsed_time > 0:
                    self.processing_fps = self.frame_count / elapsed_time
        except Exception as e:
            print(f"フレームキャプチャエラー: {e}")
            # エラー時にはこれ以上の録画を無効にするオプション
            # self.enabled = False
            # self.finalize()

    def finalize(self):
        """VideoWriterオブジェクトを解放"""
        if self.enabled and self.video_writer is not None:
            print(f"ビデオ出力の終了処理中: {self.filename}")
            
            # FFmpegでビットレートを調整する場合のコマンド例（OpenCVでは直接指定できない）
            # この部分は実装環境によって異なる場合があります
            try:
                self.video_writer.release()
                print("VideoWriter解放完了")
                
                # ビットレートを調整するために二次処理（オプション）
                if self.bitrate and os.path.exists(self.filename):
                    temp_file = self.filename + ".temp.mp4"
                    ffmpeg_cmd = f'ffmpeg -i "{self.filename}" -b:v {self.bitrate} "{temp_file}" -y'
                    
                    print(f"FFmpegでビットレート調整中: {self.bitrate}")
                    result = os.system(ffmpeg_cmd)
                    
                    if result == 0 and os.path.exists(temp_file):
                        os.remove(self.filename)
                        os.rename(temp_file, self.filename)
                        print(f"ビットレート調整完了: {self.bitrate}")
                    else:
                        print("ビットレート調整失敗。元のファイルを保持します。")
            except Exception as e:
                print(f"ビデオ終了処理エラー: {e}")
            
            # 処理統計の表示
            if self.frame_count > 0:
                elapsed_time = time.time() - self.start_time
                avg_fps = self.frame_count / elapsed_time if elapsed_time > 0 else 0
                print(f"処理フレーム数: {self.frame_count}")
                print(f"処理時間: {elapsed_time:.2f}秒")
                print(f"平均処理FPS: {avg_fps:.2f}")
            
            self.video_writer = None  # 再利用されないようにする
            print("ビデオ出力完了。")
        
        self.enabled = False  # 終了処理されたとマーク

class AudioManager:
    """
    サウンド効果と音楽を管理するクラス
    """
    def __init__(self):
        """AudioManagerを初期化"""
        # pygame.mixerが初期化されていない場合は初期化
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        
        # 効果音と音楽のボリューム
        self.sound_volume = 0.5  # 0.0〜1.0
        self.music_volume = 0.3  # 0.0〜1.0
        
        # 効果音の辞書
        self.sounds = {}
        
        # 効果音のプリロード
        self.preload_sounds()
        
        # 音楽のパス（実際のファイルが存在する場合）
        self.bgm_path = os.path.join("assets", "bgm", "race_bgm.mp3")
    
    def preload_sounds(self):
        """よく使う効果音をプリロード"""
        # 効果音のパスとキーの辞書（実際のファイルが存在する場合）
        sound_files = {
            "collision": os.path.join("assets", "sounds", "collision.wav"),
            "start": os.path.join("assets", "sounds", "start.wav"),
            "goal": os.path.join("assets", "sounds", "goal.wav"),
            "count": os.path.join("assets", "sounds", "count.wav")
        }
        
        # 各効果音をロード
        for key, file_path in sound_files.items():
            try:
                if os.path.exists(file_path):
                    self.sounds[key] = pygame.mixer.Sound(file_path)
                    self.sounds[key].set_volume(self.sound_volume)
            except Exception as e:
                print(f"効果音ロードエラー '{key}': {e}")
    
    def play_sound(self, sound_key):
        """
        効果音を再生
        
        Args:
            sound_key (str): 再生する効果音のキー
        """
        if sound_key in self.sounds:
            try:
                self.sounds[sound_key].play()
            except Exception as e:
                print(f"効果音再生エラー '{sound_key}': {e}")
    
    def play_music(self):
        """BGMを再生（ループあり）"""
        try:
            if os.path.exists(self.bgm_path):
                pygame.mixer.music.load(self.bgm_path)
                pygame.mixer.music.set_volume(self.music_volume)
                pygame.mixer.music.play(-1)  # -1はループ再生
        except Exception as e:
            print(f"BGM再生エラー: {e}")
    
    def stop_music(self):
        """BGMを停止"""
        try:
            pygame.mixer.music.stop()
        except Exception as e:
            print(f"BGM停止エラー: {e}")
    
    def set_sound_volume(self, volume):
        """
        効果音のボリュームを設定
        
        Args:
            volume (float): 0.0〜1.0のボリューム値
        """
        self.sound_volume = max(0.0, min(1.0, volume))
        for sound in self.sounds.values():
            sound.set_volume(self.sound_volume)
    
    def set_music_volume(self, volume):
        """
        BGM音量を設定
        
        Args:
            volume (float): 0.0〜1.0のボリューム値
        """
        self.music_volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.music_volume)
