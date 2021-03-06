# Cristopher Jose Rodolfo Barrios Solis 18207
# lab3

from Utilidades.utils import *
from Utilidades.sphere import Sphere
from Utilidades.math import norm, V3, dot, mul, sum, reflect, sub, length, refract
from math import tan, pi

MAX_RECURSION_DEPTH = 3


class Raytracer(object):
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.background_color = Color(54, 69, 79)
        self.scene = []
        self.light = None
        self.clear()

    def clear(self):
        self.pixels = [
            [self.background_color for x in range(self.width)]
            for y in range(self.height)
        ]

    def write(self, filename):
        writebmp(filename, self.width, self.height, self.pixels)

    def finish(self, filename="final.bmp"):
        self.write(filename)

    def point(self, x, y, c=None):
        try:
            self.pixels[y][x] = c or self.current_color
        except:
            pass

    def cast_ray(self, orig, direction, recursion=0):
        material, intersect = self.scene_intersect(orig, direction)

        if (
            material is None or recursion >= MAX_RECURSION_DEPTH
        ):  
            return self.background_color

        offset_normal = mul(intersect.normal, 1.1)

        if material.albedo[2] > 0:
            reverse_direction = mul(direction, -1)
            reflect_dir = reflect(reverse_direction, intersect.normal)
            reflect_orig = (
                sub(intersect.point, offset_normal)
                if dot(reflect_dir, intersect.normal) < 0
                else sum(intersect.point, offset_normal)
            )
            reflect_color = self.cast_ray(reflect_orig, reflect_dir, recursion + 1)
        else:
            reflect_color = Color(0, 0, 0)

        if material.albedo[3] > 0:
            refract_dir = refract(
                direction, intersect.normal, material.refractive_index
            )
            refract_orig = (
                sub(intersect.point, offset_normal)
                if dot(refract_dir, intersect.normal) < 0
                else sum(intersect.point, offset_normal)
            )
            refract_color = self.cast_ray(refract_orig, refract_dir, recursion + 1)
        else:
            refract_color = Color(0, 0, 0)

        light_dir = norm(sub(self.light.position, intersect.point))
        light_distance = length(sub(self.light.position, intersect.point))

        shadow_orig = (
            sub(intersect.point, offset_normal)
            if dot(light_dir, intersect.normal) < 0
            else sum(intersect.point, offset_normal)
        )
        shadow_material, shadow_intersect = self.scene_intersect(shadow_orig, light_dir)
        shadow_intensity = 0

        if (
            shadow_material
            and length(sub(shadow_intersect.point, shadow_orig)) < light_distance
        ):
            shadow_intensity = 0.9

        intensity = (
            self.light.intensity
            * max(0, dot(light_dir, intersect.normal))
            * (1 - shadow_intensity)
        )

        reflection = reflect(light_dir, intersect.normal)
        specular_intensity = self.light.intensity * (
            max(0, -dot(reflection, direction)) ** material.spec
        )

        diffuse = material.diffuse * intensity * material.albedo[0]
        specular = Color(255, 255, 255) * specular_intensity * material.albedo[1]
        reflection = reflect_color * material.albedo[2]
        refraction = refract_color * material.albedo[3]

        return diffuse + specular + reflection + refraction

    def scene_intersect(self, orig, direction):
        zbuffer = float("inf")

        material = None
        intersect = None

        for obj in self.scene:
            hit = obj.ray_intersect(orig, direction)
            if hit is not None:
                if hit.distance < zbuffer:
                    zbuffer = hit.distance
                    material = obj.material
                    intersect = hit

        return material, intersect

    def render_stereogram(self):
        print("Compilando...")
        fov = int(pi / 2)
        for y in range(self.height):
            for x in range(self.width):
                i = (
                    (2 * (x + 0.5) / self.width - 1)
                    * tan(fov / 2)
                    * self.width
                    / self.height
                )
                j = (2 * (y + 0.5) / self.height - 1) * tan(fov / 2)
                direction = norm(V3(i, j, -1))

                first_offset = self.cast_ray(V3(0.25, 0.5, 0), direction)
                first_camera = (first_offset / 2 + Color(100, 0, 0)) if first_offset != self.background_color else first_offset

                second_offset = self.cast_ray(V3(-0.25, 0.5, 0), direction)
                second_camera = (second_offset / 2 + Color(0, 0, 100)) if second_offset != self.background_color else second_offset

                camera_offset = first_camera + second_camera
                self.pixels[y][x] = camera_offset
