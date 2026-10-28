from pico2d import load_image, get_time, get_canvas_width, clamp
from pico2d import SDL_KEYDOWN, SDL_KEYUP, SDLK_SPACE, SDLK_LEFT, SDLK_RIGHT
from transitions import Machine


class Boy:
    def __init__(self):
        self.x, self.y = 400, 90
        self.frame = 0
        self.face_dir = 1
        self.image = load_image('animation_sheet.png')

        # 방향키가 눌려 있는지 기억해 두고, 달릴 방향(dir)을 계산한다. 오른쪽 1, 왼쪽 -1, 멈춤 0.
        self.left_pressed = False
        self.right_pressed = False
        self.dir = 0

        # IDLE 에 들어온 시각. 처음 시작 상태는 on_enter_IDLE 이 불리지 않으므로 여기서 직접 기록한다.
        self.idle_start_time = get_time()

        # IDLE --(5초 경과: time_out)--> SLEEP
        # SLEEP --(SPACE 누름: space_down)--> IDLE
        # IDLE, SLEEP --(방향키 누름: dir_down)--> RUN
        # RUN --(방향키 모두 뗌: dir_up)--> IDLE
        # ignore_invalid_triggers: IDLE 에서 SPACE 처럼 현재 상태에 없는 이벤트는 무시한다.
        self.machine = Machine(
            model=self,
            states=['IDLE', 'SLEEP', 'RUN'],
            transitions=[
                {'trigger': 'time_out', 'source': 'IDLE', 'dest': 'SLEEP'},
                {'trigger': 'space_down', 'source': 'SLEEP', 'dest': 'IDLE'},
                {'trigger': 'dir_down', 'source': ['IDLE', 'SLEEP'], 'dest': 'RUN'},
                {'trigger': 'dir_up', 'source': 'RUN', 'dest': 'IDLE'},
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
        elif event.type in (SDL_KEYDOWN, SDL_KEYUP) and event.key in (SDLK_LEFT, SDLK_RIGHT):
            pressed = event.type == SDL_KEYDOWN
            if event.key == SDLK_LEFT:
                self.left_pressed = pressed
            else:
                self.right_pressed = pressed
            self.dir = int(self.right_pressed) - int(self.left_pressed)

            # 왼쪽/오른쪽 모두 같은 이벤트로 처리한다. 방향은 self.dir 이 들고 있다.
            if self.dir != 0:
                self.dir_down()
            else:
                self.dir_up()

    def update(self):
        if self.state == 'IDLE':
            self.frame = (self.frame + 1) % 8
            if get_time() - self.idle_start_time > 5:
                self.time_out()
        elif self.state == 'SLEEP':
            self.frame = (self.frame + 1) % 8
        elif self.state == 'RUN':
            self.frame = (self.frame + 1) % 8
            self.face_dir = self.dir
            self.x += self.dir * 5
            # 그림 한 칸(100x100)의 절반인 50 만큼 안쪽까지만 가면 서 있든 달리든 누워 있든 화면 안에 다 보인다.
            self.x = clamp(50, self.x, get_canvas_width() - 50)

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
        elif self.state == 'RUN':
            # animation_sheet.png 의 RUN 줄: 오른쪽으로 달릴 때 bottom 100, 왼쪽으로 달릴 때 bottom 0
            if self.face_dir == 1:
                self.image.clip_draw(self.frame * 100, 100, 100, 100, self.x, self.y)
            else:
                self.image.clip_draw(self.frame * 100, 0, 100, 100, self.x, self.y)
