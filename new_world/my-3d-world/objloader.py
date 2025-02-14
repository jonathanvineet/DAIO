import numpy as np

class Obj:
    def __init__(self, filename):
        self.vertices = []
        self.normals = []
        self.load_obj(filename)

    def load_obj(self, filename):
        with open(filename, 'r') as file:
            for line in file:
                if line.startswith('v '):  # Vertex position
                    values = line.split()[1:]
                    self.vertices.append([float(v) for v in values])
                elif line.startswith('vn'):  # Vertex normal
                    values = line.split()[1:]
                    self.normals.append([float(v) for v in values])
                # Skip faces, as they are not needed for loading the model vertices and normals

        # Fill normals with default values if not available
        while len(self.normals) < len(self.vertices):
            self.normals.append([0.0, 0.0, 1.0])  # Default normal facing forward

        # Convert to numpy arrays
        self.vertices = np.array(self.vertices, dtype=np.float32)
        self.normals = np.array(self.normals, dtype=np.float32)

        # Create the VBOs (Vertex Buffer Objects)
        self.vbo = self.create_vbo()

    def create_vbo(self):
        data = np.hstack([self.vertices, self.normals])
        return data
