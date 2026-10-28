from pico2d import load_image
from transitions import Machine


class Boy:
    def __init__(self):
        self.x, self.y = 400, 90
        self.frame = 0
        self.face_dir = 1
        self.image = load_image('animation_sheet.png')

        # 지금은 IDLE 상태 하나만 갖는다.
        # Machine 이 self.state 에 현재 상태 이름('IDLE')을 넣어 준다.
        self.machine = Machine(
            model=self,
            states=['IDLE'],
            initial='IDLE',
            auto_transitions=False,
        )

    def update(self):
        if self.state == 'IDLE':
            self.frame = (self.frame + 1) % 8

    def draw(self):
        if self.state == 'IDLE':
            # animation_sheet.png 의 IDLE 줄: 오른쪽을 볼 때 bottom 300, 왼쪽을 볼 때 bottom 200
            if self.face_dir == 1:
                self.image.clip_draw(self.frame * 100, 300, 100, 100, self.x, self.y)
            else:
                self.image.clip_draw(self.frame * 100, 200, 100, 100, self.x, self.y)
