from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random
import math

WIDTH = 600
HEIGHT = 900

def setup_projection():
    glViewport(0,0,WIDTH,HEIGHT)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0.0,WIDTH, 0.0,HEIGHT,0,1.0)
    glMatrixMode(GL_MODELVIEW)

def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    setup_projection()

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGBA)
    glutInitWindowSize(WIDTH, HEIGHT)
    glutInitWindowPosition(0,0)
    glutCreateWindow(b"catch the daimonds")
    glClearColor(0.0,0.0,0.0,1.0)


if __name__ == "__main__":
    main()