# -*- coding: utf-8 -*-
__author__ = 'LiYuanhe'

import sys
import os
import math
import copy
import shutil
import re
import time
import random

from Python_Lib.My_Lib import *

from OpenGLContext import testingcontext
BaseContext = testingcontext.getInteractive()
from OpenGL.GL import *
from OpenGL.arrays import vbo
from OpenGLContext.arrays import *
from OpenGL.GL import shaders

from OpenGLContext.scenegraph.basenodes import Sphere

class TestContext( BaseContext ):
    """Demonstrates use of attribute types in GLSL
    """
    def OnInit( self ):
        """Initialize the context"""
        """
            L_dir = (V_pos-L_pos)
            R = 2N*(dot( N, L_dir))-L_dir
            // Note: in eye-coordinate system, Eye_pos == (0,0,0)
            Spec_factor = pow( dot( R, V_pos-Eye_pos ), shininess)
        """
        """
            // note that in Eye coordinates, Eye_EC_dir == 0,0,-1
            H = normalize( Eye_EC_dir + Light_EC_dir )
            Spec_factor = pow( dot( H, N ), shininess )
        """
        phong_weightCalc = """
        vec2 phong_weightCalc(
            in vec3 light_pos, // light position
            in vec3 half_light, // half-way vector between light and view
            in vec3 frag_normal, // geometry normal
            in float shininess
        ) {
            // returns vec2( ambientMult, diffuseMult )
            float n_dot_pos = max( 0.0, dot(
                frag_normal, light_pos
            ));
            float n_dot_half = 0.0;
            if (n_dot_pos > -.05) {
                n_dot_half = pow(max(0.0,dot(
                    half_light, frag_normal
                )), shininess);
            }
            return vec2( n_dot_pos, n_dot_half);
        }
        """
        vertex = shaders.compileShader(
        """
        attribute vec3 Vertex_position;
        attribute vec3 Vertex_normal;
        varying vec3 baseNormal;
        void main() {
            gl_Position = gl_ModelViewProjectionMatrix * vec4(
                Vertex_position, 1.0
            );
            baseNormal = gl_NormalMatrix * normalize(Vertex_normal);
        }""", GL_VERTEX_SHADER)
        fragment = shaders.compileShader( phong_weightCalc + """
        uniform vec4 Global_ambient;
        uniform vec4 Light_ambient;
        uniform vec4 Light_diffuse;
        uniform vec4 Light_specular;
        uniform vec3 Light_location;
        uniform float Material_shininess;
        uniform vec4 Material_specular;
        uniform vec4 Material_ambient;
        uniform vec4 Material_diffuse;
        varying vec3 baseNormal;
        void main() {
            // normalized eye-coordinate Light location
            vec3 EC_Light_location = normalize(
                gl_NormalMatrix * Light_location
            );
            // half-vector calculation
            vec3 Light_half = normalize(
                EC_Light_location - vec3( 0,0,-1 )
            );
            vec2 weights = phong_weightCalc(
                EC_Light_location,
                Light_half,
                baseNormal,
                Material_shininess
            );
            gl_FragColor = clamp(
            (
                (Global_ambient * Material_ambient)
                + (Light_ambient * Material_ambient)
                + (Light_diffuse * Material_diffuse * weights.x)
                // material's shininess is the only change here...
                + (Light_specular * Material_specular * weights.y)
            ), 0.0, 1.0);
        }
        """, GL_FRAGMENT_SHADER)
        self.shader = shaders.compileProgram(vertex,fragment)
        self.coords,self.indices,self.count = Sphere(
            radius = 1
        ).compile()
        for uniform in (
            'Global_ambient',
            'Light_ambient','Light_diffuse','Light_location',
            'Light_specular',
            'Material_ambient','Material_diffuse',
            'Material_shininess','Material_specular',
        ):
            location = glGetUniformLocation( self.shader, uniform )
            if location in (None,-1):
                print 'Warning, no uniform: %s'%( uniform )
            setattr( self, uniform+ '_loc', location )
        for attribute in (
            'Vertex_position','Vertex_normal',
        ):
            location = glGetAttribLocation( self.shader, attribute )
            if location in (None,-1):
                print 'Warning, no attribute: %s'%( uniform )
            setattr( self, attribute+ '_loc', location )
    def Render( self, mode = None):
        """Render the geometry for the scene."""
        BaseContext.Render( self, mode )
        glUseProgram(self.shader)
        try:
            self.coords.bind()
            self.indices.bind()
            stride = self.coords.data[0].nbytes
            try:
                glUniform4f(self.Global_ambient_loc, .05, .05, .05, .1)
                glUniform4f(self.Light_ambient_loc, .1, .1, .1, 1.0)
                glUniform4f(self.Light_diffuse_loc, .25, .25, .25, 1)
            glUniform4f(self.Light_specular_loc, 0.0, 1.0, 0, 1)
            glUniform3f(self.Light_location_loc, 6, 2, 4)
            glUniform4f(self.Material_ambient_loc, .1, .1, .1, 1.0)
            glUniform4f(self.Material_diffuse_loc, .15, .15, .15, 1)
            glUniform4f(self.Material_specular_loc, 1.0, 1.0, 1.0, 1.0)
            glUniform1f(self.Material_shininess_loc, .95)
            glEnableVertexAttribArray(self.Vertex_position_loc)
            glEnableVertexAttribArray(self.Vertex_normal_loc)
            glVertexAttribPointer(
                self.Vertex_position_loc,
                3, GL_FLOAT, False, stride, self.coords
            )
            glVertexAttribPointer(
                self.Vertex_normal_loc,
                3, GL_FLOAT, False, stride, self.coords + (5 * 4)
            )
            glDrawElements(
                GL_TRIANGLES, self.count,
                GL_UNSIGNED_SHORT, self.indices
            )
            finally:
                self.coords.unbind()
                self.indices.unbind()
                glDisableVertexAttribArray( self.Vertex_position_loc )
                glDisableVertexAttribArray( self.Vertex_normal_loc )
        finally:
            glUseProgram( 0 )
if __name__ == "__main__":
    TestContext.ContextMainLoop()