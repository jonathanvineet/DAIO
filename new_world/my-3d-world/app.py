import pywavefront
import pygame
from pygame.locals import QUIT
import OpenGL.GL as gl
import OpenGL.GLUT as glut
import OpenGL.GLU as glu

# Initialize Pygame
pygame.init()

# Set up the window for OpenGL rendering
screen = pygame.display.set_mode((800, 600), pygame.DOUBLEBUF | pygame.OPENGL)
glut.glutInit()

# Load the .obj file (including the .mtl)
scene = pywavefront.Wavefront('E:/Vineet_Ideas/DAIO//new_world/objects/letter/letter_w.obj', collect_faces=True)

# Function to set up the OpenGL environment
def setup_opengl():
    gl.glClearColor(0.0, 0.0, 0.0, 1.0)
    gl.glEnable(gl.GL_DEPTH_TEST)
    glu.gluPerspective(45, (800/600), 0.1, 50.0)
    gl.glTranslatef(0.0, 0.0, -5)

# Function to render the loaded scene
def render_scene():
    for name, mesh in scene.meshes.items():
        # Debugging the structure of the mesh
        print(f"Mesh Name: {name}")
        print(f"Mesh Data: {dir(mesh)}")  # Print the attributes of the mesh
        print(f"Mesh Faces: {mesh.faces}")

        for face in mesh.faces:
            gl.glBegin(gl.GL_TRIANGLES)
            for vertex_i in face:
                print(f"Vertex Index: {vertex_i}")
                try:
                    vertex = mesh.vertices[vertex_i]  # Use mesh.vertices to access vertex data
                    gl.glVertex3f(vertex[0], vertex[1], vertex[2])  # Render the vertex
                except Exception as e:
                    print(f"Error accessing vertex {vertex_i}: {e}")
            gl.glEnd()

# Main render loop
running = True
setup_opengl()
while running:
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False

    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
    render_scene()
    pygame.display.flip()

pygame.quit()
