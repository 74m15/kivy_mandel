# -*- coding: utf-8 -*-
"""
Created on Wed May 26 15:59:01 2021

@author: CAPUANO-P
"""

import kivy

from array import array
from functools import lru_cache, partial
from math import log
from threading import Thread
from time import time

from kivy.app import App
from kivy.clock import Clock
from kivy.graphics.texture import Texture

class MandelApp(App):
    
    def __init__(self):
        super(MandelApp, self).__init__()
        
        self.rendering = False
    
    def get_application_config(self):
        """
            Method overriden to skip file .ini read/write (dynamic configuration))
        """
        return None
    
    def build_config(self, config):
        config.setdefaults("mandel", { 
                "max_iter" : 255, 
                "min_c_real" : -2.0,
                "min_c_imag" : -1.25,
                "z_size" : 2.50
            })
        config.setdefaults("render", { 
                "mandel_color" : "(0,0,0)", 
                "algorithm" : "smooth"
            })
        
    def build_settings(self, settings):
        settings.add_json_panel("Mandel", self.config, data=\
            """[
                    {
                        "type" : "title",
                        "title" : "Mandel"
                    },
                    {
                        "type" : "numeric",
                        "title" : "Max number of iterations",
                        "section" : "mandel",
                        "key" : "max_iter"
                    },
                    {
                        "type" : "numeric",
                        "title" : "min(c) - real part",
                        "section" : "mandel",
                        "key" : "min_c_real"
                    },
                    {
                        "type" : "numeric",
                        "title" : "min(c) - imaginary part",
                        "section" : "mandel",
                        "key" : "min_c_imag"
                    },
                    {
                        "type" : "numeric",
                        "title" : "delta z - width of image",
                        "section" : "mandel",
                        "key" : "z_size"
                    },
                    {
                        "type" : "title",
                        "title" : "Render"
                    },
                    {
                        "type" : "string",
                        "title" : "RGB color of Mandelbrot set",
                        "section" : "render",
                        "key" : "mandel_color"
                    },
                    {
                        "type" : "options",
                        "title" : "Rendering Algorithm",
                        "section" : "render",
                        "key" : "algorithm",
                        "options" : [ "smooth", "log" ]
                    }
                ]""")
        
    def on_render_start(self, *args, **kwargs):
        if not self.rendering:
            print("Start rendering!")
            
            self.image = self.root.ids["image"]
            self.texture = Texture.create(size=self.image.size)
            self.start_time = time()
            
            size = self.image.size[0] * self.image.size[1] * 3
            buf = [255 for x in range(size)]
            self.array = array('B', buf)

            self.scheduler = Clock.schedule_interval(self.on_timer, 1/20.0)
            
            self.rendering = True
            self.renderer = Thread(target=self.render_mandel)
            self.renderer.start()
        else:
            print("Still rendering")
        
        return True
    
    def on_render_stop(self, *args, **kwargs):
        if self.rendering:
            print("Stop rendering!")
            
            self.scheduler.cancel()
            self.rendering = False
            self.renderer.join()
        else:
            print("Not rendering")
        
        return True
    
    def render_mandel(self):
        
        def mandel(c, max_iter=255):
            z = c
            
            for i in range(max_iter):
                z = z*z + c
                
                if abs(z) > 2:
                    return i
            
            return max_iter
        
        def get_mandel_color_algorithm(config):
            
            def _smooth(iter, max_iter, mandel_color):
                if iter == max_iter:
                    return mandel_color
                else:
                    return (
                            abs(255 - iter), 
                            abs(255 - iter * 4) % 256, 
                            abs(255 - iter * 8) % 256
                        )
            
            def _log(iter, max_iter, mandel_color):
                if iter == max_iter:
                    return mandel_color
                else:
                    return (
                            min(255, int(255 * log(iter+1)/log(max_iter))), 
                            min(255, int(255 * log(iter+1)/log(max_iter))),
                            min(255, int(255 * log(iter+1)/log(max_iter)))
                        )
            
            def _fallback(iter, max_iter, mandel_color):
                return mandel_color
            
            mandel_color = eval(config.get("render", "mandel_color"))
            
            if "smooth" == config.get("render", "algorithm"):
                return lru_cache(maxsize=max_iter)(partial(_smooth, mandel_color=mandel_color))
            elif "log" == config.get("render", "algorithm"):
                return lru_cache(maxsize=max_iter)(partial(_log, mandel_color=mandel_color))
            else:
               return lru_cache(maxsize=max_iter)(partial(_fallback, mandel_color=mandel_color))
        
        min_c_real = float(self.config.get("mandel", "min_c_real"))
        min_c_imag = float(self.config.get("mandel", "min_c_imag"))
        z_size = float(self.config.get("mandel", "z_size"))
        max_iter = int(self.config.get("mandel", "max_iter"))
        
        get_mandel_color = get_mandel_color_algorithm(self.config)
        
        for y in range(self.image.height):
            for x in range(self.image.width):
                if not self.rendering:
                    print(f"Aborting rendering at x={x}, y={y}")
                    return
                
                c = complex(min_c_real + z_size * x / self.image.width, min_c_imag + z_size * y / self.image.height)
                iter = mandel(c, max_iter=max_iter)
                color = get_mandel_color(iter, max_iter)
                
                self.array[3 * (x + y * self.image.width) + 0] = color[0]
                self.array[3 * (x + y * self.image.width) + 1] = color[1]
                self.array[3 * (x + y * self.image.width) + 2] = color[2]
    
        self.rendering = False
        print(f"Rendering complete! time spent: {time() - self.start_time:5.3g}")
    
    def on_timer(self, *args, **kwargs):
        self.texture.blit_buffer(self.array, colorfmt='rgb', bufferfmt='ubyte')
        self.image.texture = self.texture

        self.image.canvas.ask_update()
        
        return self.rendering


if __name__ == '__main__':
    MandelApp().run()