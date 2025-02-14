import numpy as np
from pywavefront import Wavefront

class LetterA:
    def __init__(self, app):
        self.app = app
        self.ctx = app.ctx
        self.program = app.load_program(vertex_shader='shaders/default.vert', fragment_shader='shaders/default.frag')
        self.vbo, self.vao = self.load_letter_a()

    def load_letter_a(self):
        obj = Wavefront('objects/Letters/a.obj', create_materials=True, collect_faces=True)
        vertices = np.array(obj.materials[list(obj.materials.keys())[0]].vertices, dtype='f4')

        vbo = self.ctx.buffer(vertices)
        vao = self.ctx.vertex_array(self.program, [(vbo, '3f', 'in_position')])
        return vbo, vao

    def render(self):
        self.vao.render()
