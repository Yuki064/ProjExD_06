import math
import random
import sys
import time
from typing import Any, List, Sequence

import pygame as pg
from pygame.rect import Rect
from pygame.sprite import AbstractGroup, Sprite
from pygame.surface import Surface


WIDTH = 1600  # ゲームウィンドウの幅
HEIGHT = 900  # ゲームウィンドウの高さ


class Camera():
    """
    カメラに関するクラス
    """
    def __init__(self, center_pos: list[float] = [0, 0]) -> None:
        self.center_pos = center_pos


class Group_support_camera(pg.sprite.Group):
    """
    Surfaceをカメラ位置に同期して描画するためのグループクラス
    """
    def __init__(self, camera: Camera, *sprites: Sprite | Sequence[Sprite]) -> None:
        super().__init__(*sprites)
        self.camera = camera

    def draw(self, surface: Surface) -> List[Rect]:
        """
        グループ内にあるSpriteをカメラ位置に合わせて描画する関数
        引数1: 描画先のSurface
        """
        # カメラ位置だけSprite達をずらす
        for sprite in self.sprites():
            sprite.rect.move_ip(
                -self.camera.center_pos[0] + WIDTH / 2,
                -self.camera.center_pos[1] + HEIGHT / 2
            )

        # 描画
        rst = super().draw(surface)

        # 動かしたSprite達の位置を戻す
        for sprite in self.sprites():
            sprite.rect.move_ip(
                self.camera.center_pos[0] - WIDTH / 2,
                self.camera.center_pos[1] - HEIGHT / 2
            )

        return rst


class Character(pg.sprite.Sprite):
    """
    PlayerやEnemyなどの基底クラス
    """
    def __init__(self, image: Surface, position: tuple[int, int], hp: int, max_invincible_tick=0) -> None:
        """
        キャラクタSurfaceを生成
        引数1: キャラの基本画像
        引数2: スポーン位置
        引数3: 体力
        引数4: ダメージを受けた際に無敵になるフレーム数（任意）
        """
        super().__init__()
        self.hp = hp
        self.max_invincible_tick = max_invincible_tick
        self.invincible_tmr = -1
        self._imgs: dict[int, list[Surface, (int | None)]] = {}
        self.set_image(image, 0)
        self.rect = image.get_rect()
        self.rect.center = position
    
    def set_image(self, image: Surface, priority: int, valid_time: int | None = None):
        """
        キャラの画像を切り替える関数
        引数1: 画像
        引数2: 画像の優先度。数値が高いほど優先して表示される。（ダメージを受けた際に数秒間だけ基本画像から変更したいときに便利）
        引数3: 画像を描画する期間（Noneで無期限になります）
        """
        self._imgs[priority] = [image, valid_time]

    def give_damage(self, damage: int) -> int:
        """
        キャラにダメージを与える関数
        引数1: ダメージ
        戻り値: 減った後のHP
        """
        if self.invincible_tmr <= 0:
            self.hp -= damage
            self.invincible_tmr = self.max_invincible_tick
            self.damaged()
        if self.hp <= 0:
            self.kill()
        return self.hp

    def damaged(self):
        """
        キャラにダメージを与えられた際に呼ばれる関数。
        """
        pass

    def update(self):
        # 無敵時間を減らす処理
        self.invincible_tmr = max(self.invincible_tmr - 1, -1)

        # 表示する画像周りの処理
        if len(self._imgs) > 0:
            # 優先度が最も高い画像を描画
            idx = max(self._imgs)
            self.image = self._imgs[idx][0]
            # 画像の有効時間を減らす処理
            if self._imgs[idx][1] != None:
                if self._imgs[idx][1] < 0:
                    del self._imgs[idx]
                    return
                self._imgs[idx][1] -= 1


def calc_orientation(org: pg.Rect, dst: pg.Rect) -> tuple[float, float]:
    """
    orgから見てdstがどこにあるかを計算し方向ベクトルを返す関数
    引数1 org:Rect
    引数2 dst:Rect
    戻り値:orgから見たdstの方向ベクトルを表すタプル
    """
    x_diff, y_diff = dst.centerx - org.centerx, dst.centery - org.centery
    norm = math.sqrt(x_diff ** 2 + y_diff ** 2)
    return x_diff / norm, y_diff / norm


