import pygame
import math
import numpy as np
import config

class Renderer:
    """
    描画を担当するクラス
    ゲームの視覚的要素をすべて管理
    """
    def __init__(self):
        """レンダラーを初期化"""
        pygame.font.init()
        
        # フォントの初期化
        try:
            self.font = pygame.font.SysFont("Arial", 24)
            self.large_font = pygame.font.SysFont("Arial", 36)
            self.small_font = pygame.font.SysFont("Arial", 18)
        except:
            self.font = pygame.font.Font(None, 24)
            self.large_font = pygame.font.Font(None, 36)
            self.small_font = pygame.font.Font(None, 18)
        
        # 背景要素（レイヤー式）
        self.create_background_layers()
    
    def create_background_layers(self):
        """背景の複数レイヤーを作成（奥行き表現）"""
        # 背景色のグラデーション
        self.bg_color_top = (30, 30, 50)  # 暗い青
        self.bg_color_bottom = (10, 10, 20)  # より暗い青
        
        # 星の生成（遠景）
        self.stars = []
        for _ in range(200):
            x = random.randint(0, config.WIDTH)
            y = random.randint(0, config.COURSE_LENGTH)
            size = random.randint(1, 3)
            brightness = random.randint(100, 255)
            color = (brightness, brightness, brightness)
            blink_speed = random.random() * 0.1
            self.stars.append({
                'pos': (x, y),
                'size': size,
                'color': color,
                'blink_speed': blink_speed,
                'blink_offset': random.random() * math.pi * 2
            })
        
        # 雲のような背景オブジェクト（中景）
        self.clouds = []
        for _ in range(30):
            x = random.randint(0, config.WIDTH)
            y = random.randint(0, config.COURSE_LENGTH)
            width = random.randint(100, 300)
            height = random.randint(50, 150)
            alpha = random.randint(5, 20)  # 透明度（低め）
            self.clouds.append({
                'pos': (x, y),
                'size': (width, height),
                'alpha': alpha
            })
    
    def draw_background(self, screen, camera_y):
        """
        背景を描画
        
        Args:
            screen (pygame.Surface): 描画対象の画面
            camera_y (int): カメラのY位置オフセット
        """
        # 背景色のグラデーション（画面全体）
        for y in range(0, config.HEIGHT, 2):
            ratio = y / config.HEIGHT
            color = [
                int(self.bg_color_top[i] * (1 - ratio) + self.bg_color_bottom[i] * ratio)
                for i in range(3)
            ]
            pygame.draw.line(screen, color, (0, y), (config.WIDTH, y))
        
        # 星の描画（遠景）
        current_time = pygame.time.get_ticks() / 1000.0
        for star in self.stars:
            # カメラ位置に応じてゆっくり動く（視差効果）
            star_y = star['pos'][1] - camera_y * 0.2
            star_y %= config.COURSE_LENGTH
            
            # 画面内にある場合のみ描画
            if 0 <= star_y <= config.HEIGHT:
                # 点滅効果
                blink = (math.sin(current_time * star['blink_speed'] + star['blink_offset']) + 1) / 2
                color = tuple(int(c * (0.5 + 0.5 * blink)) for c in star['color'])
                
                pygame.draw.circle(
                    screen, 
                    color, 
                    (star['pos'][0], star_y), 
                    star['size']
                )
        
        # 雲の描画（中景）
        for cloud in self.clouds:
            # カメラ位置に応じて中程度の速度で動く（視差効果）
            cloud_y = cloud['pos'][1] - camera_y * 0.5
            cloud_y %= config.COURSE_LENGTH
            
            # 画面内に近い場合のみ描画
            if -cloud['size'][1] <= cloud_y <= config.HEIGHT + cloud['size'][1]:
                # 半透明の雲を描画
                s = pygame.Surface(cloud['size'], pygame.SRCALPHA)
                s.fill((255, 255, 255, cloud['alpha']))
                screen.blit(s, (cloud['pos'][0] - cloud['size'][0] / 2, cloud_y - cloud['size'][1] / 2))
    
    def draw_marbles(self, screen, marbles, camera_y):
        """
        マーブルを描画
        
        Args:
            screen (pygame.Surface): 描画対象の画面
            marbles (list): マーブルのリスト
            camera_y (int): カメラのY位置オフセット
        """
        # 各マーブルを描画
        for marble in marbles:
            marble.draw(screen, camera_y)
    
    def draw_course(self, screen, course, camera_y):
        """
        コースを描画
        
        Args:
            screen (pygame.Surface): 描画対象の画面
            course (Course): コースオブジェクト
            camera_y (int): カメラのY位置オフセット
        """
        course.draw(screen, camera_y)
    
    def draw_ui(self, screen, marbles, race_time, camera_y, race_state):
        """
        UI要素（スコア、時間など）を描画
        
        Args:
            screen (pygame.Surface): 描画対象の画面
            marbles (list): マーブルのリスト
            race_time (float): レース時間（秒）
            camera_y (int): カメラのY位置オフセット
            race_state (int): レースの状態
        """
        # レース時間
        time_text = f"Time: {race_time:.2f}s"
        time_surface = self.font.render(time_text, True, config.WHITE)
        screen.blit(time_surface, (20, 20))
        
        # マーブルの位置情報（順位など）
        # Y座標に基づいてマーブルをソート（下にあるものが先頭）
        sorted_marbles = sorted(marbles, key=lambda m: m.body.position.y)
        
        # 順位表を描画（右上）
        for i, marble in enumerate(sorted_marbles):
            position = i + 1
            name = f"{marble.color_name} marble"
            position_text = f"{position}. {name}"
            
            # ゴールしたマーブルには時間を表示
            if marble.finished:
                position_text += f" - {marble.finish_time:.2f}s"
            
            text_color = marble.color
            position_surface = self.font.render(position_text, True, text_color)
            screen.blit(position_surface, (config.WIDTH - position_surface.get_width() - 20, 20 + i * 30))
        
        # 全体マップ（小さな俯瞰図、右下に配置）
        self.draw_minimap(screen, marbles, camera_y, race_state)
        
        # レース状態に応じたメッセージ
        if race_state == config.STATE_READY:
            self.draw_centered_message(screen, "Ready to Race!", 100)
        elif race_state == config.STATE_FINISHED:
            self.draw_centered_message(screen, "Race Finished!", 100)
            
            # 結果発表（中央）
            winner = next((m for m in sorted_marbles if m.finished), None)
            if winner:
                winner_text = f"Winner: {winner.color_name} marble ({winner.finish_time:.2f}s)"
                self.draw_centered_message(screen, winner_text, 150)
    
    def draw_minimap(self, screen, marbles, camera_y, race_state):
        """
        ミニマップ（全体俯瞰図）を描画
        
        Args:
            screen (pygame.Surface): 描画対象の画面
            marbles (list): マーブルのリスト
            camera_y (int): カメラのY位置オフセット
            race_state (int): レースの状態
        """
        # ミニマップの位置とサイズ
        map_width = 100
        map_height = 200
        map_x = config.WIDTH - map_width - 20
        map_y = config.HEIGHT - map_height - 20
        
        # ミニマップの背景
        pygame.draw.rect(screen, (20, 20, 30), (map_x, map_y, map_width, map_height))
        pygame.draw.rect(screen, (50, 50, 70), (map_x, map_y, map_width, map_height), 2)
        
        # コースの長さに対する比率
        ratio = map_height / config.COURSE_LENGTH
        
        # 現在の表示領域を示す長方形
        view_y = camera_y * ratio
        view_height = config.HEIGHT * ratio
        pygame.draw.rect(
            screen, 
            (100, 100, 120, 100), 
            (map_x, map_y + view_y, map_width, view_height),
            1
        )
        
        # マーブルの位置をプロット
        for marble in marbles:
            marble_y = marble.body.position.y * ratio
            pygame.draw.circle(
                screen,
                marble.color,
                (map_x + map_width // 2, map_y + marble_y),
                3
            )
        
        # ゴールラインを表示
        goal_y = (config.COURSE_LENGTH - 200) * ratio
        pygame.draw.line(
            screen,
            (255, 215, 0),  # 金色
            (map_x, map_y + goal_y),
            (map_x + map_width, map_y + goal_y),
            2
        )
    
    def draw_centered_message(self, screen, message, y_pos):
        """
        中央に大きなメッセージを表示
        
        Args:
            screen (pygame.Surface): 描画対象の画面
            message (str): 表示するメッセージ
            y_pos (int): Y座標位置
        """
        msg_surface = self.large_font.render(message, True, config.WHITE)
        msg_rect = msg_surface.get_rect(center=(config.WIDTH // 2, y_pos))
        screen.blit(msg_surface, msg_rect)
    
    def draw_intro(self, screen, marbles, stage):
        """
        イントロ画面を描画
        
        Args:
            screen (pygame.Surface): 描画対象の画面
            marbles (list): マーブルのリスト
            stage (int): イントロのステージ
        """
        # 背景を黒くする
        screen.fill((0, 0, 0))
        
        # ステージに応じて異なる表示
        if stage == 0:
            # Title
            title = self.large_font.render("Marble Race", True, config.WHITE)
            title_rect = title.get_rect(center=(config.WIDTH // 2, config.HEIGHT // 3))
            screen.blit(title, title_rect)
            
            # Subtitle
            subtitle = self.font.render("Race with 4 Colored Marbles", True, config.WHITE)
            subtitle_rect = subtitle.get_rect(center=(config.WIDTH // 2, config.HEIGHT // 3 + 50))
            screen.blit(subtitle, subtitle_rect)
            
            # "Press SPACE to start"
            start_text = self.font.render("Press SPACE to start", True, config.WHITE)
            start_rect = start_text.get_rect(center=(config.WIDTH // 2, config.HEIGHT * 2 // 3))
            screen.blit(start_text, start_rect)
            
        elif stage == 1:
            # Marble introduction
            intro_text = self.large_font.render("Today's Contestants", True, config.WHITE)
            intro_rect = intro_text.get_rect(center=(config.WIDTH // 2, 100))
            screen.blit(intro_text, intro_rect)
            
            # 各マーブルを表示
            for i, marble in enumerate(marbles):
                # 位置
                x = config.WIDTH // 5 * (i + 1)
                y = config.HEIGHT // 2
                
                # マーブル描画
                pygame.draw.circle(screen, marble.color, (x, y), marble.radius * 2)
                
                # 名前
                name_text = self.font.render(marble.color_name, True, marble.color)
                name_rect = name_text.get_rect(center=(x, y + marble.radius * 3))
                screen.blit(name_text, name_rect)
            
            # Get ready message
            ready_text = self.font.render("Get ready...", True, config.WHITE)
            ready_rect = ready_text.get_rect(center=(config.WIDTH // 2, config.HEIGHT - 100))
            screen.blit(ready_text, ready_rect)
    
    def draw_countdown(self, screen, count):
        """
        カウントダウンを描画
        
        Args:
            screen (pygame.Surface): 描画対象の画面
            count (int): カウントダウン数値
        """
        # 大きいフォントでカウントダウンを表示
        count_font = pygame.font.SysFont("Arial", 150)
        count_text = count_font.render(str(count), True, (255, 255, 255))
        count_rect = count_text.get_rect(center=(config.WIDTH // 2, config.HEIGHT // 2))
        
        # 光彩効果（周りに輪郭を描く）
        glow_color = (255, 255, 0)  # 黄色い光彩
        for offset in range(1, 5):
            glow_text = count_font.render(str(count), True, glow_color)
            glow_rect = glow_text.get_rect(center=(
                config.WIDTH // 2 + offset, 
                config.HEIGHT // 2
            ))
            screen.blit(glow_text, glow_rect)
            
            glow_rect = glow_text.get_rect(center=(
                config.WIDTH // 2, 
                config.HEIGHT // 2 + offset
            ))
            screen.blit(glow_text, glow_rect)
            
            glow_rect = glow_text.get_rect(center=(
                config.WIDTH // 2 - offset,
                config.HEIGHT // 2
            ))
            screen.blit(glow_text, glow_rect)
            
            glow_rect = glow_text.get_rect(center=(
                config.WIDTH // 2, 
                config.HEIGHT // 2 - offset
            ))
            screen.blit(glow_text, glow_rect)
        
        # メインのテキストを描画
        screen.blit(count_text, count_rect)

# 背景生成用（ランダム要素）
import random
