import moderngl_window as mglw
from scene import Scene

class GraphicsEngine(mglw.WindowConfig):
    title = "Graphics Engine"
    resource_dir = 'G:\\Vineet_Ideas\\DAIO\\3D-Graphics-Engine\\resources'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.shader_programs = {
            'default': self.load_program(
                vertex_shader='shaders/default.vert',
                fragment_shader='shaders/default.frag',
            ),
            'skybox': self.load_program(
                vertex_shader='shaders/skybox.vert',
                fragment_shader='shaders/skybox.frag',
            ),
        }
        self.scene = Scene(self)

    def on_render(self, time: float, frame_time: float):
        """Handle the rendering logic"""
        self.scene.render()

    def on_resize(self, width: int, height: int):
        """Handle window resizing"""
        self.scene.resize(width, height)

if __name__ == "__main__":
    mglw.run_window_config(GraphicsEngine)