def calc_norm(org: pg.Rect, dst: pg.Rect) -> float:
    """
    orgとdstとの間の距離を返す関数
    引数1 org:Rect
    引数2 dst:Rect
    戻り値:距離
    """
    x_diff, y_diff = dst.centerx - org.centerx, dst.centery - org.centery
    return math.sqrt(x_diff ** 2 + y_diff ** 2)


class Player(Character):
    """
    Playerに関するクラス
    """

    # Playerの画像の表示倍率
    IMAGE_SCALE = 1.2

    delta = {  # 押下キーと移動量の辞書
        pg.K_w: (0, -1),
        pg.K_s: (0, +1),
        pg.K_a: (-1, 0),
        pg.K_d: (+1, 0),
    }

    def __init__(self, xy: list[int, int], hp=50, max_invincible_tick=50):
        """
        Playerを生成
        引数1: スポーン位置
        引数2: hp(任意)
        引数3: ダメージを受けた際の無敵時間（任意）
        """
        img0 = pg.transform.rotozoom(
            pg.image.load(f"ex04/fig/3.png"), 0, self.IMAGE_SCALE)
        img = pg.transform.flip(img0, True, False)
        self.move_imgs = {
            (+1, 0): img,  # 右
            (+1, -1): pg.transform.rotozoom(img, 45, 1.0),  # 右上
            (0, -1): pg.transform.rotozoom(img, 90, 1.0),  # 上
            (-1, -1): pg.transform.rotozoom(img0, -45, 1.0),  # 左上
            (-1, 0): img0,  # 左
            (-1, +1): pg.transform.rotozoom(img0, 45, 1.0),  # 左下
            (0, +1): pg.transform.rotozoom(img, -90, 1.0),  # 下
            (+1, +1): pg.transform.rotozoom(img, -45, 1.0),  # 右下
        }
        self.dire = (1, 0)

        super().__init__(self.move_imgs[self.dire], xy ,hp, max_invincible_tick)
        self.speed = 10

    def change_img(self, num: int, priority: int, life: int | None = None):
        """
        Player画像を設定する関数
        引数1: num：Player画像ファイル名の番号
        引数2: 画像の優先度
        引数3: 表示する期間（Noneで無期限）
        """
        self.set_image(pg.transform.rotozoom(pg.image.load(f"ex04/fig/{num}.png"), 0, self.IMAGE_SCALE), priority, life)

    def damaged(self):
        """
        Playerがダメージを受けたときに実行される関数
        """
        super().damaged()

        # 数秒間だけ専用画像に切り替える
        self.change_img(8, 5, 20)

    def update(self, key_lst: list[bool]):
        """
        押下キーに応じてPlayerを移動させる
        引数1: key_lst：押下キーの真理値リスト
        """
        super().update()
        sum_mv = [0, 0]
        for k, mv in Player.delta.items():
            if key_lst[k]:
                self.rect.move_ip(+self.speed*mv[0], +self.speed*mv[1])
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.dire = tuple(sum_mv)
            self.set_image(self.move_imgs[self.dire], 0)

    def get_direction(self) -> tuple[int, int]:
        """
        Playerの向いている向きを返す関数
        戻り値: 方向ベクトル
        """
        return self.dire

    def kill(self) -> None:
        pass


class Bullet(pg.sprite.Sprite):
    """
    弾に関するクラス
    """

    # 銃弾が消えるまでの時間
    MAX_LIFE_TICK = 250

    def __init__(self, position: tuple[int, int], direction: tuple[float, float]):
        """
        銃弾Surfaceを生成する
        引数1: スポーン位置
        引数2: 飛ばす方向
        """
        super().__init__()
        self.vx, self.vy = direction
        self.image = pg.Surface((20, 10))
        self.rect = self.image.get_rect()
        pg.draw.rect(self.image, (255, 0, 0), self.rect)
        angle = math.degrees(math.atan2(-self.vy, self.vx))
        self.image = pg.transform.rotozoom(self.image, angle, 1)
        self.rect.center = position
        self.speed = 20
        self.life_tmr = 0

    def update(self):
        """
        銃弾を移動させる
        """
        self.rect.move_ip(self.speed * self.vx, self.speed * self.vy)
        if self.life_tmr > self.MAX_LIFE_TICK:
            self.kill()
        self.life_tmr += 1


