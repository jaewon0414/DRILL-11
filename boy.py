from pico2d import load_image, get_time, SDL_KEYDOWN, SDLK_SPACE
from transitions import Machine


class Boy:
    def __init__(self):
        self.x, self.y = 400, 90
        self.frame = 0
        self.face_dir = 1
        self.image = load_image('animation_sheet.png')

        # IDLE 에 들어온 시각. 처음 시작 상태는 on_enter_IDLE 이 불리지 않으므로 여기서 직접 기록한다.
        self.idle_start_time = get_time()

        # IDLE --(5초 경과: time_out)--> SLEEP
        # SLEEP --(SPACE 누름: space_down)--> IDLE
        # ignore_invalid_triggers: IDLE 에서 SPACE 처럼 현재 상태에 없는 이벤트는 무시한다.
        self.machine = Machine(
            model=self,
            states=['IDLE', 'SLEEP'],
            transitions=[
                {'trigger': 'time_out', 'source': 'IDLE', 'dest': 'SLEEP'},
                {'trigger': 'space_down', 'source': 'SLEEP', 'dest': 'IDLE'},
            ],
            initial='IDLE',
            auto_transitions=False,
            ignore_invalid_triggers=True,
        )

    # Machine 이 IDLE 상태로 들어갈 때마다 자동으로 불러 준다(entry action).
    def on_enter_IDLE(self):
        self.idle_start_time = get_time()

    def handle_event(self, event):
        if event.type == SDL_KEYDOWN and event.key == SDLK_SPACE:
            self.space_down()

    def update(self):
        if self.state == 'IDLE':
            self.frame = (self.frame + 1) % 8
            if get_time() - self.idle_start_time > 5:
                self.time_out()
        elif self.state == 'SLEEP':
            self.frame = (self.frame + 1) % 8

    def draw(self):
        if self.state == 'IDLE':
            # animation_sheet.png 의 IDLE 줄: 오른쪽을 볼 때 bottom 300, 왼쪽을 볼 때 bottom 200
            if self.face_dir == 1:
                self.image.clip_draw(self.frame * 100, 300, 100, 100, self.x, self.y)
            else:
                self.image.clip_draw(self.frame * 100, 200, 100, 100, self.x, self.y)
        elif self.state == 'SLEEP':
            # IDLE 그림을 90도 돌려 눕힌다. 눕히면 몸이 떠 보이므로 땅 쪽으로 25 내려서 그린다.
            if self.face_dir == 1:
                self.image.clip_composite_draw(self.frame * 100, 300, 100, 100,
                                               3.141592 / 2, '', self.x, self.y - 25, 100, 100)
            else:
                self.image.clip_composite_draw(self.frame * 100, 200, 100, 100,
                                               -3.141592 / 2, '', self.x, self.y - 25, 100, 100)