class Enemy(Character):
    """
    敵に関するクラス
    """
    def __init__(self, hp: int, spawn_point: list[int, int], attack_target: Character):
        """
        敵を生成する関数
        引数3: 攻撃を加える対象
        """
        super().__init__(pg.image.load(f"EX04/fig/alien1.png"), spawn_point, hp)
        self.speed = 5
        self.attack_target = attack_target

    def update(self):
        """
        敵を移動させる関数
        """
        super().update()

        # 攻撃対象に近づき過ぎたら止まる（0割り対策）
        if calc_norm(self.rect, self.attack_target.rect) < 50:
            return
        dir = list(calc_orientation(self.rect, self.attack_target.rect))
        self.rect.move_ip(dir[0] * self.speed, dir[1] * self.speed)


class Background(pg.sprite.Sprite):
    """
    背景に関するクラス
    """
    def __init__(self, camera: Camera, offset: tuple[int, int]) -> None:
        """
        背景を生成する関数
        引数1: カメラ
        引数2: 背景のデフォルト生成位置からどれだけずらすか
        """
        super().__init__()
        self.image = pg.image.load("ex05/fig/background.png")
        self.rect = self.image.get_rect()
        self.rect.topleft = (0, 0)
        self.offset = offset
        self.camera = camera

    def update(self) -> None:
        """
        カメラの位置に合わせて背景を動かす関数
        """
        super().update()
        x_offset = self.offset[0]
        if self.camera.center_pos[0] != 0:
            x_offset += self.camera.center_pos[0] // self.rect.width
        y_offset = self.offset[1]
        if self.camera.center_pos[1] != 0:
            y_offset += self.camera.center_pos[1] // self.rect.height
        self.rect.topleft = (x_offset * self.rect.width,
                             y_offset * self.rect.height)


def main():
    pg.display.set_caption("サバイブ")
    screen = pg.display.set_mode((WIDTH, HEIGHT))

    # 様々な変数の初期化
    camera = Camera([0, 0])
    background = Group_support_camera(camera)
    for i in range(-2, 3):
        for j in range(-1, 2):
            background.add(Background(camera, (i, j)))
    player = Player([0, 0])
    player_group = Group_support_camera(camera, player)
    bullets = Group_support_camera(camera)
    enemies = Group_support_camera(camera)
    tmr = 0
    clock = pg.time.Clock()

    while True:
        key_lst = pg.key.get_pressed()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return 0

        # 数秒おきに敵をスポーンさせる処理
        if tmr % 30 == 0:
            # カメラ中心位置から何pxか離れた位置に敵をスポーン
            angle = random.randint(0, 360)
            spawn_dir = [
                math.cos(math.radians(angle)),
                -math.sin(math.radians(angle))
            ]
            enemies.add(Enemy(
                20,
                [camera.center_pos[0] + (spawn_dir[0] * 1000),
                     camera.center_pos[1] + (spawn_dir[1] * 1000)],
                player)
            )

        # 敵と銃弾の当たり判定処理
        for enemy in pg.sprite.groupcollide(enemies, bullets, False, True).keys():
            enemy.give_damage(10)

        # 敵とプレイヤーの当たり判定処理
        for _ in pg.sprite.spritecollide(player, enemies, False):
            player.give_damage(10)

        # 背景の更新＆描画処理
        background.update()
        background.draw(screen)

        # ゲームオーバー処理
        # TODO: この位置にゲームオーバーがあるのは何となく微妙なので書き直す
        if player.hp <= 0:
            player.change_img(8, 10, 250)
            player.update(key_lst)
            player_group.draw(screen)
            pg.display.update()
            time.sleep(2)
            return
        
        # プレイヤー更新処理
        player.update(key_lst)
        # カメラをプレイヤーに追従させる処理
        camera.center_pos[0] = player.rect.centerx
        camera.center_pos[1] = player.rect.centery

        # 数秒おきにマウス方向に銃弾を飛ばす
        if tmr % 5 == 0:
            mouse_pos = list(pg.mouse.get_pos())
            mouse_pos[0] -= WIDTH / 2
            mouse_pos[1] -= HEIGHT / 2
            # TODO: 処理の無駄が多いのでこの辺を書き直す
            image = pg.Surface((200, 200))
            rect = image.get_rect()
            rect.center = (mouse_pos[0] + camera.center_pos[0], mouse_pos[1] + camera.center_pos[1])
            bullets.add(Bullet(player.rect.center, calc_orientation(player.rect, rect)))

        # 銃弾の更新処理
        bullets.update()
        # 敵の更新処理
        enemies.update()

        # 描画周りの処理
        player_group.draw(screen)
        bullets.draw(screen)
        enemies.draw(screen)
        pg.display.update()

        # タイマー
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
